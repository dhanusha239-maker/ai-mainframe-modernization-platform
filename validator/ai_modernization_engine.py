"""
AI Modernization Intelligence Engine - Production Final Version
================================================================

Purpose
-------
This is the single AI backend file for the project.
It reads project evidence, creates one clean AI modernization report,
optionally calls OpenAI for an LLM-enhanced narrative, and supports a
small grounded chatbot mode.

Generated files by default:
    docs/ai_modernization_report.md
    docs/ai_llm_integration_details.json

No separate ai_failure_diagnostics.md, ai_test_recommendations.md, or
ai_chat_context.json is required. Failure diagnostics and test
recommendations are included inside the main report.

Run:
    python validator/ai_modernization_engine.py
    python validator/ai_modernization_engine.py --ask "Why did AUTHDEC fail?"

Optional LLM setup:
    python -m pip install openai
    $env:OPENAI_API_KEY="your_real_key"
    $env:OPENAI_MODEL="gpt-4.1-mini"
    $env:AI_USE_LLM="1"
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


BRANCH_OPS = {
    "B", "BC", "BE", "BNE", "BNZ", "BZ", "BH", "BL", "BNH", "BNL",
    "BR", "BRC", "BCR", "BCT", "BXH", "BXLE", "J", "JE", "JNE", "JNZ",
    "JZ", "JH", "JL", "JNH", "JNL",
}

CALL_OPS = {"CALL", "BAL", "BALR", "BAS", "BASR", "LINK", "XCTL", "LOAD"}
IO_OPS = {"GET", "PUT", "OPEN", "CLOSE", "READ", "WRITE", "POINT", "CHECK"}
PACKED_DECIMAL_OPS = {"PACK", "UNPK", "ZAP", "CP", "MP", "DP", "AP", "SP", "SRP", "CVB", "CVD"}
DATA_OPS = {"DS", "DC", "DSECT", "CSECT", "USING", "DROP", "EQU", "ACB", "RPL", "EXLST", "DCB"}
GENERAL_SUPPORTED_OPS = {
    "MVC", "CLC", "CLI", "ST", "STM", "L", "LR", "LTR", "LA", "A", "AR", "SR",
    "CR", "C", "CH", "STC", "MVI", "OI", "NI", "XI", "RETURN", "SAVE", "WTO",
    "EJECT", "END", "SPACE", "TITLE", "COPY", "ORG", "LTORG", "NOP", "SVC", "TR", "TRT",
}
KNOWN_SUPPORTED_OPS = BRANCH_OPS | CALL_OPS | IO_OPS | PACKED_DECIMAL_OPS | DATA_OPS | GENERAL_SUPPORTED_OPS
KNOWN_MODULES = [
    "MAINDRV", "TXREAD", "CUSTVAL", "CARDSTAT", "LIMITCHK", "FRDCHK",
    "FEECALC", "AUTHDEC", "AUDWRITE", "VSAMPACK", "BCTCOUNT",
]


@dataclass
class ModuleProfile:
    module_name: str
    source_path: str
    loc: int
    branch_instruction_count: int
    call_instruction_count: int
    file_io_count: int
    packed_decimal_instruction_count: int
    unsupported_instruction_count: int
    comment_ratio: float
    risk_level: str
    risk_score: int
    risk_factors: List[str]
    modernization_recommendations: List[str]
    recommended_tests: List[str]


@dataclass
class FailedTest:
    name: str
    module: str
    match_score: Optional[float]
    mismatches: List[str]
    classification: str
    reason: str
    action: str


@dataclass
class BehaviorSummary:
    total_cases: Optional[int]
    passed_cases: Optional[int]
    failed_cases: Optional[int]
    average_score: Optional[float]
    failed_tests: List[FailedTest]


def now_iso() -> str:
    return _dt.datetime.now().replace(microsecond=0).isoformat()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def find_project_root(start: Optional[Path] = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in [current] + list(current.parents):
        if (candidate / "validator").exists() and ((candidate / "HLASM").exists() or (candidate / "docs").exists()):
            return candidate
    return current


def read_text(path: Path, limit: Optional[int] = None) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="ignore")
    return text[:limit] if limit else text


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def truncate(text: str, max_chars: int = 12000) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n...[truncated]..."


def dedupe(items: Iterable[str]) -> List[str]:
    seen = set()
    output: List[str] = []
    for item in items:
        key = str(item).strip().lower()
        if key and key not in seen:
            output.append(str(item).strip())
            seen.add(key)
    return output


def clean_module_name(path: Path) -> str:
    name = path.name
    lower = name.lower()
    for suffix in (".asm.txt", ".asm", ".txt"):
        if lower.endswith(suffix):
            name = name[: -len(suffix)]
            break
    return name.upper()


def find_hlasm_files(hlasm_dir: Path) -> List[Path]:
    if not hlasm_dir.exists():
        return []
    patterns = ["*.ASM", "*.asm", "*.asm.txt", "*.ASM.txt"]
    result: List[Path] = []
    for pattern in patterns:
        result.extend(hlasm_dir.rglob(pattern))
    # In this project files are *.asm.txt. Keep only likely HLASM files.
    unique = {str(path.resolve()).lower(): path for path in result if path.is_file()}
    return sorted(unique.values(), key=lambda p: p.name.upper())


def parse_opcode(raw_line: str) -> Optional[str]:
    stripped = raw_line.strip()
    if not stripped or stripped.startswith("*") or stripped.startswith(".*"):
        return None
    # Remove inline comments after a long gap if present, but keep assembler operands.
    parts = stripped.split()
    if not parts:
        return None
    first = parts[0].upper()
    if first in KNOWN_SUPPORTED_OPS:
        return first
    if len(parts) >= 2:
        return parts[1].upper()
    return first


def build_recommendations(module: str, factors: List[str]) -> List[str]:
    recs: List[str] = []
    if any("IO" in f or "VSAM" in f or "batch" in f.lower() for f in factors):
        recs.append("Preserve DDNAME/file mapping and validate input/output record counts.")
        recs.append("Separate record parsing, business transformation, and file writing in Java.")
    if any("packed decimal" in f for f in factors):
        recs.append("Validate packed decimal scale, implied cents, truncation, and rounding against the HLASM instruction sequence.")
    if any("branch" in f for f in factors):
        recs.append("Use CFG review to ensure branch paths have matching regression tests.")
    if any("source behavior" in f for f in factors):
        recs.append("Resolve or formally accept the source behavior issue before production migration sign-off.")
    if module == "AUTHDEC":
        recs.append("Review approval/rejection branch logic before treating translated output as business-correct.")
    if module == "VSAMPACK":
        recs.append("Preserve A/B/T/X fixed-width segment scanning and implied-cent numeric output.")
    if module == "MAINDRV":
        recs.append("Treat this as an orchestration module and validate complete module-to-module flow.")
    if not recs:
        recs.append("Proceed with standard translation validation and regression testing.")
    return dedupe(recs)


def build_test_recommendations(module: str, branch_count: int, io_count: int, packed_count: int) -> List[str]:
    tests: List[str] = []
    if branch_count:
        tests.append("Test true and false outcomes for major branches.")
        tests.append("Add boundary tests for equality comparison conditions.")
    if io_count:
        tests.append("Test empty input and multiple-record input files.")
        tests.append("Verify output record count and EOF behavior.")
    if packed_count:
        tests.append("Test zero, small, high-value, and fractional-cent packed decimal values.")
        tests.append("Confirm truncation/rounding behavior matches HLASM instructions.")
    if module == "LIMITCHK":
        tests.extend(["TXAMT below limit", "TXAMT equal to limit", "TXAMT above limit"])
    if module == "VSAMPACK":
        tests.extend([
            "Record with A/B/T/X segments updates B from T tax calculation.",
            "Record with B but no T keeps B unchanged.",
            "Record with T but no B avoids invalid update.",
            "Fractional-cent tax follows HLASM truncation when no SRP rounding exists.",
        ])
    if module == "AUTHDEC":
        tests.extend(["ERRCODE 0000 approval path", "Non-zero ERRCODE rejection path"])
    if not tests:
        tests.append("Run smoke test and compare RC, status fields, and output records.")
    return dedupe(tests)


def analyze_hlasm_module(path: Path, known_issues_text: str) -> ModuleProfile:
    text = read_text(path)
    lines = text.splitlines()
    code_lines = [line for line in lines if line.strip() and not line.strip().startswith("*")]
    comment_lines = [line for line in lines if line.strip().startswith("*")]
    opcodes = [op for op in (parse_opcode(line) for line in code_lines) if op]

    module = clean_module_name(path)
    branch_count = sum(op in BRANCH_OPS for op in opcodes)
    call_count = sum(op in CALL_OPS for op in opcodes)
    io_count = sum(op in IO_OPS for op in opcodes)
    packed_count = sum(op in PACKED_DECIMAL_OPS for op in opcodes)
    unsupported = sum(op not in KNOWN_SUPPORTED_OPS for op in opcodes)
    loc = len(code_lines)
    comment_ratio = round(len(comment_lines) / max(1, len(lines)), 3)

    score = 10
    factors: List[str] = []
    if loc >= 120:
        score += 15; factors.append("large module size")
    elif loc >= 60:
        score += 8; factors.append("moderate module size")
    if branch_count >= 10:
        score += 20; factors.append("complex branching")
    elif branch_count >= 4:
        score += 10; factors.append("conditional branching")
    if call_count >= 4:
        score += 15; factors.append("multiple external/control-transfer calls")
    elif call_count >= 1:
        score += 6; factors.append("cross-module/control-transfer dependency")
    if io_count >= 3:
        score += 18; factors.append("file or VSAM IO behavior")
    elif io_count >= 1:
        score += 8; factors.append("IO operation dependency")
    if packed_count >= 3:
        score += 20; factors.append("packed decimal arithmetic/comparison")
    elif packed_count >= 1:
        score += 10; factors.append("packed decimal operation")
    if unsupported > 0:
        score += min(12, unsupported * 2); factors.append("unsupported or partially supported instructions")
    if comment_ratio < 0.08 and loc >= 20:
        score += 8; factors.append("low comment ratio")
    if module in known_issues_text.upper():
        score += 20; factors.append("known source behavior issue documented")
    if module in {"MAINDRV", "VSAMPACK"}:
        score += 10; factors.append("batch orchestration or record-transformation module")

    score = min(100, score)
    risk = "High" if score >= 70 else "Medium" if score >= 40 else "Low"
    return ModuleProfile(
        module_name=module,
        source_path=str(path),
        loc=loc,
        branch_instruction_count=branch_count,
        call_instruction_count=call_count,
        file_io_count=io_count,
        packed_decimal_instruction_count=packed_count,
        unsupported_instruction_count=unsupported,
        comment_ratio=comment_ratio,
        risk_level=risk,
        risk_score=score,
        risk_factors=factors or ["simple supported instruction profile"],
        modernization_recommendations=build_recommendations(module, factors),
        recommended_tests=build_test_recommendations(module, branch_count, io_count, packed_count),
    )


def extract_summary_number(text: str, label: str) -> Optional[float]:
    pattern = rf"{re.escape(label)}\s*:\s*`?([0-9]+(?:\.[0-9]+)?)%?`?"
    m = re.search(pattern, text, flags=re.IGNORECASE)
    return float(m.group(1)) if m else None


def infer_module_from_test_name(name: str) -> str:
    upper = name.upper()
    for module in KNOWN_MODULES:
        if module in upper:
            return module
    if "APP_APPROVAL" in upper:
        return "MAINDRV"
    return "UNKNOWN"


def classify_failure(case_id: str, module: str, mismatches: List[str], known_issues_text: str) -> Tuple[str, str, str]:
    upper = f"{case_id} {module} {' '.join(mismatches)}".upper()
    known = known_issues_text.upper()
    if "AUTHDEC" in upper or "APP_APPROVAL" in upper:
        if "AUTHDEC" in known or "APPROVAL" in known:
            return (
                "Known HLASM source behavior issue",
                "The failure aligns with the documented AUTHDEC approval-path issue.",
                "Review or fix AUTHDEC source logic before production migration sign-off.",
            )
        return (
            "Probable AUTHDEC source behavior issue",
            "The failure is related to approval/rejection status handling.",
            "Review AUTHDEC branch conditions and compare with expected business approval behavior.",
        )
    if any(token in upper for token in ["DECIMAL", "PACK", "ROUND", "CENTS", "BIGDECIMAL"]):
        return (
            "Packed decimal precision issue",
            "The mismatch references decimal or packed-decimal behavior.",
            "Compare Java scale/truncation rules against PACK/MP/SRP/UNPK behavior.",
        )
    if any(token in upper for token in ["FILE", "DDNAME", "VSAM", "EOF", "RECORD"]):
        return (
            "File IO or batch-flow issue",
            "The mismatch references file, record, DDNAME, VSAM, or EOF behavior.",
            "Validate path resolution, record count, EOF handling, and output materialization.",
        )
    return (
        "Translator or test expectation review",
        "The mismatch is a real failed test but does not match a known issue category.",
        "Compare expected behavior, HLASM path, generated Java path, and test input data.",
    )


def extract_failed_tests_from_report(report_text: str, known_issues_text: str) -> List[FailedTest]:
    """Extract only real failed Test Case sections.

    This intentionally ignores summary lines such as 'Failed cases: 2',
    'Batch failed: 0', 'Failure customer IDs: None', and every
    'No mismatches detected.' line.
    """
    if not report_text:
        return []

    parts = re.split(r"(?m)^###\s+Test Case:\s+`([^`]+)`\s*$", report_text)
    if len(parts) < 3:
        return []

    failed_tests: List[FailedTest] = []
    for i in range(1, len(parts), 2):
        case_id = parts[i].strip()
        block = parts[i + 1]

        score = extract_summary_number(block, "Match score")
        mismatch_lines: List[str] = []
        if "**Mismatches:**" in block:
            tail = block.split("**Mismatches:**", 1)[1]
            # Stay inside this test block only.
            for line in tail.splitlines():
                stripped = line.strip()
                if not stripped:
                    continue
                if stripped.startswith("### Test Case:"):
                    break
                if stripped.startswith("-"):
                    mismatch_lines.append(stripped)

        is_failed = (score is not None and score < 100.0) or bool(mismatch_lines)
        if not is_failed:
            continue

        module_match = re.search(r"(?m)^-\s+Module:\s+`?([^`\n]+)`?", block)
        module = module_match.group(1).strip() if module_match else infer_module_from_test_name(case_id)
        classification, reason, action = classify_failure(case_id, module, mismatch_lines, known_issues_text)
        failed_tests.append(FailedTest(case_id, module, score, mismatch_lines, classification, reason, action))

    return failed_tests


def parse_behavior_summary(project_root: Path, known_issues_text: str) -> BehaviorSummary:
    report_text = read_text(project_root / "docs" / "behavior_comparison_report.md")
    total = extract_summary_number(report_text, "Total test cases")
    passed = extract_summary_number(report_text, "Passed cases")
    failed_count = extract_summary_number(report_text, "Failed cases")
    average = extract_summary_number(report_text, "Average behavior match score")
    failed_tests = extract_failed_tests_from_report(report_text, known_issues_text)

    # Trust summary count for Total/Passed/Failed, but never manufacture fake failure rows.
    return BehaviorSummary(
        total_cases=int(total) if total is not None else None,
        passed_cases=int(passed) if passed is not None else None,
        failed_cases=int(failed_count) if failed_count is not None else len(failed_tests),
        average_score=float(average) if average is not None else None,
        failed_tests=failed_tests,
    )


def collect_evidence(root: Optional[Path] = None) -> Dict[str, Any]:
    project_root = find_project_root(root)
    docs_dir = project_root / "docs"
    hlasm_dir = project_root / "HLASM"
    generated_dir = project_root / "generated_java"
    known_issues_text = read_text(docs_dir / "known_hlasm_issues.md")

    hlasm_files = find_hlasm_files(hlasm_dir)
    modules = [asdict(analyze_hlasm_module(path, known_issues_text)) for path in hlasm_files]
    behavior = parse_behavior_summary(project_root, known_issues_text)

    return {
        "project_root": str(project_root),
        "generated_at": now_iso(),
        "input_artifacts": {
            "HLASM assembler files": len(hlasm_files),
            "docs/behavior_comparison_report.md": (docs_dir / "behavior_comparison_report.md").exists(),
            "docs/behavior_comparison_results.json": (docs_dir / "behavior_comparison_results.json").exists(),
            "docs/known_hlasm_issues.md": (docs_dir / "known_hlasm_issues.md").exists(),
            "analysis_report.json": (project_root / "analysis_report.json").exists(),
            "instruction_coverage_matrix_v3.md": (project_root / "instruction_coverage_matrix_v3.md").exists(),
            "generated_java/*.java": generated_dir.exists() and any(generated_dir.glob("*.java")),
        },
        "hlasm_files": [str(path.relative_to(project_root)) for path in hlasm_files],
        "module_profiles": modules,
        "behavior_summary": {
            "total_cases": behavior.total_cases,
            "passed_cases": behavior.passed_cases,
            "failed_cases": behavior.failed_cases,
            "average_score": behavior.average_score,
            "failed_tests": [asdict(test) for test in behavior.failed_tests],
        },
        "known_issues_text": known_issues_text,
    }


def markdown_table(headers: List[str], rows: List[List[Any]]) -> str:
    def cell(value: Any) -> str:
        return str(value).replace("\n", " ").replace("|", "\\|")
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(cell(v) for v in row) + " |")
    return "\n".join(out)


def bullets(items: Iterable[str]) -> str:
    vals = list(items)
    return "\n".join(f"- {v}" for v in vals) if vals else "- None"


def fmt(value: Any) -> str:
    return "Not available" if value is None else str(value)


def build_report(evidence: Dict[str, Any], llm_text: Optional[str], llm_usage: Dict[str, Any]) -> str:
    behavior = evidence["behavior_summary"]
    modules = evidence["module_profiles"]
    failed_tests = behavior["failed_tests"]

    module_rows = []
    for m in sorted(modules, key=lambda x: (-int(x["risk_score"]), x["module_name"])):
        module_rows.append([
            m["module_name"], m["risk_level"], m["risk_score"], m["loc"],
            m["branch_instruction_count"], m["file_io_count"], m["packed_decimal_instruction_count"],
            ", ".join(m["risk_factors"][:3]),
        ])

    report = f"""# AI Modernization Intelligence Report

Generated: {evidence['generated_at']}

## AI / LLM Integration Details

This report is generated by `validator/ai_modernization_engine.py`.

The deterministic evidence collector is the source of truth. OpenAI is used only for explanation, summarization, modernization recommendations, and chatbot answers when a valid API key is enabled.

- LLM provider: {llm_usage.get('provider')}
- LLM model: {llm_usage.get('model')}
- LLM used: {llm_usage.get('used')}
- Prompt SHA256: `{llm_usage.get('prompt_sha256')}`
- Context SHA256: `{llm_usage.get('context_sha256')}`

## Behavior Validation Summary

- Total test cases: {fmt(behavior.get('total_cases'))}
- Passed cases: {fmt(behavior.get('passed_cases'))}
- Failed cases: {fmt(behavior.get('failed_cases'))}
- Average behavior match score: {fmt(behavior.get('average_score'))}

## HLASM Files Found

{bullets(evidence['hlasm_files'])}

## Module Risk Ranking

{markdown_table(['Module','Risk','Score','LOC','Branches','IO','Packed Decimal','Top Factors'], module_rows or [['No HLASM modules found','','','','','','','']])}

## Failure Diagnostics

"""
    if failed_tests:
        report += f"The engine found **{len(failed_tests)} real failed test case(s)** from `docs/behavior_comparison_report.md`. Summary lines and `No mismatches detected` lines are intentionally ignored.\n\n"
        for ft in failed_tests:
            report += f"""### {ft['name']}

- Module: {ft['module']}
- Match score: {fmt(ft.get('match_score'))}%
- Classification: **{ft['classification']}**
- Reason: {ft['reason']}
- Recommended action: {ft['action']}

Mismatches:
{bullets(ft.get('mismatches', []))}

"""
    else:
        report += "No failed test-case mismatches were detected.\n\n"

    report += "## Module-Level Modernization Recommendations\n\n"
    for m in sorted(modules, key=lambda x: x["module_name"]):
        report += f"""### {m['module_name']}

Risk: **{m['risk_level']}** ({m['risk_score']}/100)

Primary risk factors:
{bullets(m['risk_factors'])}

Recommendations:
{bullets(m['modernization_recommendations'])}

Recommended tests:
{bullets(m['recommended_tests'])}

"""

    report += "## Grounding Artifact Status\n\n"
    artifact_rows = [[k, v if isinstance(v, int) else ("Found" if v else "Missing")] for k, v in evidence["input_artifacts"].items()]
    report += markdown_table(["Artifact", "Status"], artifact_rows)

    decision = "Review Required" if failed_tests else "Ready for next modernization review stage"
    report += f"""

## Human-in-the-Loop Migration Decision

Current recommendation: **{decision}**.

Reason: Most translated behavior is validated, but known source behavior issues or failed test cases must be reviewed before production migration sign-off. The platform should not silently change original business behavior.
"""

    report += "\n---\n\n# LLM-Enhanced Modernization Narrative\n\n"
    if llm_text:
        report += llm_text.strip() + "\n"
    else:
        report += f"LLM enhancement was not used. Deterministic report was generated.\n\nReason: {llm_usage.get('error')}\n"
    return report


def is_placeholder_key(api_key: str) -> bool:
    lower = (api_key or "").strip().lower()
    if not lower:
        return True
    return any(token in lower for token in ["your", "paste", "here", "example", "xxxx", "dummy"])


def build_llm_prompt(evidence: Dict[str, Any]) -> str:
    compact = {
        "behavior_summary": evidence["behavior_summary"],
        "module_profiles": evidence["module_profiles"],
        "input_artifacts": evidence["input_artifacts"],
        "known_issues_text": evidence.get("known_issues_text", "")[:2500],
    }
    return (
        "You are an enterprise legacy modernization architect.\n"
        "Use only the evidence JSON below. Do not invent facts.\n"
        "Write a concise modernization narrative with these sections:\n"
        "1. Executive summary\n"
        "2. Why this is AI-powered\n"
        "3. Risk interpretation\n"
        "4. Behavior validation interpretation\n"
        "5. Failure diagnostics\n"
        "6. Recommended next engineering actions\n\n"
        f"Evidence JSON:\n{json.dumps(compact, indent=2, ensure_ascii=False)}"
    )


def call_openai(prompt: str, purpose: str, evidence: Dict[str, Any]) -> Tuple[Optional[str], Dict[str, Any]]:
    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini").strip()
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    use_llm = os.getenv("AI_USE_LLM", "1").strip().lower() not in {"0", "false", "no"}
    usage = {
        "provider": "openai",
        "purpose": purpose,
        "model": model,
        "enabled": bool(use_llm),
        "used": False,
        "error": None,
        "prompt_sha256": sha256_text(prompt),
        "context_sha256": sha256_text(json.dumps(evidence, sort_keys=True, default=str)),
        "timestamp": now_iso(),
    }
    if not use_llm:
        usage["error"] = "AI_USE_LLM is disabled."
        return None, usage
    if is_placeholder_key(api_key):
        usage["error"] = "OPENAI_API_KEY is missing or still contains a placeholder value."
        return None, usage
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        response = client.responses.create(
            model=model,
            instructions="Generate evidence-grounded modernization explanations. Use only provided evidence.",
            input=prompt,
        )
        text = getattr(response, "output_text", None) or str(response)
        usage["used"] = True
        return text, usage
    except Exception as exc:
        usage["error"] = f"{type(exc).__name__}: {exc}"
        return None, usage


def generate_all(root: Optional[Path] = None) -> Dict[str, Path]:
    project_root = find_project_root(root)
    docs_dir = project_root / "docs"
    evidence = collect_evidence(project_root)
    prompt = build_llm_prompt(evidence)
    llm_text, usage = call_openai(prompt, "ai_modernization_report_generation", evidence)
    report = build_report(evidence, llm_text, usage)
    integration_details = {
        **usage,
        "generated_files": ["docs/ai_modernization_report.md", "docs/ai_llm_integration_details.json"],
        "input_artifacts": evidence["input_artifacts"],
        "important_note": "The deterministic evidence collector is the source of truth; LLM is an explanation layer.",
    }
    report_path = docs_dir / "ai_modernization_report.md"
    llm_details_path = docs_dir / "ai_llm_integration_details.json"
    write_text(report_path, report)
    write_json(llm_details_path, integration_details)
    return {"report": report_path, "llm_details": llm_details_path}


def answer_question(question: str, root: Optional[Path] = None) -> str:
    evidence = collect_evidence(find_project_root(root))
    # Small retrieval: include matching modules/failures plus summary.
    q = question.upper()
    focused: Dict[str, Any] = {
        "behavior_summary": evidence["behavior_summary"],
        "matched_modules": [m for m in evidence["module_profiles"] if m["module_name"] in q],
        "matched_failures": [f for f in evidence["behavior_summary"]["failed_tests"] if f["name"].upper() in q or f["module"].upper() in q],
        "known_issues_text": evidence.get("known_issues_text", "")[:2000],
    }
    if not focused["matched_modules"] and not focused["matched_failures"]:
        focused["matched_failures"] = evidence["behavior_summary"]["failed_tests"]
        focused["matched_modules"] = evidence["module_profiles"][:5]
    prompt = (
        "Answer the user question using only this project evidence. Be direct.\n\n"
        f"Question: {question}\n\nEvidence:\n{json.dumps(focused, indent=2, ensure_ascii=False)}"
    )
    text, usage = call_openai(prompt, "grounded_chatbot_answer", evidence)
    if text:
        return text + f"\n\nAI integration details: model={usage['model']}, prompt_sha256={usage['prompt_sha256']}"
    return (
        "Offline grounded answer: LLM was not used.\n\n"
        f"Reason: {usage.get('error')}\n\n"
        f"Relevant evidence:\n{json.dumps(focused, indent=2, ensure_ascii=False)[:4000]}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="AI Modernization Intelligence Engine")
    parser.add_argument("--ask", help="Ask a grounded chatbot question about the project.")
    parser.add_argument("--root", help="Project root path. Defaults to auto-detection.")
    args = parser.parse_args()
    root = Path(args.root).resolve() if args.root else None
    if args.ask:
        print(answer_question(args.ask, root))
        return
    paths = generate_all(root)
    print("AI Modernization Intelligence files generated:")
    for label, path in paths.items():
        print(f"- {label}: {path}")


if __name__ == "__main__":
    main()
