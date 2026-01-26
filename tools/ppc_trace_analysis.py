#!/usr/bin/env python3
"""
PPC Recompiled Code Trace Analysis
===================================
Traces execution through the ACTUAL binary code in LibertyRecompLib/ppc
All address calculations verified with Python
"""

def lis_instruction(value):
    """
    Simulate PPC 'lis' (Load Immediate Shifted) instruction
    lis rD, imm => rD = imm << 16 (sign extended)
    """
    # The value is a signed 16-bit immediate
    # It gets shifted left by 16 bits
    if value < 0:
        # Sign extend for negative values
        result = (value & 0xFFFF) << 16
        # Sign extend to 32-bit
        if result & 0x80000000:
            result = result | 0xFFFFFFFF00000000
        return result & 0xFFFFFFFF
    else:
        return (value & 0xFFFF) << 16

def calculate_address(lis_value, offset):
    """
    Calculate effective address from lis + offset (lwz/stw instructions)
    """
    base = lis_instruction(lis_value)
    # Handle signed offset
    if offset < 0:
        effective = (base + offset) & 0xFFFFFFFF
    else:
        effective = (base + offset) & 0xFFFFFFFF
    return effective

print("=" * 80)
print("PPC RECOMPILED CODE TRACE ANALYSIS")
print("=" * 80)

print("\n" + "=" * 80)
print("TRACE 1: sub_82625CA0 - Content Sync (BLOCKING POINT)")
print("=" * 80)
print("""
Source: ppc_recomp.71.cpp lines 25408-25454

PPC_FUNC_IMPL(__imp__sub_82625CA0) {
    // clrlwi r11,r3,24        => r11 = r3 & 0xFF (get low byte of arg)
    // cmplwi cr6,r11,0        => compare r11 with 0
    // lis r11,-31998          => r11 = -31998 << 16
    // lwz r3,30248(r11)       => r3 = *(r11 + 30248)  <-- LOAD SEMAPHORE HANDLE
    // beq cr6,0x82625cd8      => if arg == 0, goto non-blocking path
    // bl 0x827dacd8           => CALL sub_827DACD8 (blocking wait)
    ...
}
""")

# Calculate semaphore address from sub_82625CA0
lis_val = -31998
offset = 30248
sem_addr = calculate_address(lis_val, offset)
print(f"Address Calculation (dword_83027628):")
print(f"  lis r11, -31998:")
print(f"    -31998 decimal = 0x{(-31998) & 0xFFFF:04X} (16-bit)")
print(f"    Shifted left 16 = 0x{lis_instruction(-31998):08X}")
print(f"  lwz r3, 30248(r11):")
print(f"    offset = {offset} = 0x{offset:04X}")
print(f"  Effective address = 0x{lis_instruction(-31998):08X} + 0x{offset:04X}")
print(f"                    = 0x{sem_addr:08X}")
print(f"\n  => SEMAPHORE HANDLE stored at 0x{sem_addr:08X}")

print("\n" + "=" * 80)
print("TRACE 2: sub_82625C90 - Signal Semaphore (dword_8302762C)")
print("=" * 80)
print("""
Source: ppc_recomp.71.cpp lines 25392-25406

PPC_FUNC_IMPL(__imp__sub_82625C90) {
    // lis r11,-31998          => r11 = -31998 << 16
    // lwz r3,30252(r11)       => r3 = *(r11 + 30252)  <-- LOAD OTHER SEMAPHORE
    // b 0x827dad60            => JUMP to sub_827DAD60 (signal semaphore)
}
""")

# Calculate other semaphore address from sub_82625C90
offset2 = 30252
sem_addr2 = calculate_address(lis_val, offset2)
print(f"Address Calculation (dword_8302762C):")
print(f"  lis r11, -31998 = 0x{lis_instruction(-31998):08X}")
print(f"  lwz r3, 30252(r11):")
print(f"    offset = {offset2} = 0x{offset2:04X}")
print(f"  Effective address = 0x{lis_instruction(-31998):08X} + 0x{offset2:04X}")
print(f"                    = 0x{sem_addr2:08X}")
print(f"\n  => SECOND SEMAPHORE stored at 0x{sem_addr2:08X}")

# Verify offset difference
print(f"\n  Offset difference: {offset2} - {offset} = {offset2 - offset} bytes")
print(f"  Address difference: 0x{sem_addr2:08X} - 0x{sem_addr:08X} = {sem_addr2 - sem_addr} bytes")

print("\n" + "=" * 80)
print("TRACE 3: sub_827DACD8 - Wait on Semaphore (INFINITE)")
print("=" * 80)

# Search for sub_827DACD8 in PPC code
print("""
This function calls sub_829A2380 with timeout = -1 (infinite wait)

From ppc_recomp.88.cpp (sub_827DACD8):
    // cmplwi r3,0             => if semaphore handle == 0, return
    // beqlr                   => early return if NULL
    // li r4,-1                => r4 = -1 (INFINITE timeout)
    // b 0x829a2380            => JUMP to NtWaitForSingleObjectEx wrapper
    
The -1 timeout means INFINITE WAIT - thread blocks forever until signaled.
""")

print("\n" + "=" * 80)
print("TRACE 4: sub_82626210 - Enumerate Content Thread (STUCK LOOP)")
print("=" * 80)

# Let me trace the enumerate content thread
print("""
This is the thread that SHOULD signal dword_83027628 but never does.

Need to find this function in PPC code...
""")

print("\n" + "=" * 80)
print("TRACE 5: sub_829DDC90 - GPU Command Processor (SPINNING)")
print("=" * 80)

# Calculate timeout from GPU command processor
timeout_raw = -300000
timeout_ms = abs(timeout_raw) / 10000
print(f"""
GPU Command Processor loop timeout calculation:

From ppc_recomp.135.cpp (sub_829DDC90):
    // lis r11,-5              => r11 = -5 << 16 = 0xFFFB0000
    // ori r11,r11,27680       => r11 = r11 | 27680 = 0xFFFB6C20
    // std r11,80(r1)          => store timeout value on stack
    
Timeout value calculation:
    lis r11, -5:
      -5 << 16 = 0x{lis_instruction(-5):08X}
    ori r11, r11, 27680:
      0x{lis_instruction(-5):08X} | 0x{27680:04X} = 0x{(lis_instruction(-5) | 27680):08X}
    
    As signed 64-bit: {(lis_instruction(-5) | 27680) - 0x100000000 if (lis_instruction(-5) | 27680) > 0x7FFFFFFF else (lis_instruction(-5) | 27680)}
    
    In 100ns units: {timeout_raw}
    In milliseconds: {timeout_ms} ms
    In seconds: {timeout_ms/1000} s
""")

# Calculate the actual value
lis_minus5 = lis_instruction(-5)
ori_val = 27680
combined = lis_minus5 | ori_val
# Sign extend to get actual value
if combined & 0x80000000:
    signed_val = combined - 0x100000000
else:
    signed_val = combined
    
print(f"Verified calculation:")
print(f"  lis -5 = 0x{lis_minus5:08X}")
print(f"  ori 27680 = 0x{ori_val:04X}")
print(f"  Combined = 0x{combined:08X}")
print(f"  As signed = {signed_val}")
print(f"  Matches expected -300000? {signed_val == -300000}")

print("\n" + "=" * 80)
print("SUMMARY OF PPC CODE TRACE")
print("=" * 80)
print(f"""
BLOCKING SEMAPHORE:
  Address: 0x{sem_addr:08X} (dword_83027628)
  Loaded in: sub_82625CA0 via 'lis r11,-31998; lwz r3,30248(r11)'
  Wait function: sub_827DACD8 -> sub_829A2380 with timeout=-1 (INFINITE)

SIGNALING SEMAPHORE:
  Address: 0x{sem_addr2:08X} (dword_8302762C)  
  Loaded in: sub_82625C90 via 'lis r11,-31998; lwz r3,30252(r11)'
  Signal function: sub_827DAD60 -> sub_829A2290

GPU TIMEOUT:
  Value: {signed_val} (100ns units) = {timeout_ms}ms
  Calculated via: 'lis r11,-5; ori r11,r11,27680'
  
THE DEADLOCK:
  1. Main thread enters sub_82269140
  2. Checks byte at offset 349 of structure (lbz r11,349(r31))
  3. If non-zero, calls sub_82625CA0 with r4 (the second argument)
  4. sub_82625CA0 loads semaphore from 0x{sem_addr:08X}
  5. If arg != 0, calls sub_827DACD8 (infinite wait)
  6. Thread blocks forever waiting for semaphore signal
  
  The Enumerate Content thread (sub_82626210) should signal this,
  but it's stuck in its own loop waiting for:
  - XNotifyGetNext to return true, OR
  - Semaphore at 0x{sem_addr2:08X} to be signaled
  
  Neither happens, so dword_83027628 is never signaled.
""")

if __name__ == "__main__":
    pass
