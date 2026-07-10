# Local PS/QSAM/VSAM Test File Setup

Place these files in your project exactly as shown:

```text
test_cases/
  ps/
    txread_input.ps
    vsampack_input.ps
    vsampack_output.ps
```

## txread_input.ps layout

Each record is 53 characters:

```text
TXCARD   0-15   16 chars
TXCUST   16-25  10 chars
TXAMT    26-33   8 chars, cents
TXTYPE   34-35   2 chars
TXSTAT   36-36   1 char
TXLIMIT  37-44   8 chars, cents
TXFEE    45-52   8 chars, cents
```

Example:

```text
CARD000000000001CUST00000100010000POA0005000000000000
```

This means:

```text
TXCUST  = CUST000001
TXAMT   = 100.00
TXTYPE  = PO
TXSTAT  = A
TXLIMIT = 500.00
TXFEE   = 0.00
```

## vsampack_input.ps layout

Each record is 100 characters. It is a local fixed-width simulation file for VSAMPACK scanning logic.

## Test case additions

Append the objects in `behavior_test_cases_local_io_additions.json` to:

```text
test_cases/behavior_test_cases.json
```

Do not replace your existing tests. Add them at the end of the JSON array.

## Runtime behavior

The generated `AsmRuntime.IO.get()` supports two modes:

1. Normal behavior-comparator CSV mode:
   - Existing context fields such as TXCUST/TXAMT/TXLIMIT are already loaded.
   - TXREAD does not overwrite them.

2. Local file-read mode:
   - Set `IO_FORCE_READ` to `"true"` in the test case input.
   - Provide `INRPL_PATH`, `INVSAM_PATH`, or `CURRTX_PATH`.
   - TXREAD reads from `test_cases/ps/txread_input.ps`.
