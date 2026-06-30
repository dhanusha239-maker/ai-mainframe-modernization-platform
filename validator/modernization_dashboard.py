import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict


PROJECT_ROOT = Path(__file__).resolve().parent.parent

ANALYSIS_REPORT = PROJECT_ROOT / "analysis_report.json"
BEHAVIOR_RESULTS = PROJECT_ROOT / "docs" / "behavior_comparison_results.json"

DOCS_DIR = PROJECT_ROOT / "docs"
DASHBOARD_JSON = DOCS_DIR / "modernization_dashboard.json"
DASHBOARD_MD = DOCS_DIR / "modernization_dashboard.md"


ERROR_REASON_MAP = {
    "E001": "Customer validation failure",
    "E002": "Card status failure",
    "E003": "Limit exceeded",
    "E004": "Fraud risk detected",
    "0000": "No error",
    "": "No error code captured",
}


def load_json(path):
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def all_modules(analysis):
    modules = set()

    for section in [
        "reads",
        "writes",
        "return_codes",
        "conditions",
        "module_parameter_context",
        "register_map",
        "record_buffer_reads",
        "record_buffer_writes",
        "condition_branches",
        "cfg",
        "pdg",
        "control_flow_graph",
        "program_dependency_graph",
    ]:
        value = analysis.get(section, {})
        if isinstance(value, dict):
            modules.update(value.keys())

    return sorted(modules)


def get_first_existing_dict(data, keys):
    for key in keys:
        value = data.get(key)
        if isinstance(value, dict) and value:
            return key, value

    return None, {}


def build_cfg_pdg_summary(analysis):
    """
    Build dashboard-level CFG/PDG metrics.

    Even if raw CFG/PDG graph objects are not exported in analysis_report.json,
    we can still calculate useful summary metrics from existing analyzer output.

    CFG summary uses:
      - conditions
      - condition_branches

    PDG summary uses:
      - reads
      - writes
      - symbol_readers
      - symbol_writers
    """

    conditions = analysis.get("conditions", {})
    condition_branches = analysis.get("condition_branches", {})

    reads = analysis.get("reads", {})
    writes = analysis.get("writes", {})
    symbol_readers = analysis.get("symbol_readers", {})
    symbol_writers = analysis.get("symbol_writers", {})

    modules = set()
    modules.update(conditions.keys())
    modules.update(condition_branches.keys())
    modules.update(reads.keys())
    modules.update(writes.keys())

    cfg_condition_count = sum(
        len(items) for items in conditions.values()
        if isinstance(items, list)
    )

    cfg_branch_count = sum(
        len(items) for items in condition_branches.values()
        if isinstance(items, list)
    )

    cfg_module_count = len(
        set(conditions.keys()) | set(condition_branches.keys())
    )

    pdg_read_edges = sum(
        len(items) for items in reads.values()
        if isinstance(items, list)
    )

    pdg_write_edges = sum(
        len(items) for items in writes.values()
        if isinstance(items, list)
    )

    pdg_symbol_dependency_edges = 0

    all_symbols = set(symbol_readers.keys()) | set(symbol_writers.keys())

    for symbol in all_symbols:
        readers = symbol_readers.get(symbol, [])
        writers = symbol_writers.get(symbol, [])

        pdg_symbol_dependency_edges += len(readers) + len(writers)

    pdg_module_count = len(set(reads.keys()) | set(writes.keys()))

    return {
        "cfg_available": cfg_condition_count > 0 or cfg_branch_count > 0,
        "pdg_available": pdg_read_edges > 0 or pdg_write_edges > 0,
        "cfg_source_key": "derived_from_conditions_and_branches",
        "pdg_source_key": "derived_from_reads_writes_and_symbol_dependencies",
        "cfg_module_count": cfg_module_count,
        "pdg_module_count": pdg_module_count,
        "cfg_condition_count": cfg_condition_count,
        "cfg_branch_count": cfg_branch_count,
        "pdg_read_edges": pdg_read_edges,
        "pdg_write_edges": pdg_write_edges,
        "pdg_symbol_dependency_edges": pdg_symbol_dependency_edges,
    }

def build_module_summary(analysis, behavior_results):
    modules = all_modules(analysis)
    behavior_by_module = defaultdict(list)

    for result in behavior_results:
        module = result.get("module", "UNKNOWN")
        behavior_by_module[module].append(result)

    summaries = []

    for module in modules:
        reads = analysis.get("reads", {}).get(module, [])
        writes = analysis.get("writes", {}).get(module, [])
        return_codes = analysis.get("return_codes", {}).get(module, [])
        conditions = analysis.get("conditions", {}).get(module, [])

        module_results = behavior_by_module.get(module, [])
        match_scores = [
            item.get("comparison", {}).get("match_score", 0)
            for item in module_results
        ]

        avg_match = round(sum(match_scores) / len(match_scores), 2) if match_scores else None

        summaries.append(
            {
                "module": module,
                "fields_read": reads,
                "fields_written": writes,
                "return_codes": return_codes,
                "condition_count": len(conditions),
                "behavior_test_count": len(module_results),
                "average_behavior_match": avg_match,
            }
        )

    return summaries


def diagnose_failed_case(item):
    case_id = str(item.get("case_id", ""))
    module = str(item.get("module", ""))
    expected = item.get("expected_asm_output", {})
    actual = item.get("actual_java_output", {})
    mismatches = item.get("comparison", {}).get("mismatched_fields", [])
    mismatch_text = " ".join(str(x) for x in mismatches).upper()

    if module == "AUTHDEC" or "AUTHDEC" in case_id or "AUTHSTAT" in mismatch_text:
        expected_auth = expected.get("AUTHSTAT")
        actual_auth = actual.get("AUTHSTAT")

        if expected_auth == "APPRV" and actual_auth != "APPRV":
            return (
                "AUTHDEC approval-path mismatch. When ERRCODE is 0000, "
                "expected AUTHSTAT is APPRV, but generated Java did not produce APPRV. "
                "Suggested review: approval branch translation in AUTHDEC."
            )

    if "TXFEE" in mismatch_text:
        return (
            "Fee calculation mismatch. Suggested review: packed-decimal ZAP/MP/SRP "
            "translation and rounding behavior."
        )

    if "ERRCODE" in mismatch_text:
        return (
            "Error-code mismatch. Suggested review: validation branch ordering and "
            "reject-path control flow."
        )

    if "RC" in mismatch_text:
        return (
            "Return-code mismatch. Suggested review: final application RC preservation "
            "and validation-path return behavior."
        )

    return "Review generated Java output against expected assembler behavior."


def build_behavior_summary(behavior_results):
    total = len(behavior_results)
    passed = sum(
        1
        for item in behavior_results
        if item.get("comparison", {}).get("match_score") == 100.0
    )
    failed = total - passed

    avg_score = (
        round(
            sum(item.get("comparison", {}).get("match_score", 0) for item in behavior_results) / total,
            2,
        )
        if total
        else 0
    )

    failed_cases = []

    for item in behavior_results:
        comparison = item.get("comparison", {})
        if comparison.get("match_score") == 100.0:
            continue

        failed_cases.append(
            {
                "case_id": item.get("case_id"),
                "module": item.get("module"),
                "customer_id": item.get("customer_id", ""),
                "match_score": comparison.get("match_score"),
                "mismatches": comparison.get("mismatched_fields", []),
                "expected": item.get("expected_asm_output", {}),
                "actual": item.get("actual_java_output", {}),
                "diagnosis": diagnose_failed_case(item),
            }
        )

    return {
        "total_test_cases": total,
        "passed": passed,
        "failed": failed,
        "average_behavior_match": avg_score,
        "failed_cases": failed_cases,
    }


def build_batch_summary(behavior_results):
    batch_items = [
        item
        for item in behavior_results
        if item.get("source") == "batch_csv" or str(item.get("case_id", "")).startswith("TX")
    ]

    total = len(batch_items)
    passed = sum(
        1
        for item in batch_items
        if item.get("comparison", {}).get("match_score") == 100.0
    )
    failed = total - passed

    failed_customers = []

    for item in batch_items:
        if item.get("comparison", {}).get("match_score") != 100.0:
            failed_customers.append(
                {
                    "case_id": item.get("case_id"),
                    "customer_id": item.get("customer_id", item.get("input", {}).get("TXCUST", "")),
                    "module": item.get("module"),
                    "mismatches": item.get("comparison", {}).get("mismatched_fields", []),
                    "diagnosis": diagnose_failed_case(item),
                }
            )

    return {
        "batch_records": total,
        "batch_passed": passed,
        "batch_failed": failed,
        "failed_customers": failed_customers,
    }


def build_change_impact_summary(analysis):
    readers = analysis.get("symbol_readers", {})
    writers = analysis.get("symbol_writers", {})

    symbols = sorted(set(readers.keys()) | set(writers.keys()))
    impact_items = []

    for symbol in symbols:
        read_by = readers.get(symbol, [])
        written_by = writers.get(symbol, [])

        impacted_modules = []
        for module in written_by + read_by:
            if module not in impacted_modules:
                impacted_modules.append(module)

        impact_count = len(impacted_modules)

        if impact_count >= 5:
            impact_level = "High"
        elif impact_count >= 3:
            impact_level = "Medium"
        else:
            impact_level = "Low"

        impact_items.append(
            {
                "symbol": symbol,
                "written_by": written_by,
                "read_by": read_by,
                "impacted_modules": impacted_modules,
                "impact_count": impact_count,
                "impact_level": impact_level,
                "recommendation": build_change_recommendation(symbol, impact_level),
            }
        )

    impact_items.sort(key=lambda x: x["impact_count"], reverse=True)
    return impact_items


def build_change_recommendation(symbol, impact_level):
    if impact_level == "High":
        return (
            f"Changing {symbol} may affect several modules. "
            "Review downstream validations, generated Java mappings, and behavior test cases."
        )

    if impact_level == "Medium":
        return (
            f"Changing {symbol} has moderate impact. "
            "Run module and application behavior validation after modification."
        )

    return (
        f"Changing {symbol} appears low impact, but regression validation is still recommended."
    )


def build_recommendations(behavior_summary, batch_summary, change_impact):
    recommendations = []

    authdec_cases = [
        case
        for case in behavior_summary["failed_cases"]
        if "AUTHDEC" in str(case.get("case_id", "")) or "AUTHSTAT" in str(case.get("mismatches", "")).upper()
    ]

    if authdec_cases:
        recommendations.append(
            "AUTHDEC approval path requires review: when ERRCODE = 0000, "
            "expected AUTHSTAT is APPRV. The validation engine detected this as the main remaining behavior gap."
        )

    if behavior_summary["failed"] > 0:
        recommendations.append(
            "Review failed behavior comparison cases and update translator rules or document known limitations."
        )

    if batch_summary["batch_failed"] > 0:
        recommendations.append(
            "Review failed batch customer IDs. The current failed batch case is linked to the same AUTHDEC approval-path behavior."
        )

    high_impact = [item for item in change_impact if item["impact_level"] == "High"]
    if high_impact:
        recommendations.append(
            "High-impact business fields detected. Any change to these fields should trigger full application and batch regression testing."
        )

    recommendations.append(
        "Use this dashboard with the Week 1 ML risk predictor output to create a combined modernization intelligence report."
    )

    return recommendations


def build_dashboard():
    analysis = load_json(ANALYSIS_REPORT)
    behavior_results = load_json(BEHAVIOR_RESULTS)

    module_summary = build_module_summary(analysis, behavior_results)
    behavior_summary = build_behavior_summary(behavior_results)
    batch_summary = build_batch_summary(behavior_results)
    change_impact = build_change_impact_summary(analysis)
    cfg_pdg_summary = build_cfg_pdg_summary(analysis)

    return {
        "generated_on": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "project": "AI-Powered Legacy Software Intelligence & Modernization Platform",
        "version": "Week 2 Modernization Dashboard",
        "summary": {
            "module_count": len(module_summary),
            "behavior_match_score": behavior_summary["average_behavior_match"],
            "total_behavior_tests": behavior_summary["total_test_cases"],
            "passed_tests": behavior_summary["passed"],
            "failed_tests": behavior_summary["failed"],
            "batch_records": batch_summary["batch_records"],
            "batch_passed": batch_summary["batch_passed"],
            "batch_failed": batch_summary["batch_failed"],
        },
        "cfg_pdg_summary": cfg_pdg_summary,
        "module_summary": module_summary,
        "behavior_summary": behavior_summary,
        "batch_summary": batch_summary,
        "change_impact_analysis": change_impact,
        "recommendations": build_recommendations(
            behavior_summary,
            batch_summary,
            change_impact,
        ),
    }


def save_json(dashboard):
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    with open(DASHBOARD_JSON, "w", encoding="utf-8") as f:
        json.dump(dashboard, f, indent=2)

    return DASHBOARD_JSON


def save_markdown(dashboard):
    lines = []

    lines.append("# Modernization Dashboard")
    lines.append("")
    lines.append(f"Generated on: `{dashboard['generated_on']}`")
    lines.append("")

    lines.append("## 1. Executive Summary")
    lines.append("")
    summary = dashboard["summary"]
    lines.append(f"- Modules analyzed: `{summary['module_count']}`")
    lines.append(f"- Behavior match score: `{summary['behavior_match_score']}%`")
    lines.append(f"- Total behavior tests: `{summary['total_behavior_tests']}`")
    lines.append(f"- Passed tests: `{summary['passed_tests']}`")
    lines.append(f"- Failed tests: `{summary['failed_tests']}`")
    lines.append(f"- Batch records: `{summary['batch_records']}`")
    lines.append(f"- Batch passed: `{summary['batch_passed']}`")
    lines.append(f"- Batch failed: `{summary['batch_failed']}`")
    lines.append("")

    lines.append("## 2. CFG / PDG Summary")
    lines.append("")
    cfg_pdg = dashboard["cfg_pdg_summary"]
    lines.append(f"- CFG available: `{cfg_pdg['cfg_available']}`")
    lines.append(f"- PDG available: `{cfg_pdg['pdg_available']}`")
    lines.append(f"- CFG source key: `{cfg_pdg['cfg_source_key']}`")
    lines.append(f"- PDG source key: `{cfg_pdg['pdg_source_key']}`")
    lines.append(f"- CFG module count: `{cfg_pdg['cfg_module_count']}`")
    lines.append(f"- PDG module count: `{cfg_pdg['pdg_module_count']}`")
    lines.append(f"- CFG condition count: `{cfg_pdg['cfg_condition_count']}`")
    lines.append(f"- CFG branch count: `{cfg_pdg['cfg_branch_count']}`")
    lines.append(f"- PDG read edges: `{cfg_pdg['pdg_read_edges']}`")
    lines.append(f"- PDG write edges: `{cfg_pdg['pdg_write_edges']}`")
    lines.append(f"- PDG symbol dependency edges: `{cfg_pdg['pdg_symbol_dependency_edges']}`")
    lines.append("")

    lines.append("## 3. Module Summary")
    lines.append("")
    lines.append("| Module | Reads | Writes | Conditions | Behavior Match |")
    lines.append("|---|---:|---:|---:|---:|")

    for item in dashboard["module_summary"]:
        match = item["average_behavior_match"]
        match_text = "N/A" if match is None else f"{match}%"

        lines.append(
            f"| `{item['module']}` "
            f"| {len(item['fields_read'])} "
            f"| {len(item['fields_written'])} "
            f"| {item['condition_count']} "
            f"| {match_text} |"
        )

    lines.append("")

    lines.append("## 4. Behavior Validation Summary")
    lines.append("")
    behavior = dashboard["behavior_summary"]
    lines.append(f"- Total tests: `{behavior['total_test_cases']}`")
    lines.append(f"- Passed: `{behavior['passed']}`")
    lines.append(f"- Failed: `{behavior['failed']}`")
    lines.append(f"- Average match score: `{behavior['average_behavior_match']}%`")
    lines.append("")

    if behavior["failed_cases"]:
        lines.append("### Failed Behavior Cases")
        lines.append("")
        for case in behavior["failed_cases"]:
            lines.append(f"- `{case['case_id']}` in module `{case['module']}`")
            if case.get("customer_id"):
                lines.append(f"  - Customer ID: `{case['customer_id']}`")
            lines.append(f"  - Match score: `{case['match_score']}%`")
            lines.append(f"  - Diagnosis: {case['diagnosis']}")
        lines.append("")
    else:
        lines.append("No failed behavior cases detected.")
        lines.append("")

    lines.append("## 5. Batch Validation Summary")
    lines.append("")
    batch = dashboard["batch_summary"]
    lines.append(f"- Batch records: `{batch['batch_records']}`")
    lines.append(f"- Batch passed: `{batch['batch_passed']}`")
    lines.append(f"- Batch failed: `{batch['batch_failed']}`")
    lines.append("")

    if batch["failed_customers"]:
        lines.append("### Failed Batch Customers")
        lines.append("")
        for item in batch["failed_customers"]:
            lines.append(
                f"- Case `{item['case_id']}` / Customer `{item['customer_id']}` / Module `{item['module']}`"
            )
            lines.append(f"  - Diagnosis: {item['diagnosis']}")
        lines.append("")
    else:
        lines.append("No failed batch customers detected.")
        lines.append("")

    lines.append("## 6. Change Impact Analysis")
    lines.append("")
    lines.append("| Symbol | Written By | Read By | Impacted Modules | Impact Level |")
    lines.append("|---|---|---|---:|---|")

    for item in dashboard["change_impact_analysis"][:15]:
        lines.append(
            f"| `{item['symbol']}` "
            f"| {', '.join(f'`{x}`' for x in item['written_by']) or 'None'} "
            f"| {', '.join(f'`{x}`' for x in item['read_by']) or 'None'} "
            f"| {item['impact_count']} "
            f"| `{item['impact_level']}` |"
        )

    lines.append("")

    lines.append("## 7. AI-Style Modernization Recommendations")
    lines.append("")
    for rec in dashboard["recommendations"]:
        lines.append(f"- {rec}")
    lines.append("")

    lines.append("## 8. Week 1 ML Integration Placeholder")
    lines.append("")
    lines.append(
        "Week 1 ML risk predictor output can be added here later. "
        "This dashboard intentionally does not retrain ML models. "
        "It consumes modernization and validation outputs from Week 2."
    )
    lines.append("")

    content = "\n".join(lines)

    with open(DASHBOARD_MD, "w", encoding="utf-8") as f:
        f.write(content)

    return DASHBOARD_MD


def main():
    dashboard = build_dashboard()

    json_path = save_json(dashboard)
    md_path = save_markdown(dashboard)

    print("Modernization dashboard generated.")
    print(f"JSON: {json_path}")
    print(f"Markdown: {md_path}")


if __name__ == "__main__":
    main()
