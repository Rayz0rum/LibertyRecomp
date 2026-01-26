#!/usr/bin/env python3
"""
Trace crash in sub_8216A288 using register values from LLDB session.
Crash: EXC_BAD_ACCESS at address 0x400000000
Instruction: str w8, [x19, x9] at sub_8216A288+744
"""

# Register values at crash from LLDB
regs = {
    'x0': 0x000000097b6ed0b0,
    'x1': 0x0000000300000000,
    'x8': 0x00000000ffffffff,
    'x9': 0x00000000ffffffff,
    'x10': 0x00000000ffffffff,
    'x19': 0x0000000300000000,  # base pointer
    'x20': 0x00000001753ec600,  # PPCContext pointer
    'x27': 0x000000007ce00000,
}

# The crash instruction: str w8, [x19, x9]
# Computes: base (x19) + offset (x9) = 0x300000000 + 0xFFFFFFFF
crash_addr = (regs['x19'] + regs['x9']) & 0xFFFFFFFFFFFFFFFF
print(f"Crash address calculation:")
print(f"  x19 (base)   = 0x{regs['x19']:016X}")
print(f"  x9 (offset)  = 0x{regs['x9']:016X}")
print(f"  sum          = 0x{crash_addr:016X}")
print()

# Looking at the PPC recompiled code, the crash is at line 36332:
# // stwx r30,r8,r27
# PPC_STORE_U32(ctx.r8.u32 + ctx.r27.u32, ctx.r30.u32);
#
# So x9 in ARM = ctx.r8.u32 + ctx.r27.u32 in PPC terms
# Need to figure out what r8 and r27 contain

print("=== PPC Register Analysis ===")
print()

# From the recompiled code sub_8216A288:
# Line 36212: ctx.r27.u64 = ctx.r3.u64;  // r27 = a1 (first parameter)
# Line 36218: ctx.r28.u64 = ctx.r4.u64;  // r28 = a2 (second parameter)

# r8 is computed at lines 36309-36314:
# // addi r11,r26,36
# ctx.r11.s64 = ctx.r26.s64 + 36;
# // rlwinm r8,r11,2,0,29  (rotate left and mask)
# ctx.r8.u64 = __builtin_rotateleft64(ctx.r11.u32 | (ctx.r11.u64 << 32), 2) & 0xFFFFFFFC;

# r26 is loaded at line 36211:
# // lbz r26,268(r13)
# ctx.r26.u64 = PPC_LOAD_U8(ctx.r13.u32 + 268);

print("Tracing r8 computation:")
print("  r26 = PPC_LOAD_U8(r13 + 268)  // Thread local data")
print("  r11 = r26 + 36")
print("  r8  = rotl(r11, 2) & 0xFFFFFFFC  // effectively: (r11 << 2) & 0xFFFFFFFC")
print()

# The crash has x9 = 0xFFFFFFFF
# x9 = r8 + r27
# So: r8 + r27 = 0xFFFFFFFF

# If we know r27 came from the caller (sub_82169C58), let's work backwards
# From pseudo-code: sub_8216A288(a1, a1 + 80) where a1 = dword_83137CA8

# Let's compute what r8 must be for different values of r27
print("Working backwards from crash address 0xFFFFFFFF:")
print()

# x9 = 0xFFFFFFFF as 32-bit
x9_crash = 0xFFFFFFFF

# Various possible r27 values (a1 parameter)
# dword_83137CA8 is likely in the 0x82XXXXXX or 0x83XXXXXX range
test_r27_values = [
    0x00000000,
    0x83137CA8,  # The global pointer itself (unlikely)
    0xC9000000,  # Typical allocated object address
    0xA0000000,  # Physical memory region
]

print("If r8 + r27 = 0xFFFFFFFF, then r8 = 0xFFFFFFFF - r27:")
for r27 in test_r27_values:
    r8 = (x9_crash - r27) & 0xFFFFFFFF
    print(f"  r27=0x{r27:08X} -> r8=0x{r8:08X}")
print()

# Now let's reverse the r8 computation to find r26
# r8 = (r11 << 2) & 0xFFFFFFFC where r11 = r26 + 36
# So r11 = r8 >> 2 (approximately, if r8 aligned)
# And r26 = r11 - 36

print("Reverse computing r26 from r8:")
print("  r8 = (r11 << 2) & 0xFFFFFFFC")
print("  r11 = r26 + 36")
print("  So: r26 = (r8 >> 2) - 36")
print()

for r27 in test_r27_values:
    r8 = (x9_crash - r27) & 0xFFFFFFFF
    r11 = r8 >> 2
    r26 = (r11 - 36) & 0xFFFFFFFF
    r26_byte = r26 & 0xFF  # r26 is loaded as a byte (lbz)
    print(f"  r27=0x{r27:08X}: r8=0x{r8:08X}, r11=0x{r11:08X}, r26=0x{r26:08X} (byte: 0x{r26_byte:02X})")
print()

# Key insight: r26 is loaded as a BYTE from r13+268
# So r26 should be 0x00-0xFF
# If the computed r26 is outside this range (as a sensible index), something is wrong

print("=== Analysis of PCR+268 (r13+268) ===")
print()
print("The crash reads a byte from r13+268 (thread-local storage)")
print("r13 points to the PCR (Processor Control Region)")
print()
print("From guest_thread.cpp, PCR layout:")
print("  0x00  - tls_ptr")
print("  0x30  - pcr_ptr (self)")
print("  0x70  - stack_base")
print("  0x74  - stack_limit")
print("  0x100 - current_thread (TEB)")
print("  0x10C - current_cpu")
print()
print(f"Offset 268 = 0x{268:X} = 0x10C")
print("This is the 'current_cpu' field!")
print()

# X360_PCR structure
pcr_offsets = {
    0x00: 'tls_ptr',
    0x30: 'pcr_ptr',
    0x70: 'stack_base',
    0x74: 'stack_limit',
    0x100: 'current_thread',
    0x10C: 'current_cpu',
    0x150: 'dpc_active',
}

offset = 268
print(f"Offset {offset} (0x{offset:X}):")
if offset in pcr_offsets:
    print(f"  Known field: {pcr_offsets[offset]}")
else:
    print(f"  NOT a known PCR field! May be uninitialized memory.")
    # Find closest known field
    closest = max([o for o in pcr_offsets.keys() if o <= offset], default=0)
    print(f"  Closest known: 0x{closest:X} ({pcr_offsets.get(closest, 'unknown')})")
    print(f"  Offset from closest: +{offset - closest} bytes")
print()

# Let's check if offset 268 is within a known region
print("Memory layout check:")
print(f"  PCR size from code: 0x100 bytes (256)")  
print(f"  TLS offset: 0x100")
print(f"  TEB offset: 0x1000")
print(f"  Offset 268 (0x10C) is past PCR, into TLS region")
print()

# From guest_thread.h, let's check X360_TLS
print("=== Checking TLS region ===")
print("TLS starts at PCR+0x100")
print(f"Offset 268 from PCR base = 268 - 256 = offset 12 (0xC) within TLS")
print()

# The issue: the code reads from r13+268, which should be PCR+268
# But PCR is only 256 bytes, so 268 is into the TLS region
# TLS starts at PCR+256, so offset 268 is TLS+12

print("=== ROOT CAUSE HYPOTHESIS ===")
print()
print("The game code reads PCR+268 expecting the CPU/worker index.")
print("But the PCR structure we initialize only covers 256 bytes.")
print("Offset 268 is 12 bytes into the TLS region (which starts at PCR+256).")
print()
print("This value is used as an array index:")
print("  r26 = byte at PCR+268 (should be worker index 0-5)")
print("  r11 = r26 + 36")  
print("  r8 = r11 * 4 (left shift by 2)")
print("  final_addr = a1 + r8")
print()
print("If r26 is garbage (e.g., 0xFF or 0x00 from uninitialized memory),")
print("the computed offset becomes huge, causing the crash.")
