# Modernization Dashboard

Generated on: `2026-06-28 19:41:33`

## 1. Executive Summary

- Modules analyzed: `9`
- Behavior match score: `93.75%`
- Total behavior tests: `16`
- Passed tests: `13`
- Failed tests: `3`
- Batch records: `4`
- Batch passed: `3`
- Batch failed: `1`

## 2. CFG / PDG Summary

- CFG available: `False`
- PDG available: `False`
- CFG module count: `0`
- PDG module count: `0`

## 3. Module Summary

| Module | Reads | Writes | Conditions | Behavior Match |
|---|---:|---:|---:|---:|
| `AUDWRITE` | 5 | 5 | 0 | N/A |
| `AUTHDEC` | 1 | 1 | 1 | 75.0% |
| `CARDSTAT` | 1 | 1 | 1 | 100.0% |
| `CUSTVAL` | 1 | 1 | 1 | 100.0% |
| `FEECALC` | 2 | 2 | 0 | 100.0% |
| `FRDCHK` | 2 | 1 | 2 | 100.0% |
| `LIMITCHK` | 2 | 1 | 1 | 100.0% |
| `MAINDRV` | 0 | 0 | 7 | 90.0% |
| `TXREAD` | 1 | 1 | 1 | N/A |

## 4. Behavior Validation Summary

- Total tests: `16`
- Passed: `13`
- Failed: `3`
- Average match score: `93.75%`

### Failed Behavior Cases

- `AUTHDEC_APPROVE_001` in module `AUTHDEC`
  - Match score: `50.0%`
- `APP_APPROVAL_FLOW_001` in module `MAINDRV`
  - Customer ID: `CUST000001`
  - Match score: `75.0%`
- `TX001` in module `MAINDRV`
  - Customer ID: `CUST000001`
  - Match score: `75.0%`

## 5. Batch Validation Summary

- Batch records: `4`
- Batch passed: `3`
- Batch failed: `1`

### Failed Batch Customers

- Case `TX001` / Customer `CUST000001` / Module `MAINDRV`

## 6. Change Impact Analysis

| Symbol | Written By | Read By | Impacted Modules | Impact Level |
|---|---|---|---:|---|
| `ERRCODE` | `CARDSTAT`, `CUSTVAL`, `FRDCHK`, `LIMITCHK` | None | 4 | `Medium` |
| `TXAMT` | None | `AUDWRITE`, `FEECALC`, `FRDCHK`, `LIMITCHK` | 4 | `Medium` |
| `AUTHSTAT` | `AUTHDEC` | `AUDWRITE`, `AUTHDEC` | 2 | `Low` |
| `TXCUST` | None | `AUDWRITE`, `CUSTVAL` | 2 | `Low` |
| `CURRTX` | `TXREAD` | None | 1 | `Low` |
| `FEEWORK` | `FEECALC` | `FEECALC` | 1 | `Low` |
| `INRPL` | None | `TXREAD` | 1 | `Low` |
| `LOGBUFF` | `AUDWRITE` | `AUDWRITE` | 1 | `Low` |
| `LOGCUST` | `AUDWRITE` | None | 1 | `Low` |
| `LOGMASK` | `AUDWRITE` | None | 1 | `Low` |
| `LOGPAN` | `AUDWRITE` | None | 1 | `Low` |
| `LOGSTAT` | `AUDWRITE` | None | 1 | `Low` |
| `TXCARD` | None | `AUDWRITE` | 1 | `Low` |
| `TXFEE` | `FEECALC` | None | 1 | `Low` |
| `TXLIMIT` | None | `LIMITCHK` | 1 | `Low` |

## 7. Recommendations

- Review failed behavior comparison cases and update translator rules or document known limitations.
- Review failed batch customer IDs and confirm whether expected ASM behavior or generated Java behavior should be adjusted.
- Use this dashboard with the Week 1 ML risk predictor output to create a combined modernization intelligence report.

## 8. Week 1 ML Integration Placeholder

Week 1 ML risk predictor output can be added here later. This dashboard intentionally does not retrain ML models. It consumes modernization and validation outputs from Week 2.
