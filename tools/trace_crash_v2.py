#!/usr/bin/env python3
"""
Trace crash in sub_8216A288 using actual PPC recompiled code.
Crash: EXC_BAD_ACCESS at address 0x400000000
Instruction: str w8, [x19, x9] at sub_8216A288+744

Correct PCR layout from guest_thread.h:
- PCR size: 0xAB0 (2736 bytes)
- Offset 0x10C (268): current_cpu field
"""

print("=== CORRECT PCR Layout (from guest_thread.h) ===")
print(f"X360_PCR_SIZE   = 0xAB0 ({0xAB0} bytes)")
print(f"X360_TLS_OFFSET = 0xAB0 (starts after PCR)")
print(f"X360_TEB_OFFSET = 0xBB0 (PCR + TLS)")
print()

# PCR structure fields
pcr_fields = {
    0x00: ('tls_ptr', 'be<uint32_t>'),
    0x30: ('pcr_ptr', 'be<uint32_t>'),
    0x70: ('stack_base', 'be<uint32_t>'),
    0x74: ('stack_limit', 'be<uint32_t>'),
    0x100: ('current_thread', 'be<uint32_t>'),
    0x10C: ('current_cpu', 'uint8_t'),
    0x150: ('dpc_active', 'be<uint32_t>'),
}

offset = 268  # 0x10C
print(f"Offset 268 (0x{offset:X}):")
if offset in pcr_fields:
    field_name, field_type = pcr_fields[offset]
    print(f"  Field: {field_name} ({field_type})")
    print(f"  This is INSIDE PCR (PCR ends at 0xAB0 = {0xAB0})")
else:
    print(f"  Not a named field, but within PCR region")
print()

print("=== Tracing sub_8216A288 from PPC code ===")
print()
print("Key lines from ppc_recomp.3.cpp:")
print()
print("Line 36211: // lbz r26,268(r13)")
print("           ctx.r26.u64 = PPC_LOAD_U8(ctx.r13.u32 + 268);")
print("           -> Loads current_cpu byte from PCR+0x10C")
print()
print("Line 36309-36314: Computing r8 as array index")
print("           // addi r11,r26,36")
print("           ctx.r11.s64 = ctx.r26.s64 + 36;")
print("           // rlwinm r8,r11,2,0,29")
print("           ctx.r8.u64 = rotl(r11, 2) & 0xFFFFFFFC  // = (r26 + 36) * 4")
print()
print("Line 36331-36332: The crashing store")
print("           // stwx r30,r8,r27")
print("           PPC_STORE_U32(ctx.r8.u32 + ctx.r27.u32, ctx.r30.u32);")
print("           -> Stores to address: a1 + (current_cpu + 36) * 4")
print()

# Register values from LLDB crash
print("=== LLDB Register Values at Crash ===")
regs = {
    'x8': 0xFFFFFFFF,
    'x9': 0xFFFFFFFF,  # = r8 + r27 (guest address offset)
    'x19': 0x300000000,  # base pointer
    'x27': 0x7CE00000,  # This might be r27 (a1 parameter)
}

print(f"x9 (computed guest addr) = 0x{regs['x9']:08X}")
print(f"x27 (possibly r27/a1)    = 0x{regs['x27']:08X}")
print()

# The crash: x9 = 0xFFFFFFFF
# This is r8 + r27 in PPC terms
# r8 = (r26 + 36) * 4
# r27 = a1 (first parameter to sub_8216A288)

print("=== Working backwards from crash ===")
print()

# If x9 = r8 + r27 = 0xFFFFFFFF, what values could produce this?
x9 = 0xFFFFFFFF

# Test: if r27 is around 0x7CE00000 (from x27)
r27_guess = 0x7CE00000
r8_computed = (x9 - r27_guess) & 0xFFFFFFFF
print(f"If r27 = 0x{r27_guess:08X}:")
print(f"   r8 = 0x{x9:08X} - 0x{r27_guess:08X} = 0x{r8_computed:08X}")

# r8 = (r26 + 36) * 4, so r26 = (r8 / 4) - 36
if r8_computed % 4 == 0:
    r11 = r8_computed // 4
    r26 = (r11 - 36) & 0xFFFFFFFF
    print(f"   r11 = r8 / 4 = 0x{r11:08X}")
    print(f"   r26 = r11 - 36 = 0x{r26:08X}")
    print(f"   r26 as byte = 0x{r26 & 0xFF:02X}")
else:
    print(f"   r8 not aligned to 4, math doesn't work cleanly")
print()

# But wait - r26 is loaded as a BYTE (lbz instruction)
# So r26 should be 0-255. If current_cpu is not initialized properly,
# it could be 0 or garbage.

print("=== Key Insight ===")
print()
print("The code computes: addr = a1 + (current_cpu + 36) * 4")
print()
print("For valid worker threads, current_cpu should be 0-5.")
print("Expected addr range: a1 + (0+36)*4 = a1 + 144")
print("                 to: a1 + (5+36)*4 = a1 + 164")
print()
print("If current_cpu = 0xFF (uninitialized/garbage):")
print("   addr = a1 + (255 + 36) * 4 = a1 + 1164")
print()
print("If current_cpu = 0x00 but a1 is garbage:")
print("   The problem is a1 (r27), not current_cpu")
print()

# Let's examine what happens with a1 = 0
print("=== Testing with a1 = 0 ===")
r27_zero = 0
for cpu in [0, 1, 2, 3, 4, 5, 0xFF]:
    r11 = cpu + 36
    r8 = (r11 << 2) & 0xFFFFFFFC
    addr = (r27_zero + r8) & 0xFFFFFFFF
    print(f"  current_cpu={cpu}: r8=0x{r8:08X}, addr=0x{addr:08X}")
print()

# What r27 value would make addr = 0xFFFFFFFF?
print("=== What a1 value causes addr = 0xFFFFFFFF? ===")
target = 0xFFFFFFFF
for cpu in [0, 1, 2, 3, 4, 5]:
    r11 = cpu + 36
    r8 = (r11 << 2) & 0xFFFFFFFC
    r27_needed = (target - r8) & 0xFFFFFFFF
    print(f"  current_cpu={cpu}: r8=0x{r8:08X}, a1 would need to be 0x{r27_needed:08X}")
print()

print("=== CRITICAL: Check if a1 (r27) is valid ===")
print()
print("From backtrace:")
print("  sub_8216A288 called from sub_82169C58")
print("  sub_82169C58 calls: sub_8216A288(a1, a1 + 80)")
print("  where a1 = dword_83137CA8 (a global pointer)")
print()
print("If dword_83137CA8 is not properly initialized or is NULL/garbage,")
print("then a1 passed to sub_8216A288 will be invalid.")
print()

# Let's compute: if x9 = 0xFFFFFFFF and current_cpu = 0
# Then r8 = (0 + 36) * 4 = 144 = 0x90
# So r27 = 0xFFFFFFFF - 0x90 = 0xFFFFFF6F
# This is a huge address, suggesting a1 is garbage

r8_with_cpu0 = (0 + 36) * 4
r27_if_cpu0 = (0xFFFFFFFF - r8_with_cpu0) & 0xFFFFFFFF
print(f"If current_cpu = 0:")
print(f"   r8 = {r8_with_cpu0} (0x{r8_with_cpu0:X})")
print(f"   r27 (a1) = 0xFFFFFFFF - 0x{r8_with_cpu0:X} = 0x{r27_if_cpu0:08X}")
print()
print("0xFFFFFF6F is NOT a valid guest address!")
print("This strongly suggests a1 (the first parameter) is garbage/NULL.")
print()

print("=== HYPOTHESIS ===")
print()
print("The crash is NOT caused by current_cpu being wrong.")
print("The crash is caused by the first parameter (a1) to sub_8216A288")
print("being an invalid/garbage pointer.")
print()
print("a1 comes from dword_83137CA8 which is a global pointer")
print("that should point to some audio/streaming manager object.")
print()
print("If this pointer is NULL (0x00000000) or uninitialized,")
print("then addr = 0 + 144 = 144 (0x90), which would crash differently.")
print()
print("If the pointer is 0xFFFFFF6F or similar garbage,")
print("then addr = 0xFFFFFF6F + 144 = 0xFFFFFFFF (wraparound), matching our crash!")
print()

# Actually, let me reconsider. The ARM x9 contains the final offset
# and x19 is the base. The crash is at 0x400000000 = x19 + x9
# x19 = 0x300000000 (this is the PPC memory base)
# x9 = 0xFFFFFFFF (this is the 32-bit guest address)

print("=== Re-examining ARM registers ===")
print()
print("ARM instruction: str w8, [x19, x9]")
print("  x19 = 0x300000000 (PPC memory base)")
print("  x9  = 0xFFFFFFFF (32-bit guest offset)")
print("  Access: 0x300000000 + 0xFFFFFFFF = 0x3FFFFFFFF")
print()
print("The guest code computed address 0xFFFFFFFF")
print("This is r8 + r27 in PPC terms")
print()
print("If r27 (a1 parameter) = 0xFFFFFF6F and r8 = 0x90:")
print("  0xFFFFFF6F + 0x90 = 0x100000000 - 1 = 0xFFFFFFFF (32-bit wrap)")
print()
print("CONCLUSION: The first parameter to sub_8216A288 is garbage.")
print("This is passed from sub_82169C58 which gets it from dword_83137CA8.")
