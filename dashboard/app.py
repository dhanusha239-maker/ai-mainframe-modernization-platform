import json
from pathlib import Path

import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DASHBOARD_JSON = PROJECT_ROOT / "docs" / "modernization_dashboard.json"


st.set_page_config(
    page_title="Legacy Modernization Dashboard",
    page_icon="🧠",
    layout="wide",
)


def load_dashboard():
    if not DASHBOARD_JSON.exists():
        st.error(f"Dashboard JSON not found: {DASHBOARD_JSON}")
        st.stop()

    with open(DASHBOARD_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def answer_question(question, dashboard):
    q = question.lower()

    if "tx001" in q or "failed customer" in q:
        return (
            "TX001 failed because AUTHDEC did not produce AUTHSTAT = APPRV "
            "when ERRCODE was 0000. This is the known approval-path translation gap."
        )

    if "authdec" in q:
        return (
            "AUTHDEC has an approval-path mismatch. Expected AUTHSTAT is APPRV "
            "when ERRCODE = 0000, but generated Java produced REJCT or blank."
        )

    if "behavior" in q or "score" in q:
        score = dashboard["summary"]["behavior_match_score"]
        return f"The current behavior match score is {score}%."

    if "batch" in q:
        batch = dashboard["batch_summary"]
        return (
            f"Batch validation processed {batch['batch_records']} records. "
            f"{batch['batch_passed']} passed and {batch['batch_failed']} failed."
        )

    if "impact" in q or "change" in q:
        return (
            "Change impact analysis shows which assembler symbols affect other modules. "
            "For example, ERRCODE and TXAMT have medium impact because multiple modules depend on them."
        )

    if "cfg" in q or "pdg" in q:
        cfg = dashboard["cfg_pdg_summary"]
        return (
            f"CFG available: {cfg['cfg_available']}. "
            f"PDG available: {cfg['pdg_available']}. "
            f"CFG conditions: {cfg.get('cfg_condition_count', 0)}, "
            f"PDG dependency edges: {cfg.get('pdg_symbol_dependency_edges', 0)}."
        )

    return (
        "I can answer questions about AUTHDEC, TX001, behavior score, "
        "batch validation, CFG/PDG, and change impact analysis."
    )


dashboard = load_dashboard()
summary = dashboard["summary"]

st.title("🧠 AI-Powered Legacy Modernization Dashboard")
st.caption("Week 2 Modernization Intelligence Layer")

st.subheader("Executive Summary")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Modules", summary["module_count"])
c2.metric("Behavior Match", f"{summary['behavior_match_score']}%")
c3.metric("Passed Tests", summary["passed_tests"])
c4.metric("Failed Tests", summary["failed_tests"])

c5, c6, c7 = st.columns(3)
c5.metric("Batch Records", summary["batch_records"])
c6.metric("Batch Passed", summary["batch_passed"])
c7.metric("Batch Failed", summary["batch_failed"])

st.divider()

st.subheader("CFG / PDG Summary")
cfg = dashboard["cfg_pdg_summary"]

c1, c2, c3, c4 = st.columns(4)
c1.metric("CFG Available", str(cfg["cfg_available"]))
c2.metric("PDG Available", str(cfg["pdg_available"]))
c3.metric("CFG Branches", cfg.get("cfg_branch_count", 0))
c4.metric("PDG Edges", cfg.get("pdg_symbol_dependency_edges", 0))

st.divider()

st.subheader("Module Summary")
module_df = pd.DataFrame(dashboard["module_summary"])
st.dataframe(module_df, use_container_width=True)

st.subheader("Behavior Failures")
failed_cases = dashboard["behavior_summary"]["failed_cases"]
if failed_cases:
    st.dataframe(pd.DataFrame(failed_cases), use_container_width=True)
else:
    st.success("No behavior failures detected.")

st.subheader("Batch Validation")
batch = dashboard["batch_summary"]
if batch["failed_customers"]:
    st.dataframe(pd.DataFrame(batch["failed_customers"]), use_container_width=True)
else:
    st.success("No failed batch customers.")

st.subheader("Change Impact Analysis")
impact_df = pd.DataFrame(dashboard["change_impact_analysis"])
st.dataframe(impact_df, use_container_width=True)

st.subheader("AI-Style Recommendations")
for rec in dashboard["recommendations"]:
    st.write(f"- {rec}")

st.divider()

st.subheader("💬 Ask the Modernization Assistant")
question = st.text_input(
    "Ask about failed cases, AUTHDEC, batch validation, CFG/PDG, or impact analysis:"
)

if question:
    st.info(answer_question(question, dashboard))