import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from risk_analysis_agent import RiskAnalysisInput, analyze_risks


def run(input_path: str) -> dict:
    source = Path(input_path)
    payload = json.loads(source.read_text(encoding="utf-8"))
    if "risk_analysis_input" in payload:
        payload = payload["risk_analysis_input"]
    validated = RiskAnalysisInput.model_validate(payload).model_dump()
    result, telemetry = analyze_risks(validated)
    report = {
        "run_timestamp": datetime.now(timezone.utc).isoformat(),
        "input": validated,
        "result": result,
        "telemetry": telemetry,
    }
    out = Path("reports") / f"risk_analysis_{validated['issue_key']}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


def main():
    parser = argparse.ArgumentParser(description="Run Risk Analysis Agent from a READY handoff artifact")
    parser.add_argument("input_path")
    args = parser.parse_args()
    run(args.input_path)


if __name__ == "__main__":
    main()
