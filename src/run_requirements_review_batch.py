import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import httpx

from jira_requirements import load_requirement
from requirement_precheck import parse_issue_keys, precheck_requirement, validate_issue_key
from requirements_review_agent import PROMPT_PATH, review_requirement
from requirements_review_cache import (
    build_review_payload,
    content_hash,
    get_cached_review,
    load_cache,
    put_cached_review,
    save_cache,
)


def _write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _is_true(name: str) -> bool:
    return (os.getenv(name) or "").strip().lower() in {"1", "true", "yes", "on"}


def _clarification_gaps(review: dict) -> list[dict]:
    if review.get("decision") != "NEEDS_CLARIFICATION":
        return []
    return [gap for gap in review.get("gaps", []) if gap.get("gap_type") == "BLOCKING_GAP"]


def _safe_rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round((numerator / denominator) * 100, 1)


def _batch_quality_metrics(issues: list[dict]) -> dict:
    eligible = sum(1 for item in issues if item.get("precheck") == "ELIGIBLE")
    cached = sum(1 for item in issues if item.get("cache_hit") is True)
    llm_attempted = sum(
        1
        for item in issues
        if item.get("precheck") == "ELIGIBLE" and item.get("cache_hit") is not True
    )
    ready = sum(1 for item in issues if item.get("decision") == "READY")
    needs_clarification = sum(1 for item in issues if item.get("decision") == "NEEDS_CLARIFICATION")

    return {
        "eligible": eligible,
        "ready": ready,
        "needs_clarification": needs_clarification,
        "cache_hits": cached,
        "llm_attempted": llm_attempted,
        "cache_hit_rate_pct": _safe_rate(cached, eligible),
        "llm_execution_rate_pct": _safe_rate(llm_attempted, eligible),
        "avoided_llm_calls": cached,
    }


def _append_github_summary(batch: dict):
    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return

    totals = batch["totals"]
    quality = batch["quality_metrics"]
    lines = [
        "## Requirements Review Batch",
        "",
        f"**Run ID:** `{batch['run_id']}`  ",
        f"**Force review:** {'yes' if batch['force_review'] else 'no'}",
        "",
        "### Batch quality and execution",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Requested | {totals['requested']} |",
        f"| Eligible after pre-check | {quality['eligible']} |",
        f"| Rejected before LLM | {totals['rejected']} |",
        f"| READY | {quality['ready']} |",
        f"| NEEDS_CLARIFICATION | {quality['needs_clarification']} |",
        f"| Cache hits | {quality['cache_hits']} |",
        f"| LLM attempts | {quality['llm_attempted']} |",
        f"| Successful fresh LLM reviews | {totals['executed']} |",
        f"| Failed during execution | {totals['failed']} |",
        f"| Cache hit rate | {quality['cache_hit_rate_pct']:.1f}% |",
        f"| LLM execution rate | {quality['llm_execution_rate_pct']:.1f}% |",
        f"| Avoided LLM calls | {quality['avoided_llm_calls']} |",
        f"| Input tokens | {totals['input_tokens']:,} |",
        f"| Output tokens | {totals['output_tokens']:,} |",
        f"| Total tokens | {totals['total_tokens']:,} |",
        f"| Actual estimated batch cost | ${totals['estimated_cost_usd']:.6f} |",
        "",
        "### Per-story result",
        "",
        "| Issue | Pre-check | Agent result | Tokens | Cost |",
        "| --- | --- | --- | ---: | ---: |",
    ]
    for item in batch["issues"]:
        precheck = item["precheck"]
        decision = item.get("decision") or item.get("error") or "-"
        if item.get("cache_hit"):
            decision = f"CACHED {decision}"
        tokens = item.get("total_tokens", 0)
        cost = item.get("estimated_cost_usd", 0.0)
        reason = "; ".join(item.get("rejection_reasons", []))
        precheck_text = precheck if not reason else f"{precheck}: {reason}"
        lines.append(f"| `{item['issue_key']}` | {precheck_text} | {decision} | {tokens:,} | ${cost:.6f} |")

    clarification_items = [item for item in batch["issues"] if item.get("clarification_gaps")]
    if clarification_items:
        lines.extend(["", "## Clarification Required", ""])
        for item in clarification_items:
            cache_label = " (cached review)" if item.get("cache_hit") else ""
            lines.append(
                f"### {item['issue_key']} — NEEDS_CLARIFICATION ({item.get('readiness_score', 0)}/100){cache_label}"
            )
            lines.append("")
            for index, gap in enumerate(item["clarification_gaps"], start=1):
                lines.extend(
                    [
                        f"**Gap {index}: {gap.get('category') or gap.get('criterion') or 'Requirement gap'}**",
                        f"- Priority / severity: **{str(gap.get('severity') or 'unknown').upper()}**",
                        f"- Criterion: `{gap.get('criterion') or 'other'}`",
                        f"- Finding: {gap.get('finding') or '-'}",
                        f"- Clarification question: {gap.get('clarification_question') or '-'}",
                        "",
                    ]
                )

    with open(summary_path, "a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def run_batch(raw_issue_keys: str) -> dict:
    issue_keys = parse_issue_keys(raw_issue_keys)
    run_id = "REQ-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    issues = []
    total_input = 0
    total_output = 0
    total_cost = 0.0
    executed = 0
    cached = 0
    rejected = 0
    failed = 0

    cache = load_cache()
    force_review = _is_true("REQUIREMENTS_REVIEW_FORCE")
    model = os.getenv("REQUIREMENTS_REVIEW_MODEL") or os.getenv("SUT_MODEL") or ""
    prompt_text = PROMPT_PATH.read_text(encoding="utf-8")

    for issue_key in issue_keys:
        item = {"issue_key": issue_key, "precheck": "PENDING"}
        key_reasons = validate_issue_key(issue_key)
        if key_reasons:
            item.update(precheck="REJECTED", rejection_reasons=key_reasons)
            rejected += 1
            issues.append(item)
            continue

        try:
            requirement = load_requirement(issue_key)
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code
            message = "issue not found or inaccessible" if status_code == 404 else f"Jira returned HTTP {status_code}"
            item.update(precheck="REJECTED", rejection_reasons=[message])
            rejected += 1
            issues.append(item)
            continue
        except Exception as exc:
            item.update(precheck="REJECTED", rejection_reasons=[f"Jira load failed: {exc}"])
            rejected += 1
            issues.append(item)
            continue

        reasons = precheck_requirement(requirement)
        if reasons:
            item.update(precheck="REJECTED", rejection_reasons=reasons)
            rejected += 1
            issues.append(item)
            continue

        item["precheck"] = "ELIGIBLE"
        review_payload = build_review_payload(requirement)
        fingerprint = content_hash(review_payload, model=model, prompt_text=prompt_text)
        cached_entry = None if force_review else get_cached_review(cache, issue_key, fingerprint)

        if cached_entry:
            review = cached_entry["review"]
            cached += 1
            item.update(
                cache_hit=True,
                decision=review["decision"],
                readiness_score=review["readiness_score"],
                clarification_gaps=_clarification_gaps(review),
                total_tokens=0,
                estimated_cost_usd=0.0,
                cached_from=cached_entry.get("reviewed_at"),
                report=f"reports/requirements_review_{issue_key}.json",
            )
            _write_json(
                Path(item["report"]),
                {
                    "run_timestamp": datetime.now(timezone.utc).isoformat(),
                    "batch_run_id": run_id,
                    "issue_key": issue_key,
                    "cache_hit": True,
                    "cached_from": cached_entry.get("reviewed_at"),
                    "content_hash": fingerprint,
                    "review_payload": review_payload,
                    "review": review,
                    "telemetry": {
                        "agent": "requirements_review",
                        "model": cached_entry.get("model"),
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "total_tokens": 0,
                        "estimated_cost_usd": 0.0,
                        "cache_hit": True,
                    },
                },
            )
            issues.append(item)
            continue

        try:
            review, telemetry = review_requirement(review_payload)
            executed += 1
            total_input += telemetry["input_tokens"]
            total_output += telemetry["output_tokens"]
            total_cost += float(telemetry.get("estimated_cost_usd") or 0.0)
            reviewed_at = datetime.now(timezone.utc).isoformat()
            put_cached_review(
                cache,
                issue_key,
                fingerprint,
                review=review,
                model=telemetry.get("model") or model,
                reviewed_at=reviewed_at,
            )
            item.update(
                cache_hit=False,
                decision=review["decision"],
                readiness_score=review["readiness_score"],
                clarification_gaps=_clarification_gaps(review),
                total_tokens=telemetry["total_tokens"],
                estimated_cost_usd=float(telemetry.get("estimated_cost_usd") or 0.0),
                report=f"reports/requirements_review_{issue_key}.json",
            )
            _write_json(
                Path(item["report"]),
                {
                    "run_timestamp": reviewed_at,
                    "batch_run_id": run_id,
                    "issue_key": issue_key,
                    "cache_hit": False,
                    "content_hash": fingerprint,
                    "review_payload": review_payload,
                    "review": review,
                    "telemetry": telemetry,
                },
            )
        except Exception as exc:
            failed += 1
            item.update(cache_hit=False, error=f"agent execution failed: {exc}")
        issues.append(item)

    save_cache(cache)

    quality_metrics = _batch_quality_metrics(issues)
    batch = {
        "run_id": run_id,
        "run_timestamp": datetime.now(timezone.utc).isoformat(),
        "force_review": force_review,
        "issues": issues,
        "quality_metrics": quality_metrics,
        "totals": {
            "requested": len(issue_keys),
            "executed": executed,
            "cached": cached,
            "rejected": rejected,
            "failed": failed,
            "input_tokens": total_input,
            "output_tokens": total_output,
            "total_tokens": total_input + total_output,
            "estimated_cost_usd": round(total_cost, 6),
        },
    }
    _write_json(Path("reports") / f"requirements_review_batch_{run_id}.json", batch)
    _append_github_summary(batch)
    return batch


def main():
    parser = argparse.ArgumentParser(description="Run Requirements Review Agent for a manual batch of Jira issues")
    parser.add_argument("issue_keys", help="Comma/space/semicolon-separated Jira issue keys")
    args = parser.parse_args()

    batch = run_batch(args.issue_keys)
    totals = batch["totals"]
    quality = batch["quality_metrics"]
    print(f"Run ID: {batch['run_id']}")
    print(f"Requested: {totals['requested']}")
    print(f"Eligible after pre-check: {quality['eligible']}")
    print(f"READY: {quality['ready']}")
    print(f"NEEDS_CLARIFICATION: {quality['needs_clarification']}")
    print(f"Executed with LLM: {totals['executed']}")
    print(f"LLM attempts: {quality['llm_attempted']}")
    print(f"Skipped unchanged (cache): {totals['cached']}")
    print(f"Cache hit rate: {quality['cache_hit_rate_pct']:.1f}%")
    print(f"LLM execution rate: {quality['llm_execution_rate_pct']:.1f}%")
    print(f"Avoided LLM calls: {quality['avoided_llm_calls']}")
    print(f"Rejected before LLM: {totals['rejected']}")
    print(f"Failed during execution: {totals['failed']}")
    print(f"Usage: {totals['input_tokens']} input + {totals['output_tokens']} output = {totals['total_tokens']} tokens")
    print(f"Estimated batch cost: ${totals['estimated_cost_usd']:.6f}")
    for item in batch["issues"]:
        if item["precheck"] == "REJECTED":
            print(f"{item['issue_key']}: REJECTED - {'; '.join(item['rejection_reasons'])}")
        elif item.get("error"):
            print(f"{item['issue_key']}: ERROR - {item['error']}")
        elif item.get("cache_hit"):
            print(f"{item['issue_key']}: CACHED {item['decision']} ({item['readiness_score']}/100) - 0 tokens")
        else:
            print(f"{item['issue_key']}: {item['decision']} ({item['readiness_score']}/100)")

        if item.get("clarification_gaps"):
            print(f"  Clarification required: {len(item['clarification_gaps'])} blocking gap(s)")
            for index, gap in enumerate(item["clarification_gaps"], start=1):
                severity = str(gap.get("severity") or "unknown").upper()
                criterion = gap.get("criterion") or "other"
                finding = gap.get("finding") or "-"
                question = gap.get("clarification_question") or "-"
                print(f"    {index}. [{severity}] {criterion}: {finding}")
                print(f"       Question: {question}")


if __name__ == "__main__":
    main()
