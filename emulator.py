import struct

def encode_packed_decimal(number, length=4):
    """Simulates IBM COMP-3 Packed Decimal generation."""
    sign = 0xC if number >= 0 else 0xD
    num_str = f"{abs(number):0{length*2-1}d}" + f"{sign:X}"
    return bytes.fromhex(num_str)

def decode_packed_decimal(packed_bytes):
    """Decodes IBM COMP-3 Packed Decimal back to an integer."""
    hex_str = packed_bytes.hex()
    digits = hex_str[:-1]
    sign_char = hex_str[-1].upper()
    val = int(digits)
    return val if sign_char in ['C', 'F', 'A'] else -val

def emulate_hlasm_pipeline(card_pan, cust_id, amount_cents, limit_cents, tx_type, card_stat):
    """Emulates Modules 1 through 9 behavior in pure Python."""
    err_code = "0000"
    auth_stat = "APPRV"
    fee_cents = 0
    
    # Module 3: CUSTVAL
    if not cust_id.startswith("CUST"):
        err_code = "E001"
        auth_stat = "REJCT"
        
    # Module 4: CARDSTAT
    if err_code == "0000" and card_stat != "A":
        err_code = "E002"
        auth_stat = "REJCT"
        
    # Module 5: LIMITCHK
    if err_code == "0000" and amount_cents > limit_cents:
        err_code = "E003"
        auth_stat = "REJCT"
        
    # Module 6: FRDCHK
    if err_code == "0000" and amount_cents > 50000 and tx_type == "RE":
        err_code = "E004"
        auth_stat = "REJCT"
        
    # Module 7: FEECALC (1.5% packed math simulation)
    if auth_stat == "APPRV":
        # Simulate MP and SRP rounding logic
        fee_cents = int(round((amount_cents * 15) / 1000))
        
    # Module 9: AUDWRITE Masking & Security Matrix Token
    masked_pan = card_pan[:4] + "XXXXXXXX" + card_pan[12:]
    
    # Replicate the HLASM XOR operation (X 4, =X'EF7A9BC1')
    # Amount packed bytes converted to a 4-byte big-endian integer
    packed_amt_bytes = encode_packed_decimal(amount_cents, length=4)
    raw_int = struct.unpack(">I", packed_amt_bytes)[0]
    xor_token = raw_int ^ 0xEF7A9BC1
    
    # Construct expected string matching the 80-byte audit log layout
    token_hex = f"{xor_token & 0xFFFFFFFF:08X}"
    expected_log = f"AUDIT|{cust_id.strip():<10}|PAN:{masked_pan}|RES:{auth_stat:<5}|MSK:{token_hex}"
    
    return auth_stat, fee_cents, err_code, expected_log[:80]

# --- QUICK TEST RUN ---
if __name__ == "__main__":
    # Test valid approval
    print(emulate_hlasm_pipeline("4111222233334444", "CUST9901A", 25000, 100000, "RE", "A"))
    # Test fraud rejection trigger
    print(emulate_hlasm_pipeline("4111222233334444", "CUST9901A", 60000, 100000, "RE", "A"))
