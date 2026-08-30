import argparse
import json
import os
import sys
from pathlib import Path

from anthropic import Anthropic


EXPECTED_FIELDS = (
    "correctness",
    "groundedness",
    "hallucination",
    "constraint_adherence",
)


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_json_text(text: str):
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return json.loads(text.strip())


def evaluate_case(client, model, system_prompt, rubric, case):
    prompt = (
        f"Q:{case['query']}\n"
        f"X:{case['expected_behavior']}\n"
        f"E:{case['retrieved_context']}\n"
        f"A:{case['actual_answer']}\n"
        'JSON:{"correctness":true,"groundedness":true,"hallucination":false,'
        '"constraint_adherence":true,"context_coverage":100,'
        '"context_sufficient":true,"reason":null}'
    )

    response = client.messages.create(
        model=model,
        max_tokens=220,
        thinking={"type": "disabled"},
        system=f"{system_prompt}\n\n{rubric}",
        messages=[{"role": "user", "content": prompt}],
    )

    text = "".join(
        block.text for block in response.content if block.type == "text"
    ).strip()
    result = normalize_json_text(text)
    return result, response


def run_calibration(root: Path, dataset_path: Path, output_path: Path):
    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        raise RuntimeError("LLM_API_KEY is required for Judge calibration")

    config = load_json(root / "config" / "judge_config.json")
    system_prompt = load_text(root / "config" / "judge_prompt.txt")
    rubric = load_text(root / "config" / "judge_rubric.txt")
    dataset = load_json(dataset_path)

    model = config["primary_model"]
    client = Anthropic(api_key=api_key, max_retries=2)

    case_results = []
    total_fields = 0
    matching_fields = 0
    false_passes = 0
    false_fails = 0
    input_tokens = 0
    output_tokens = 0

    for case in dataset:
        actual, response = evaluate_case(
            client, model, system_prompt, rubric, case
        )
        expected = case["expected"]
        field_results = {}

        for field in EXPECTED_FIELDS:
            exp = bool(expected[field])
            got = bool(actual.get(field))
            match = exp == got
            field_results[field] = {
                "expected": exp,
                "actual": got,
                "match": match,
            }
            total_fields += 1
            matching_fields += int(match)

        expected_case_pass = all(
            expected[field] for field in ("correctness", "groundedness", "constraint_adherence")
        ) and not expected["hallucination"]
        actual_case_pass = all(
            bool(actual.get(field)) for field in ("correctness", "groundedness", "constraint_adherence")
        ) and not bool(actual.get("hallucination"))

        if actual_case_pass and not expected_case_pass:
            false_passes += 1
        if expected_case_pass and not actual_case_pass:
            false_fails += 1

        usage = response.usage
        input_tokens += int(getattr(usage, "input_tokens", 0) or 0)
        output_tokens += int(getattr(usage, "output_tokens", 0) or 0)

        case_results.append(
            {
                "id": case["id"],
                "field_results": field_results,
                "expected_case_pass": expected_case_pass,
                "actual_case_pass": actual_case_pass,
                "reason": actual.get("reason"),
            }
        )

    agreement = matching_fields / total_fields if total_fields else 0.0
    summary = {
        "configuration": {
            "model": model,
            "prompt_version": config.get("prompt_version"),
            "rubric_version": config.get("rubric_version"),
        },
        "cases": len(dataset),
        "agreement": round(agreement, 4),
        "matching_fields": matching_fields,
        "total_fields": total_fields,
        "false_passes": false_passes,
        "false_fails": false_fails,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "case_results": case_results,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


def compare_results(old_path: Path, new_path: Path, min_agreement: float, max_drop: float):
    old = load_json(old_path)
    new = load_json(new_path)

    delta = new["agreement"] - old["agreement"]

    print("Judge Calibration — OLD vs NEW")
    print("--------------------------------")
    print(f"OLD config: {old['configuration']}")
    print(f"NEW config: {new['configuration']}")
    print(f"OLD human agreement: {old['agreement']:.2%}")
    print(f"NEW human agreement: {new['agreement']:.2%}")
    print(f"Delta: {delta:+.2%}")
    print(f"OLD false passes/fails: {old['false_passes']}/{old['false_fails']}")
    print(f"NEW false passes/fails: {new['false_passes']}/{new['false_fails']}")

    failures = []
    if new["agreement"] < min_agreement:
        failures.append(
            f"NEW agreement {new['agreement']:.2%} is below minimum {min_agreement:.2%}"
        )
    if delta < -max_drop:
        failures.append(
            f"Agreement dropped {abs(delta):.2%}, exceeding allowed drop {max_drop:.2%}"
        )
    if new["false_passes"] > old["false_passes"]:
        failures.append("NEW Judge introduced additional false PASS verdicts")

    if failures:
        print("\nRESULT: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nRESULT: PASS")
    return 0


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--root", required=True)
    run_parser.add_argument("--dataset", required=True)
    run_parser.add_argument("--output", required=True)

    compare_parser = subparsers.add_parser("compare")
    compare_parser.add_argument("--old", required=True)
    compare_parser.add_argument("--new", required=True)
    compare_parser.add_argument("--min-agreement", type=float, default=0.90)
    compare_parser.add_argument("--max-drop", type=float, default=0.05)

    args = parser.parse_args()

    if args.command == "run":
        run_calibration(Path(args.root), Path(args.dataset), Path(args.output))
        return 0

    return compare_results(
        Path(args.old), Path(args.new), args.min_agreement, args.max_drop
    )


if __name__ == "__main__":
    sys.exit(main())
