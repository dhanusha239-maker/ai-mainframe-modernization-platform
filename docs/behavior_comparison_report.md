# Behavior Comparison Report

This report compares expected assembler behavior against actual generated Java execution output.

## Summary

- Total test cases: `3`
- Passed cases: `3`
- Failed cases: `0`
- Average behavior match score: `100.0%`

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
  "TXCUST": "BAD000001"
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
  "TXLIMIT": "500.00"
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
