# HLASM Module Behavior Report

Generated from `analysis_report.json`.

## File / DDNAME Summary

- `INACB` uses DDNAME `INVSAM` in module `MAINDRV`
- `OUTACB` uses DDNAME `OUTVSAM` in module `MAINDRV`

## Module Behavior Summary

### Module: `AUDWRITE`

**Parameter block received:**

- `AUDPARM` → `OUTRPL`

**Resolved register map:**

- `R2` → `OUTRPL`

**Inputs used / fields read:**

- None detected

**Outputs / fields written:**

- `LOGBUFF`
- `LOGCUST`
- `LOGSTAT`
- `LOGPAN`
- `LOGMASK`

**Condition checks:**

- None detected

**Return codes set:**

- RC `0`

### Module: `AUTHDEC`

**Parameter block received:**

- `DECPARM` → `CURRTX`, `ERRCODE`, `AUTHSTAT`

**Resolved register map:**

- `R2` → `ERRCODE`
- `R3` → `AUTHSTAT`
- `R4` → `AUTHSTAT`

**Inputs used / fields read:**

- `AUTHSTAT`

**Outputs / fields written:**

- `AUTHSTAT`

**Condition checks:**

- `CLC` `AUTHSTAT`, `=C'0000'`

**Return codes set:**

- RC `0`

**Analyzer notes:**

- AUTHDEC: AUTHSTAT mapped to multiple registers [3, 4]. Check LM/L parameter offsets.
- Parameter block `DECPARM` contains: `CURRTX`, `ERRCODE`, `AUTHSTAT`.
- `AUTHSTAT` is resolved through multiple registers: `R3`, `R4`. This may indicate ambiguous or suspicious parameter offset usage.
- Review condition checks in this module before Java conversion, because register ambiguity can change which business field is actually being compared.
- Recommendation: do not auto-convert this module without manual review of parameter offsets and register usage.

### Module: `CARDSTAT`

**Parameter block received:**

- `BUSPARM` → `CURRTX`, `ERRCODE`

**Resolved register map:**

- `R2` → `CURRTX`
- `R3` → `ERRCODE`

**Inputs used / fields read:**

- `TXSTAT`

**Outputs / fields written:**

- `ERRCODE`

**Condition checks:**

- `CLI` `TXSTAT`, `C'A'`

**Return codes set:**

- RC `4`
- RC `0`

### Module: `CUSTVAL`

**Parameter block received:**

- `BUSPARM` → `CURRTX`, `ERRCODE`

**Resolved register map:**

- `R2` → `CURRTX`
- `R3` → `ERRCODE`

**Inputs used / fields read:**

- `TXCUST`

**Outputs / fields written:**

- `ERRCODE`

**Condition checks:**

- `CLC` `TXCUST`, `=C'CUST'`

**Return codes set:**

- RC `4`
- RC `0`

### Module: `FEECALC`

**Parameter block received:**

- `BUSPARM` → `CURRTX`, `ERRCODE`

**Resolved register map:**

- `R2` → `CURRTX`
- `R3` → `ERRCODE`

**Inputs used / fields read:**

- `TXAMT`
- `FEEWORK`

**Outputs / fields written:**

- `FEEWORK`
- `TXFEE`

**Condition checks:**

- None detected

**Return codes set:**

- RC `0`

### Module: `FRDCHK`

**Parameter block received:**

- `BUSPARM` → `CURRTX`, `ERRCODE`

**Resolved register map:**

- `R2` → `CURRTX`
- `R3` → `ERRCODE`

**Inputs used / fields read:**

- `TXAMT`
- `TXTYPE`

**Outputs / fields written:**

- `ERRCODE`

**Condition checks:**

- `CP` `TXAMT`, `=P'50000'`
- `CLC` `TXTYPE`, `=C'RE'`

**Return codes set:**

- RC `4`
- RC `0`

### Module: `LIMITCHK`

**Parameter block received:**

- `BUSPARM` → `CURRTX`, `ERRCODE`

**Resolved register map:**

- `R2` → `CURRTX`
- `R3` → `ERRCODE`

**Inputs used / fields read:**

- `TXAMT`
- `TXLIMIT`

**Outputs / fields written:**

- `ERRCODE`

**Condition checks:**

- `CP` `TXAMT`, `TXLIMIT`

**Return codes set:**

- RC `4`
- RC `0`

### Module: `MAINDRV`

**Inputs used / fields read:**

- None detected

**Outputs / fields written:**

- None detected

**Condition checks:**

- `LTR` `15`, `15`
- `LTR` `15`, `15`
- `C` `15`, `=F'4'`
- `LTR` `15`, `15`
- `LTR` `15`, `15`
- `LTR` `15`, `15`
- `LTR` `15`, `15`

**Return codes set:**

- RC `0`
- RC `12`
- RC `16`

### Module: `TXREAD`

**Parameter block received:**

- `READPARM` → `INRPL`

**Resolved register map:**

- `R2` → `INRPL`

**Inputs used / fields read:**

- `INRPL`

**Outputs / fields written:**

- None detected

**Condition checks:**

- `LTR` `15`, `15`

**Return codes set:**

- RC `8`
- RC `4`
- RC `0`

## Analyzer Notes / Warnings

- AUTHDEC: AUTHSTAT mapped to multiple registers [3, 4]. Check LM/L parameter offsets.

These warnings do not necessarily mean the program is invalid. They indicate areas where register usage, parameter offsets, or data-flow inference should be manually reviewed before Java conversion.
