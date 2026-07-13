"""
Dashboard section: New Module Pre-Modernization Assessment

This section supports two input options:
1. Upload/paste a new HLASM module that is not yet part of the project.
2. Select an existing module from the HLASM folder.

It calls validator/new_module_assessor.py and displays:
- ML artifact prediction when a saved model is available
- static fallback risk score
- extracted features
- evidence proof
- modernization recommendations
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import streamlit as st

try:
    from new_module_assessor import assess_hlasm_file, assess_hlasm_text, find_model_artifact, find_project_root
except ImportError:
    from validator.new_module_assessor import assess_hlasm_file, assess_hlasm_text, find_model_artifact, find_project_root


def _find_hlasm_files() -> List[Path]:
    project_root = find_project_root()
    hlasm_dir = project_root / "HLASM"
    if not hlasm_dir.exists():
        return []

    paths: List[Path] = []
    for pattern in ["*.ASM", "*.asm", "*.asm.txt", "*.ASM.txt", "*.txt"]:
        paths.extend(hlasm_dir.rglob(pattern))
    return sorted(set(paths), key=lambda p: p.name.upper())


def _features_dataframe(features: Dict[str, Any]) -> pd.DataFrame:
    rows = []
    for key, value in features.items():
        if isinstance(value, list):
            display_value = ", ".join(str(item) for item in value[:20])
        else:
            display_value = value
        rows.append({"Feature": key, "Value": display_value})
    return pd.DataFrame(rows)


def _score_dataframe(score_details: Dict[str, int]) -> pd.DataFrame:
    return pd.DataFrame([{"Risk Factor": key, "Points": value} for key, value in score_details.items()])


def _render_result(result: Dict[str, Any]) -> None:
    risk_level = result.get("risk_level", "Unknown")
    risk_score = result.get("risk_score", "N/A")
    confidence = result.get("confidence", "N/A")
    risk_source = result.get("risk_source", "Unknown")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Risk Level", risk_level)
    col2.metric("Static Risk Score", risk_score)
    col3.metric("Confidence", confidence)
    col4.metric("Risk Source", risk_source)

    ml_info = result.get("ml_prediction", {})
    with st.expander("ML Prediction Details", expanded=True):
        st.json(ml_info)
        if ml_info.get("used"):
            st.success("Saved ML model artifact was used for risk prediction.")
        else:
            st.warning("No usable ML artifact was used. Static evidence fallback was used instead.")

    st.subheader("Extracted Features")
    features = result.get("features", {})
    st.dataframe(_features_dataframe(features), use_container_width=True, hide_index=True)

    st.subheader("Static Risk Factors")
    score_details = result.get("score_details", {})
    if score_details:
        st.dataframe(_score_dataframe(score_details), use_container_width=True, hide_index=True)
    else:
        st.write("No static risk points were added.")

    st.subheader("Modernization Recommendations")
    for item in result.get("recommendations", []):
        st.write(f"- {item}")

    st.subheader("Evidence Proof")
    evidence = result.get("evidence", {})
    for section_name, lines in evidence.items():
        with st.expander(section_name.replace("_", " ").title()):
            if lines:
                st.code("\n".join(lines[:30]), language="text")
            else:
                st.write("No evidence found for this category.")

    with st.expander("Full Assessment JSON"):
        st.json(result)


def render_new_module_assessment() -> None:
    st.header("New Module Pre-Modernization Assessment")

    st.write(
        "Use this page before translation. You can either upload a new HLASM file or select a module "
        "already present in the HLASM folder. The assessor extracts features, tries to use the saved Week 1 ML "
        "model artifact when available, and generates evidence-backed modernization recommendations."
    )

    st.info(
        "This assessment is pre-modernization risk analysis. It does not replace Java generation, Java compilation, "
        "or behavior validation. After translation, still run java_generator.py and behavior_comparator.py."
    )

    detected_model = find_model_artifact()
    if detected_model:
        st.success(f"Saved ML artifact detected: `{detected_model}`")
    else:
        st.warning(
            "No saved ML artifact was detected. The page will use static evidence fallback. "
            "When the Week 1 RandomForest artifact is added, this page can use it automatically."
        )

    prefer_ml = st.checkbox("Use saved ML model artifact when available", value=True)

    input_mode = st.radio(
        "Choose module input source",
        ["Upload or paste new module", "Select module from HLASM folder"],
        horizontal=True,
    )

    source_text = ""
    module_name = "UPLOADED_MODULE"
    selected_file_path: Path | None = None

    if input_mode == "Upload or paste new module":
        uploaded_file = st.file_uploader(
            "Upload a new HLASM module",
            type=["asm", "txt"],
            help="Example file names: NEWMOD.asm, NEWMOD.asm.txt",
        )

        pasted_text = st.text_area(
            "Or paste HLASM source here",
            height=220,
            placeholder="Paste HLASM source here if you do not want to upload a file...",
        )

        if uploaded_file is not None:
            module_name = uploaded_file.name
            source_text = uploaded_file.getvalue().decode("utf-8", errors="ignore")
        elif pasted_text.strip():
            module_name = "PASTED_MODULE"
            source_text = pasted_text

    else:
        hlasm_files = _find_hlasm_files()
        if not hlasm_files:
            st.warning("No HLASM files found in the HLASM folder.")
        else:
            project_root = find_project_root()
            options = {str(path.relative_to(project_root)): path for path in hlasm_files}
            selected_label = st.selectbox("Select HLASM module", list(options.keys()))
            selected_file_path = options[selected_label]
            module_name = selected_file_path.name
            source_text = selected_file_path.read_text(encoding="utf-8", errors="ignore")

            with st.expander("Preview selected HLASM source"):
                st.code("\n".join(source_text.splitlines()[:80]), language="asm")

    if st.button("Analyze Module Risk", use_container_width=True):
        if not source_text.strip():
            st.warning("Upload, paste, or select a HLASM module first.")
            return

        with st.spinner("Assessing module using ML artifact/static evidence..."):
            if selected_file_path is not None:
                result = assess_hlasm_file(selected_file_path, prefer_ml=prefer_ml)
            else:
                result = assess_hlasm_text(source_text=source_text, module_name=module_name, prefer_ml=prefer_ml)

        _render_result(result)

        st.markdown(
            """
**Presentation explanation:**

This page is useful before translation. A modernization engineer can upload a new HLASM module or select an existing HLASM file. The system extracts features, attempts ML-based risk prediction using the saved model artifact, falls back to static evidence if needed, and gives recommendations before Java generation.
"""
        )
