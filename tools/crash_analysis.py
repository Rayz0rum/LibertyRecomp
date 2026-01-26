#!/usr/bin/env python3
"""
Crash Analysis for sub_822EF570 segfault
"""

print("=" * 70)
print("CRASH ANALYSIS: sub_822EF570 + 552")
print("=" * 70)

# From LLDB register read
x19 = 0x0000000300000000  # PPC memory base
x8 = 0x00000000ffffffff   # Offset (0xFFFFFFFF = -1 unsigned, or garbage)
x20 = 0x000000016fdfd140  # PPCContext pointer
x27 = 0x0000000383137bb4  # Some PPC address

# Calculate crash address
crash_calc = x19 + x8
print(f"\nCrash calculation:")
print(f"  x19 (base)   = 0x{x19:016X}")
print(f"  x8 (offset)  = 0x{x8:016X} (= {x8} = 0xFFFFFFFF)")
print(f"  x19 + x8     = 0x{crash_calc:016X}")
print(f"  Actual crash = 0x400000000")

# The instruction is: ldr w8, [x19, x8]
# This loads a 32-bit word from address x19 + x8
# x8 = 0xFFFFFFFF means the offset is garbage/uninitialized

print("\n" + "=" * 70)
print("KEY INSIGHT: x8 = 0xFFFFFFFF is an invalid offset")
print("=" * 70)
print("""
x8 = 0xFFFFFFFF (4294967295) is likely:
  1. An uninitialized value (-1 as signed)
  2. A NULL pointer + some offset calculation gone wrong
  3. Result of reading from uninitialized memory
""")

# From the call stack:
print("\n" + "=" * 70)
print("CALL STACK ANALYSIS")
print("=" * 70)
call_stack = [
    ("sub_822EF570", "CRASH - loading from garbage offset"),
    ("sub_822EF850", "Caller - passes data to sub_822EF570"),
    ("sub_821221A8", "Main game loop iteration"),
    ("sub_82121E80", "Game state update"),
    ("sub_821200D0", "Main entry/update"),
    ("sub_8218BEB0", "Boot sequence"),
    ("sub_827D89B8", "Thread entry wrapper"),
    ("sub_8218BEA8", "Main entry point"),
    ("_xstart", "Guest code start"),
]
for func, desc in call_stack:
    print(f"  {func}: {desc}")

# The log shows this was called after runaway loop warning
print("\n" + "=" * 70)
print("CONTEXT FROM LOG")
print("=" * 70)
print("""
Last log entries before crash:
  [sub_827827C8] WARNING: Possible runaway loop from caller 0x822EF614 (1001 calls)
  [sub_8218BE28] [ALLOC] sub_8218BE28 #4000 46464 bytes -> 0xD75A00B0

The runaway loop at 0x822EF614 is INSIDE sub_822EF570!
This loop calls sub_827827C8 over 1000 times.
""")

# Address calculations for the loop
print("\n" + "=" * 70)
print("LOOP ANALYSIS: 0x822EF614 inside sub_822EF570")
print("=" * 70)

# From ppc_recomp.24.cpp lines 4350-4380:
# The loop at loc_822EF604 calls sub_827827C8 with ctx.lr = 0x822EF614
# Counter r29 comes from: rlwinm r29,r10,29,3,31 which extracts bits
# r10 is loaded from *(r11 + 192) 

print("""
PPC code at loc_822EF604:
  r29 = (r10 >> 3) & 0x1FFFFFFF   ; Extract count from r10
  
Loop:
  li r4, 16
  mr r3, r28
  addi r29, r29, -1               ; Decrement counter
  bl sub_827827C8                 ; lr = 0x822EF614
  lwz r11, 0(r30)                 ; Load from r30
  stw r11, 0(r3)                  ; Store to result
  lwz r11, 4(r30)
  addi r30, r30, 8                ; Advance pointer
  stw r11, 4(r3)
  bne r29, loop                   ; Loop while r29 != 0

The loop ran 1001+ times, meaning r29 started at ~1001+
""")

# The crash happens AFTER the allocation
print("\n" + "=" * 70)
print("ROOT CAUSE HYPOTHESIS")
print("=" * 70)
print("""
The crash happens when accessing data after the loop.
x8 = 0xFFFFFFFF suggests:
  1. Reading from a NULL or garbage pointer
  2. An array access with invalid index
  3. Structure field at offset that doesn't exist

Looking at the PPC code after loc_822EF630:
  lhz r10, 44(r31)      ; Load halfword from r31+44
  ...
  lwz r10, 40(r31)      ; Load word from r31+40
  
If r31 points to garbage, the loads will get garbage values.
""")

# Key register analysis
print("\n" + "=" * 70)
print("REGISTER TO PPC MAPPING")
print("=" * 70)
print("""
ARM64 register mapping in recompiled code:
  x19 = base (PPC memory base 0x300000000)
  x20 = &ctx (PPCContext pointer)
  x21 = 0x822ef578 (return address / code pointer in PPC space)
  x27 = 0x383137bb4 = base + 0x83137BB4 (a PPC address)
  
Let's check what 0x83137BB4 is...
""")

ppc_addr = 0x83137BB4
base_offset = ppc_addr - 0x82000000
print(f"  0x83137BB4 is in PPC data region")
print(f"  Offset from 0x82000000 = 0x{base_offset:08X} ({base_offset} bytes)")

# This is near dword_83137CA8 which is the audio manager!
print(f"\n  dword_83137CA8 = 0x83137CA8")
print(f"  Difference: 0x{0x83137CA8 - ppc_addr:X} = {0x83137CA8 - ppc_addr} bytes after x27")
print("""
  x27 points near the audio/streaming manager structure!
  This suggests the crash is related to accessing uninitialized
  streaming/audio data structures.
""")

print("\n" + "=" * 70)
print("NEXT STEPS")
print("=" * 70)
print("""
1. Read sub_822EF570 PPC code to find the exact crash point
2. Identify what PPC register maps to x8 (the garbage offset)
3. Trace back where that register gets its value
4. Find the NULL/uninitialized pointer source
""")
