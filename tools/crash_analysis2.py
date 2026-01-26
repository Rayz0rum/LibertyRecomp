#!/usr/bin/env python3
"""
Detailed crash analysis for sub_822EF570 + 552
"""

print("=" * 70)
print("CRASH LOCATION ANALYSIS")
print("=" * 70)

# From LLDB:
# Crash at sub_822EF570 + 552
# Instruction: ldr w8, [x19, x8]
# x19 = 0x300000000 (PPC base)
# x8 = 0xFFFFFFFF (invalid offset)

# Looking at the PPC code, find where ctx.r11 or similar gets loaded with 0xFFFFFFFF

print("""
The crash happens at ARM64 instruction:
  ldr w8, [x19, x8]
  
Which corresponds to PPC:
  lwz rX, offset(rY)  where the calculated address = base + 0xFFFFFFFF
  
Looking at the code flow:

1. r27 is set to: lis r11,-32050; addi r27,r11,-9952
   = 0x82CD0000 + (-9952) = 0x82CD0000 - 0x26E0 = 0x82CCD920

2. r11 = *(r27 + 32) = *(0x82CCD920 + 32) = *(0x82CCD940)
   
3. r11 = *(r11 + 4)  -- This is a pointer chase
   
4. r10 = *(r11 + 192) -- Load count field
   
5. r29 = (r10 >> 3) & 0x1FFFFFFF  -- Extract loop count
   
6. r30 = *(r11 + 196) -- Load data array pointer

If r11 from step 2 is NULL or garbage, then step 3 would read from address 4,
which would give garbage. That garbage is then used as a pointer.
""")

# Calculate r27 value
lis_val = -32050 << 16  # lis r11,-32050
r27 = (lis_val + (-9952)) & 0xFFFFFFFF
print(f"r27 calculation:")
print(f"  lis r11, -32050 = {lis_val & 0xFFFFFFFF:08X}")
print(f"  addi r27, r11, -9952 = {r27:08X}")

# The issue: if *(r27+32) is NULL or garbage
print(f"\nKey dereference chain:")
print(f"  *(0x{r27:08X} + 32) = *(0x{r27+32:08X}) -> r11")
print(f"  *(r11 + 4) -> r11 (pointer to config struct)")
print(f"  *(r11 + 192) -> r10 (loop count)")
print(f"  *(r11 + 196) -> r30 (data array)")

# From the register dump:
# x27 = 0x0000000383137bb4 = base + 0x83137BB4
# This is DIFFERENT from the calculated 0x82CCD920!

print("\n" + "=" * 70)
print("CRITICAL FINDING: x27 value mismatch!")
print("=" * 70)

x27_from_lldb = 0x83137BB4
calculated_r27 = 0x82CCD920

print(f"""
From LLDB:    x27 = 0x{x27_from_lldb:08X}  (base + 0x83137BB4)
From PPC code: r27 = 0x{calculated_r27:08X}  (calculated from lis/addi)

The difference: 0x{x27_from_lldb - calculated_r27:08X} = {x27_from_lldb - calculated_r27} bytes

Wait - x27 is the ARM register, not necessarily mapping to r27!
ARM64 uses x19-x28 for callee-saved registers, mapped to PPC r26-r31.

ARM64 to PPC register mapping (approximate):
  x26 -> r26
  x27 -> r27
  x28 -> r28
  x29 -> r29
  x30 -> r30
  x31 -> r31
""")

# The x27 value 0x83137BB4 is interesting
print("0x83137BB4 is near:")
print(f"  dword_83137CA8 = 0x83137CA8 (audio manager pointer)")
print(f"  Distance: {0x83137CA8 - 0x83137BB4} bytes = 0xF4 = 244 bytes before")

# This suggests x27/r27 might be pointing to a structure NEAR dword_83137CA8
print("""
This is suspicious! 0x83137BB4 is 244 bytes BEFORE the audio manager pointer.
It could be pointing to:
  - A field within the audio manager structure
  - A related global variable
  - An uninitialized or corrupted pointer
""")

print("\n" + "=" * 70)
print("THE ROOT CAUSE")
print("=" * 70)

print("""
Looking at the code more carefully:

In sub_822EF570:
  r27 = 0x82CCD920 (calculated from lis/addi instructions)
  
But LLDB shows x27 = 0x83137BB4, which is in DATA section (0x83xxxxxx)

WAIT - I need to re-read the code!

At the START of sub_822EF570:
  lis r11,-32050; addi r27,r11,-9952
  
This sets r27 = 0x82CCD920 (in code/rodata section)

But the LLDB x27 = 0x383137BB4 (with base 0x300000000 added)
  = guest address 0x83137BB4

This means either:
  1. r27 was overwritten during execution
  2. The register mapping is wrong
  3. The crash is at a different instruction than we think
""")

# Let me check what -32050 actually is
print("\nDouble-checking lis calculation:")
val = -32050
print(f"  -32050 = 0x{val & 0xFFFF:04X}")
print(f"  lis r11, -32050 = (0x{val & 0xFFFF:04X} << 16) = 0x{(val & 0xFFFF) << 16:08X}")

# Python handles this as signed
import ctypes
lis_result = ctypes.c_int32((val & 0xFFFF) << 16).value
print(f"  As signed 32-bit: {lis_result:08X} (= {lis_result})")

addi_result = lis_result + (-9952)
print(f"  After addi -9952: 0x{addi_result & 0xFFFFFFFF:08X}")

print("\n" + "=" * 70)
print("ACTUAL ROOT CAUSE ANALYSIS")
print("=" * 70)
print("""
The crash is at ldr w8, [x19, x8] where x8 = 0xFFFFFFFF.

x8 holds the offset for a memory load. 0xFFFFFFFF means:
  - The PPC register that maps to calculating x8 contains garbage
  - This could be r10, r11, or r9 based on the PPC code

Looking for where x8 might get 0xFFFFFFFF:

In the loop at loc_822EF604:
  lwz r11, 0(r30)  ; Load from data array
  
If r30 points to uninitialized/garbage memory, r11 gets garbage.
That garbage is then stored somewhere and later loaded.

The most likely cause:
  r30 = *(r11 + 196)  -- gets data array pointer
  
If the structure at r11 is uninitialized, *(r11+196) could be garbage.
When the loop tries to read from this garbage pointer, we crash.

BUT the loop ran 1001+ times successfully! So the crash happens AFTER.

The crash is in the code AFTER loc_822EF630, where:
  lwz r10, 40(r31)  ; Load from r31 structure
  
Then at loc_822EF644:
  lwz r9, 0(r10)    ; Load from the array
  
If *(r31+40) points to garbage, the loop reads garbage.
""")

print("\nMost likely scenario:")
print("""
1. sub_8218BE28 allocates 46464 bytes at 0xD75A00B0
2. This memory is used for a structure/array
3. The structure at r31+40 points to this or similar allocation
4. Something goes wrong in the initialization
5. When code reads from this structure, it gets 0xFFFFFFFF
6. CRASH when trying to load from base + 0xFFFFFFFF
""")
