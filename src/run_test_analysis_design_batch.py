import argparse
import json
import os
import re
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

import httpx

from jira_requirements import load_requirement
from requirement_precheck import parse_issue_keys, validate_issue_key
from test_analysis_design_agent import PROMPT_PATH, analyze_test_design
from test_analysis_design_cache import DEFAULT_CACHE_PATH, content_fingerprint, get_cached, load_cache, put_cached, save_cache

REPORT_PATH = Path("reports/test_analysis_design_batch.json")
DATASETS = {
    "pr_critical": Path("datasets/pr_critical_dataset.json"),
    "regression": Path("datasets/regression_dataset.json"),
    "nightly": Path("datasets/nightly_dataset.json"),
    "golden": Path("datasets/golden_dataset.json"),
}


def _read_json(path): return json.loads(path.read_text(encoding="utf-8"))
def _write_json(path, value): path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
def _force(): return (os.getenv("TEST_ANALYSIS_DESIGN_FORCE") or "").lower() in {"1", "true", "yes", "on"}
def _model(): return (os.getenv("TEST_ANALYSIS_DESIGN_MODEL") or os.getenv("RISK_ANALYSIS_MODEL") or os.getenv("SUT_MODEL") or "").strip()
def _escape(value): return str(value).replace("|", "\\|").replace("\n", "<br>")
def _table(headers, rows): return ["| " + " | ".join(headers) + " |", "| " + " | ".join(":---:" for _ in headers) + " |", *["| " + " | ".join(_escape(v) for v in row) + " |" for row in rows]]
def _summary(lines):
    path = os.getenv("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a", encoding="utf-8") as handle: handle.write("\n".join(lines) + "\n")


def _compact_value(value, preferred_key=None):
    if value is None: return "-"
    if isinstance(value, dict):
        if preferred_key and value.get(preferred_key) is not None: return str(value[preferred_key])
        if len(value) == 1: return str(next(iter(value.values())))
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    if isinstance(value, list): return "; ".join(str(item) for item in value)
    return str(value)


def _similarity_summary(proposal: dict) -> str:
    cases = proposal.get("similar_cases") or []
    if not cases:
        return "-"
    rendered = []
    for case in sorted(cases, key=lambda x: x.get("similarity_score", 0.0), reverse=True):
        case_id = case.get("case_id") or "unknown"
        score = case.get("similarity_score")
        score_text = f"{score:.0%}" if isinstance(score, (int, float)) else "n/a"
        note = case.get("coverage_note") or "Similarity evidence not provided"
        rendered.append(f"**{case_id} ({score_text})** — {note}")
    return "<br>".join(rendered)


def _proposal_summary(results: list[dict]) -> list[str]:
    lines = ["", "## Test Analysis & Design — Coverage Proposals", ""]
    global_trace_rows = []
    total_manual_minutes = 0

    for item in results:
        if item.get("status") == "ERROR": continue
        proposals = item.get("result", {}).get("proposals", [])
        gaps = item.get("result", {}).get("coverage_gaps", [])
        issue_key = item["issue_key"]
        lines.extend(["<details>", f"<summary><strong>{issue_key}</strong></summary>", ""])
        if not proposals:
            lines.extend(["No new material coverage proposed.", "", "</details>", ""])
            continue

        ac_labels = OrderedDict()
        groups = OrderedDict()
        for proposal in proposals:
            trace = proposal.get("traceability") or {}
            acs = trace.get("acceptance_criteria") or ["Unmapped AC"]
            labels = []
            for ac in acs:
                if ac not in ac_labels: ac_labels[ac] = f"AC{len(ac_labels) + 1}"
                labels.append(ac_labels[ac])
            ac_label = ", ".join(labels)
            risk_label = ", ".join(trace.get("risk_ids") or []) or "Unmapped risk"
            groups.setdefault((ac_label, risk_label), []).append(proposal)

        for (ac_label, risk_label), grouped in groups.items():
            lines.extend([f"### {ac_label}", f"**Risk:** `{risk_label}`", ""])
            functional = [p for p in grouped if p.get("test_kind") == "functional"]
            ai = [p for p in grouped if p.get("test_kind") == "ai"]

            if functional:
                rows = []
                for proposal in functional:
                    minutes = int(proposal.get("estimated_manual_minutes") or 0)
                    total_manual_minutes += minutes
                    steps = proposal.get("steps") or []
                    rows.append([
                        proposal.get("proposed_id") or "-", proposal["title"], proposal.get("priority") or "-",
                        f"{minutes} min" if minutes else "-",
                        "<br>".join(f"{index}. {step}" for index, step in enumerate(steps, start=1)),
                        _compact_value(proposal.get("expected"), "behavior"),
                    ])
                lines.extend(["#### Functional", "", *_table(["ID", "Test", "Priority", "Est. Manual", "Steps", "Expected"], rows), ""])

            if ai:
                rows = []
                rationales = []
                for proposal in ai:
                    minutes = int(proposal.get("estimated_manual_minutes") or 0)
                    total_manual_minutes += minutes
                    rows.append([
                        proposal.get("proposed_id") or "-", proposal["title"], proposal.get("priority") or "-",
                        f"{minutes} min" if minutes else "-",
                        _compact_value(proposal.get("input"), "query"), _compact_value(proposal.get("expected"), "behavior"),
                        _similarity_summary(proposal), proposal.get("oracle_type") or "-", proposal.get("target_suite") or "-", proposal.get("action") or "-",
                    ])
                    if proposal.get("target_rationale"):
                        rationales.append(f"- **{proposal['proposed_id']} rationale:** {proposal['target_rationale']}")
                lines.extend(["#### AI Quality", "", *_table(["ID", "Test", "Priority", "Est. Manual", "Input", "Expected", "Similarity / Coverage Evidence", "Oracle", "Dataset", "Action"], rows), ""])
                if rationales: lines.extend(rationales + [""])

        trace_rows = []
        for ac, ac_label in ac_labels.items():
            linked = [p for p in proposals if ac in ((p.get("traceability") or {}).get("acceptance_criteria") or [])]
            risks = sorted({r for p in linked for r in ((p.get("traceability") or {}).get("risk_ids") or [])})
            functional_ids = [p.get("proposed_id", "-") for p in linked if p.get("test_kind") == "functional"]
            ai_new = [p.get("proposed_id", "-") for p in linked if p.get("test_kind") == "ai" and p.get("action") != "SKIP"]
            existing = []
            for p in linked:
                if p.get("test_kind") != "ai": continue
                if p.get("existing_case_id"): existing.append(p["existing_case_id"])
                existing.extend(c.get("case_id") for c in (p.get("similar_cases") or []) if c.get("case_id") and (p.get("action") == "SKIP" or c.get("similarity_score", 0) >= 0.8))
            status = "GAP" if any(ac in str(gap) for gap in gaps) else ("COVERED" if linked else "GAP")
            row = [issue_key, ac_label, ", ".join(risks) or "-", ", ".join(functional_ids) or "-", ", ".join(ai_new) or "-", ", ".join(dict.fromkeys(existing)) or "-", status]
            trace_rows.append(row[1:])
            global_trace_rows.append(row)

        lines.extend(["### Traceability & Coverage", "", *_table(["AC", "Risk", "Functional Tests", "AI Tests", "Existing Coverage", "Status"], trace_rows), "", "</details>", ""])

    if global_trace_rows:
        covered = sum(1 for row in global_trace_rows if row[-1] == "COVERED")
        lines.extend([
            "## Consolidated Traceability & Coverage", "",
            *_table(["Issue", "AC", "Risk", "Functional Tests", "AI Tests", "Existing Coverage", "Status"], global_trace_rows), "",
            f"**Coverage:** {covered}/{len(global_trace_rows)} AC mappings covered | **Uncovered:** {len(global_trace_rows) - covered} | **Estimated manual execution:** {total_manual_minutes} min",
            "",
        ])
    return lines


def _extract_risks(description: str) -> list[dict]:
    marker = re.search(r"(?is)(?:reviewed\s+risk\s+context|prioritized\s+risk\s+register|risk\s+register)(.*)$", description or "")
    if not marker: return []
    text = marker.group(1).strip(); risks = []
    blocks = re.split(r"(?im)(?=\brisk\s+id\s*:\s*)", text)
    for block in blocks:
        rid = re.search(r"(?im)risk\s+id\s*:\s*([^\n]+)", block)
        statement = re.search(r"(?im)^\s*(?:[-*]\s*)?risk\s*:\s*([^\n]+)", block)
        if rid and statement:
            def field(name):
                found = re.search(rf"(?im)^\s*(?:[-*]\s*)?{name}\s*:\s*([^\n]+)", block)
                return found.group(1).strip() if found else ""
            risks.append({"risk_id": rid.group(1).strip(), "risk_statement": statement.group(1).strip(), "priority": field("priority"), "mitigation": field("mitigation"), "recommended_test_focus": field("recommended test focus")})
    return risks


def _dataset_snapshot() -> dict:
    snapshot = {}
    for name, path in DATASETS.items():
        if path.exists(): snapshot[name] = _read_json(path)
    return snapshot


def _health(snapshot: dict) -> list[dict]:
    findings = []
    for name, records in snapshot.items():
        seen = set()
        for index, record in enumerate(records):
            record_id = str(record.get("ID") or "").strip()
            if not record_id: findings.append({"severity": "ERROR", "code": "MISSING_ID", "message": "Dataset record ID is missing", "dataset": name, "record_id": f"row-{index + 1}"})
            elif record_id in seen: findings.append({"severity": "ERROR", "code": "DUPLICATE_ID", "message": f"Duplicate record ID: {record_id}", "dataset": name, "record_id": record_id})
            seen.add(record_id)
            if not str(record.get("Query") or "").strip(): findings.append({"severity": "ERROR", "code": "MISSING_QUERY", "message": "Dataset Query is missing", "dataset": name, "record_id": record_id or f"row-{index + 1}"})
    return findings


def run(raw_issue_keys: str) -> dict:
    issue_keys = parse_issue_keys(raw_issue_keys)
    if not issue_keys: raise ValueError("At least one Jira issue key is required")
    snapshot = _dataset_snapshot(); health = _health(snapshot)
    blocking = any(item["severity"] == "ERROR" for item in health)
    eligibility = []; requirements = []
    for key in issue_keys:
        reasons = validate_issue_key(key); requirement = None
        if not reasons:
            try: requirement = load_requirement(key)
            except httpx.HTTPStatusError as exc: reasons = ["ticket not found or inaccessible" if exc.response.status_code == 404 else f"Jira returned HTTP {exc.response.status_code}"]
            except Exception as exc: reasons = [f"Jira load failed: {exc}"]
        risks = _extract_risks((requirement or {}).get("description", "")) if requirement else []
        if requirement and not str(requirement.get("acceptance_criteria") or "").strip(): reasons.append("acceptance criteria are missing")
        if requirement and not risks: reasons.append("reviewed Risk Register is missing from Jira Description")
        status = "ELIGIBLE" if not reasons else "INELIGIBLE"
        eligibility.append({"issue_key": key, "status": status, "reasons": reasons})
        if status == "ELIGIBLE": requirements.append((requirement, risks))
    eligibility_rows = [[x["issue_key"], x["status"], "; ".join(x["reasons"]) or "-"] for x in eligibility]
    _summary(["## Test Analysis & Design — Eligibility", "", *_table(["Issue", "Eligibility", "Reason"], eligibility_rows)])
    if blocking:
        rows = [[x["dataset"], x.get("record_id") or "-", x["severity"], x["code"], x["message"]] for x in health]
        _summary(["", "## Dataset Health — BLOCKED", "", *_table(["Dataset", "Record", "Severity", "Code", "Finding"], rows)])
    cache = load_cache(DEFAULT_CACHE_PATH); results = []; total_tokens = 0; total_cost = 0.0; hits = 0; attempts = 0
    prompt = PROMPT_PATH.read_text(encoding="utf-8")
    if not blocking:
        for requirement, risks in requirements:
            key = requirement["issue_key"]
            content_hash = content_fingerprint(issue_key=key, acceptance_criteria=requirement["acceptance_criteria"], risks=risks, dataset_snapshot=snapshot, model=_model(), prompt_text=prompt)
            cached = None if _force() else get_cached(cache, key, content_hash)
            try:
                if cached:
                    hits += 1; result = cached["result"]; telemetry = {"model": cached.get("model") or _model(), "total_tokens": 0, "estimated_cost_usd": 0.0, "cache_hit": True, "attempts": 0}
                    status = "CACHED"
                else:
                    attempts += 1
                    payload = {"issue_key": key, "summary": requirement.get("summary", ""), "acceptance_criteria": requirement["acceptance_criteria"], "reviewed_risks": risks, "dataset_snapshot": snapshot, "dataset_health_findings": health}
                    result, telemetry = analyze_test_design(payload); total_tokens += telemetry["total_tokens"]; total_cost += telemetry["estimated_cost_usd"]
                    put_cached(cache, key, content_hash, result=result, model=telemetry.get("model") or _model(), created_at=datetime.now(timezone.utc).isoformat()); status = "ANALYZED"
                results.append({"issue_key": key, "status": status, "cache_hit": bool(cached), "result": result, "telemetry": telemetry})
            except Exception as exc:
                results.append({"issue_key": key, "status": "ERROR", "cache_hit": False, "error": str(exc)})
    save_cache(cache, DEFAULT_CACHE_PATH)
    failed = [item for item in results if item.get("status") == "ERROR"]
    _summary([*_proposal_summary(results), "### Agent execution", f"**Succeeded:** {len(results)-len(failed)} | **Failed:** {len(failed)} | **Cache hits:** {hits} | **LLM inference calls:** {attempts} | **Tokens:** {total_tokens:,} | **Estimated cost:** ${total_cost:.6f}", *(["", *_table(["Issue", "Status", "Error"], [[x["issue_key"], "ERROR", x["error"]] for x in failed])] if failed else []), "", "### Human decision contract", "AI Quality only: `APPROVE = add new` · `REJECT = no change` · `EDIT = edit proposal before add` · `EXTEND_EXISTING = modify existing case after BEFORE → AFTER review`. Functional tests are review-only until TMS integration."])
    report = {"run_timestamp": datetime.now(timezone.utc).isoformat(), "requested": len(issue_keys), "eligible": len(requirements), "ineligible": len(issue_keys)-len(requirements), "dataset_blocked": blocking, "dataset_health": health, "cache_hits": hits, "llm_attempts": attempts, "failed": len(failed), "total_tokens": total_tokens, "estimated_cost_usd": round(total_cost, 6), "eligibility": eligibility, "results": results}
    _write_json(REPORT_PATH, report); print(json.dumps(report, ensure_ascii=False, indent=2)); return report


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("issue_keys"); args = parser.parse_args(); run(args.issue_keys)

if __name__ == "__main__": main()
