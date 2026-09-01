import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import httpx

from agent_content_cache import fingerprint, get_cached, load_cache, put_cached, save_cache
from jira_requirements import load_requirement
from requirement_precheck import parse_issue_keys, validate_issue_key
from risk_analysis_agent import PROMPT_PATH, analyze_risks, build_risk_analysis_input

STATE_PATH = Path("reports/risk_analysis_batch_state.json")
REPORT_PATH = Path("reports/risk_analysis_batch.json")
DEFAULT_CACHE_PATH = Path(".cache/risk-analysis/cache.json")
DEFAULT_REVIEW_LABEL = "review-completed"

def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
def _read_json(path: Path) -> dict: return json.loads(path.read_text(encoding="utf-8"))
def _review_label() -> str: return (os.getenv("JIRA_REVIEW_COMPLETED_LABEL") or DEFAULT_REVIEW_LABEL).strip()
def _cache_path() -> Path:
    configured=(os.getenv("RISK_ANALYSIS_CACHE_PATH") or "").strip(); return Path(configured) if configured else DEFAULT_CACHE_PATH
def _force_analysis() -> bool: return (os.getenv("RISK_ANALYSIS_FORCE") or "").strip().lower() in {"1","true","yes","on"}
def _model() -> str: return (os.getenv("RISK_ANALYSIS_MODEL") or os.getenv("REQUIREMENTS_REVIEW_MODEL") or os.getenv("SUT_MODEL") or "").strip()
def eligibility_reasons(requirement: dict, review_label: str | None=None) -> list[str]:
    reasons=[]; required_label=(review_label or _review_label()).casefold(); labels={str(x).strip().casefold() for x in requirement.get("labels") or []}
    if required_label not in labels: reasons.append(f"required label '{review_label or _review_label()}' is missing")
    if not str(requirement.get("acceptance_criteria") or "").strip(): reasons.append("acceptance criteria are missing")
    return reasons
def _escape(value) -> str: return str(value).replace("|","\\|").replace("\n"," ")
def _append_summary(lines: list[str]) -> None:
    path=os.getenv("GITHUB_STEP_SUMMARY")
    if path:
        with open(path,"a",encoding="utf-8") as handle: handle.write("\n".join(lines)+"\n")
def _centered_markdown_table(headers, rows):
    lines=["| "+" | ".join(headers)+" |","| "+" | ".join(":---:" for _ in headers)+" |"]
    lines += ["| "+" | ".join(_escape(v) for v in row)+" |" for row in rows]; return lines
def _print_console_table(headers, rows):
    if not rows: print("No rows to display."); return
    text_rows=[[str(v).replace("\n"," ") for v in row] for row in rows]; widths=[len(str(h)) for h in headers]
    for row in text_rows:
        for i,v in enumerate(row): widths[i]=max(widths[i],len(v))
    render=lambda row: "| "+" | ".join(v.center(widths[i]) for i,v in enumerate(row))+" |"
    print(render([str(h) for h in headers])); print("|-"+"-|-".join("-"*w for w in widths)+"-|")
    for row in text_rows: print(render(row))

def check(raw_issue_keys: str) -> dict:
    issue_keys=parse_issue_keys(raw_issue_keys)
    if not issue_keys: raise ValueError("At least one Jira issue key is required")
    items=[]; eligible_requirements=[]; review_label=_review_label()
    for issue_key in issue_keys:
        item={"issue_key":issue_key,"status":"PENDING","reasons":[]}; key_reasons=validate_issue_key(issue_key)
        if key_reasons: item.update(status="INELIGIBLE",reasons=key_reasons); items.append(item); continue
        try: requirement=load_requirement(issue_key)
        except httpx.HTTPStatusError as exc:
            code=exc.response.status_code; item.update(status="INELIGIBLE",reasons=["ticket not found or inaccessible" if code==404 else f"Jira returned HTTP {code}"]); items.append(item); continue
        except Exception as exc: item.update(status="INELIGIBLE",reasons=[f"Jira load failed: {exc}"]); items.append(item); continue
        reasons=eligibility_reasons(requirement,review_label)
        if reasons: item.update(status="INELIGIBLE",reasons=reasons)
        else: item["status"]="ELIGIBLE"; eligible_requirements.append(requirement)
        items.append(item)
    state={"run_timestamp":datetime.now(timezone.utc).isoformat(),"review_completed_label":review_label,"requested":len(issue_keys),"eligible":len(eligible_requirements),"ineligible":len(issue_keys)-len(eligible_requirements),"items":items,"eligible_requirements":eligible_requirements}; _write_json(STATE_PATH,state)
    rows=[[i["issue_key"],i["status"],"; ".join(i["reasons"]) or "-"] for i in items]
    _append_summary(["## Risk Analysis — Eligibility Check","",f"**Required Jira label:** `{review_label}`  ",f"**Requested:** {state['requested']} | **Eligible:** {state['eligible']} | **Ineligible:** {state['ineligible']}","",*_centered_markdown_table(["Issue","Eligibility","Reason"],rows),"","No LLM call is made for ineligible tickets."])
    print("\n=== Risk Analysis — Eligibility Check ==="); _print_console_table(["Issue","Eligibility","Reason"],rows)
    print("\nNo eligible tickets for Risk Analysis." if not eligible_requirements else f"\nEligible tickets for Risk Analysis: {len(eligible_requirements)}"); return state

def analyze() -> dict:
    state=_read_json(STATE_PATH); results=[]; total_tokens=0; total_cost=0.0; cache_hits=0; llm_attempts=0; cache=load_cache(_cache_path()); force=_force_analysis(); model=_model(); prompt_text=PROMPT_PATH.read_text(encoding="utf-8")
    for requirement in state.get("eligible_requirements",[]):
        issue_key=requirement["issue_key"]
        try:
            payload=build_risk_analysis_input(requirement,{"decision":"READY","known_constraints":[],"dependencies":[]}); content_hash=fingerprint(agent="risk_analysis",semantic_input=payload,model=model,prompt_text=prompt_text); cached=None if force else get_cached(cache,issue_key,content_hash)
            if cached:
                cache_hits+=1; results.append({"issue_key":issue_key,"status":"CACHED","cache_hit":True,"content_hash":content_hash,"cached_from":cached.get("created_at"),"result":cached["result"],"telemetry":{"agent":"risk_analysis","model":cached.get("model") or model,"input_tokens":0,"output_tokens":0,"total_tokens":0,"estimated_cost_usd":0.0,"cache_hit":True}}); continue
            llm_attempts+=1; result,telemetry=analyze_risks(payload); total_tokens+=int(telemetry.get("total_tokens") or 0); total_cost+=float(telemetry.get("estimated_cost_usd") or 0.0); created_at=datetime.now(timezone.utc).isoformat(); put_cached(cache,issue_key,content_hash,result=result,model=telemetry.get("model") or model,created_at=created_at); results.append({"issue_key":issue_key,"status":"ANALYZED","cache_hit":False,"content_hash":content_hash,"result":result,"telemetry":telemetry})
        except Exception as exc: results.append({"issue_key":issue_key,"status":"ERROR","cache_hit":False,"error":str(exc)})
    save_cache(cache,_cache_path()); report={"run_timestamp":datetime.now(timezone.utc).isoformat(),"force_analysis":force,"requested":state["requested"],"eligible":state["eligible"],"analyzed":sum(i["status"]=="ANALYZED" for i in results),"cached":cache_hits,"llm_attempts":llm_attempts,"failed":sum(i["status"]=="ERROR" for i in results),"total_tokens":total_tokens,"estimated_cost_usd":round(total_cost,6),"eligibility":state["items"],"results":results}; _write_json(REPORT_PATH,report)
    _append_summary(["## Risk Analysis — Execution","",f"**Fresh LLM analyses:** {report['analyzed']} | **Cache hits:** {report['cached']} | **LLM attempts:** {report['llm_attempts']} | **Failed:** {report['failed']}",f"**Force analysis:** {'yes' if force else 'no'} | **Actual tokens this run:** {total_tokens:,} | **Estimated cost:** ${report['estimated_cost_usd']:.6f}","","Unchanged ticket semantic content + unchanged Risk Agent prompt + unchanged model reuses cached output and spends 0 LLM tokens."])
    print("\n=== Risk Analysis — Execution ==="); _print_console_table(["Fresh","Cached","LLM Attempts","Failed","Tokens","Cost"],[[report["analyzed"],report["cached"],report["llm_attempts"],report["failed"],report["total_tokens"],f"${report['estimated_cost_usd']:.6f}"]]); return report

def _risk_rows(report):
    return [{"issue_key":item["issue_key"],**risk} for item in report.get("results",[]) if item.get("status") in {"ANALYZED","CACHED"} for risk in item["result"].get("risks",[])]
def render_scores():
    risks=_risk_rows(_read_json(REPORT_PATH)); rows=[[r["issue_key"],r["risk_id"],r["likelihood"],r["impact"],f"{r['likelihood']} × {r['impact']}",r["risk_score"]] for r in risks]; headers=["Issue","Risk ID","Likelihood","Impact","Calculation","Risk Score"]; _append_summary(["## Risk Analysis — Likelihood × Impact","",*_centered_markdown_table(headers,rows)]); print("\n=== Risk Analysis — Likelihood × Impact ==="); _print_console_table(headers,rows)
def _join(values): return "; ".join(values) if values else "-"
def render_prioritized():
    report=_read_json(REPORT_PATH); risks=sorted(_risk_rows(report),key=lambda r:(-int(r["risk_score"]),r["issue_key"],r["risk_id"])); rows=[[i,r["issue_key"],r["risk_type"],r["category"],r["risk_statement"],_join(r.get("mitigation") or []),_join(r.get("recommended_test_focus") or []),r["likelihood"],r["impact"],r["risk_score"],str(r["priority"]).upper()] for i,r in enumerate(risks,1)]; headers=["#","Issue","Risk Type","Category","Risk","Mitigation","Recommended Test Focus","Likelihood","Impact","Score","Priority"]
    _append_summary(["## Prioritized Risk Register","",*_centered_markdown_table(headers,rows),"" if rows else "No risks were produced.","","**Human review required:** risks, mitigation proposals, and recommended test focus are decision-support outputs.","",f"**LLM usage this run:** {report.get('total_tokens',0):,} tokens | **Estimated cost:** ${report.get('estimated_cost_usd',0.0):.6f} | **Cache hits:** {report.get('cached',0)}"]); print("\n=== Prioritized Risk Register ==="); _print_console_table(headers,rows)
def main():
    parser=argparse.ArgumentParser(description="Run Jira-driven Risk Analysis Agent batch"); sub=parser.add_subparsers(dest="command",required=True); check_parser=sub.add_parser("check"); check_parser.add_argument("issue_keys"); sub.add_parser("analyze"); sub.add_parser("scores"); sub.add_parser("prioritized"); args=parser.parse_args(); {"check":lambda:check(args.issue_keys),"analyze":analyze,"scores":render_scores,"prioritized":render_prioritized}[args.command]()
if __name__=="__main__": main()
