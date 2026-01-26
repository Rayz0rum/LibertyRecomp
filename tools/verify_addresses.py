#!/usr/bin/env python3
"""
Verify address calculations from audio callback analysis.
Cross-references PPC recomp code calculations with expected addresses.
"""

import struct

def signed_to_unsigned_32(val):
    """Convert signed 32-bit to unsigned 32-bit"""
    if val < 0:
        return val + 0x100000000
    return val

def verify_calculation(description, signed_base, offset, expected_hex):
    """Verify a calculation and print result"""
    result_signed = signed_base + offset
    result_unsigned = signed_to_unsigned_32(result_signed)
    expected = int(expected_hex, 16)
    
    match = "✅ MATCH" if result_unsigned == expected else "❌ MISMATCH"
    
    print(f"\n{description}")
    print(f"  Calculation: {signed_base} + {offset}")
    print(f"  Signed result: {result_signed}")
    print(f"  Unsigned (hex): 0x{result_unsigned:08X}")
    print(f"  Expected: {expected_hex} (0x{expected:08X})")
    print(f"  Status: {match}")
    
    return result_unsigned == expected

def main():
    print("=" * 60)
    print("ADDRESS CALCULATION VERIFICATION")
    print("=" * 60)
    
    all_pass = True
    
    # From ppc_recomp.3.cpp sub_82169578 - callback address calculation
    # Lines 34853-34856:
    # ctx.r10.s64 = -2112421888;  // lis r10,-32233
    # ctx.r4.s64 = ctx.r10.s64 + 11240;  // addi r4,r10,11240
    all_pass &= verify_calculation(
        "1. Audio callback address (sub_82172BE8)",
        -2112421888,  # lis r10,-32233 -> 0x82170000 as signed
        11240,        # addi offset
        "0x82172BE8"
    )
    
    # Verify the lis instruction value
    print(f"\n  Verifying lis r10,-32233:")
    print(f"    -32233 << 16 = {-32233 * 65536} = 0x{(-32233 * 65536) & 0xFFFFFFFF:08X}")
    print(f"    As signed 32-bit: {-32233 * 65536}")
    
    # From ppc_recomp.3.cpp sub_82169400 - audio event address
    # Lines 34093-34096:
    # ctx.r11.s64 = -2095906816;  // lis r11,-31981
    # ctx.r29.s64 = ctx.r11.s64 + 31616;  // addi r29,r11,31616
    all_pass &= verify_calculation(
        "2. Audio event address (byte_83137B80)",
        -2095906816,  # lis r11,-31981 -> 0x83130000 as signed
        31616,        # addi offset (31616 = 0x7B80)
        "0x83137B80"
    )
    
    # From ppc_recomp.3.cpp sub_82169400 - semaphore address
    # Lines 34090-34092:
    # ctx.r11.s64 = -2095906816;  // lis r11,-31981
    # ctx.r27.s64 = ctx.r11.s64 + 31596;  // addi r27,r11,31596
    all_pass &= verify_calculation(
        "3. Semaphore address (unk_83137B6C)",
        -2095906816,  # lis r11,-31981
        31596,        # addi offset (31596 = 0x7B6C)
        "0x83137B6C"
    )
    
    # From ppc_recomp.3.cpp sub_82169B00 - audio context pointer
    # Lines 35086-35093:
    # ctx.r11.s64 = -2095906816;  // lis r11,-31981
    # ctx.r30.u64 = PPC_LOAD_U32(ctx.r11.u32 + 31912);  // lwz r30,31912(r11)
    all_pass &= verify_calculation(
        "4. Audio context pointer address (dword_83137CA8)",
        -2095906816,  # lis r11,-31981
        31912,        # lwz offset (31912 = 0x7CA8)
        "0x83137CA8"
    )
    
    # From ppc_recomp.3.cpp sub_82169400 - second event address
    # Lines 34086-34088:
    # ctx.r11.s64 = -2095906816;  // lis r11,-31981
    # ctx.r28.s64 = ctx.r11.s64 + 31580;  // addi r28,r11,31580
    all_pass &= verify_calculation(
        "5. Second event address (byte_83137B5C)",
        -2095906816,  # lis r11,-31981
        31580,        # addi offset (31580 = 0x7B5C)
        "0x83137B5C"
    )
    
    # Verify lis instruction for -31981
    print(f"\n  Verifying lis r11,-31981:")
    print(f"    -31981 << 16 = {-31981 * 65536} = 0x{(-31981 * 65536) & 0xFFFFFFFF:08X}")
    
    # From ppc_recomp.3.cpp sub_82169578 - worker thread entry points
    # Lines 34647-34650:
    # ctx.r11.s64 = -2112421888;  // lis r11,-32233
    # ctx.r7.s64 = ctx.r11.s64 + -27648;  // addi r7,r11,-27648 (sub_82169400)
    all_pass &= verify_calculation(
        "6. Worker thread entry point (sub_82169400)",
        -2112421888,  # lis r11,-32233
        -27648,       # addi offset (-27648 = -0x6C00)
        "0x82169400"
    )
    
    # Lines 34643-34644:
    # ctx.r10.s64 = -2112421888;  // lis r10,-32233
    # ctx.r7.s64 = ctx.r10.s64 + -27448;  // addi r7,r10,-27448 (sub_821694C8)
    all_pass &= verify_calculation(
        "7. Alternative worker entry point (sub_821694C8)",
        -2112421888,  # lis r10,-32233
        -27448,       # addi offset
        "0x821694C8"
    )
    
    print("\n" + "=" * 60)
    if all_pass:
        print("ALL CALCULATIONS VERIFIED ✅")
    else:
        print("SOME CALCULATIONS FAILED ❌")
    print("=" * 60)
    
    # Additional verification: Check function mapping gap
    print("\n" + "=" * 60)
    print("FUNCTION MAPPING GAP ANALYSIS")
    print("=" * 60)
    
    # From ppc_func_mapping.cpp
    mapping_entries = [
        0x82172B20,
        0x82172B88,
        0x82172BF8,  # Next entry after B88
        0x82172C70,
    ]
    
    print("\nFunction mapping entries around 0x82172BE8:")
    for addr in mapping_entries:
        marker = " <-- MISSING 0x82172BE8 HERE!" if addr == 0x82172BF8 else ""
        print(f"  0x{addr:08X}{marker}")
    
    print(f"\n  Gap: 0x82172B88 to 0x82172BF8 = {0x82172BF8 - 0x82172B88} bytes")
    print(f"  Missing: 0x82172BE8 (callback function)")
    print(f"  0x82172BE8 - 0x82172B88 = {0x82172BE8 - 0x82172B88} bytes from previous")
    print(f"  0x82172BF8 - 0x82172BE8 = {0x82172BF8 - 0x82172BE8} bytes to next")

if __name__ == "__main__":
    main()
