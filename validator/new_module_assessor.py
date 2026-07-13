"""
New Module Assessment Utility

Analyze one new HLASM module before translation and produce:
- static / CFG-style / PDG-style feature evidence
- optional ML model artifact prediction when a saved model is available
- safe fallback rule-based risk scoring when no ML artifact is available
- modernization recommendations grounded in extracted evidence

PowerShell:
    python validator/new_module_assessor.py HLASM/BCTCOUNT.asm.txt
"""
from __future__ import annotations

import json
import pickle
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

BRANCH_OPS = {
    "B", "BC", "BCR", "BE", "BNE", "BNZ", "BZ", "BH", "BL", "BNH", "BNL",
    "BO", "BNO", "BP", "BM", "BCT", "BCTR", "BR", "BAL", "BALR", "BAS", "BASR",
    "J", "JE", "JNE", "JNZ", "JZ", "JH", "JL", "JNH", "JNL"
}
CALL_OPS = {"CALL", "LINK", "XCTL", "ATTACH", "LOAD"}
FILE_IO_OPS = {"OPEN", "CLOSE", "GET", "PUT", "READ", "WRITE", "CHECK", "MODCB", "SHOWCB"}
PACKED_DECIMAL_OPS = {"PACK", "UNPK", "ZAP", "AP", "SP", "MP", "DP", "CP", "SRP", "ED", "EDMK"}
COMPARE_OPS = {"CLC", "CLI", "C", "CR", "CH", "CP", "TM", "TRT"}
MOVE_OPS = {"MVC", "MVI", "MVCL", "MVN", "MVZ", "IC", "ST", "L", "LA", "LR", "STC"}
ARITHMETIC_OPS = {"A", "AR", "AH", "S", "SR", "SH", "M", "MR", "D", "DR", "AL", "ALR", "SL", "SLR", "XR"}
LOGICAL_OPS = {"OI", "NI", "XI", "OC", "NC", "XC", "TR"}
MACRO_LIKE_OPS = {"SAVE", "RETURN", "ABEND", "WTO"}
DB_OPS = {"EXEC", "SELECT", "INSERT", "UPDATE", "DELETE", "FETCH", "COMMIT", "ROLLBACK"}
SUPPORTED_OPS = BRANCH_OPS | CALL_OPS | FILE_IO_OPS | PACKED_DECIMAL_OPS | COMPARE_OPS | MOVE_OPS | ARITHMETIC_OPS | LOGICAL_OPS | MACRO_LIKE_OPS | DB_OPS
DIRECTIVES = {
    "START", "END", "CSECT", "DSECT", "USING", "DROP", "EQU", "ORG", "LTORG",
    "DC", "DS", "COPY", "TITLE", "SPACE", "EJECT", "PRINT", "ENTRY", "EXTRN",
    "AMODE", "RMODE", "RENT", "STM", "LM", "DSORG", "DCB", "ACB", "RPL"
}
KNOWN_OPS = SUPPORTED_OPS | DIRECTIVES
DEFAULT_MODEL_PATTERNS = [
    "*random*forest*.joblib", "*random*forest*.pkl", "*risk*model*.joblib",
    "*risk*model*.pkl", "*model*.joblib", "*model*.pkl"
]


def _is_comment(line: str) -> bool:
    stripped = line.strip()
    return bool(stripped) and (line.startswith("*") or stripped.startswith(".*"))


def _parse_line(line: str) -> Dict[str, Any]:
    if not line.strip() or _is_comment(line):
        return {"label": "", "opcode": "", "operands": "", "raw": line.rstrip("\n")}

    tokens = line.strip().split()
    first = tokens[0].upper().rstrip(",") if tokens else ""
    second = tokens[1].upper().rstrip(",") if len(tokens) > 1 else ""

    if line[:1].isspace() or first in KNOWN_OPS:
        return {"label": "", "opcode": first, "operands": " ".join(tokens[1:]), "raw": line.rstrip("\n")}

    return {"label": first, "opcode": second, "operands": " ".join(tokens[2:]) if len(tokens) > 2 else "", "raw": line.rstrip("\n")}


def _extract_symbols(parsed_lines: List[Dict[str, Any]]) -> Dict[str, Any]:
    declared, referenced = [], []
    for item in parsed_lines:
        label = item.get("label", "")
        opcode = item.get("opcode", "")
        operands = item.get("operands", "")
        if label and opcode in {"DC", "DS", "DSECT", "EQU", "ACB", "RPL", "DCB"}:
            declared.append(label)
        for token in re.findall(r"[A-Z][A-Z0-9_@$#]{1,30}", operands.upper()):
            if token not in KNOWN_OPS and not token.startswith(("C", "X", "F", "H", "P")):
                referenced.append(token)

    declared_u = sorted(set(declared))
    referenced_u = sorted(set(referenced))
    shared = sorted(set(declared_u).intersection(referenced_u))
    return {
        "declared_symbols": declared_u,
        "referenced_symbols": referenced_u[:100],
        "shared_symbols": shared,
        "declared_symbol_count": len(declared_u),
        "referenced_symbol_count": len(referenced_u),
        "shared_symbol_count": len(shared),
    }


def _classify_module_role(features: Dict[str, Any]) -> str:
    if features["file_io_count"] > 0 and features["packed_decimal_count"] > 0:
        return "batch_file_decimal_processing"
    if features["file_io_count"] > 0:
        return "file_io_processing"
    if features["packed_decimal_count"] > 0:
        return "decimal_business_rule"
    if features["branch_count"] > 0:
        return "control_flow_validation"
    return "utility_or_simple_logic"


def find_project_root(start: Optional[Path] = None) -> Path:
    candidates = []
    if start:
        candidates.append(start.resolve())
    try:
        candidates.append(Path(__file__).resolve())
    except NameError:
        pass
    candidates.append(Path.cwd().resolve())

    seen, expanded = set(), []
    for candidate in candidates:
        if candidate.is_file():
            candidate = candidate.parent
        for item in [candidate] + list(candidate.parents):
            if item not in seen:
                expanded.append(item)
                seen.add(item)
    for candidate in expanded:
        if (candidate / "validator").exists() and ((candidate / "HLASM").exists() or (candidate / "docs").exists()):
            return candidate
    return Path.cwd().resolve()


def find_model_artifact(project_root: Optional[Path] = None) -> Optional[Path]:
    root = project_root or find_project_root()
    for directory in [root / "ml_risk_predictor", root / "models", root / "artifacts", root]:
        if not directory.exists():
            continue
        for pattern in DEFAULT_MODEL_PATTERNS:
            matches = sorted(directory.rglob(pattern))
            if matches:
                return matches[0]
    return None


def _load_model_artifact(model_path: Path) -> Any:
    try:
        import joblib  # type: ignore
        return joblib.load(model_path)
    except Exception:
        with open(model_path, "rb") as f:
            return pickle.load(f)


def _build_ml_feature_row(module_name: str, features: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "application_name": "UploadedAssessment",
        "business_process": "PreModernizationReview",
        "module_name": module_name,
        "module_role": _classify_module_role(features),
        "lines_of_code": features["code_lines"],
        "branch_instruction_count": features["branch_count"],
        "called_module_count": features["call_count"],
        "calling_module_count": 0,
        "file_io_count": features["file_io_count"],
        "database_access_count": features["database_access_count"],
        "macro_call_count": features["macro_call_count"],
        "packed_decimal_instruction_count": features["packed_decimal_count"],
        "historical_defect_count": 0,
        "change_count_last_12_months": 0,
        "comment_ratio": features["comment_ratio"],
        "unsupported_instruction_count": features["unsupported_instruction_count"],
    }


def _predict_with_ml_artifact(module_name: str, features: Dict[str, Any], model_path: Optional[str] = None) -> Dict[str, Any]:
    explicit = Path(model_path) if model_path else None
    artifact_path = explicit if explicit and explicit.exists() else find_model_artifact()
    if not artifact_path:
        return {"used": False, "source": "static_rule_fallback", "model_path": None, "model_type": None, "prediction": None, "confidence": None, "reason": "No saved ML model artifact found. Used static evidence scoring instead."}

    try:
        artifact = _load_model_artifact(artifact_path)
        model, feature_columns, label_encoder = artifact, None, None
        if isinstance(artifact, dict):
            model = artifact.get("model") or artifact.get("pipeline") or artifact.get("estimator")
            feature_columns = artifact.get("feature_columns") or artifact.get("features")
            label_encoder = artifact.get("label_encoder")
        if model is None:
            raise ValueError("Model artifact dictionary did not contain model/pipeline/estimator.")

        import pandas as pd  # type: ignore
        row = _build_ml_feature_row(module_name, features)
        if feature_columns:
            input_df = pd.DataFrame([{col: row.get(col, 0) for col in feature_columns}])
        elif hasattr(model, "feature_names_in_"):
            cols = list(getattr(model, "feature_names_in_"))
            input_df = pd.DataFrame([{col: row.get(col, 0) for col in cols}])
        else:
            cols = [
                "lines_of_code", "branch_instruction_count", "called_module_count", "calling_module_count",
                "file_io_count", "database_access_count", "macro_call_count", "packed_decimal_instruction_count",
                "historical_defect_count", "change_count_last_12_months", "comment_ratio", "unsupported_instruction_count",
            ]
            input_df = pd.DataFrame([{col: row.get(col, 0) for col in cols}])

        raw_prediction = model.predict(input_df)[0]
        prediction = raw_prediction
        if label_encoder is not None and hasattr(label_encoder, "inverse_transform"):
            try:
                prediction = label_encoder.inverse_transform([raw_prediction])[0]
            except Exception:
                prediction = raw_prediction

        confidence, probabilities = None, None
        if hasattr(model, "predict_proba"):
            try:
                proba = model.predict_proba(input_df)[0]
                probabilities = [float(x) for x in proba]
                confidence = round(float(max(proba)), 3)
            except Exception:
                pass

        return {
            "used": True,
            "source": "ml_artifact",
            "model_path": str(artifact_path),
            "model_type": type(model).__name__,
            "prediction": str(prediction),
            "confidence": confidence,
            "probabilities": probabilities,
            "feature_row": row,
            "reason": "Risk prediction generated using saved ML model artifact.",
        }
    except Exception as exc:
        return {"used": False, "source": "static_rule_fallback", "model_path": str(artifact_path), "model_type": None, "prediction": None, "confidence": None, "reason": f"ML artifact was found but could not be used: {type(exc).__name__}: {exc}"}


def _static_risk_score(features: Dict[str, Any]) -> Tuple[int, str, Dict[str, int]]:
    score, details = 0, {}
    def add(name: str, value: int) -> None:
        nonlocal score
        score += value
        details[name] = value

    if features["code_lines"] > 250:
        add("Large module size", 15)
    elif features["code_lines"] > 100:
        add("Moderate module size", 10)
    elif features["code_lines"] > 40:
        add("Small-to-moderate module size", 5)

    if features["branch_count"] > 12:
        add("High branching complexity", 25)
    elif features["branch_count"] > 6:
        add("Moderate branching complexity", 15)
    elif features["branch_count"] > 0:
        add("Some branching logic", 7)

    if features["packed_decimal_count"] > 6:
        add("Heavy packed decimal usage", 20)
    elif features["packed_decimal_count"] > 0:
        add("Packed decimal usage", 10)

    if features["file_io_count"] > 3:
        add("Multiple file or VSAM operations", 15)
    elif features["file_io_count"] > 0:
        add("File or VSAM operation", 10)

    if features["database_access_count"] > 0:
        add("Database access indicator", 10)

    if features["call_count"] > 2:
        add("Multiple external calls", 15)
    elif features["call_count"] > 0:
        add("External call dependency", 8)

    if features["unsupported_instruction_count"] > 10:
        add("High unsupported instruction count", 25)
    elif features["unsupported_instruction_count"] > 3:
        add("Moderate unsupported instruction count", 15)
    elif features["unsupported_instruction_count"] > 0:
        add("Some unsupported instructions", 5)

    if features["comment_ratio"] < 0.10 and features["code_lines"] > 20:
        add("Low comment ratio", 10)
    elif features["comment_ratio"] < 0.20 and features["code_lines"] > 20:
        add("Limited comments", 5)

    score = max(0, min(score, 100))
    return score, "High" if score >= 60 else "Medium" if score >= 30 else "Low", details


def _build_recommendations(risk_level: str, features: Dict[str, Any], unique_unsupported_ops: List[str], ml_prediction: Dict[str, Any]) -> List[str]:
    recs = []
    if ml_prediction.get("used"):
        recs.append(f"ML artifact prediction is available. The saved model predicted `{ml_prediction.get('prediction')}` risk with confidence `{ml_prediction.get('confidence')}`. Use this together with CFG/PDG evidence before translation.")
    else:
        recs.append("No usable saved ML artifact was found for this module, so the dashboard used static evidence fallback. Connect the saved Week 1 RandomForest artifact later for model-based prediction.")

    if risk_level == "High":
        recs.append("Treat this module as high-risk before translation. Review control flow, data dependencies, and test coverage before Java generation.")
    elif risk_level == "Medium":
        recs.append("Review this module before translation and add focused tests for the main business paths.")
    else:
        recs.append("This module appears lower risk based on current evidence, but behavior validation is still required after translation.")

    if features["branch_count"] > 0:
        recs.append("CFG evidence shows branch or loop logic. Add branch/path test cases before accepting translation output.")
    if features["packed_decimal_count"] > 0:
        recs.append("Packed decimal instructions are present. Review precision, scale, rounding, implied decimals, and sign handling.")
    if features["file_io_count"] > 0:
        recs.append("File or VSAM style operations are present. Validate input/output using representative batch records and boundary records.")
    if features["call_count"] > 0:
        recs.append("External calls or module dependencies are present. Review called modules before isolating this module for migration.")
    if features["shared_symbol_count"] > 0:
        recs.append("PDG-style evidence shows declared symbols are referenced by logic. Review field-level read/write impact before changing layouts.")
    if features["unsupported_instruction_count"] > 0:
        recs.append(f"Review unsupported or uncommon instructions before translation. Detected examples: {', '.join(unique_unsupported_ops[:8])}.")
    if features["comment_ratio"] < 0.20:
        recs.append("Comment coverage is limited. Add business-rule documentation before migration sign-off.")
    recs.append("After translation, run Java compilation and behavior comparison to verify that generated Java preserves legacy behavior.")
    return recs


def assess_hlasm_text(source_text: str, module_name: str = "UPLOADED_MODULE", model_path: Optional[str] = None, prefer_ml: bool = True) -> Dict[str, Any]:
    raw_lines = source_text.splitlines()
    comment_lines, code_lines = 0, 0
    labels, parsed_lines, opcodes = set(), [], []
    evidence = {"control_flow_evidence": [], "data_impact_evidence": [], "file_io_evidence": [], "packed_decimal_evidence": [], "unsupported_instruction_evidence": []}

    for idx, line in enumerate(raw_lines, start=1):
        if not line.strip():
            continue
        if _is_comment(line):
            comment_lines += 1
            continue
        item = _parse_line(line)
        item["line_number"] = idx
        opcode = item.get("opcode", "")
        if opcode:
            code_lines += 1
            if item.get("label"):
                labels.add(item["label"])
            parsed_lines.append(item)
            opcodes.append(opcode.upper())
            e = f"L{idx}: {item['raw']}"
            if opcode in BRANCH_OPS:
                evidence["control_flow_evidence"].append(e)
            if opcode in FILE_IO_OPS:
                evidence["file_io_evidence"].append(e)
            if opcode in PACKED_DECIMAL_OPS:
                evidence["packed_decimal_evidence"].append(e)

    symbols = _extract_symbols(parsed_lines)
    if symbols["declared_symbols"]:
        evidence["data_impact_evidence"].append("Declared symbols: " + ", ".join(symbols["declared_symbols"][:20]))
    if symbols["shared_symbols"]:
        evidence["data_impact_evidence"].append("Referenced declared symbols: " + ", ".join(symbols["shared_symbols"][:20]))

    instruction_count = len(opcodes)
    unsupported_ops = [op for op in opcodes if op not in SUPPORTED_OPS and op not in DIRECTIVES]
    unique_unsupported_ops = sorted(set(unsupported_ops))
    for item in parsed_lines:
        if item["opcode"] in unique_unsupported_ops:
            evidence["unsupported_instruction_evidence"].append(f"L{item['line_number']}: {item['raw']}")

    total_non_blank = code_lines + comment_lines
    features: Dict[str, Any] = {
        "code_lines": code_lines,
        "comment_lines": comment_lines,
        "comment_ratio": round(comment_lines / total_non_blank, 3) if total_non_blank else 0.0,
        "instruction_count": instruction_count,
        "label_count": len(labels),
        "branch_count": sum(1 for op in opcodes if op in BRANCH_OPS),
        "branch_density": round(sum(1 for op in opcodes if op in BRANCH_OPS) / instruction_count, 3) if instruction_count else 0.0,
        "call_count": sum(1 for op in opcodes if op in CALL_OPS),
        "file_io_count": sum(1 for op in opcodes if op in FILE_IO_OPS),
        "packed_decimal_count": sum(1 for op in opcodes if op in PACKED_DECIMAL_OPS),
        "compare_count": sum(1 for op in opcodes if op in COMPARE_OPS),
        "move_count": sum(1 for op in opcodes if op in MOVE_OPS),
        "macro_call_count": sum(1 for op in opcodes if op in MACRO_LIKE_OPS),
        "database_access_count": sum(1 for op in opcodes if op in DB_OPS),
        "unsupported_instruction_count": len(unsupported_ops),
        "unique_unsupported_ops": unique_unsupported_ops,
        **symbols,
    }

    static_score, static_risk_level, score_details = _static_risk_score(features)
    ml_prediction = _predict_with_ml_artifact(module_name, features, model_path=model_path) if prefer_ml else {"used": False, "source": "static_rule_fallback", "reason": "ML disabled for this assessment."}

    if ml_prediction.get("used") and ml_prediction.get("prediction"):
        risk_level = str(ml_prediction["prediction"]).title()
        risk_source = "ML artifact + static evidence"
        confidence = ml_prediction.get("confidence") or 0.80
    else:
        risk_level = static_risk_level
        risk_source = "Static evidence fallback"
        confidence = round(max(0.55, min(0.95, 0.92 - (len(unsupported_ops) / instruction_count if instruction_count else 0))), 2)

    return {
        "module_name": module_name,
        "risk_level": risk_level,
        "risk_score": static_score,
        "risk_source": risk_source,
        "confidence": confidence,
        "ml_prediction": ml_prediction,
        "features": features,
        "score_details": score_details,
        "evidence": evidence,
        "recommendations": _build_recommendations(risk_level, features, unique_unsupported_ops, ml_prediction),
        "note": "This is a pre-modernization assessment. It predicts/estimates risk before translation and does not replace Java generation, Java compilation, or behavior validation.",
    }


def assess_hlasm_file(file_path: str | Path, model_path: Optional[str] = None, prefer_ml: bool = True) -> Dict[str, Any]:
    path = Path(file_path)
    return assess_hlasm_text(path.read_text(encoding="utf-8", errors="ignore"), module_name=path.stem, model_path=model_path, prefer_ml=prefer_ml)


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python validator/new_module_assessor.py <path-to-hlasm-file> [optional-model-path]")
        return 2
    model_path = sys.argv[2] if len(sys.argv) >= 3 else None
    print(json.dumps(assess_hlasm_file(sys.argv[1], model_path=model_path, prefer_ml=True), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
