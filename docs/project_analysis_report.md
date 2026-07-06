# Legacy Program Intelligence + Verification Report

Generated on: `2026-07-06 13:00:45`

## 1. Project Purpose

This report summarizes analysis results from the HLASM codebase. The system scans assembler modules, identifies program flow, extracts business data dependencies, detects parameter passing, captures VSAM/RPL record-buffer effects, records return-code behavior, and highlights modernization risks before Java conversion.

## 2. Repository Analysis Summary

- Total analyzed modules: `11`
- Analysis artifacts generated:
  - `analysis_report.json`
  - `docs/generated_behavior_report.md`
  - `docs/project_analysis_report.md`

**Modules detected:**

- `AUDWRITE`
- `AUTHDEC`
- `BCTCOUNT`
- `CARDSTAT`
- `CUSTVAL`
- `FEECALC`
- `FRDCHK`
- `LIMITCHK`
- `MAINDRV`
- `TXREAD`
- `VSAMPACK`

## 3. File / DDNAME Summary

- `INACB` references DDNAME `INVSAM` in module `MAINDRV`
- `OUTACB` references DDNAME `OUTVSAM` in module `MAINDRV`
- `INVSAM` references DDNAME `VSAMIN` in module `VSAMPACK`
- `OUTFILE` references DDNAME `VSAMOUT` in module `VSAMPACK`

## 4. Parameter Passing Summary

**Parameter blocks:**

- `READPARM` → `INRPL`, `CURRTX`
- `BUSPARM` → `CURRTX`, `ERRCODE`
- `DECPARM` → `CURRTX`, `ERRCODE`, `AUTHSTAT`
- `AUDPARM` → `OUTRPL`, `CURRTX`, `AUTHSTAT`

**Module parameter context:**

- `TXREAD` receives `READPARM` → `INRPL`, `CURRTX`
- `CUSTVAL` receives `BUSPARM` → `CURRTX`, `ERRCODE`
- `CARDSTAT` receives `BUSPARM` → `CURRTX`, `ERRCODE`
- `LIMITCHK` receives `BUSPARM` → `CURRTX`, `ERRCODE`
- `FRDCHK` receives `BUSPARM` → `CURRTX`, `ERRCODE`
- `FEECALC` receives `BUSPARM` → `CURRTX`, `ERRCODE`
- `AUTHDEC` receives `DECPARM` → `CURRTX`, `ERRCODE`, `AUTHSTAT`
- `AUDWRITE` receives `AUDPARM` → `OUTRPL`, `CURRTX`, `AUTHSTAT`

**Resolved register maps:**

- `AUDWRITE`: `R2`→`OUTRPL`, `R3`→`CURRTX`, `R4`→`AUTHSTAT`
- `AUTHDEC`: `R2`→`ERRCODE`, `R3`→`AUTHSTAT`, `R4`→`AUTHSTAT`
- `CARDSTAT`: `R2`→`CURRTX`, `R3`→`ERRCODE`
- `CUSTVAL`: `R2`→`CURRTX`, `R3`→`ERRCODE`
- `FEECALC`: `R2`→`CURRTX`, `R3`→`ERRCODE`
- `FRDCHK`: `R2`→`CURRTX`, `R3`→`ERRCODE`
- `LIMITCHK`: `R2`→`CURRTX`, `R3`→`ERRCODE`
- `TXREAD`: `R2`→`INRPL`, `R3`→`CURRTX`

## 5. Business Data Dependency Summary

### `AUDWRITE`

- Business Fields Read: `TXCUST`, `AUTHSTAT`, `TXCARD`, `TXAMT`, `LOGBUFF`
- Business Fields Written: `LOGBUFF`, `LOGCUST`, `LOGSTAT`, `LOGPAN`, `LOGMASK`

### `AUTHDEC`

- Business Fields Read: `AUTHSTAT`
- Business Fields Written: `AUTHSTAT`

### `BCTCOUNT`

- Business Fields Read: `COUNT`
- Business Fields Written: `TOTAL`

### `CARDSTAT`

- Business Fields Read: `TXSTAT`
- Business Fields Written: `ERRCODE`

### `CUSTVAL`

- Business Fields Read: `TXCUST`
- Business Fields Written: `ERRCODE`

### `FEECALC`

- Business Fields Read: `TXAMT`, `FEEWORK`
- Business Fields Written: `FEEWORK`, `TXFEE`

### `FRDCHK`

- Business Fields Read: `TXAMT`, `TXTYPE`
- Business Fields Written: `ERRCODE`

### `LIMITCHK`

- Business Fields Read: `TXAMT`, `TXLIMIT`
- Business Fields Written: `ERRCODE`

### `TXREAD`

- Business Fields Read: `INRPL`
- Business Fields Written: `CURRTX`

### `VSAMPACK`

- Business Fields Read: `WS_PACKED_AMT`, `WS_TAX_AMT`, `WS_ZONED_TAX`, `IN_RECORD`
- Business Fields Written: `WS_TAX_AMT`, `OUT_RECORD`

## 6. Record Buffer / VSAM I/O Effects

### `AUDWRITE`

- Record buffers read/written out: `LOGBUFF`

### `TXREAD`

- Record buffers written/populated: `CURRTX`

## 7. Return Code Summary

- `AUDWRITE` sets RC/R15 values: `0`
- `AUTHDEC` sets RC/R15 values: `0`
- `CARDSTAT` sets RC/R15 values: `4`, `0`
- `CUSTVAL` sets RC/R15 values: `4`, `0`
- `FEECALC` sets RC/R15 values: `0`
- `FRDCHK` sets RC/R15 values: `4`, `0`
- `LIMITCHK` sets RC/R15 values: `4`, `0`
- `MAINDRV` sets RC/R15 values: `0`, `12`, `16`
- `TXREAD` sets RC/R15 values: `8`, `4`, `0`

## 8. Condition Check Summary

### `AUTHDEC`

- `CLC` `AUTHSTAT`, `=C'0000'`

### `CARDSTAT`

- `CLI` `TXSTAT`, `C'A'`

### `CUSTVAL`

- `CLC` `TXCUST`, `=C'CUST'`

### `FRDCHK`

- `CP` `TXAMT`, `=P'50000'`
- `CLC` `TXTYPE`, `=C'RE'`

### `LIMITCHK`

- `CP` `TXAMT`, `TXLIMIT`

### `MAINDRV`

- `LTR` `15`, `15`
- `LTR` `15`, `15`
- `C` `15`, `=F'4'`
- `LTR` `15`, `15`
- `LTR` `15`, `15`
- `LTR` `15`, `15`
- `LTR` `15`, `15`

### `TXREAD`

- `LTR` `15`, `15`

### `VSAMPACK`

- `LTR` `R15`, `R15`
- `CLI` `0(R4)`, `C'A'`
- `CLI` `0(R4)`, `C'B'`
- `CLI` `0(R4)`, `C'T'`
- `CLI` `0(R4)`, `C'X'`
- `LTR` `R5`, `R5`

## 9. Impact Analysis Summary

### `LOGBUFF`

- Written by: `AUDWRITE`
- Read by: `AUDWRITE`
- Impacted modules: `AUDWRITE`

### `LOGCUST`

- Written by: `AUDWRITE`
- Read by: None
- Impacted modules: `AUDWRITE`

### `LOGPAN`

- Written by: `AUDWRITE`
- Read by: None
- Impacted modules: `AUDWRITE`

### `LOGSTAT`

- Written by: `AUDWRITE`
- Read by: None
- Impacted modules: `AUDWRITE`

### `LOGMASK`

- Written by: `AUDWRITE`
- Read by: None
- Impacted modules: `AUDWRITE`

### `COUNT`

- Written by: None
- Read by: `BCTCOUNT`
- Impacted modules: `BCTCOUNT`

### `TOTAL`

- Written by: `BCTCOUNT`
- Read by: None
- Impacted modules: `BCTCOUNT`

### `FEEWORK`

- Written by: `FEECALC`
- Read by: `FEECALC`
- Impacted modules: `FEECALC`

### `CURRTX`

- Written by: `TXREAD`
- Read by: None
- Impacted modules: `TXREAD`

### `TXCARD`

- Written by: None
- Read by: `AUDWRITE`
- Impacted modules: `AUDWRITE`

### `TXCUST`

- Written by: None
- Read by: `AUDWRITE`, `CUSTVAL`
- Impacted modules: `AUDWRITE`, `CUSTVAL`

### `TXAMT`

- Written by: None
- Read by: `AUDWRITE`, `FEECALC`, `FRDCHK`, `LIMITCHK`
- Impacted modules: `AUDWRITE`, `FEECALC`, `FRDCHK`, `LIMITCHK`

### `TXTYPE`

- Written by: None
- Read by: `FRDCHK`
- Impacted modules: `FRDCHK`

### `TXSTAT`

- Written by: None
- Read by: `CARDSTAT`
- Impacted modules: `CARDSTAT`

### `TXLIMIT`

- Written by: None
- Read by: `LIMITCHK`
- Impacted modules: `LIMITCHK`

### `TXFEE`

- Written by: `FEECALC`
- Read by: None
- Impacted modules: `FEECALC`

### `ERRCODE`

- Written by: `CARDSTAT`, `CUSTVAL`, `FRDCHK`, `LIMITCHK`
- Read by: None
- Impacted modules: `CARDSTAT`, `CUSTVAL`, `FRDCHK`, `LIMITCHK`

### `AUTHSTAT`

- Written by: `AUTHDEC`
- Read by: `AUDWRITE`, `AUTHDEC`
- Impacted modules: `AUDWRITE`, `AUTHDEC`

### `IN_RECORD`

- Written by: None
- Read by: `VSAMPACK`
- Impacted modules: `VSAMPACK`

### `OUT_RECORD`

- Written by: `VSAMPACK`
- Read by: None
- Impacted modules: `VSAMPACK`

### `WS_PACKED_AMT`

- Written by: None
- Read by: `VSAMPACK`
- Impacted modules: `VSAMPACK`

### `WS_TAX_AMT`

- Written by: `VSAMPACK`
- Read by: `VSAMPACK`
- Impacted modules: `VSAMPACK`

### `WS_ZONED_TAX`

- Written by: None
- Read by: `VSAMPACK`
- Impacted modules: `VSAMPACK`

## 10. Analyzer Notes / Modernization Risks

- AUTHDEC: AUTHSTAT mapped to multiple registers [3, 4]. Check LM/L parameter offsets.

These warnings indicate areas that should be reviewed before automatic Java conversion. They may represent register ambiguity, suspicious parameter offsets, VSAM/RPL buffer inference uncertainty, or data-flow uncertainty.

## 11. Recommended Next Steps

1. Review analyzer warnings before Java generation.
2. Use `generated_behavior_report.md` for module-level understanding.
3. Use `analysis_report.json` as the source for Java code generation.
4. Generate Java translation candidates module by module.
5. Validate Java behavior against expected assembler behavior using test cases.
6. Add ML-based behavioral validation after deterministic test harness is stable.
