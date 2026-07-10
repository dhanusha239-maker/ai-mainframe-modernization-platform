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


def impact_badge(level):
    level = str(level).lower()

    if level == "high":
        return "🔴 High"
    if level == "medium":
        return "🟠 Medium"
    return "🟢 Low"


def find_failed_case(question, dashboard):
    q = question.lower().strip()

    for case in dashboard["behavior_summary"]["failed_cases"]:

        searchable = [
            case.get("case_id"),
            case.get("module"),
            case.get("customer_id"),
        ]

        for value in searchable:
            if not value:
                continue

            value = str(value).lower()

            if value == q:
                return case

            if value in q:
                return case

    return None

def answer_question(question, dashboard):

    q = question.lower().strip()

    # ----------------------------------------------------
    # Executive summary
    # ----------------------------------------------------

    if any(word in q for word in ["summary", "overview", "status"]):

        s = dashboard["summary"]

        return (
            f"""
### Executive Summary

Modules analysed : **{s['module_count']}**

Behavior score : **{s['behavior_match_score']}%**

Passed tests : **{s['passed_tests']}**

Failed tests : **{s['failed_tests']}**

Batch records : **{s['batch_records']}**
"""
        )

    # ----------------------------------------------------
    # Module search
    # ----------------------------------------------------

    for module in dashboard["module_summary"]:

        module_name = module["module"].lower()

        if module_name == q or module_name in q:

            reads = module.get("fields_read", [])
            writes = module.get("fields_written", [])

            read_text = ", ".join(reads) if reads else "None"
            write_text = ", ".join(writes) if writes else "None"

            return (
                f"""
### 📦 Module : {module['module']}

📥 Reads Fields

{read_text}

📤 Writes Fields

{write_text}

🔀 Conditions

{module['condition_count']}

✅ Behavior Match

{module['average_behavior_match']}%

🧪 Behavior Tests

{module['behavior_test_count']}
"""
            )

    # ----------------------------------------------------
    # Change impact search
    # ----------------------------------------------------

    for impact in dashboard["change_impact_analysis"]:

        symbol = impact["symbol"].lower()

        if symbol == q or symbol in q:

            return (
                f"""
### Change Impact : {impact['symbol']}

Impact Level : {impact['impact_level']}

Written By :

{", ".join(impact['written_by']) or "None"}

Read By :

{", ".join(impact['read_by']) or "None"}

Impacted Modules :

{", ".join(impact['impacted_modules'])}

Recommendation :

{impact['recommendation']}
"""
            )

    # ----------------------------------------------------
    # Failed behavior search
    # ----------------------------------------------------

    failed_case = find_failed_case(q, dashboard)

    if failed_case:

        return (
            f"""
### Failed Case : {failed_case['case_id']}

Module :

{failed_case['module']}

Customer :

{failed_case.get('customer_id','N/A')}

Behavior Score :

{failed_case['match_score']}%

Diagnosis :

{failed_case['diagnosis']}
"""
        )

    # ----------------------------------------------------
    # Behavior summary
    # ----------------------------------------------------

    if "behavior" in q or "match" in q:

        b = dashboard["behavior_summary"]

        return (
            f"""
Behavior Match :

{b['average_behavior_match']}%

Passed :

{b['passed']}

Failed :

{b['failed']}
"""
        )

    # ----------------------------------------------------
    # Batch summary
    # ----------------------------------------------------

    if "batch" in q:

        b = dashboard["batch_summary"]

        return (
            f"""
Batch Validation

Records :

{b['batch_records']}

Passed :

{b['batch_passed']}

Failed :

{b['batch_failed']}
"""
        )

    # ----------------------------------------------------
    # CFG / PDG
    # ----------------------------------------------------

    if "cfg" in q or "pdg" in q:

        cfg = dashboard["cfg_pdg_summary"]

        return (
            f"""
CFG Available :

{cfg['cfg_available']}

PDG Available :

{cfg['pdg_available']}

CFG Modules :

{cfg['cfg_module_count']}

PDG Modules :

{cfg['pdg_module_count']}

CFG Branches :

{cfg['cfg_branch_count']}

CFG Conditions :

{cfg['cfg_condition_count']}

PDG Read Edges :

{cfg['pdg_read_edges']}

PDG Write Edges :

{cfg['pdg_write_edges']}
"""
        )

    # ----------------------------------------------------
    # Recommendations
    # ----------------------------------------------------

    if "recommend" in q or "suggest" in q:

        rec = ""

        for r in dashboard["recommendations"]:
            rec += f"• {r}\n\n"

        return rec

    # ----------------------------------------------------
    # Help
    # ----------------------------------------------------

    return """
### I can answer questions like:

• txamt

• errcode

• authdec

• custval

• maindrv

• tx001

• cust000001

• behavior

• cfg

• pdg

• batch

• recommendations

• summary
"""


def normalize_module_table(module_summary):
    rows = []

    for item in module_summary:
        rows.append(
            {
                "Module": item["module"],
                "Reads": len(item.get("fields_read", [])),
                "Writes": len(item.get("fields_written", [])),
                "Conditions": item.get("condition_count", 0),
                "Behavior Match": item.get("average_behavior_match"),
                "Tests": item.get("behavior_test_count", 0),
            }
        )

    return pd.DataFrame(rows)


def normalize_failed_cases(failed_cases):
    rows = []

    for case in failed_cases:
        rows.append(
            {
                "Case ID": case.get("case_id"),
                "Module": case.get("module"),
                "Customer ID": case.get("customer_id"),
                "Match Score": case.get("match_score"),
                "Diagnosis": case.get("diagnosis"),
            }
        )

    return pd.DataFrame(rows)


def normalize_change_impact(change_impact):
    rows = []

    for item in change_impact:
        rows.append(
            {
                "Symbol": item["symbol"],
                "Written By": ", ".join(item.get("written_by", [])) or "None",
                "Read By": ", ".join(item.get("read_by", [])) or "None",
                "Impacted Modules": item.get("impact_count", 0),
                "Impact Level": impact_badge(item.get("impact_level")),
                "Recommendation": item.get("recommendation", ""),
            }
        )

    return pd.DataFrame(rows)


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

st.subheader("Validation Charts")

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    pass_fail_df = pd.DataFrame(
        {
            "Status": ["Passed", "Failed"],
            "Count": [summary["passed_tests"], summary["failed_tests"]],
        }
    )
    st.bar_chart(pass_fail_df, x="Status", y="Count")

with chart_col2:
    module_chart_df = normalize_module_table(dashboard["module_summary"])
    module_chart_df = module_chart_df.dropna(subset=["Behavior Match"])
    st.bar_chart(module_chart_df, x="Module", y="Behavior Match")

st.divider()

st.subheader("CFG / PDG Summary")
cfg = dashboard["cfg_pdg_summary"]

c1, c2, c3, c4 = st.columns(4)
c1.metric("CFG Available", str(cfg["cfg_available"]))
c2.metric("PDG Available", str(cfg["pdg_available"]))
c3.metric("CFG Branches", cfg.get("cfg_branch_count", 0))
c4.metric("PDG Edges", cfg.get("pdg_symbol_dependency_edges", 0))

c5, c6, c7 = st.columns(3)
c5.metric("CFG Conditions", cfg.get("cfg_condition_count", 0))
c6.metric("PDG Reads", cfg.get("pdg_read_edges", 0))
c7.metric("PDG Writes", cfg.get("pdg_write_edges", 0))

st.divider()

st.subheader("Module Summary")
module_df = normalize_module_table(dashboard["module_summary"])
st.dataframe(module_df, use_container_width=True)

st.subheader("Behavior Failures")
failed_cases = dashboard["behavior_summary"]["failed_cases"]
if failed_cases:
    st.dataframe(normalize_failed_cases(failed_cases), use_container_width=True)
else:
    st.success("No behavior failures detected.")

st.subheader("Batch Validation")
batch = dashboard["batch_summary"]
if batch["failed_customers"]:
    st.dataframe(pd.DataFrame(batch["failed_customers"]), use_container_width=True)
else:
    st.success("No failed batch customers.")

st.subheader("Change Impact Analysis")
impact_df = normalize_change_impact(dashboard["change_impact_analysis"])
st.dataframe(impact_df, use_container_width=True)

st.subheader("AI-Style Recommendations")
for rec in dashboard["recommendations"]:
    st.write(f"- {rec}")

st.divider()

st.subheader("💬 Ask the Modernization Assistant")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

question = st.chat_input(
    "Ask about failed cases, AUTHDEC, batch validation, CFG/PDG, or impact analysis..."
)

if question:
    response = answer_question(question, dashboard)
    st.session_state.chat_history.append(("user", question))
    st.session_state.chat_history.append(("assistant", response))

for role, message in st.session_state.chat_history:
    with st.chat_message(role):
        st.markdown(message)