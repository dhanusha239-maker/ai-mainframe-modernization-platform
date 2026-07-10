# Known HLASM Source Issue

## AUTHDEC approval path

AUTHDEC currently produces REJCT even when ERRCODE is 0000.

This affects:
- AUTHDEC_APPROVE_001
- APP_APPROVAL_FLOW_001

This is treated as an HLASM source behavior issue, not a Java generator defect.
