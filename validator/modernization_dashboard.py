"""
AI Modernization Dashboard

Purpose:
- Visual dashboard for the AI-Powered Legacy Software Intelligence & Modernization Platform.
- Reads existing project artifacts; does not create new files.
- Provides module exploration, CFG/PDG-style dependency views, field impact analysis, report viewer, and grounded chatbot.

Run from project root:
    python -m streamlit run validator/modernization_dashboard.py

Expected companion files:
    validator/ai_modernization_engine.py
    docs/ai_modernization_report.md
    docs/ai_llm_integration_details.json
    docs/behavior_comparison_report.md
    docs/known_hlasm_issues.md
    HLASM/*.asm.txt
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pandas as pd
import streamlit as st

try:
    from new_module_assessment_dashboard_section import render_new_module_assessment
except ImportError:
    from validator.new_module_assessment_dashboard_section import render_new_module_assessment


# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

BRANCH_OPS = {
    "B", "BC", "BE", "BNE", "BNZ", "BZ", "BH", "BL", "BNH", "BNL",
    "BR", "BRC", "BCR", "J", "JE", "JNE", "JNZ", "JZ", "JH", "JL",
    "JNH", "JNL", "BCT",
}

CALL_OPS = {"CALL", "BAL", "BALR", "BAS", "BASR", "LINK", "XCTL", "LOAD"}
IO_OPS = {"GET", "PUT", "OPEN", "CLOSE", "READ", "WRITE", "POINT", "CHECK"}
PACKED_DECIMAL_OPS = {"PACK", "UNPK", "ZAP", "CP", "MP", "DP", "AP", "SP", "SRP", "CVB", "CVD"}
DATA_OPS = {"DS", "DC", "DSECT", "CSECT", "USING", "DROP", "EQU", "ACB", "RPL", "EXLST", "DCB"}

KNOWN_OPS = (
    BRANCH_OPS
    | CALL_OPS
    | IO_OPS
    | PACKED_DECIMAL_OPS
    | DATA_OPS
    | {
        "MVC", "CLC", "CLI", "ST", "STM", "L", "LR", "LTR", "LA", "A", "AR", "SR",
        "CR", "C", "CH", "STC", "MVI", "OI", "NI", "XI", "RETURN", "SAVE", "EJECT",
        "END", "SPACE", "TITLE", "WTO", "COPY", "MACRO", "MEND", "NOP",
    }
)

REGISTER_PATTERN = re.compile(r"^R?\d+$", re.IGNORECASE)


@dataclass
class ModuleProfile:
    module: str
    source_path: str
    risk_level: str
    risk_score: int
    loc: int
    branches: int
    calls: int
    file_io: int
    packed_decimal: int
    unsupported: int
    comment_ratio: float
    called_modules: List[str]
    calling_modules: List[str]
    top_factors: List[str]
    recommendations: List[str]
    evidence_preview: List[str]


@dataclass
class FieldImpact:
    field: str
    defined_in: List[str]
    reader_modules: List[str]
    writer_modules: List[str]
    all_modules: List[str]
    risk_level: str
    reason: str
    evidence_lines: List[str]


# -----------------------------------------------------------------------------
# Project and file helpers
# -----------------------------------------------------------------------------


def find_project_root() -> Path:
    candidates = []

    try:
        candidates.append(Path.cwd().resolve())
    except Exception:
        pass

    try:
        candidates.append(Path(__file__).resolve().parent.parent)
        candidates.append(Path(__file__).resolve().parent)
    except Exception:
        pass

    for start in candidates:
        for candidate in [start] + list(start.parents):
            if (candidate / "validator").exists() and ((candidate / "HLASM").exists() or (candidate / "docs").exists()):
                return candidate

    return Path.cwd().resolve()


PROJECT_ROOT = find_project_root()
DOCS_DIR = PROJECT_ROOT / "docs"
HLASM_DIR = PROJECT_ROOT / "HLASM"
GENERATED_JAVA_DIR = PROJECT_ROOT / "generated_java"


def read_text(path: Path, limit: Optional[int] = None) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="ignore")
    return text[:limit] if limit else text


def read_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return None


def find_hlasm_files() -> List[Path]:
    if not HLASM_DIR.exists():
        return []
    patterns = ["*.ASM", "*.asm", "*.asm.txt", "*.ASM.txt"]
    paths: List[Path] = []
    for pattern in patterns:
        paths.extend(HLASM_DIR.rglob(pattern))
    return sorted(set(paths), key=lambda p: p.name.upper())


def module_name_from_path(path: Path) -> str:
    name = path.name
    for suffix in [".asm.txt", ".ASM.txt", ".ASM", ".asm", ".txt"]:
        if name.endswith(suffix):
            name = name[: -len(suffix)]
            break
    return name.upper()


def parse_opcode(raw_line: str) -> Optional[str]:
    stripped = raw_line.strip()
    if not stripped or stripped.startswith("*") or stripped.startswith(".*"):
        return None
    parts = stripped.split()
    if not parts:
        return None
    first = parts[0].upper()
    if first in KNOWN_OPS:
        return first
    if len(parts) >= 2:
        return parts[1].upper()
    return first


def opcode_and_operands(raw_line: str) -> Tuple[Optional[str], str, str]:
    stripped = raw_line.strip()
    if not stripped or stripped.startswith("*"):
        return None, "", ""
    parts = stripped.split(None, 2)
    if not parts:
        return None, "", ""

    first = parts[0].upper()
    if first in KNOWN_OPS:
        opcode = first
        operands = parts[1] if len(parts) > 1 else ""
        if len(parts) > 2:
            operands += " " + parts[2]
        return opcode, "", operands

    if len(parts) >= 2:
        opcode = parts[1].upper()
        operands = parts[2] if len(parts) >= 3 else ""
        return opcode, parts[0].upper(), operands

    return first, "", ""


def split_operands(operands: str) -> List[str]:
    # Good enough for assembler examples in this project; keeps literals intact enough for display.
    result = []
    current = []
    quote = False
    paren_depth = 0
    for ch in operands:
        if ch == "'":
            quote = not quote
        elif not quote:
            if ch == "(":
                paren_depth += 1
            elif ch == ")" and paren_depth > 0:
                paren_depth -= 1
            elif ch == "," and paren_depth == 0:
                token = "".join(current).strip()
                if token:
                    result.append(token)
                current = []
                continue
        current.append(ch)
    token = "".join(current).strip()
    if token:
        result.append(token)
    return result


def clean_symbol(token: str) -> str:
    token = token.strip().upper()
    token = re.sub(r"[=CLPXFBAH]'[^']*'", "", token)
    token = token.split("+")[0]
    token = token.split("-")[0]
    token = re.sub(r"\([^)]*\)", "", token)
    token = re.sub(r"[^A-Z0-9_@$#]", "", token)
    return token


def is_field_like(token: str) -> bool:
    if not token:
        return False
    if token in KNOWN_OPS:
        return False
    if token.startswith("R") and REGISTER_PATTERN.match(token):
        return False
    if REGISTER_PATTERN.match(token):
        return False
    if token in {"F", "C", "X", "P", "CL", "PL", "INPUT", "OUTPUT", "SEQ", "RP", "PM"}:
        return False
    if len(token) < 3:
        return False
    return bool(re.match(r"^[A-Z][A-Z0-9_@$#]*$", token))


def extract_defined_fields(path: Path) -> List[str]:
    fields: List[str] = []
    for raw_line in read_text(path).splitlines():
        opcode, label, operands = opcode_and_operands(raw_line)
        if opcode in DATA_OPS and label and is_field_like(label):
            fields.append(label)
        elif label and opcode in {"DS", "DC", "EQU", "ACB", "RPL", "EXLST", "DCB"} and is_field_like(label):
            fields.append(label)
    return sorted(set(fields))


def extract_all_field_mentions_from_line(raw_line: str, known_fields: Iterable[str]) -> List[str]:
    upper = raw_line.upper()
    mentions = []
    for field in known_fields:
        if re.search(rf"(?<![A-Z0-9_@$#]){re.escape(field)}(?![A-Z0-9_@$#])", upper):
            mentions.append(field)
    return mentions


def infer_field_access(opcode: Optional[str], operands: str, field: str) -> str:
    if not opcode:
        return "reference"
    ops = split_operands(operands)
    first = clean_symbol(ops[0]) if ops else ""
    upper_ops = operands.upper()

    if opcode in {"MVC", "ZAP", "ST", "STC", "STM", "MVI", "OI", "NI", "XI", "UNPK", "PACK"}:
        if first == field or upper_ops.strip().startswith(field):
            return "writer"
        return "reader"

    if opcode in {"CLC", "CLI", "CP", "C", "CR", "CH", "LTR", "L", "LA", "A", "AP", "SP", "MP", "DP", "SRP"}:
        # Arithmetic packed ops may update first operand and read both operands.
        if opcode in {"AP", "SP", "MP", "DP", "SRP"} and first == field:
            return "writer"
        return "reader"

    if opcode in IO_OPS:
        return "io_reference"

    return "reference"


# -----------------------------------------------------------------------------
# Analysis builders
# -----------------------------------------------------------------------------


def build_dependency_map(paths: List[Path]) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    module_names = {module_name_from_path(path) for path in paths}
    called: Dict[str, set] = {name: set() for name in module_names}
    calling: Dict[str, set] = {name: set() for name in module_names}

    for path in paths:
        current = module_name_from_path(path)
        text = read_text(path).upper()
        for target in module_names:
            if target == current:
                continue
            if re.search(rf"(?<![A-Z0-9_@$#]){re.escape(target)}(?![A-Z0-9_@$#])", text):
                # Consider it a dependency when target appears in code. This works for CALL-style and parm-list examples.
                called[current].add(target)
                calling[target].add(current)

    return (
        {key: sorted(value) for key, value in called.items()},
        {key: sorted(value) for key, value in calling.items()},
    )


def build_recommendations(module: str, factors: List[str]) -> List[str]:
    recs: List[str] = []
    if any("IO" in f or "file" in f.lower() or "VSAM" in f for f in factors):
        recs.append("Preserve DDNAME-to-file mapping and validate input/output record counts.")
        recs.append("Separate record parsing, business rules, and output writing in Java.")
    if any("packed" in f.lower() or "decimal" in f.lower() for f in factors):
        recs.append("Validate packed decimal scale, truncation, rounding, and implied-cent behavior.")
        recs.append("Add boundary tests for zero, equality, high-value, and fractional-cent cases.")
    if any("branch" in f.lower() for f in factors):
        recs.append("Use CFG review to ensure every branch condition has a matching test case.")
    if any("dependency" in f.lower() or "call" in f.lower() for f in factors):
        recs.append("Review parameter-block contracts before refactoring modules into Java services.")
    if module == "MAINDRV":
        recs.append("Treat MAINDRV as the orchestration layer and validate complete end-to-end flow.")
    if module == "VSAMPACK":
        recs.append("Preserve fixed-width A/B/T/X segment scanning and implied-cent numeric output.")
    if module == "AUTHDEC":
        recs.append("Review AUTHDEC approval/rejection branch logic before production migration sign-off.")
    if not recs:
        recs.append("Proceed with standard regression testing and generated Java review.")
    return list(dict.fromkeys(recs))


def analyze_module(path: Path, called: Dict[str, List[str]], calling: Dict[str, List[str]], known_issues_text: str) -> ModuleProfile:
    module = module_name_from_path(path)
    lines = read_text(path).splitlines()
    code_lines = [line for line in lines if line.strip() and not line.strip().startswith("*")]
    comment_lines = [line for line in lines if line.strip().startswith("*")]
    opcodes = [parse_opcode(line) for line in code_lines]
    opcodes = [op for op in opcodes if op]

    loc = len(code_lines)
    branches = sum(1 for op in opcodes if op in BRANCH_OPS)
    calls = sum(1 for op in opcodes if op in CALL_OPS)
    file_io = sum(1 for op in opcodes if op in IO_OPS)
    packed = sum(1 for op in opcodes if op in PACKED_DECIMAL_OPS)
    unsupported = sum(1 for op in opcodes if op not in KNOWN_OPS)
    comment_ratio = round(len(comment_lines) / max(1, len(lines)), 3)

    score = 10
    factors: List[str] = []

    if loc >= 80:
        score += 15
        factors.append("larger modernization surface")
    elif loc >= 40:
        score += 8
        factors.append("moderate module size")

    if branches >= 10:
        score += 20
        factors.append("complex branching / CFG risk")
    elif branches >= 3:
        score += 10
        factors.append("conditional branching")

    dep_count = len(called.get(module, [])) + len(calling.get(module, []))
    if dep_count >= 5:
        score += 16
        factors.append("high module dependency impact")
    elif dep_count >= 1:
        score += 8
        factors.append("cross-module dependency")

    if file_io >= 3:
        score += 18
        factors.append("file or VSAM IO behavior")
    elif file_io >= 1:
        score += 8
        factors.append("file IO dependency")

    if packed >= 3:
        score += 18
        factors.append("packed decimal arithmetic/comparison")
    elif packed >= 1:
        score += 9
        factors.append("packed decimal operation")

    if unsupported > 0:
        score += min(15, unsupported * 2)
        factors.append("unsupported or partially supported instruction review")

    if module in known_issues_text.upper():
        score += 20
        factors.append("known source behavior issue documented")

    if module in {"MAINDRV", "VSAMPACK"}:
        score += 8
        factors.append("batch/orchestration module")

    score = min(100, score)
    risk = "High" if score >= 70 else "Medium" if score >= 40 else "Low"

    evidence_preview = [line.strip() for line in code_lines[:8]]

    return ModuleProfile(
        module=module,
        source_path=str(path.relative_to(PROJECT_ROOT) if path.is_relative_to(PROJECT_ROOT) else path),
        risk_level=risk,
        risk_score=score,
        loc=loc,
        branches=branches,
        calls=calls,
        file_io=file_io,
        packed_decimal=packed,
        unsupported=unsupported,
        comment_ratio=comment_ratio,
        called_modules=called.get(module, []),
        calling_modules=calling.get(module, []),
        top_factors=factors or ["simple supported instruction profile"],
        recommendations=build_recommendations(module, factors),
        evidence_preview=evidence_preview,
    )


def build_module_profiles() -> List[ModuleProfile]:
    paths = find_hlasm_files()
    called, calling = build_dependency_map(paths)
    known_issues_text = read_text(DOCS_DIR / "known_hlasm_issues.md")
    return [analyze_module(path, called, calling, known_issues_text) for path in paths]


def build_field_index(paths: List[Path]) -> Dict[str, FieldImpact]:
    module_by_path = {path: module_name_from_path(path) for path in paths}
    defined_fields_by_module: Dict[str, List[str]] = {}
    all_fields: set = set()

    for path in paths:
        module = module_by_path[path]
        fields = extract_defined_fields(path)
        defined_fields_by_module[module] = fields
        all_fields.update(fields)

    # Add important known project fields even if parser misses them.
    all_fields.update(
        {
            "ERRCODE", "AUTHSTAT", "CURRTX", "TXCARD", "TXCUST", "TXAMT", "TXTYPE", "TXSTAT",
            "TXLIMIT", "TXFEE", "LOGBUFF", "LOGCUST", "LOGPAN", "LOGSTAT", "LOGMASK",
            "COUNT", "TOTAL", "FEEWORK", "WS_PACKED_AMT", "WS_TAX_AMT", "WS_ZONED_TAX",
            "IN_RECORD", "OUT_RECORD",
        }
    )

    index: Dict[str, Dict[str, Any]] = {
        field: {
            "defined_in": set(),
            "readers": set(),
            "writers": set(),
            "all": set(),
            "evidence": [],
        }
        for field in all_fields
        if is_field_like(field)
    }

    for module, fields in defined_fields_by_module.items():
        for field in fields:
            if field in index:
                index[field]["defined_in"].add(module)

    for path in paths:
        module = module_by_path[path]
        for line_no, raw_line in enumerate(read_text(path).splitlines(), start=1):
            if not raw_line.strip() or raw_line.strip().startswith("*"):
                continue
            opcode, _label, operands = opcode_and_operands(raw_line)
            mentions = extract_all_field_mentions_from_line(raw_line, index.keys())
            for field in mentions:
                access = infer_field_access(opcode, operands, field)
                index[field]["all"].add(module)
                if access == "writer":
                    index[field]["writers"].add(module)
                elif access in {"reader", "io_reference"}:
                    index[field]["readers"].add(module)
                else:
                    index[field]["readers"].add(module)
                if len(index[field]["evidence"]) < 20:
                    index[field]["evidence"].append(f"{module}:{line_no}: {raw_line.strip()}")

    result: Dict[str, FieldImpact] = {}
    for field, value in index.items():
        defined_in = sorted(value["defined_in"])
        readers = sorted(value["readers"])
        writers = sorted(value["writers"])
        all_modules = sorted(value["all"] | value["defined_in"])
        evidence = value["evidence"]

        if not all_modules and not defined_in:
            continue

        if len(all_modules) >= 4 or field in {"ERRCODE", "AUTHSTAT", "CURRTX", "LOGBUFF", "IN_RECORD", "OUT_RECORD"}:
            risk = "High"
            reason = "Shared field with broad module impact or business-control behavior."
        elif len(all_modules) >= 2:
            risk = "Medium"
            reason = "Field is used across multiple modules and should be regression-tested."
        else:
            risk = "Low"
            reason = "Field appears localized but should still be validated in module-level tests."

        result[field] = FieldImpact(
            field=field,
            defined_in=defined_in,
            reader_modules=readers,
            writer_modules=writers,
            all_modules=all_modules,
            risk_level=risk,
            reason=reason,
            evidence_lines=evidence,
        )

    return dict(sorted(result.items()))


# -----------------------------------------------------------------------------
# Behavior and report parsing
# -----------------------------------------------------------------------------


def extract_number(text: str, patterns: Iterable[str]) -> Optional[float]:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            raw = match.group(1).replace("`", "").replace("%", "").strip()
            try:
                return float(raw)
            except Exception:
                continue
    return None


def parse_behavior_summary() -> Dict[str, Any]:
    report = read_text(DOCS_DIR / "behavior_comparison_report.md")
    ai_report = read_text(DOCS_DIR / "ai_modernization_report.md")
    text = report + "\n" + ai_report

    total = extract_number(text, [r"Total test cases:\s*`?([0-9]+)`?", r"Total test cases:\s*([0-9]+)"])
    passed = extract_number(text, [r"Passed cases:\s*`?([0-9]+)`?", r"Passed cases:\s*([0-9]+)"])
    failed = extract_number(text, [r"Failed cases:\s*`?([0-9]+)`?", r"Failed cases:\s*([0-9]+)"])
    score = extract_number(text, [r"Average behavior match score:\s*`?([0-9.]+)%?`?", r"Behavior Match Score:\s*`?([0-9.]+)%?`?"])

    # Fallback to known current result if report exists but numbers were formatted differently.
    if report and total is None and "BEHAVIOR COMPARISON" in report.upper():
        total = extract_number(report, [r"Total\s+test\s+cases[^0-9]*([0-9]+)"])
        passed = extract_number(report, [r"Passed\s+cases[^0-9]*([0-9]+)"])
        failed = extract_number(report, [r"Failed\s+cases[^0-9]*([0-9]+)"])
        score = extract_number(report, [r"Average[^0-9]*([0-9.]+)%"])

    failures: List[Dict[str, str]] = []
    known = read_text(DOCS_DIR / "known_hlasm_issues.md").upper()

    # Only include real current failed cases, not summary lines like "No mismatches detected".
    if re.search(r"AUTHDEC[_\s-]*APPROVE", text, flags=re.IGNORECASE):
        failures.append(
            {
                "Test Case": "AUTHDEC_APPROVE_001",
                "Module": "AUTHDEC",
                "Classification": "Known HLASM source behavior issue" if "AUTHDEC" in known else "Needs source review",
                "Action": "Review/fix AUTHDEC approval branch before production migration sign-off.",
            }
        )

    if re.search(r"APP[_\s-]*APPROVAL[_\s-]*FLOW", text, flags=re.IGNORECASE):
        failures.append(
            {
                "Test Case": "APP_APPROVAL_FLOW_001",
                "Module": "MAINDRV / AUTHDEC",
                "Classification": "Downstream known HLASM source behavior issue" if "AUTHDEC" in known else "Needs source review",
                "Action": "Do not silently fix generated Java; resolve or accept AUTHDEC source behavior.",
            }
        )

    return {
        "total": int(total) if total is not None else None,
        "passed": int(passed) if passed is not None else None,
        "failed": int(failed) if failed is not None else len(failures),
        "score": float(score) if score is not None else None,
        "failures": failures,
    }


# -----------------------------------------------------------------------------
# Chatbot helpers
# -----------------------------------------------------------------------------


def format_list(items: List[str]) -> str:
    return ", ".join(items) if items else "None"


def structured_module_answer(module: ModuleProfile) -> str:
    rows = {
        "Module": module.module,
        "Risk Level": module.risk_level,
        "Risk Score": f"{module.risk_score}/100",
        "LOC": module.loc,
        "Branch Count": module.branches,
        "File I/O Count": module.file_io,
        "Packed Decimal Count": module.packed_decimal,
        "Called Modules": format_list(module.called_modules),
        "Calling Modules": format_list(module.calling_modules),
        "Top Risk Factors": format_list(module.top_factors),
    }
    lines = ["### Module Answer", "", "| Item | Value |", "|---|---|"]
    for key, value in rows.items():
        lines.append(f"| {key} | {value} |")
    lines.append("\n### Modernization Recommendations")
    for rec in module.recommendations:
        lines.append(f"- {rec}")
    return "\n".join(lines)


def structured_field_answer(field: FieldImpact) -> str:
    lines = [
        "### Field Impact Answer",
        "",
        "| Item | Value |",
        "|---|---|",
        f"| Field | {field.field} |",
        f"| Defined In | {format_list(field.defined_in)} |",
        f"| Writer Modules | {format_list(field.writer_modules)} |",
        f"| Reader Modules | {format_list(field.reader_modules)} |",
        f"| Impacted Modules | {format_list(field.all_modules)} |",
        f"| Modernization Risk | {field.risk_level} |",
        f"| Reason | {field.reason} |",
        "",
        "### Evidence Lines",
    ]
    if field.evidence_lines:
        for line in field.evidence_lines[:10]:
            lines.append(f"- `{line}`")
    else:
        lines.append("- No direct source evidence lines found; field may come from generated analysis or known layout.")
    return "\n".join(lines)


def tokenize_question(question: str) -> List[str]:
    return [token.upper() for token in re.findall(r"[A-Za-z0-9_@$#]+", question)]


def is_module_intent(question: str) -> bool:
    q = question.lower()
    return any(
        word in q
        for word in [
            "module", "modules", "call", "calls", "calling", "called",
            "risk", "modernize", "modernization", "dependency", "dependencies",
            "loc", "branch", "branches", "bctcount", "vsampack", "maindrv",
        ]
    )


def is_field_intent(question: str) -> bool:
    q = question.lower()
    return any(
        word in q
        for word in [
            "field", "fields", "use", "uses", "using", "impact", "impacts",
            "read", "reads", "write", "writes", "writer", "reader", "pdg",
        ]
    )


def tax_calculation_answer(modules: List[ModuleProfile]) -> str:
    rows: List[List[str]] = []

    for path in find_hlasm_files():
        module = module_name_from_path(path)
        text = read_text(path).upper()
        evidence: List[str] = []

        for raw_line in read_text(path).splitlines():
            upper_line = raw_line.upper()
            if any(token in upper_line for token in ["TAX", "0.05", "WS_TAX", "P'0.05'", "MP "]):
                evidence.append(raw_line.strip())
            if len(evidence) >= 4:
                break

        is_tax = any(token in text for token in ["WS_TAX", "TAX_AMT", "P'0.05'", "0.05"])
        is_fee = module == "FEECALC" or "FEE" in text

        if is_tax:
            rows.append(
                [
                    module,
                    "Tax calculation / record transformation",
                    "High" if module == "VSAMPACK" else next((m.risk_level for m in modules if m.module == module), "Review"),
                    "Uses packed decimal tax calculation and fixed-width record update.",
                    " ; ".join(evidence) if evidence else "Tax-related source pattern detected.",
                ]
            )
        elif is_fee:
            rows.append(
                [
                    module,
                    "Fee calculation, not tax",
                    next((m.risk_level for m in modules if m.module == module), "Review"),
                    "Related packed-decimal percentage calculation; useful comparison for tax logic.",
                    " ; ".join(evidence) if evidence else "Fee-related source pattern detected.",
                ]
            )

    if not rows:
        return (
            "### Tax Calculation Answer\n\n"
            "No tax calculation module was found from the indexed HLASM source. "
            "Check whether tax-related source lines use different names than TAX, WS_TAX, or P'0.05'."
        )

    lines = [
        "### Tax Calculation Modules",
        "",
        "| Module | Type | Risk | Why it matters | Evidence |",
        "|---|---|---|---|---|",
    ]
    for row in rows:
        safe = [str(item).replace("|", "\\|") for item in row]
        lines.append("| " + " | ".join(safe) + " |")

    lines.extend(
        [
            "",
            "### Recommendation",
            "- Treat VSAMPACK as the main tax calculation module because it applies the 5% tax transformation and updates the B segment.",
            "- Treat FEECALC as related percentage/packed-decimal logic, but not the tax module unless your business meaning calls that fee a tax.",
            "- Add tests for whole-cent and fractional-cent values to confirm HLASM-style truncation when no SRP rounding is present.",
        ]
    )
    return "\n".join(lines)


def answer_direct_question(question: str, modules: List[ModuleProfile], fields: Dict[str, FieldImpact]) -> Optional[str]:
    q = question.upper().strip()
    tokens = tokenize_question(question)
    module_by_name = {module.module: module for module in modules}

    # Domain/business intent first: questions like "tax calculation modules" should not be treated as fields.
    if "TAX" in q or "TAXES" in q:
        return tax_calculation_answer(modules)

    # Exact single-token query: if it is a module, return module answer before field answer.
    # This fixes cases like "bctcount", where BCTCOUNT may also appear as a data label/field.
    if len(tokens) == 1 and tokens[0] in module_by_name:
        return structured_module_answer(module_by_name[tokens[0]])

    # Strong module intent: prioritize module over field.
    if is_module_intent(question):
        for module in modules:
            if re.search(rf"(?<![A-Z0-9_@$#]){re.escape(module.module)}(?![A-Z0-9_@$#])", q):
                return structured_module_answer(module)

    # Strong field intent: answer field impact questions from PDG-style index.
    if is_field_intent(question):
        for field_name, impact in fields.items():
            if re.search(rf"(?<![A-Z0-9_@$#]){re.escape(field_name)}(?![A-Z0-9_@$#])", q):
                return structured_field_answer(impact)

    # General fallback: check modules first, then fields.
    for module in modules:
        if re.search(rf"(?<![A-Z0-9_@$#]){re.escape(module.module)}(?![A-Z0-9_@$#])", q):
            return structured_module_answer(module)

    for field_name, impact in fields.items():
        if re.search(rf"(?<![A-Z0-9_@$#]){re.escape(field_name)}(?![A-Z0-9_@$#])", q):
            return structured_field_answer(impact)

    if "AUTHDEC" in q or "APPROVAL" in q or "FAIL" in q:
        return (
            "### Failure Diagnostic Answer\n\n"
            "| Item | Value |\n|---|---|\n"
            "| Main Failed Area | AUTHDEC approval path |\n"
            "| Classification | Known HLASM source behavior issue |\n"
            "| Affected Tests | AUTHDEC_APPROVE_001, APP_APPROVAL_FLOW_001 |\n"
            "| Recommendation | Review or fix AUTHDEC source logic before production migration sign-off. |\n\n"
            "The Java generator should not silently change business behavior that appears incorrect in the source program."
        )

    return None

def llm_answer(question: str, modules: List[ModuleProfile], fields: Dict[str, FieldImpact], behavior: Dict[str, Any]) -> Tuple[str, bool]:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

    if not api_key or any(token in api_key.lower() for token in ["your", "paste", "placeholder", "here"]):
        return (
            "OpenAI key is not configured for this session. Direct module/field questions still work. "
            "Set `$env:OPENAI_API_KEY` locally to enable LLM-enhanced answers.",
            False,
        )

    compact_modules = [asdict(m) for m in modules]
    compact_fields = {k: asdict(v) for k, v in list(fields.items())[:80]}
    report_excerpt = read_text(DOCS_DIR / "ai_modernization_report.md", limit=12000)

    prompt = f"""
You are a legacy modernization assistant. Answer using only the evidence below.
Format the answer neatly with sections: Answer, Evidence, Recommendation.
Do not invent files, scores, or failures.

Question:
{question}

Behavior summary:
{json.dumps(behavior, indent=2)}

Module profiles:
{json.dumps(compact_modules, indent=2)}

Field impact index sample:
{json.dumps(compact_fields, indent=2)}

AI report excerpt:
{report_excerpt}
""".strip()

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        response = client.responses.create(
            model=model,
            instructions="Give concise evidence-grounded modernization answers. Use markdown tables when helpful.",
            input=prompt,
            temperature=0.2,
        )
        text = getattr(response, "output_text", None) or str(response)
        return text + f"\n\n_LLM: OpenAI {model}_", True
    except Exception as exc:
        return f"LLM answer failed: {type(exc).__name__}: {exc}", False


# -----------------------------------------------------------------------------
# Streamlit UI
# -----------------------------------------------------------------------------


st.set_page_config(
    page_title="AI Legacy Modernization Dashboard",
    page_icon="🧠",
    layout="wide",
)

st.title("AI-Powered Legacy Software Intelligence & Modernization Dashboard")
st.caption("ML risk intelligence + HLASM analysis + Java modernization + behavior validation + LLM-assisted reporting")

with st.spinner("Loading project artifacts..."):
    hlasm_paths = find_hlasm_files()
    modules = build_module_profiles()
    field_index = build_field_index(hlasm_paths)
    behavior = parse_behavior_summary()
    llm_details = read_json(DOCS_DIR / "ai_llm_integration_details.json") or {}
    ai_report = read_text(DOCS_DIR / "ai_modernization_report.md")

module_df = pd.DataFrame(
    [
        {
            "Module": m.module,
            "Risk": m.risk_level,
            "Risk Score": m.risk_score,
            "LOC": m.loc,
            "Branches": m.branches,
            "File I/O": m.file_io,
            "Packed Decimal": m.packed_decimal,
            "Called Modules": format_list(m.called_modules),
            "Calling Modules": format_list(m.calling_modules),
            "Top Factors": format_list(m.top_factors),
        }
        for m in modules
    ]
)

field_df = pd.DataFrame(
    [
        {
            "Field": f.field,
            "Risk": f.risk_level,
            "Defined In": format_list(f.defined_in),
            "Writers": format_list(f.writer_modules),
            "Readers": format_list(f.reader_modules),
            "Impacted Modules": format_list(f.all_modules),
        }
        for f in field_index.values()
    ]
)

# Sidebar navigation and status
used_value = llm_details.get("used", False)
llm_used = used_value is True or str(used_value).strip().lower() == "true"
llm_model = llm_details.get("model", "not available")
llm_error = llm_details.get("error")

st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Go to",
    [
        "1. Executive Summary",
        "2. Module Explorer",
        "3. Field Impact Explorer",
        "4. New Module Assessment",
        "5. AI Chatbot",
        "6. AI Report / LLM Details",
    ],
    index=0,
)

st.sidebar.divider()
st.sidebar.header("Project Artifact Status")
st.sidebar.write(f"Project root: `{PROJECT_ROOT}`")
st.sidebar.write(f"HLASM files found: **{len(hlasm_paths)}**")
st.sidebar.write(f"Module profiles: **{len(modules)}**")
st.sidebar.write(f"Fields indexed: **{len(field_index)}**")
st.sidebar.write(f"LLM used: **{'Yes' if llm_used else 'No'}**")
st.sidebar.write(f"LLM model: `{llm_model}`")

if llm_used:
    st.sidebar.success("LLM integration active")
elif llm_details:
    st.sidebar.warning("LLM was not used in the latest generated report")
    if llm_error:
        st.sidebar.caption(f"Reason: {llm_error}")
else:
    st.sidebar.info("Run ai_modernization_engine.py to generate LLM details")

if st.sidebar.button("Refresh dashboard data"):
    st.rerun()


if page == "1. Executive Summary":
    st.subheader("Executive Modernization Summary")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Behavior Match", f"{behavior['score']}%" if behavior.get("score") is not None else "N/A")
    c2.metric("Passed", behavior.get("passed") if behavior.get("passed") is not None else "N/A")
    c3.metric("Failed", behavior.get("failed") if behavior.get("failed") is not None else "N/A")
    c4.metric("HLASM Modules", len(modules))
    c5.metric("LLM Used", "Yes" if llm_used else "No")

    if not llm_used:
        st.info(
            "LLM Used shows 'No' when docs/ai_llm_integration_details.json says used=false, "
            "or when the file was generated without a valid OPENAI_API_KEY. "
            "Set the key locally, run `python validator\\ai_modernization_engine.py`, then refresh this dashboard."
        )

    if behavior.get("failed"):
        st.warning("Final status: Review Required. Known AUTHDEC source behavior issue remains.")
    else:
        st.success("Final status: Ready for review. No behavior failures detected in available results.")

    st.markdown("### What this dashboard proves")
    st.markdown(
        """
- **ML / risk intelligence:** module risk ranking based on size, branching, IO, packed decimal logic, dependencies, and known issues.
- **CFG-style analysis:** branch and module dependency information for modernization impact.
- **PDG-style analysis:** field read/write/impact exploration across modules.
- **Behavior validation:** generated Java behavior results are visible in the summary.
- **LLM integration:** OpenAI model details are recorded in the LLM integration details artifact.
        """
    )

    st.markdown("### Module Risk Ranking")
    if not module_df.empty:
        st.dataframe(module_df.sort_values(["Risk Score", "Module"], ascending=[False, True]), use_container_width=True)
    else:
        st.info("No module profiles found. Check HLASM file location and naming.")

    if behavior.get("failures"):
        st.markdown("### Current Behavior Failure Diagnostics")
        st.dataframe(pd.DataFrame(behavior["failures"]), use_container_width=True)


elif page == "2. Module Explorer":
    st.subheader("Module Explorer")
    if not modules:
        st.info("No modules found.")
    else:
        module_names = sorted([m.module for m in modules])
        selected_module_name = st.selectbox("Select module", module_names, index=module_names.index("MAINDRV") if "MAINDRV" in module_names else 0)
        selected_module = next(m for m in modules if m.module == selected_module_name)

        details = pd.DataFrame(
            [
                ["Module", selected_module.module],
                ["Source File", selected_module.source_path],
                ["Risk Level", selected_module.risk_level],
                ["Risk Score", f"{selected_module.risk_score}/100"],
                ["LOC", selected_module.loc],
                ["Branch Count", selected_module.branches],
                ["File I/O Count", selected_module.file_io],
                ["Packed Decimal Count", selected_module.packed_decimal],
                ["Unsupported / Review Count", selected_module.unsupported],
                ["Called Modules", format_list(selected_module.called_modules)],
                ["Calling Modules", format_list(selected_module.calling_modules)],
                ["Top Risk Factors", format_list(selected_module.top_factors)],
            ],
            columns=["Item", "Value"],
        )
        st.dataframe(details, use_container_width=True, hide_index=True)

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("### Modernization Recommendations")
            for rec in selected_module.recommendations:
                st.markdown(f"- {rec}")
        with col_b:
            st.markdown("### Source Evidence Preview")
            for line in selected_module.evidence_preview:
                st.code(line, language="asm")

        st.markdown("### All Modules")
        st.dataframe(module_df.sort_values(["Risk Score", "Module"], ascending=[False, True]), use_container_width=True)


elif page == "3. Field Impact Explorer":
    st.subheader("Field Impact Explorer")
    st.caption("Search a field and see which modules define, read, write, and are impacted by it.")

    if not field_index:
        st.info("No fields indexed.")
    else:
        common_fields = [f for f in ["ERRCODE", "AUTHSTAT", "TXAMT", "TXLIMIT", "TXFEE", "LOGPAN", "COUNT", "TOTAL", "WS_TAX_AMT"] if f in field_index]
        all_fields = sorted(field_index.keys())
        field_options = common_fields + [f for f in all_fields if f not in common_fields]

        selected_field = st.selectbox("Select field", field_options)
        manual_field = st.text_input("Or type field name", value=selected_field)
        normalized_field = manual_field.strip().upper() or selected_field

        impact = field_index.get(normalized_field)
        if impact is None:
            st.warning(f"Field `{normalized_field}` was not found in the indexed HLASM artifacts.")
        else:
            impact_table = pd.DataFrame(
                [
                    ["Field", impact.field],
                    ["Defined In", format_list(impact.defined_in)],
                    ["Writer Modules", format_list(impact.writer_modules)],
                    ["Reader Modules", format_list(impact.reader_modules)],
                    ["Impacted Modules", format_list(impact.all_modules)],
                    ["Modernization Risk", impact.risk_level],
                    ["Reason", impact.reason],
                ],
                columns=["Item", "Value"],
            )
            st.dataframe(impact_table, use_container_width=True, hide_index=True)

            st.markdown("### Field Evidence Lines")
            if impact.evidence_lines:
                for line in impact.evidence_lines[:20]:
                    st.code(line, language="asm")
            else:
                st.info("No direct source lines found for this field.")

        with st.expander("Show full field index"):
            st.dataframe(field_df.sort_values(["Risk", "Field"], ascending=[True, True]), use_container_width=True)


elif page == "4. New Module Assessment":
    render_new_module_assessment()

elif page == "5. AI Chatbot":
    st.subheader("Grounded AI Chatbot")
    st.caption("Ask about modules, fields, failures, risk, CFG/PDG impact, or modernization recommendations.")

    examples = [
        "Which modules use ERRCODE?",
        "bctcount",
        "Which module performs tax calculation?",
        "Why is VSAMPACK high risk?",
        "What modules call AUTHDEC?",
        "What fields impact AUDWRITE?",
        "Why did AUTHDEC fail?",
        "What tests should I add for LIMITCHK?",
    ]

    selected_example = st.selectbox("Example questions", [""] + examples)
    question = st.text_area("Ask a question", value=selected_example, height=100)

    use_llm = st.checkbox("Use OpenAI LLM for open-ended questions", value=True)

    if st.button("Ask") and question.strip():
        direct = answer_direct_question(question, modules, field_index)
        if direct:
            st.markdown(direct)
            st.info("Answer type: deterministic structured answer from project artifacts.")
        elif use_llm:
            with st.spinner("Generating LLM-enhanced grounded answer..."):
                answer, used = llm_answer(question, modules, field_index, behavior)
            st.markdown(answer)
            st.info("Answer type: LLM-enhanced grounded answer." if used else "Answer type: fallback message.")
        else:
            st.warning("No direct module or field match found. Enable LLM for open-ended questions.")


elif page == "6. AI Report / LLM Details":
    st.subheader("AI Modernization Report")
    if ai_report:
        st.markdown(ai_report)
    else:
        st.info("docs/ai_modernization_report.md was not found. Run `python validator\\ai_modernization_engine.py` first.")

    st.divider()
    st.subheader("AI / LLM Integration Details")
    if llm_details:
        st.json(llm_details)
    else:
        st.info("docs/ai_llm_integration_details.json was not found.")

    st.markdown("### Run commands")
    st.code(
        """python validator\\ai_modernization_engine.py
python -m streamlit run validator\\modernization_dashboard.py""",
        language="powershell",
    )
