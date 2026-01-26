#!/usr/bin/env python3
"""
Analyze the speechbanks address calculation in sub_828A58C8.
This script simulates the PPC code to understand how 0xFFFF020E is produced.
"""
import struct

print("=" * 70)
print("SPEECHBANKS ADDRESS CALCULATION ANALYSIS")
print("=" * 70)

# Known values from the crash
CRASH_ADDRESS = 0xFFFF020E
URL_SIZE = 65010

# Verify the relationship
crash_signed = struct.unpack('>i', struct.pack('>I', CRASH_ADDRESS))[0]
print(f"\nCrash address: 0x{CRASH_ADDRESS:08X}")
print(f"As signed int32: {crash_signed}")
print(f"URL size: {URL_SIZE}")
print(f"Relationship: {crash_signed} == -{URL_SIZE}? {crash_signed == -URL_SIZE}")

print("\n" + "=" * 70)
print("CAUSE 1: BUFFER DATA NOT READ CORRECTLY")
print("=" * 70)

def simulate_with_buffer_values(r27, r22, r23, r10, r26, description):
    """Simulate the address calculation with given buffer values."""
    print(f"\n--- {description} ---")
    print(f"r27 (buffer ptr) = 0x{r27:016X}")
    print(f"r22 (file size)  = 0x{r22:016X} ({r22})")
    print(f"r23 (from buf+0) = 0x{r23:016X}")
    print(f"r10 (from buf+offset) = 0x{r10:016X}")
    print(f"r26 (from buf+offset) = 0x{r26:016X}")
    
    # Line 10454-10455: addi r25,r27,4
    r25 = (r27 + 4) & 0xFFFFFFFFFFFFFFFF
    print(f"\nr25 = r27 + 4 = 0x{r25:016X}")
    
    # Line 10462-10463: add r11,r25,r23
    r11 = (r25 + r23) & 0xFFFFFFFFFFFFFFFF
    print(f"r11 = r25 + r23 = 0x{r11:016X}")
    
    # Line 10468-10469: addi r20,r11,4
    r20 = (r11 + 4) & 0xFFFFFFFFFFFFFFFF
    print(f"r20 = r11 + 4 = 0x{r20:016X}")
    
    # Line 10470-10471: mulli r11,r10,14 (SIGNED)
    r10_signed = struct.unpack('>q', struct.pack('>Q', r10))[0]
    r11_mulli = (r10_signed * 14) & 0xFFFFFFFFFFFFFFFF
    print(f"r11 = r10 * 14 (signed) = 0x{r11_mulli:016X}")
    
    # Line 10472-10473: add r11,r11,r20
    r11 = (r11_mulli + r20) & 0xFFFFFFFFFFFFFFFF
    print(f"r11 = r11 + r20 = 0x{r11:016X}")
    
    # Line 10476-10477: addi r21,r11,4
    r21 = (r11 + 4) & 0xFFFFFFFFFFFFFFFF
    print(f"r21 = r11 + 4 = 0x{r21:016X}")
    
    # Line 10480-10481: rlwinm r11,r26,2,0,29 (r26 << 2, masked)
    r26_u32 = r26 & 0xFFFFFFFF
    r11_rlwinm = (r26_u32 << 2) & 0xFFFFFFFC
    print(f"r11 = rlwinm(r26, 2) = 0x{r11_rlwinm:016X}")
    
    # Line 10482-10483: add r11,r26,r11
    r11 = (r26 + r11_rlwinm) & 0xFFFFFFFFFFFFFFFF
    print(f"r11 = r26 + r11 = 0x{r11:016X}  (r26 * 5)")
    
    # Line 10484-10485: rlwinm r11,r11,1,0,30 (r11 << 1, masked)
    r11_u32 = r11 & 0xFFFFFFFF
    r11 = (r11_u32 << 1) & 0xFFFFFFFE
    print(f"r11 = rlwinm(r11, 1) = 0x{r11:016X}  (r26 * 10)")
    
    # Line 10486-10487: add r5,r11,r21
    r5 = (r11 + r21) & 0xFFFFFFFFFFFFFFFF
    print(f"r5 = r11 + r21 = 0x{r5:016X}")
    
    r5_u32 = r5 & 0xFFFFFFFF
    print(f"\nFINAL r5 (lower 32): 0x{r5_u32:08X}")
    
    if r5_u32 == CRASH_ADDRESS:
        print("*** MATCHES CRASH ADDRESS! ***")
    
    return r5_u32

# Scenario 1: Buffer contains zeros (not read)
simulate_with_buffer_values(
    r27=0x00000000B9528380,  # Valid buffer pointer
    r22=0x00000000_00084EB0,  # Valid file size (~544KB)
    r23=0,  # Zero - buffer not read
    r10=0,  # Zero
    r26=0,  # Zero
    description="Scenario 1: Buffer not read (all zeros)"
)

# Scenario 2: Buffer read correctly with typical values
simulate_with_buffer_values(
    r27=0x00000000B9528380,
    r22=0x00000000_00084EB0,
    r23=0x00010000,  # Header offset ~64KB
    r10=0x00000021,  # Count = 33
    r26=0x00000021,  # Count = 33
    description="Scenario 2: Buffer read correctly (typical values)"
)

print("\n" + "=" * 70)
print("CAUSE 2: SIGNED/UNSIGNED MIXING")
print("=" * 70)

print("""
The PPC code mixes .s64 and .u64 operations.
Let's check if large values cause sign issues.
""")

def check_signed_unsigned_mixing():
    # If r27 is interpreted as signed negative...
    r27_unsigned = 0x00000000B9528380
    
    # The .s64 view of the same bits
    r27_signed = struct.unpack('>q', struct.pack('>Q', r27_unsigned))[0]
    
    print(f"r27.u64 = 0x{r27_unsigned:016X}")
    print(f"r27.s64 = {r27_signed} (same bits, signed interpretation)")
    
    # addi r25,r27,4 uses .s64
    r25_s64 = r27_signed + 4
    print(f"\nr25.s64 = r27.s64 + 4 = {r25_s64}")
    print(f"r25 as hex = 0x{r25_s64 & 0xFFFFFFFFFFFFFFFF:016X}")
    
    # This is still positive because 0xB9528380 < 0x8000000000000000
    # So signed interpretation is still positive in 64-bit
    
    print("\nConclusion: 64-bit signed values with upper bits = 0 are positive.")
    print("Signed/unsigned mixing is NOT the cause if upper 32 bits are clean.")

check_signed_unsigned_mixing()

print("\n" + "=" * 70)
print("CAUSE 3: ENDIANNESS ISSUE")
print("=" * 70)

print("""
Xbox 360 uses big-endian, PC uses little-endian.
PPC_LOAD_U32 should byte-swap. Let's check what happens if it doesn't.
""")

def check_endianness(value_be, description):
    """Check what happens with different endianness interpretations."""
    print(f"\n{description}")
    print(f"Value in memory (BE): 0x{value_be:08X}")
    
    # Byte swap: BE to LE
    bytes_be = struct.pack('>I', value_be)
    value_le = struct.unpack('<I', bytes_be)[0]
    print(f"After byte-swap (LE): 0x{value_le:08X}")
    
    # What if NO swap happened?
    print(f"If NO swap (wrong): 0x{value_be:08X}")
    
    return value_le, value_be

# Example: If the header offset in speech.dat is 0x00010000 (BE)
check_endianness(0x00010000, "Header offset 0x00010000")
check_endianness(0x00000021, "Count value 33 (0x21)")

# What if a negative size is stored?
check_endianness(0xFFFF020E, "Negative size -65010")

print("\n" + "=" * 70)
print("HYPOTHESIS: SIZE CONFUSED WITH ADDRESS")
print("=" * 70)

print("""
The memory URL contains:
  - Address: 0xFFFF020E (= -65010 signed)
  - Size: 65010

What if the calculation is using (buffer_end - total_size) but
getting the SIGN wrong?
""")

r27 = 0xB9528380  # buffer base
r22 = 0x84EB0     # file size (~544KB)
buffer_end = r27 + r22

print(f"buffer_base = 0x{r27:08X}")
print(f"file_size   = 0x{r22:08X} ({r22})")
print(f"buffer_end  = 0x{buffer_end:08X}")

# If speechbanks is 65010 bytes from the end
speechbanks_size = 65010
expected_addr = buffer_end - speechbanks_size
print(f"\nIf speechbanks is at (buffer_end - {speechbanks_size}):")
print(f"  Expected: 0x{expected_addr:08X}")

# What if the subtraction is done wrong?
# If we compute: size - buffer_end (wrong order)
wrong_calc = speechbanks_size - buffer_end
print(f"\nIf wrong: {speechbanks_size} - 0x{buffer_end:08X} = {wrong_calc}")
print(f"  As unsigned: 0x{wrong_calc & 0xFFFFFFFF:08X}")

# What about -size?
neg_size = -speechbanks_size
print(f"\n-{speechbanks_size} = {neg_size}")
print(f"  As unsigned 32-bit: 0x{neg_size & 0xFFFFFFFF:08X}")

print("\n" + "=" * 70)
print("CONCLUSION")
print("=" * 70)
print("""
The value 0xFFFF020E = -65010 in signed 32-bit.
65010 is the SIZE in the URL.

Most likely scenarios:
1. The calculation computes (0 - size) due to uninitialized pointers
2. A subtraction operand order is reversed
3. The size value is being used where an offset should be

To confirm, we need to capture ACTUAL runtime values of:
  - r27 (buffer pointer)
  - r23, r10, r26 (values loaded from buffer)
  - r21 (intermediate pointer)
""")
