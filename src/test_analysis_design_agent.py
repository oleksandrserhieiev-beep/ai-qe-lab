import json
import os
import time
from pathlib import Path

from anthropic import Anthropic

from cost_reporting import estimate_cost
from test_analysis_design import TestAnalysisDesignResult

PROMPT_PATH = Path(__file__).resolve().parents[1] / "config" / "test_analysis_design_prompt.txt"
PRIMARY_MAX_TOKENS = 6000
RETRY_MAX_TOKENS = 9000


def _configuration() -> tuple[str, str]:
    api_key = os.getenv("LLM_API_KEY")
    model = os.getenv("TEST_ANALYSIS_DESIGN_MODEL") or os.getenv("RISK_ANALYSIS_MODEL") or os.getenv("SUT_MODEL")
    if not api_key:
        raise ValueError("LLM_API_KEY is missing")
    if not model:
        raise ValueError("TEST_ANALYSIS_DESIGN_MODEL, RISK_ANALYSIS_MODEL or SUT_MODEL is missing")
    return api_key, model


def _extract_json(text: str) -> dict:
    cleaned = text.strip()
    if not cleaned:
        raise ValueError("Test Analysis & Design Agent returned an empty response")
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(cleaned[start : end + 1])
            except json.JSONDecodeError:
                pass
        raise ValueError("Test Analysis & Design Agent returned truncated or malformed JSON") from exc


def _normalise_enum(value, mapping: dict[str, str]):
    if value is None:
        return value
    key = str(value).strip().lower().replace("-", "_").replace(" ", "_")
    return mapping.get(key, value)


def _as_list(value) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _normalise_contract(raw: dict, issue_key: str) -> dict:
    data = dict(raw)
    data.setdefault("issue_key", issue_key)
    data.setdefault("health_findings", [])
    data.setdefault("coverage_gaps", [])
    data.setdefault("proposals", [])
    data.setdefault("human_decision_required", True)

    normalised = []
    for index, original in enumerate(data.get("proposals") or [], start=1):
        proposal = dict(original)
        proposal["proposed_id"] = proposal.get("proposed_id") or proposal.get("proposal_id") or f"{issue_key}-P{index}"
        proposal["title"] = proposal.get("title") or proposal.get("name") or proposal.get("test_title") or f"Proposed test {index}"
        proposal["test_kind"] = _normalise_enum(
            proposal.get("test_kind") or proposal.get("test_type") or proposal.get("kind") or "functional",
            {"functional": "functional", "ai": "ai", "ai_specific": "ai"},
        )
        trace = dict(proposal.get("traceability") or {})
        trace["issue_key"] = trace.get("issue_key") or trace.get("jira_issue") or trace.get("requirement") or issue_key
        trace["acceptance_criteria"] = _as_list(trace.get("acceptance_criteria") or trace.get("ac"))
        trace["risk_ids"] = _as_list(trace.get("risk_ids") or trace.get("risks"))
        proposal["traceability"] = trace

        proposal["preconditions"] = _as_list(proposal.get("preconditions") or proposal.get("setup") or proposal.get("test_data"))
        proposal["assertions"] = _as_list(proposal.get("assertions") or proposal.get("checks") or proposal.get("verification"))
        proposal["priority"] = _normalise_enum(
            proposal.get("priority") or proposal.get("test_priority"),
            {"critical": "CRITICAL", "high": "HIGH", "medium": "MEDIUM", "low": "LOW"},
        )
        proposal["estimated_manual_minutes"] = proposal.get("estimated_manual_minutes") or proposal.get("manual_minutes") or proposal.get("estimated_minutes")

        proposal["expected"] = proposal.get("expected") or proposal.get("expected_output") or proposal.get("expected_behavior") or {}
        if not isinstance(proposal["expected"], dict):
            proposal["expected"] = {"behavior": proposal["expected"]}

        if proposal["test_kind"] == "functional":
            proposal["steps"] = _as_list(proposal.get("steps") or proposal.get("test_steps"))
            for field in ("input", "oracle_type", "target_suite", "target_rationale", "action", "similar_cases", "existing_case_id", "proposed_extension"):
                proposal.pop(field, None)
            normalised.append(proposal)
            continue

        proposal["input"] = proposal.get("input") or proposal.get("test_input") or proposal.get("query") or {}
        if not isinstance(proposal["input"], dict):
            proposal["input"] = {"query": proposal["input"]}
        proposal["oracle_type"] = _normalise_enum(
            proposal.get("oracle_type") or proposal.get("oracle") or "semantic",
            {"deterministic": "deterministic", "semantic": "semantic", "semantic_llm": "semantic", "llm": "semantic"},
        )
        proposal["target_suite"] = _normalise_enum(
            proposal.get("target_suite") or proposal.get("target") or "regression",
            {
                "pr_critical": "pr_critical",
                "prcritical": "pr_critical",
                "regression": "regression",
                "nightly": "nightly",
                "golden": "golden_candidate",
                "golden_candidate": "golden_candidate",
            },
        )
        proposal["action"] = str(proposal.get("action") or "ADD").strip().upper()
        rationale = proposal.get("target_rationale") or proposal.get("rationale") or proposal.get("reason")
        proposal["target_rationale"] = rationale if rationale else None
        similar_cases = []
        for similar in proposal.get("similar_cases") or []:
            item = dict(similar)
            item["case_id"] = item.get("case_id") or item.get("existing_case_id") or item.get("id")
            item["similarity_score"] = item.get("similarity_score", item.get("similarity", 0.0))
            item["coverage_note"] = item.get("coverage_note") or item.get("note") or item.get("rationale") or "Similar coverage; review overlap and differences."
            similar_cases.append(item)
        proposal["similar_cases"] = similar_cases
        proposal.setdefault("existing_case_id", None)
        proposal.setdefault("proposed_extension", None)
        proposal.pop("steps", None)
        normalised.append(proposal)
    data["proposals"] = normalised
    return data


def _response_text(response) -> str:
    return "".join(block.text for block in response.content if block.type == "text")


def analyze_test_design(payload: dict) -> tuple[dict, dict]:
    api_key, model = _configuration()
    prompt = PROMPT_PATH.read_text(encoding="utf-8")
    client = Anthropic(api_key=api_key)
    compact = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    base_message = "Analyze this requirement, reviewed Risk Register, and governed dataset snapshot. Optimize for the smallest risk-driven test set with concrete preconditions/assertions, explicit traceability, explainable similarity, priority, suite rationale, and manual-time estimate. Return one complete compact JSON object matching the TestAnalysisDesignResult contract only. Do not echo the dataset snapshot or Jira text.\n" + compact
    messages = [{"role": "user", "content": base_message}]
    responses = []
    started = time.perf_counter()
    result = None
    last_error = None
    for attempt, max_tokens in enumerate((PRIMARY_MAX_TOKENS, RETRY_MAX_TOKENS), start=1):
        response = client.messages.create(model=model, max_tokens=max_tokens, system=prompt, messages=messages)
        responses.append(response)
        text = _response_text(response)
        try:
            if response.stop_reason == "max_tokens":
                raise ValueError(f"response was truncated at max_tokens={max_tokens}")
            raw = _extract_json(text)
            result = TestAnalysisDesignResult.model_validate(_normalise_contract(raw, payload["issue_key"])).model_dump(exclude_none=True)
            if result["issue_key"] != payload["issue_key"]:
                raise ValueError("output issue_key does not match input")
            break
        except Exception as exc:
            last_error = exc
            if attempt == 2:
                raise ValueError(f"Test Analysis & Design contract failure after retry: {exc}") from exc
            messages = [{
                "role": "user",
                "content": base_message + "\nPrevious attempt failed contract validation. Return a smaller complete JSON object using the exact conditional fields from the system instruction. Every proposal requires traceability, concrete assertions, priority, and estimated_manual_minutes. Functional also requires steps. AI also requires input/oracle/target/action/target_rationale.",
            }]
    if result is None:
        raise ValueError(f"Test Analysis & Design did not produce a result: {last_error}")
    input_tokens = sum(int(getattr(r.usage, "input_tokens", 0) or 0) for r in responses)
    output_tokens = sum(int(getattr(r.usage, "output_tokens", 0) or 0) for r in responses)
    telemetry = {
        "agent": "test_analysis_design",
        "model": responses[-1].model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "latency_ms": round((time.perf_counter() - started) * 1000, 2),
        "attempts": len(responses),
        "contract_retry_used": len(responses) > 1,
        "stop_reason": responses[-1].stop_reason,
        "estimated_cost_usd": estimate_cost(responses[-1].model, input_tokens, output_tokens),
    }
    return result, telemetry
