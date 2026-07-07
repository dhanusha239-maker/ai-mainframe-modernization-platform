# Known HLASM Source Issue

## AUTHDEC approval path

Current AUTHDEC source logic causes AUTHSTAT to become REJCT even when ERRCODE is 0000.

Impact:
- AUTHDEC_APPROVE_001 fails
- APP_APPROVAL_FLOW_001 shows REJCT instead of APPRV
- MAINDRV audit output shows REJCT for all records, including valid approval records

This is treated as a source-program issue, not a Java generator defect.
