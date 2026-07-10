# Behavior Comparison Report

This report compares expected assembler behavior against actual generated Java execution output.

## Summary

- Total test cases: `17`
- Passed cases: `15`
- Failed cases: `2`
- Average behavior match score: `95.59%`

## Batch Validation Summary

- Batch records processed: `1`
- Batch passed: `1`
- Batch failed: `0`
- Failure customer IDs: `None`

## Validation Flow

1. Read expected assembler behavior from `test_cases/behavior_test_cases.json`.
2. Generate `generated_java/BehaviorTestRunner.java` dynamically.
3. Compile generated Java using `javac`.
4. Execute generated Java using `java BehaviorTestRunner`.
5. Capture actual Java output from `generated_java/java_behavior_output.json`.
6. Compare expected assembler output vs actual Java output.

## Detailed Results

### Test Case: `CUSTVAL_VALID_001`

- Mode: `module`
- Module: `CUSTVAL`
- Description: Customer ID begins with CUST and should pass validation.
- Match score: `100.0%`
- Fields matched: `2/2`

**Input:**

```json
{
  "TXCUST": "CUST000001",
  "ERRCODE": "0000"
}
```

**Expected ASM Output:**

```json
{
  "RC": "0",
  "ERRCODE": "0000"
}
```

**Actual Java Output:**

```json
{
  "case_id": "CUSTVAL_VALID_001",
  "module": "CUSTVAL",
  "RC": "0",
  "ERRCODE": "0000",
  "AUTHSTAT": "",
  "TXFEE": "",
  "TXAMT": "",
  "TXLIMIT": "",
  "TXCUST": "CUST000001",
  "TXSTAT": "",
  "TXTYPE": ""
}
```

No mismatches detected.

### Test Case: `CUSTVAL_INVALID_001`

- Mode: `module`
- Module: `CUSTVAL`
- Description: Customer ID does not begin with CUST and should set E001.
- Match score: `100.0%`
- Fields matched: `2/2`

**Input:**

```json
{
  "TXCUST": "BAD000001",
  "ERRCODE": "0000"
}
```

**Expected ASM Output:**

```json
{
  "RC": "4",
  "ERRCODE": "E001"
}
```

**Actual Java Output:**

```json
{
  "case_id": "CUSTVAL_INVALID_001",
  "module": "CUSTVAL",
  "RC": "4",
  "ERRCODE": "E001",
  "AUTHSTAT": "",
  "TXFEE": "",
  "TXAMT": "",
  "TXLIMIT": "",
  "TXCUST": "BAD000001",
  "TXSTAT": "",
  "TXTYPE": ""
}
```

No mismatches detected.

### Test Case: `CARDSTAT_ACTIVE_001`

- Mode: `module`
- Module: `CARDSTAT`
- Description: Card status is active and should pass validation.
- Match score: `100.0%`
- Fields matched: `2/2`

**Input:**

```json
{
  "TXSTAT": "A",
  "ERRCODE": "0000"
}
```

**Expected ASM Output:**

```json
{
  "RC": "0",
  "ERRCODE": "0000"
}
```

**Actual Java Output:**

```json
{
  "case_id": "CARDSTAT_ACTIVE_001",
  "module": "CARDSTAT",
  "RC": "0",
  "ERRCODE": "0000",
  "AUTHSTAT": "",
  "TXFEE": "",
  "TXAMT": "",
  "TXLIMIT": "",
  "TXCUST": "",
  "TXSTAT": "A",
  "TXTYPE": ""
}
```

No mismatches detected.

### Test Case: `CARDSTAT_BLOCKED_001`

- Mode: `module`
- Module: `CARDSTAT`
- Description: Card status is not active and should set E002.
- Match score: `100.0%`
- Fields matched: `2/2`

**Input:**

```json
{
  "TXSTAT": "B",
  "ERRCODE": "0000"
}
```

**Expected ASM Output:**

```json
{
  "RC": "4",
  "ERRCODE": "E002"
}
```

**Actual Java Output:**

```json
{
  "case_id": "CARDSTAT_BLOCKED_001",
  "module": "CARDSTAT",
  "RC": "4",
  "ERRCODE": "E002",
  "AUTHSTAT": "",
  "TXFEE": "",
  "TXAMT": "",
  "TXLIMIT": "",
  "TXCUST": "",
  "TXSTAT": "B",
  "TXTYPE": ""
}
```

No mismatches detected.

### Test Case: `LIMITCHK_APPROVE_001`

- Mode: `module`
- Module: `LIMITCHK`
- Description: Transaction amount is within limit and should pass.
- Match score: `100.0%`
- Fields matched: `2/2`

**Input:**

```json
{
  "TXAMT": "250.00",
  "TXLIMIT": "500.00",
  "ERRCODE": "0000"
}
```

**Expected ASM Output:**

```json
{
  "RC": "0",
  "ERRCODE": "0000"
}
```

**Actual Java Output:**

```json
{
  "case_id": "LIMITCHK_APPROVE_001",
  "module": "LIMITCHK",
  "RC": "0",
  "ERRCODE": "0000",
  "AUTHSTAT": "",
  "TXFEE": "",
  "TXAMT": "250.00",
  "TXLIMIT": "500.00",
  "TXCUST": "",
  "TXSTAT": "",
  "TXTYPE": ""
}
```

No mismatches detected.

### Test Case: `LIMITCHK_REJECT_001`

- Mode: `module`
- Module: `LIMITCHK`
- Description: Transaction amount exceeds limit and should set E003.
- Match score: `100.0%`
- Fields matched: `2/2`

**Input:**

```json
{
  "TXAMT": "750.00",
  "TXLIMIT": "500.00",
  "ERRCODE": "0000"
}
```

**Expected ASM Output:**

```json
{
  "RC": "4",
  "ERRCODE": "E003"
}
```

**Actual Java Output:**

```json
{
  "case_id": "LIMITCHK_REJECT_001",
  "module": "LIMITCHK",
  "RC": "4",
  "ERRCODE": "E003",
  "AUTHSTAT": "",
  "TXFEE": "",
  "TXAMT": "750.00",
  "TXLIMIT": "500.00",
  "TXCUST": "",
  "TXSTAT": "",
  "TXTYPE": ""
}
```

No mismatches detected.

### Test Case: `FRDCHK_NORMAL_001`

- Mode: `module`
- Module: `FRDCHK`
- Description: Normal transaction should pass fraud check.
- Match score: `100.0%`
- Fields matched: `2/2`

**Input:**

```json
{
  "TXAMT": "100.00",
  "TXTYPE": "PO",
  "ERRCODE": "0000"
}
```

**Expected ASM Output:**

```json
{
  "RC": "0",
  "ERRCODE": "0000"
}
```

**Actual Java Output:**

```json
{
  "case_id": "FRDCHK_NORMAL_001",
  "module": "FRDCHK",
  "RC": "0",
  "ERRCODE": "0000",
  "AUTHSTAT": "",
  "TXFEE": "",
  "TXAMT": "100.00",
  "TXLIMIT": "",
  "TXCUST": "",
  "TXSTAT": "",
  "TXTYPE": "PO"
}
```

No mismatches detected.

### Test Case: `FRDCHK_REMOTE_HIGH_001`

- Mode: `module`
- Module: `FRDCHK`
- Description: High amount remote transaction should set E004.
- Match score: `100.0%`
- Fields matched: `2/2`

**Input:**

```json
{
  "TXAMT": "600.00",
  "TXTYPE": "RE",
  "ERRCODE": "0000"
}
```

**Expected ASM Output:**

```json
{
  "RC": "4",
  "ERRCODE": "E004"
}
```

**Actual Java Output:**

```json
{
  "case_id": "FRDCHK_REMOTE_HIGH_001",
  "module": "FRDCHK",
  "RC": "4",
  "ERRCODE": "E004",
  "AUTHSTAT": "",
  "TXFEE": "",
  "TXAMT": "600.00",
  "TXLIMIT": "",
  "TXCUST": "",
  "TXSTAT": "",
  "TXTYPE": "RE"
}
```

No mismatches detected.

### Test Case: `FEECALC_BASIC_001`

- Mode: `module`
- Module: `FEECALC`
- Description: Fee calculation should populate TXFEE.
- Match score: `100.0%`
- Fields matched: `2/2`

**Input:**

```json
{
  "TXAMT": "100.00",
  "TXFEE": "0.00",
  "ERRCODE": "0000"
}
```

**Expected ASM Output:**

```json
{
  "RC": "0",
  "TXFEE": "1.50"
}
```

**Actual Java Output:**

```json
{
  "case_id": "FEECALC_BASIC_001",
  "module": "FEECALC",
  "RC": "0",
  "TXFEE": "1.50",
  "ERRCODE": "0000",
  "AUTHSTAT": "",
  "TXAMT": "100.00",
  "TXLIMIT": "",
  "TXCUST": "",
  "TXSTAT": "",
  "TXTYPE": ""
}
```

No mismatches detected.

### Test Case: `AUTHDEC_APPROVE_001`

- Mode: `module`
- Module: `AUTHDEC`
- Description: No error code should approve authorization.
- Match score: `50.0%`
- Fields matched: `1/2`

**Input:**

```json
{
  "ERRCODE": "0000",
  "AUTHSTAT": ""
}
```

**Expected ASM Output:**

```json
{
  "RC": "0",
  "AUTHSTAT": "APPRV"
}
```

**Actual Java Output:**

```json
{
  "case_id": "AUTHDEC_APPROVE_001",
  "module": "AUTHDEC",
  "RC": "0",
  "AUTHSTAT": "REJCT",
  "ERRCODE": "0000",
  "TXFEE": "",
  "TXAMT": "",
  "TXLIMIT": "",
  "TXCUST": "",
  "TXSTAT": "",
  "TXTYPE": ""
}
```

**Mismatches:**

- `AUTHSTAT` expected `APPRV` but Java produced `REJCT`

### Test Case: `AUTHDEC_REJECT_001`

- Mode: `module`
- Module: `AUTHDEC`
- Description: Any error code should reject authorization.
- Match score: `100.0%`
- Fields matched: `2/2`

**Input:**

```json
{
  "ERRCODE": "E003",
  "AUTHSTAT": ""
}
```

**Expected ASM Output:**

```json
{
  "RC": "0",
  "AUTHSTAT": "REJCT"
}
```

**Actual Java Output:**

```json
{
  "case_id": "AUTHDEC_REJECT_001",
  "module": "AUTHDEC",
  "RC": "0",
  "AUTHSTAT": "REJCT",
  "ERRCODE": "E003",
  "TXFEE": "",
  "TXAMT": "",
  "TXLIMIT": "",
  "TXCUST": "",
  "TXSTAT": "",
  "TXTYPE": ""
}
```

No mismatches detected.

### Test Case: `APP_APPROVAL_FLOW_001`

- Mode: `application`
- Module: `MAINDRV`
- Description: End-to-end approval flow through MAINDRV.
- Match score: `75.0%`
- Fields matched: `3/4`

**Input:**

```json
{
  "TXCUST": "CUST000001",
  "TXSTAT": "A",
  "TXAMT": "100.00",
  "TXLIMIT": "500.00",
  "TXTYPE": "PO",
  "ERRCODE": "0000",
  "AUTHSTAT": "",
  "TXFEE": "0.00"
}
```

**Expected ASM Output:**

```json
{
  "RC": "0",
  "ERRCODE": "0000",
  "AUTHSTAT": "APPRV",
  "TXFEE": "1.50"
}
```

**Actual Java Output:**

```json
{
  "case_id": "APP_APPROVAL_FLOW_001",
  "module": "MAINDRV",
  "RC": "0",
  "ERRCODE": "0000",
  "AUTHSTAT": "REJCT",
  "TXFEE": "1.50",
  "TXAMT": "100.00",
  "TXLIMIT": "500.00",
  "TXCUST": "CUST000001",
  "TXSTAT": "A",
  "TXTYPE": "PO"
}
```

**Mismatches:**

- `AUTHSTAT` expected `APPRV` but Java produced `REJCT`

### Test Case: `TXREAD_LOCAL_PS_001`

- Mode: `module`
- Module: `TXREAD`
- Description: TXREAD reads the first local PS/QSAM-style transaction record and returns RC=0 when a record is available.
- Match score: `100.0%`
- Fields matched: `7/7`

**Input:**

```json
{
  "IO_FORCE_READ": "true",
  "INRPL_PATH": "test_cases/ps/INVSAM.txt",
  "INVSAM_PATH": "test_cases/ps/INVSAM.txt",
  "CURRTX_PATH": "test_cases/ps/INVSAM.txt",
  "ERRCODE": "0000"
}
```

**Expected ASM Output:**

```json
{
  "RC": "0",
  "TXCUST": "CUST000001",
  "TXSTAT": "A",
  "TXAMT": "100.00",
  "TXLIMIT": "500.00",
  "TXTYPE": "PO",
  "TXFEE": "0.00"
}
```

**Actual Java Output:**

```json
{
  "case_id": "TXREAD_LOCAL_PS_001",
  "module": "TXREAD",
  "RC": "0",
  "TXCUST": "CUST000001",
  "TXSTAT": "A",
  "TXAMT": "100.00",
  "TXLIMIT": "500.00",
  "TXTYPE": "PO",
  "TXFEE": "0.00",
  "ERRCODE": "0000",
  "AUTHSTAT": ""
}
```

No mismatches detected.

### Test Case: `VSAMPACK_LOCAL_PS_SMOKE_001`

- Mode: `module`
- Module: `VSAMPACK`
- Description: VSAMPACK uses local fixed-width input/output files through the generated IO adapter.
- Match score: `100.0%`
- Fields matched: `1/1`

**Input:**

```json
{
  "IO_FORCE_READ": "true",
  "IO_RECORD_FIELD": "IN_RECORD",
  "IO_OUTPUT_RECORD_FIELD": "OUT_RECORD",
  "INVSAM_PATH": "test_cases/ps/VSAMIN.txt",
  "VSAMIN_PATH": "test_cases/ps/VSAMIN.txt",
  "OUTFILE_PATH": "test_cases/ps/VSAMOUT.txt",
  "OUTDD_PATH": "test_cases/ps/VSAMOUT.txt"
}
```

**Expected ASM Output:**

```json
{
  "RC": "0"
}
```

**Actual Java Output:**

```json
{
  "case_id": "VSAMPACK_LOCAL_PS_SMOKE_001",
  "module": "VSAMPACK",
  "RC": "0",
  "ERRCODE": "",
  "AUTHSTAT": "",
  "TXFEE": "",
  "TXAMT": "",
  "TXLIMIT": "",
  "TXCUST": "",
  "TXSTAT": "",
  "TXTYPE": ""
}
```

No mismatches detected.

### Test Case: `BCTCOUNT_COUNT_5_001`

- Mode: `module`
- Module: `BCTCOUNT`
- Description: BCTCOUNT should lower a backward BCT branch into a Java loop and accumulate 5+4+3+2+1.
- Match score: `100.0%`
- Fields matched: `2/2`

**Input:**

```json
{
  "COUNT": "5",
  "TOTAL": "0"
}
```

**Expected ASM Output:**

```json
{
  "RC": "0",
  "TOTAL": "15"
}
```

**Actual Java Output:**

```json
{
  "case_id": "BCTCOUNT_COUNT_5_001",
  "module": "BCTCOUNT",
  "RC": "0",
  "TOTAL": "15",
  "ERRCODE": "",
  "AUTHSTAT": "",
  "TXFEE": "",
  "TXAMT": "",
  "TXLIMIT": "",
  "TXCUST": "",
  "TXSTAT": "",
  "TXTYPE": ""
}
```

No mismatches detected.

### Test Case: `BCTCOUNT_COUNT_3_001`

- Mode: `module`
- Module: `BCTCOUNT`
- Description: BCTCOUNT should lower a backward BCT branch into a Java loop and accumulate 3+2+1.
- Match score: `100.0%`
- Fields matched: `2/2`

**Input:**

```json
{
  "COUNT": "3",
  "TOTAL": "0"
}
```

**Expected ASM Output:**

```json
{
  "RC": "0",
  "TOTAL": "6"
}
```

**Actual Java Output:**

```json
{
  "case_id": "BCTCOUNT_COUNT_3_001",
  "module": "BCTCOUNT",
  "RC": "0",
  "TOTAL": "6",
  "ERRCODE": "",
  "AUTHSTAT": "",
  "TXFEE": "",
  "TXAMT": "",
  "TXLIMIT": "",
  "TXCUST": "",
  "TXSTAT": "",
  "TXTYPE": ""
}
```

No mismatches detected.

### Test Case: `MAINDRV_DDNAME_FILE_FLOW_001`

- Mode: `application`
- Module: `MAINDRV`
- Description: Run discovered file-aware driver orchestration using DDNAME-based input/output text files.
- Match score: `100.0%`
- Fields matched: `1/1`

**Input:**

```json
{
  "IO_FORCE_READ": "true",
  "INRPL_PATH": "test_cases/ps/INVSAM.txt",
  "INVSAM_PATH": "test_cases/ps/INVSAM.txt",
  "CURRTX_PATH": "test_cases/ps/INVSAM.txt",
  "OUTRPL_PATH": "test_cases/ps/OUTVSAM.txt",
  "OUTACB_PATH": "test_cases/ps/OUTVSAM.txt",
  "LOGBUFF_PATH": "test_cases/ps/OUTVSAM.txt",
  "ERRCODE": "0000"
}
```

**Expected ASM Output:**

```json
{
  "RC": "0"
}
```

**Actual Java Output:**

```json
{
  "case_id": "MAINDRV_DDNAME_FILE_FLOW_001",
  "module": "MAINDRV",
  "RC": "0",
  "ERRCODE": "E004",
  "AUTHSTAT": "REJCT",
  "TXFEE": "0.00",
  "TXAMT": "600.00",
  "TXLIMIT": "700.00",
  "TXCUST": "CUST000004",
  "TXSTAT": "A",
  "TXTYPE": "RE"
}
```

No mismatches detected.
