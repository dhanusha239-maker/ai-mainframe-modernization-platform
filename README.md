# AI-Powered Mainframe Modernization Platform

## Functionality-Only Overview

## Executive Summary

This project is an AI-powered modernization platform for legacy mainframe assembler applications. It helps modernization teams understand risk, analyze legacy logic, generate modern Java code for supported patterns, validate behavior, and produce evidence-backed recommendations through a dashboard.

The purpose is not only to convert code. The purpose is to modernize safely by giving teams visibility into risk, dependencies, field impact, test results, and known source-code issues before making major modernization decisions.

## Business Problem

Many enterprise systems still rely on legacy mainframe applications that support critical business processes. These systems are often stable, but modernization is risky because important business logic can be hidden inside older technical code.

Common modernization challenges include complex branches, field-level dependencies, packed decimal calculations, batch file processing, limited documentation, and uncertainty about whether generated code preserves behavior.

This platform is designed to reduce that uncertainty.

## Platform Purpose

The platform answers five key questions:

| Question | Platform Capability |
|---|---|
| Which legacy components are risky? | Risk prediction and feature analysis |
| Why are they risky? | Evidence from branches, data usage, dependencies, and unsupported patterns |
| Can generated code preserve behavior? | Behavior validation using test cases |
| What fields or logic are impacted? | Field impact and dependency analysis |
| What should engineers do next? | AI-assisted modernization recommendations |

## End-to-End Functionality

The platform supports a full modernization review lifecycle:

```text
Legacy source code
        ↓
Risk prediction
        ↓
Static analysis
        ↓
Control-flow and data-impact analysis
        ↓
Code generation
        ↓
Behavior validation
        ↓
AI-assisted reporting
        ↓
Dashboard review
```

Each step produces evidence that can be reviewed by engineers and stakeholders.

## Main Capabilities

### 1. Risk Prediction

The platform predicts modernization risk using engineering features such as code size, branch count, dependency count, file input/output usage, packed decimal usage, unsupported instruction count, comment ratio, and change or defect indicators when available.

The result identifies whether a component appears Low, Medium, or High risk before modernization work continues.

The risk model does not rely only on code size. A large component can be lower risk if its logic is simple, while a smaller component can be higher risk if it contains business-critical branching, calculations, or dependencies.

### 2. New Module Assessment

The dashboard includes a pre-modernization assessment option.

A user can either upload a new legacy source file or select an existing source file from the project. The system then extracts features, checks for a saved machine learning model artifact, predicts risk when possible, and produces evidence-backed recommendations.

This is useful before translation because teams can estimate complexity and testing needs early.

The assessment shows risk level, confidence, risk source, extracted features, model prediction details when available, control-flow evidence, data-impact evidence, and recommended modernization actions.

### 3. Static Source Analysis

The platform analyzes legacy source code and identifies important technical patterns, including instruction structure, labels, operations, branches, loops, calls, dependencies, data declarations, file input/output patterns, packed decimal operations, and unsupported or review-required instructions.

This gives modernization engineers a clearer understanding of what the legacy code is doing before conversion.

### 4. Control-Flow Analysis

Control-flow analysis helps identify how program execution moves through conditions, branches, and loops.

This matters because modernization failures often happen when a branch, loop, or edge case is misunderstood.

Control-flow analysis supports branch risk review, path-based testing, loop behavior validation, and impact analysis before refactoring.

### 5. Data-Impact Analysis

Data-impact analysis helps identify which fields are defined, read, written, or shared.

This matters because a field change in one part of a legacy system can affect other processing steps.

Data-impact analysis supports field usage review, reader and writer identification, shared-data impact assessment, and regression testing guidance.

### 6. Instruction Translation Support

The platform separates instruction meaning from full code generation.

This makes the modernization process easier to extend because instruction behavior can be reviewed independently before complete Java code is generated.

Supported translation concepts include comparisons, field movement, decimal-style operations, loop behavior, file input/output behavior, and batch record processing.

### 7. Java Code Generation

The platform generates Java code for supported legacy patterns.

The generator is designed around a safety principle:

> Generated code should preserve source behavior. If the source behavior appears incorrect or ambiguous, the system should document the issue instead of silently changing the business logic.

This is important because modernization should not accidentally rewrite business rules without review.

### 8. Behavior Validation

Behavior validation checks whether generated Java behaves like the expected legacy behavior.

The platform runs test cases, compares outputs, and generates a behavior match score.

Current validation summary:

| Metric | Result |
|---|---|
| Total behavior tests | 17 |
| Passed tests | 15 |
| Failed tests | 2 |
| Behavior match score | 95.59% |

The remaining failures are documented as a source-program behavior issue. This is intentional transparency, not hidden failure.

### 9. AI-Assisted Modernization Reporting

The AI layer generates readable modernization guidance from project evidence.

The AI is not treated as the source of truth. It explains evidence from deterministic artifacts such as source analysis, generated code, behavior validation, known issues, and instruction coverage.

This makes the AI output more trustworthy because it is grounded in project evidence instead of unsupported assumptions.

The AI reporting layer helps produce modernization summaries, risk explanations, behavior failure explanations, field impact explanations, engineering recommendations, and audit metadata for LLM usage.

### 10. Dashboard Review

The dashboard provides a single review interface for the modernization workflow.

It supports executive summary, module-level risk review, field impact exploration, new module assessment, AI-assisted questions, modernization report viewing, and LLM usage details.

The dashboard is designed to be understandable for both business users and technical engineers.

## Trust and Evidence

The platform uses evidence-first modernization.

The trusted source of truth comes from source code, static analysis, control-flow analysis, data-impact analysis, generated code, behavior validation results, known issue documentation, and instruction coverage evidence.

The AI layer helps explain this evidence, but it does not replace engineering validation.

## Current Status

| Area | Status |
|---|---|
| Legacy source analysis | Available |
| Risk prediction | Available |
| New module assessment | Available |
| Java generation | Available for supported patterns |
| Behavior validation | Available |
| AI reporting | Available |
| Dashboard | Available |
| CI validation | Available |
| Known limitations | Documented |

## CI and Quality Validation

The project includes automated validation through GitHub Actions.

The CI process helps confirm that the project can be checked automatically after changes. It validates syntax, analysis tests, Java generation, Java compilation, behavior comparison, report generation, and secret-safety checks.

This improves confidence that the project is repeatable and not only working manually in one local environment.

## Business Value

The platform helps organizations reduce modernization uncertainty, prioritize high-risk components, identify risky calculations and dependencies, preserve business behavior, document known issues clearly, improve testing strategy, support better modernization planning, and provide technical evidence to stakeholders.

The core value is safer modernization with traceability.

## Current Limitations

This project is a strong proof-of-concept, not a complete enterprise migration product.

Current limitations include partial instruction coverage, behavior validation limited to available test cases, source behavior that requires human review, incomplete support for every enterprise macro or addressing pattern, and deployment packaging planned as future work.

These limitations are documented because real modernization requires transparency, testing, and engineering sign-off.

## Future Direction

Future improvements can include broader legacy instruction coverage, stronger model explainability, more automated test generation, richer dependency visualization, richer field-impact visualization, PDF report export, human review workflow, service API layer, container-based deployment, and enterprise integration support.

## Final Summary

This project demonstrates a complete modernization intelligence workflow.

It predicts risk, analyzes legacy structure, generates Java, validates behavior, assesses new modules before translation, identifies known source issues, and uses AI to produce evidence-backed recommendations.

The main goal is safe modernization: before changing legacy business logic, the platform explains risk, validates behavior, and gives engineers traceable guidance.
