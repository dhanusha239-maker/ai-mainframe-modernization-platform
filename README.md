# AI-Powered Legacy Software Intelligence & Modernization Platform

## Executive Summary

This project is an AI-powered legacy modernization platform that analyzes HLASM assembler modules, predicts modernization risk, generates Java code for supported logic, validates generated behavior, and produces AI-assisted modernization recommendations through a Streamlit dashboard.

The goal is not only to translate legacy code. The goal is to modernize safely by understanding risk, preserving business behavior, identifying source-code issues, and giving engineers evidence-based recommendations.

---

## Project Status

Current implementation status:

| Area | Current Status |
|---|---|
| HLASM modules analyzed | 11 modules |
| Java generation | Working for supported HLASM patterns |
| Behavior validation | 15 / 17 tests passed |
| Behavior match score | 95.59% |
| Known issue | AUTHDEC approval-path behavior documented as source issue |
| AI reporting | OpenAI LLM integration supported |
| Dashboard | Streamlit dashboard available |
| Production generator | `validator/java_generator.py` |
| AI files | `validator/ai_modernization_engine.py`, `validator/modernization_dashboard.py` |

---

## Business Problem

Many enterprises still depend on mainframe systems written in HLASM, COBOL, PL/I, and other legacy technologies. These systems are business-critical, but modernization is risky because legacy code often contains:

- Complex branching and loops
- Interlinked modules and parameter passing
- Packed decimal arithmetic
- File and VSAM-style I/O
- External calls and macros
- Limited documentation
- Business rules hidden inside technical instructions

Before modernizing legacy applications, engineers need to answer:

- Which modules are risky to modernize?
- Why are those modules risky?
- Can generated Java preserve the original behavior?
- Which fields and modules are impacted by a change?
- Which modernization steps should engineers follow?

This project addresses those questions using ML-style risk intelligence, static analysis, Java generation, behavior validation, and AI-assisted reporting.

---

## What This Platform Does

The platform performs five major functions:

1. **ML-Based Risk Intelligence**  
   Evaluates modernization risk using engineering features such as LOC, branching, dependencies, file I/O, packed decimal usage, unsupported instructions, defect/change indicators, and documentation quality.

2. **HLASM Static Analysis**  
   Parses HLASM modules and identifies labels, opcodes, operands, branches, calls, data declarations, packed decimal operations, and file I/O behavior.

3. **HLASM-to-Java Modernization**  
   Generates Java code for supported HLASM patterns, including validation logic, packed decimal-style operations, DDNAME-based local I/O, BCT loop behavior, and batch record processing.

4. **Behavioral Validation**  
   Runs test cases against generated Java output and compares behavior with expected legacy outcomes.

5. **AI Modernization Intelligence**  
   Uses project artifacts and an optional OpenAI LLM integration to produce modernization reports, failure diagnostics, field impact explanations, and dashboard-based recommendations.

---

## Architecture

```text
HLASM/*.asm.txt
        ↓
Scanner / CFG / PDG Analysis
        ↓
documentation_generator.py
        ↓
analysis_report.json
        ↓
Instruction Semantics + Instruction Translator
        ↓
Java Generator
        ↓
generated_java/*.java
        ↓
Behavior Comparator
        ↓
docs/behavior_comparison_report.md
docs/behavior_comparison_results.json
        ↓
AI Modernization Engine
        ↓
docs/ai_modernization_report.md
docs/ai_llm_integration_details.json
        ↓
Streamlit Modernization Dashboard
```

---

## Week 1: ML-Based Legacy Code Risk Intelligence

The Week 1 component focuses on predicting modernization risk before translation begins.

The risk model is designed to learn from multiple software engineering signals, not just module size.

Example risk features:

- Lines of code
- Branch instruction count
- Called module count
- Calling module count
- File I/O operation count
- Database access operation count
- Macro call count
- Packed decimal instruction count
- Historical defect count
- Change count in the last 12 months
- Comment ratio
- Unsupported instruction count

Risk output:

- Low / Medium / High modernization risk
- Prediction confidence
- Top risk factors
- Feature importance explanation
- SHAP-style sample explanation when model artifacts are available

Important idea:

> A large reporting module can be low risk if it has simple logic and few dependencies. A small authorization module can be high risk if it has deep branching, frequent changes, packed decimal logic, unsupported instructions, or business-critical dependencies.

---

## Week 2: HLASM-to-Java Modernization and Validation

The Week 2 component modernizes supported HLASM modules and validates behavior.

Main modules in the sample modernization flow:

| Module | Purpose |
|---|---|
| `MAINDRV` | Main orchestration module |
| `TXREAD` | Reads transaction records |
| `CUSTVAL` | Customer validation |
| `CARDSTAT` | Card status validation |
| `LIMITCHK` | Limit check |
| `FRDCHK` | Fraud/risk check |
| `FEECALC` | Packed decimal-style fee calculation |
| `AUTHDEC` | Authorization decision |
| `AUDWRITE` | Audit record output |
| `VSAMPACK` | Batch record transformation and tax-style packed decimal logic |
| `BCTCOUNT` | BCT loop behavior validation |

---

## Instruction Translation Layer

The translation layer separates instruction meaning from complete Java generation.

| File | Purpose |
|---|---|
| `validator/instruction_semantics.py` | Defines semantic meaning for supported HLASM instructions |
| `validator/instruction_translator.py` | Converts individual HLASM instructions into Java-friendly translation patterns |
| `validator/java_generator.py` | Uses those patterns to generate complete Java module files |

Example translation concepts:

- `CLC` / `CLI` → Java comparison logic
- `MVC` → field/string movement
- `PACK`, `ZAP`, `MP`, `UNPK`, `SRP` → decimal-style operations
- `BCT` → loop behavior
- `GET` / `PUT` / DDNAME → local file input/output behavior

---

## AI / LLM Integration

The project uses the LLM as an explanation and reporting layer. The LLM is **not** the source of truth.

The deterministic source of truth comes from:

- HLASM source modules
- CFG / PDG analysis
- Java generation output
- Behavior comparison results
- Known source issue documentation
- Instruction coverage artifacts

The AI engine generates:

- `docs/ai_modernization_report.md`
- `docs/ai_llm_integration_details.json`

The LLM integration details file records:

- Provider
- Model name
- Whether the LLM call was used
- Prompt SHA256
- Context SHA256
- Input artifacts used
- Timestamp

This makes the AI layer auditable and evidence-based.

---

## Dashboard Features

The Streamlit dashboard provides a production-style modernization review interface.

Dashboard pages:

1. **Executive Summary**  
   Shows behavior match score, passed/failed tests, HLASM module count, and LLM usage status.

2. **Module Explorer**  
   Allows selecting a module from a dropdown and viewing risk score, called modules, calling modules, technical factors, and modernization recommendations.

3. **Field Impact Explorer**  
   Allows searching fields such as `ERRCODE`, `TXAMT`, `AUTHSTAT`, `TXFEE`, and shows writer modules, reader modules, impacted modules, and evidence lines.

4. **AI Chatbot**  
   Answers grounded questions about modules, fields, behavior failures, risk, and modernization recommendations.

5. **AI Report / LLM Details**  
   Displays the generated AI modernization report and LLM integration metadata.

Example chatbot questions:

```text
bctcount
tax calculation modules
Which modules use ERRCODE?
Why did AUTHDEC fail?
Why is VSAMPACK high risk?
What tests should I add for LIMITCHK?
```

---

## Project Structure

```text
AI-Powered Legacy Software Intelligence & Modernization Platform/
│
├── HLASM/                         # Sample HLASM source modules
├── generated_java/                # Generated Java files
├── ml_risk_predictor/             # ML risk intelligence component
├── test_cases/                    # Behavior test inputs and expected paths
├── tests/                         # Scanner / CFG / PDG / runtime tests
├── validator/                     # Core modernization pipeline
│   ├── asm_scanner.py
│   ├── cfg_builder.py
│   ├── pdg_builder.py
│   ├── impact_analyzer.py
│   ├── instruction_semantics.py
│   ├── instruction_translator.py
│   ├── java_generator.py
│   ├── behavior_comparator.py
│   ├── ai_modernization_engine.py
│   └── modernization_dashboard.py
│
├── docs/                          # Generated reports and AI documentation
├── analysis_report.json
├── instruction_coverage_matrix_v3.md
├── LOCAL_IO_SETUP.md
├── PROJECT_RUNBOOK.md
├── README.md
└── requirements.txt
```

---

## Quick Start

### 1. Activate the environment

```powershell
cd "C:\Users\dhanu\AI-Powered Legacy Software Intelligence & Modernization Platform"
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 3. Run static-analysis tests

```powershell
python tests\test_scanner.py
python tests\test_cfg_builder.py
python tests\test_pdg_builder.py
```

### 4. Generate analysis documentation

```powershell
python validator\documentation_generator.py
python validator\impact_analyzer.py
```

### 5. Demonstrate instruction-level translation

```powershell
python validator\instruction_translator.py
```

### 6. Generate Java

```powershell
python validator\java_generator.py
```

### 7. Compile generated Java

```powershell
cd generated_java
javac *.java
cd ..
```

### 8. Run behavior validation

```powershell
python validator\behavior_comparator.py
```

Expected result:

```text
Total test cases: 17
Passed cases: 15
Failed cases: 2
Average behavior match score: 95.59%
```

### 9. Generate AI modernization report

To run with LLM enabled, set your key locally in PowerShell. Do not commit the key.

```powershell
$env:OPENAI_API_KEY = "paste_your_key_here"
$env:OPENAI_MODEL = "gpt-4.1-mini"
$env:AI_USE_LLM = "1"

python validator\ai_modernization_engine.py
```

To run without LLM:

```powershell
$env:AI_USE_LLM = "0"
python validator\ai_modernization_engine.py
```

### 10. Run dashboard

```powershell
python -m streamlit run validator\modernization_dashboard.py
```

---

## Behavior Validation Results

Current result:

| Metric | Value |
|---|---|
| Total test cases | 17 |
| Passed cases | 15 |
| Failed cases | 2 |
| Behavior match score | 95.59% |

The two accepted failures are related to the documented `AUTHDEC` approval-path behavior.

---

## Known Limitation

The current behavior validation has two accepted failures related to `AUTHDEC` approval behavior.

This is documented as a source-program issue, not a Java generator defect. The generator should not silently change business behavior. The correct modernization approach is to review or fix the original source logic before production migration sign-off.

See:

```text
docs/known_hlasm_issues.md
```

---

## Reports and Artifacts

| File | Purpose |
|---|---|
| `docs/project_analysis_report.md` | Static analysis and module analysis report |
| `docs/generated_behavior_report.md` | Generated behavior documentation |
| `docs/behavior_comparison_report.md` | Behavior validation summary |
| `docs/behavior_comparison_results.json` | Machine-readable validation result |
| `docs/ai_modernization_report.md` | Final AI-generated modernization report |
| `docs/ai_llm_integration_details.json` | LLM integration metadata and audit details |
| `docs/known_hlasm_issues.md` | Documents known source behavior issues |
| `instruction_coverage_matrix_v3.md` | Instruction coverage evidence |
| `LOCAL_IO_SETUP.md` | Local DDNAME/file setup notes |
| `PROJECT_RUNBOOK.md` | Step-by-step runbook for demo and review |

---

## Adding a New HLASM Module

Basic flow:

```powershell
Copy-Item "C:\Users\dhanu\Downloads\NEWMOD.asm.txt" HLASM\NEWMOD.asm.txt -Force

python tests\test_scanner.py
python tests\test_cfg_builder.py
python tests\test_pdg_builder.py

python validator\documentation_generator.py
python validator\java_generator.py
python validator\behavior_comparator.py
python validator\ai_modernization_engine.py
python -m streamlit run validator\modernization_dashboard.py
```

If the new module requires behavior validation, add a test case to:

```text
test_cases/behavior_test_cases.json
```

Static analysis and AI reporting can detect the module immediately, but behavior score coverage requires a behavior test case.

---

## CI/CD Readiness

Recommended CI/CD checks:

- Python syntax check
- Scanner test
- CFG builder test
- PDG builder test
- Java generation
- Java compilation
- Behavior comparison
- AI report generation in offline mode using `AI_USE_LLM=0`

The AI report can run offline in CI so no OpenAI key is required in GitHub Actions.

---

## Future Enhancements

Planned enhancements are documented in:

```text
docs/future_enhancements.md
```

Important future improvements include:

- Expanded HLASM instruction coverage
- Stronger Week 1 ML model integration into the dashboard
- SHAP explanation per module
- Automated test case generation from CFG/PDG
- Module dependency graph visualization
- Field impact graph visualization
- Exportable PDF modernization report
- Human-in-the-loop review workflow
- Docker or cloud deployment

---

## Usage Notice

This repository is shared as a professional portfolio project to demonstrate skills in mainframe modernization, HLASM analysis, Java generation, behavioral validation, ML-based risk intelligence, and AI-assisted modernization reporting.

The project uses synthetic/sample HLASM programs and test data. It does not contain proprietary client code, production mainframe assets, or confidential business data.

Organizations are welcome to review this repository for hiring, technical evaluation, and discussion purposes. For commercial reuse, production adoption, or integration into enterprise systems, please contact the author.

---

## Final Summary

This project is not just a translator and not just an ML model. It is an integrated modernization platform that predicts risk, analyzes HLASM, generates Java, validates behavior, documents known source issues, and uses AI to provide modernization guidance.

The core value is safe modernization: before changing legacy business logic, the platform explains risk, validates behavior, and gives engineers evidence-based recommendations.
