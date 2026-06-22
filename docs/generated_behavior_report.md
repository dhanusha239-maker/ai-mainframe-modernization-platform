# HLASM Module Behavior Report

Generated from `analysis_report.json`.

## File / DDNAME Summary

- `INACB` uses DDNAME `INVSAM` in module `MAINDRV`
- `OUTACB` uses DDNAME `OUTVSAM` in module `MAINDRV`

## Module Behavior Summary

### Module: `AUDWRITE`

**Parameter block received:**

- `AUDPARM` → `OUTRPL`, `CURRTX`, `AUTHSTAT`

**Parameter addresses received:**

- Address of `OUTRPL`
- Address of `CURRTX`
- Address of `AUTHSTAT`

**Resolved register map:**

- `R2` → address of `OUTRPL`
- `R3` → address of `CURRTX`
- `R4` → address of `AUTHSTAT`

**Business/data fields read by instructions:**

- `TXCUST`
- `AUTHSTAT`
- `TXCARD`
- `TXAMT`

**Output fields written by instructions:**

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

**Parameter addresses received:**

- Address of `CURRTX`
- Address of `ERRCODE`
- Address of `AUTHSTAT`

**Resolved register map:**

- `R2` → address of `ERRCODE`
- `R3` → address of `AUTHSTAT`
- `R4` → address of `AUTHSTAT`

**Business/data fields read by instructions:**

- `AUTHSTAT`

**Output fields written by instructions:**

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

**Parameter addresses received:**

- Address of `CURRTX`
- Address of `ERRCODE`

**Resolved register map:**

- `R2` → address of `CURRTX`
- `R3` → address of `ERRCODE`

**Business/data fields read by instructions:**

- `TXSTAT`

**Output fields written by instructions:**

- `ERRCODE`

**Condition checks:**

- `CLI` `TXSTAT`, `C'A'`

**Return codes set:**

- RC `4`
- RC `0`

### Module: `CUSTVAL`

**Parameter block received:**

- `BUSPARM` → `CURRTX`, `ERRCODE`

**Parameter addresses received:**

- Address of `CURRTX`
- Address of `ERRCODE`

**Resolved register map:**

- `R2` → address of `CURRTX`
- `R3` → address of `ERRCODE`

**Business/data fields read by instructions:**

- `TXCUST`

**Output fields written by instructions:**

- `ERRCODE`

**Condition checks:**

- `CLC` `TXCUST`, `=C'CUST'`

**Return codes set:**

- RC `4`
- RC `0`

### Module: `FEECALC`

**Parameter block received:**

- `BUSPARM` → `CURRTX`, `ERRCODE`

**Parameter addresses received:**

- Address of `CURRTX`
- Address of `ERRCODE`

**Resolved register map:**

- `R2` → address of `CURRTX`
- `R3` → address of `ERRCODE`

**Business/data fields read by instructions:**

- `TXAMT`
- `FEEWORK`

**Output fields written by instructions:**

- `FEEWORK`
- `TXFEE`

**Condition checks:**

- None detected

**Return codes set:**

- RC `0`

### Module: `FRDCHK`

**Parameter block received:**

- `BUSPARM` → `CURRTX`, `ERRCODE`

**Parameter addresses received:**

- Address of `CURRTX`
- Address of `ERRCODE`

**Resolved register map:**

- `R2` → address of `CURRTX`
- `R3` → address of `ERRCODE`

**Business/data fields read by instructions:**

- `TXAMT`
- `TXTYPE`

**Output fields written by instructions:**

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

**Parameter addresses received:**

- Address of `CURRTX`
- Address of `ERRCODE`

**Resolved register map:**

- `R2` → address of `CURRTX`
- `R3` → address of `ERRCODE`

**Business/data fields read by instructions:**

- `TXAMT`
- `TXLIMIT`

**Output fields written by instructions:**

- `ERRCODE`

**Condition checks:**

- `CP` `TXAMT`, `TXLIMIT`

**Return codes set:**

- RC `4`
- RC `0`

### Module: `MAINDRV`

**Business/data fields read by instructions:**

- None detected

**Output fields written by instructions:**

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

- `READPARM` → `INRPL`, `CURRTX`

**Parameter addresses received:**

- Address of `INRPL`
- Address of `CURRTX`

**Resolved register map:**

- `R2` → address of `INRPL`
- `R3` → address of `CURRTX`

**Business/data fields read by instructions:**

- `INRPL`

**Output fields written by instructions:**

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
