# Behavior Comparison Report

This report compares expected assembler behavior against actual generated Java execution output.

## Summary

- Total test cases: `16`
- Passed cases: `13`
- Failed cases: `3`
- Average behavior match score: `93.75%`

## Batch Validation Summary

- Batch records processed: `4`
- Batch passed: `3`
- Batch failed: `1`
- Failure customer IDs: `CUST000001`

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

### Test Case: `TX001`

- Mode: `application`
- Module: `MAINDRV`
- Description: Batch transaction validation for TX001
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
  "case_id": "TX001",
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

**Failure customer ID:** `CUST000001`

- `AUTHSTAT` expected `APPRV` but Java produced `REJCT`

### Test Case: `TX002`

- Mode: `application`
- Module: `MAINDRV`
- Description: Batch transaction validation for TX002
- Match score: `100.0%`
- Fields matched: `4/4`

**Input:**

```json
{
  "TXCUST": "CUST000002",
  "TXSTAT": "A",
  "TXAMT": "700.00",
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
  "RC": "4",
  "ERRCODE": "E003",
  "AUTHSTAT": "REJCT",
  "TXFEE": "0.00"
}
```

**Actual Java Output:**

```json
{
  "case_id": "TX002",
  "module": "MAINDRV",
  "RC": "4",
  "ERRCODE": "E003",
  "AUTHSTAT": "REJCT",
  "TXFEE": "0.00",
  "TXAMT": "700.00",
  "TXLIMIT": "500.00",
  "TXCUST": "CUST000002",
  "TXSTAT": "A",
  "TXTYPE": "PO"
}
```

No mismatches detected.

### Test Case: `TX003`

- Mode: `application`
- Module: `MAINDRV`
- Description: Batch transaction validation for TX003
- Match score: `100.0%`
- Fields matched: `4/4`

**Input:**

```json
{
  "TXCUST": "CUST000003",
  "TXSTAT": "B",
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
  "RC": "4",
  "ERRCODE": "E002",
  "AUTHSTAT": "REJCT",
  "TXFEE": "0.00"
}
```

**Actual Java Output:**

```json
{
  "case_id": "TX003",
  "module": "MAINDRV",
  "RC": "4",
  "ERRCODE": "E002",
  "AUTHSTAT": "REJCT",
  "TXFEE": "0.00",
  "TXAMT": "100.00",
  "TXLIMIT": "500.00",
  "TXCUST": "CUST000003",
  "TXSTAT": "B",
  "TXTYPE": "PO"
}
```

No mismatches detected.

### Test Case: `TX004`

- Mode: `application`
- Module: `MAINDRV`
- Description: Batch transaction validation for TX004
- Match score: `100.0%`
- Fields matched: `4/4`

**Input:**

```json
{
  "TXCUST": "CUST000004",
  "TXSTAT": "A",
  "TXAMT": "600.00",
  "TXLIMIT": "700.00",
  "TXTYPE": "RE",
  "ERRCODE": "0000",
  "AUTHSTAT": "",
  "TXFEE": "0.00"
}
```

**Expected ASM Output:**

```json
{
  "RC": "4",
  "ERRCODE": "E004",
  "AUTHSTAT": "REJCT",
  "TXFEE": "0.00"
}
```

**Actual Java Output:**

```json
{
  "case_id": "TX004",
  "module": "MAINDRV",
  "RC": "4",
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
