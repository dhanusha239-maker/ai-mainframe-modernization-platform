# AI-Powered Mainframe Modernization Platform  
## Concise Business and Technical Overview

## Executive Snapshot

This project is a proof-of-concept modernization platform for legacy HLASM mainframe programs. It combines machine learning, static code analysis, Java generation, behavior validation, and AI-assisted reporting to help modernization teams understand risk before changing business-critical legacy logic.

The platform does not focus only on code conversion. Its main purpose is safe modernization: identify risky modules, explain why they are risky, generate Java for supported patterns, validate behavior, and provide evidence-backed recommendations.

## Business Problem

Many enterprises still depend on mainframe systems for banking, insurance, healthcare, finance, and batch processing. These systems are stable, but modernization is difficult because business rules are often hidden inside older assembler programs.

Modernization can fail when teams do not fully understand:

- which modules are risky
- which fields are shared across modules
- how branches and loops affect behavior
- whether decimal calculations are preserved
- whether generated code still matches expected legacy behavior

This project addresses those risks with an analysis-first modernization approach.

## Platform Solution

The platform supports the modernization lifecycle in this order:

```text
HLASM source
    ↓
Risk prediction and static analysis
    ↓
CFG / PDG evidence extraction
    ↓
Java generation
    ↓
Behavior validation
    ↓
AI modernization report
    ↓
Dashboard review
```

This creates a repeatable process for reviewing legacy code before and after translation.

## Core Capabilities

| Capability | Purpose |
|---|---|
| ML risk prediction | Predict Low / Medium / High modernization risk using engineering features |
| HLASM analysis | Parse modules, labels, opcodes, operands, branches, calls, and data declarations |
| CFG analysis | Identify control-flow behavior such as branches and loops |
| PDG-style analysis | Identify field usage, data impact, readers, writers, and shared symbols |
| Java generation | Generate Java code for supported HLASM patterns |
| Behavior validation | Compare generated Java behavior against expected legacy behavior |
| AI reporting | Summarize risks, failures, and recommendations using project evidence |
| Dashboard | Provide a single review interface for engineers and stakeholders |
| New module assessment | Upload/select a module and predict risk before translation |

## Current Results

| Area | Result |
|---|---|
| HLASM modules analyzed | 11 |
| Generated Java modules | 11 |
| Behavior test cases | 17 |
| Passed tests | 15 |
| Failed tests | 2 |
| Behavior match score | 95.59% |
| Known issue | AUTHDEC approval behavior documented as source issue |
| CI/CD | GitHub Actions workflow added and passing |
| Dashboard | Streamlit dashboard with module, field, AI, and new-module views |

The two failed tests are documented instead of hidden. They are treated as a source-program behavior issue, not silently corrected by the generator.

## New Module Assessment

The dashboard includes a pre-modernization assessment feature.

A user can either:

- upload or paste a new HLASM module
- select an existing module from the `HLASM` folder

The system extracts modernization features such as:

- lines of code
- branch count
- file I/O count
- packed decimal count
- unsupported instruction count
- comment ratio
- symbol/data references

When the saved Week 1 ML model artifact is available, the system uses it for risk prediction. If the model artifact is not available, it clearly falls back to static evidence scoring.

Output includes:

- risk level
- confidence
- risk source
- extracted features
- ML prediction details
- evidence lines
- modernization recommendations

This helps teams review a module before translation and decide how much testing and engineering review is needed.

## AI and Trust

The LLM is not the source of truth.

The trusted evidence comes from:

- HLASM source files
- CFG / PDG analysis
- generated Java
- behavior comparison results
- known issue documentation
- instruction coverage artifacts

The LLM is used as an explanation layer. It summarizes and explains the evidence, but final decisions are based on deterministic project artifacts and validation results.

## Business Value

This platform helps modernization teams:

- prioritize risky modules
- reduce manual code-review effort
- identify field and module impact
- validate generated Java behavior
- document known source-code issues
- create evidence-backed modernization reports
- review new modules before translation

The value is not only automation. The value is safer modernization with traceability.

## Technical Foundation

Main project components:

| File / Area | Purpose |
|---|---|
| `ml_risk_predictor/` | ML-based modernization risk intelligence |
| `validator/asm_scanner.py` | HLASM scanning |
| `validator/cfg_builder.py` | Control-flow analysis |
| `validator/pdg_builder.py` | Data-impact analysis |
| `validator/instruction_semantics.py` | Supported instruction meaning |
| `validator/instruction_translator.py` | Instruction-level translation support |
| `validator/java_generator.py` | Java generation |
| `validator/behavior_comparator.py` | Behavior validation |
| `validator/ai_modernization_engine.py` | AI modernization report generation |
| `validator/new_module_assessor.py` | New module risk assessment |
| `validator/modernization_dashboard.py` | Streamlit dashboard |
| `.github/workflows/ci.yml` | GitHub Actions CI pipeline |

## CI/CD Validation

The project includes a GitHub Actions workflow that validates the project automatically on push and pull request.

The CI pipeline checks:

- Python syntax
- scanner / CFG / PDG tests
- documentation generation
- Java generation
- Java compilation
- behavior comparison
- AI report generation in offline mode
- obvious committed API key patterns

This shows that the project is repeatable and not dependent only on manual local execution.

## Current Limitations

This is a modernization proof-of-concept, not a complete enterprise migration product.

Current limitations:

- HLASM instruction coverage is partial
- behavior validation depends on available test cases
- not every assembler macro or addressing pattern is supported
- AUTHDEC approval behavior requires source review
- Docker, FastAPI, and cloud deployment are future enhancements

These limitations are documented because enterprise modernization requires transparency and engineering review.

## Future Direction

Planned improvements include:

- broader HLASM instruction coverage
- more test cases and automated test generation
- SHAP-based model explanation per module
- dependency graph and field-impact visualization
- FastAPI service layer
- Docker packaging
- enterprise deployment support
- human review and approval workflow

## Final Summary

This project demonstrates an integrated approach to mainframe modernization.

It predicts risk, analyzes HLASM structure, generates Java, validates behavior, identifies source issues, assesses new modules before translation, and uses AI to provide evidence-backed modernization guidance.

The core value is safe modernization: before changing legacy business logic, the platform explains risk, validates behavior, and gives engineers traceable recommendations.
