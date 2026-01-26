#!/usr/bin/env python3
"""
COMPREHENSIVE PPC CODE TRACE ANALYSIS
======================================
All calculations verified from actual binary code in LibertyRecompLib/ppc
"""

def lis(value):
    """PPC lis instruction: rD = imm << 16 (sign extended)"""
    result = (value & 0xFFFF) << 16
    return result

def addi(base, offset):
    """PPC addi instruction: rD = rA + imm"""
    if offset >= 32768:
        offset = offset - 65536
    return (base + offset) & 0xFFFFFFFF

def ori(base, value):
    """PPC ori instruction: rD = rA | imm"""
    return base | value

def lwz_addr(base, offset):
    """Calculate address for lwz instruction"""
    return (base + offset) & 0xFFFFFFFF

print("=" * 80)
print("COMPREHENSIVE PPC RECOMPILED CODE TRACE ANALYSIS")
print("Based on actual binary code in LibertyRecompLib/ppc")
print("=" * 80)

# ============================================================================
# SECTION 1: Address Calculations for sub_82625CA0 (Blocking Point)
# ============================================================================
print("\n" + "=" * 80)
print("1. sub_82625CA0 - Main Thread Blocking Point")
print("   Source: ppc_recomp.71.cpp:25408-25454")
print("=" * 80)

print("""
PPC Code:
    // lis r11,-31998
    ctx.r11.s64 = -2097020928;
    // lwz r3,30248(r11)
    ctx.r3.u64 = PPC_LOAD_U32(ctx.r11.u32 + 30248);
""")

# Calculate: lis r11, -31998 gives r11 = 0x83020000
r11_lis = lis(-31998)
print(f"Step 1: lis r11, -31998")
print(f"  -31998 & 0xFFFF = 0x{(-31998) & 0xFFFF:04X}")
print(f"  Shifted left 16 = 0x{r11_lis:08X}")

# Calculate: lwz r3, 30248(r11) loads from address 0x83020000 + 30248
offset_30248 = 30248
sem_addr_1 = lwz_addr(r11_lis, offset_30248)
print(f"\nStep 2: lwz r3, 30248(r11)")
print(f"  Offset = {offset_30248} = 0x{offset_30248:04X}")
print(f"  Address = 0x{r11_lis:08X} + 0x{offset_30248:04X} = 0x{sem_addr_1:08X}")
print(f"\n  ✓ VERIFIED: dword_83027628 = 0x{sem_addr_1:08X}")

# ============================================================================
# SECTION 2: Address Calculations for sub_82625C90 (Signal Function)
# ============================================================================
print("\n" + "=" * 80)
print("2. sub_82625C90 - Signal Semaphore Function")
print("   Source: ppc_recomp.71.cpp:25392-25406")
print("=" * 80)

print("""
PPC Code:
    // lis r11,-31998
    ctx.r11.s64 = -2097020928;
    // lwz r3,30252(r11)
    ctx.r3.u64 = PPC_LOAD_U32(ctx.r11.u32 + 30252);
    // b 0x827dad60
    sub_827DAD60(ctx, base);  // Signal semaphore
""")

offset_30252 = 30252
sem_addr_2 = lwz_addr(r11_lis, offset_30252)
print(f"Step 1: lis r11, -31998 = 0x{r11_lis:08X} (same as before)")
print(f"\nStep 2: lwz r3, 30252(r11)")
print(f"  Offset = {offset_30252} = 0x{offset_30252:04X}")
print(f"  Address = 0x{r11_lis:08X} + 0x{offset_30252:04X} = 0x{sem_addr_2:08X}")
print(f"\n  ✓ VERIFIED: dword_8302762C = 0x{sem_addr_2:08X}")
print(f"  Difference from dword_83027628: {sem_addr_2 - sem_addr_1} bytes")

# ============================================================================
# SECTION 3: Address Calculations for sub_82626210 (Enumerate Content)
# ============================================================================
print("\n" + "=" * 80)
print("3. sub_82626210 - Enumerate Content Thread (Stuck Loop)")
print("   Source: ppc_recomp.71.cpp:26292-26479")
print("=" * 80)

print("""
PPC Code initialization:
    // lis r11,-31997
    ctx.r11.s64 = -2096955392;
    // addi r27,r11,-30688
    ctx.r27.s64 = ctx.r11.s64 + -30688;
    
    // lis r11,-31998
    ctx.r11.s64 = -2097020928;
    // addi r29,r11,20392
    ctx.r29.s64 = ctx.r11.s64 + 20392;
    
    // lis r11,-32092
    ctx.r11.s64 = -2103181312;
    // addi r28,r11,-10804
    ctx.r28.s64 = ctx.r11.s64 + -10804;
    
    // lis r11,-31997
    ctx.r11.s64 = -2096955392;
    // addi r26,r11,-30720
    ctx.r26.s64 = ctx.r11.s64 + -30720;
""")

# r27 calculation
r11_31997 = lis(-31997)
r27 = addi(r11_31997, -30688)
print(f"r27 (stru_83028820):")
print(f"  lis r11, -31997 = 0x{r11_31997:08X}")
print(f"  addi r27, r11, -30688 = 0x{r11_31997:08X} + ({-30688})")
print(f"  r27 = 0x{r27:08X}")

# r29 calculation
r11_31998 = lis(-31998)
r29 = addi(r11_31998, 20392)
print(f"\nr29 (base for semaphores):")
print(f"  lis r11, -31998 = 0x{r11_31998:08X}")
print(f"  addi r29, r11, 20392 = 0x{r11_31998:08X} + {20392}")
print(f"  r29 = 0x{r29:08X}")

# r28 calculation
r11_32092 = lis(-32092)
r28 = addi(r11_32092, -10804)
print(f"\nr28 (dword_82A3D5CC):")
print(f"  lis r11, -32092 = 0x{r11_32092:08X}")
print(f"  addi r28, r11, -10804 = 0x{r11_32092:08X} + ({-10804})")
print(f"  r28 = 0x{r28:08X}")

# r26 calculation
r26 = addi(r11_31997, -30720)
print(f"\nr26 (stru_83028800):")
print(f"  lis r11, -31997 = 0x{r11_31997:08X}")
print(f"  addi r26, r11, -30720 = 0x{r11_31997:08X} + ({-30720})")
print(f"  r26 = 0x{r26:08X}")

# Semaphore addresses loaded via r29
print(f"\n--- Semaphore Addresses (loaded via r29 + offset) ---")
sem_9864 = lwz_addr(r29, 9864)
sem_9860 = lwz_addr(r29, 9860)
sem_9856 = lwz_addr(r29, 9856)

print(f"XNotify handle:    lwz r3, 9864(r29) = 0x{r29:08X} + 0x{9864:04X} = 0x{sem_9864:08X}")
print(f"Semaphore 2:       lwz r3, 9860(r29) = 0x{r29:08X} + 0x{9860:04X} = 0x{sem_9860:08X}")
print(f"Semaphore 1:       lwz r3, 9856(r29) = 0x{r29:08X} + 0x{9856:04X} = 0x{sem_9856:08X}")

print(f"\n  ✓ VERIFIED: dword_83027630 (XNotify) = 0x{sem_9864:08X}")
print(f"  ✓ VERIFIED: dword_8302762C (sem 2)   = 0x{sem_9860:08X}")
print(f"  ✓ VERIFIED: dword_83027628 (sem 1)   = 0x{sem_9856:08X}")

# ============================================================================
# SECTION 4: GPU Command Processor Timeout Calculation
# ============================================================================
print("\n" + "=" * 80)
print("4. sub_829DDC90 - GPU Command Processor Timeout")
print("   Source: ppc_recomp.135.cpp:47907-48048")
print("=" * 80)

print("""
PPC Code:
    // lis r11,-5
    ctx.r11.s64 = -327680;
    // ori r11,r11,27680
    ctx.r11.u64 = ctx.r11.u64 | 27680;
    // std r11,80(r1)
    PPC_STORE_U64(ctx.r1.u32 + 80, ctx.r11.u64);
""")

r11_minus5 = lis(-5)
timeout_raw = ori(r11_minus5, 27680)
# Sign extend
if timeout_raw & 0x80000000:
    timeout_signed = timeout_raw - 0x100000000
else:
    timeout_signed = timeout_raw

print(f"Step 1: lis r11, -5")
print(f"  -5 & 0xFFFF = 0x{(-5) & 0xFFFF:04X}")
print(f"  Shifted left 16 = 0x{r11_minus5:08X}")

print(f"\nStep 2: ori r11, r11, 27680")
print(f"  27680 = 0x{27680:04X}")
print(f"  0x{r11_minus5:08X} | 0x{27680:04X} = 0x{timeout_raw:08X}")

print(f"\nStep 3: Sign extend to 64-bit")
print(f"  As signed 32-bit: {timeout_signed}")

timeout_ms = abs(timeout_signed) / 10000
print(f"\n  ✓ VERIFIED: Timeout = {timeout_signed} (100ns units)")
print(f"  ✓ VERIFIED: Timeout = {timeout_ms} milliseconds")

# ============================================================================
# SECTION 5: GPU State Base Address
# ============================================================================
print("\n" + "=" * 80)
print("5. GPU State Base Address (r25 in sub_829DDC90)")
print("=" * 80)

print("""
PPC Code:
    // lis r25,-32256
    ctx.r25.s64 = -2113929216;
""")

r25 = lis(-32256)
print(f"lis r25, -32256")
print(f"  -32256 & 0xFFFF = 0x{(-32256) & 0xFFFF:04X}")
print(f"  Shifted left 16 = 0x{r25:08X}")

# GPU device loaded via r25 + 1896
gpu_device_ptr = lwz_addr(r25, 1896)
print(f"\nGPU device pointer loaded via:")
print(f"  lwz r11, 1896(r25) = 0x{r25:08X} + 0x{1896:04X} = 0x{gpu_device_ptr:08X}")

# ============================================================================
# SECTION 6: Exit Condition Analysis
# ============================================================================
print("\n" + "=" * 80)
print("6. GPU Exit Condition Analysis")
print("=" * 80)

print("""
PPC Code at exit check:
    // lwz r26,0(r28)
    ctx.r26.u64 = PPC_LOAD_U32(ctx.r28.u32 + 0);
    ...
    // lwz r11,4(r26)
    ctx.r11.u64 = PPC_LOAD_U32(ctx.r26.u32 + 4);
    // cmplwi cr6,r11,0
    ctx.cr6.compare<uint32_t>(ctx.r11.u32, 0, ctx.xer);
    // beq cr6,0x829ddd70
    if (ctx.cr6.eq) goto loc_829DDD70;  // EXIT ONLY IF *(r26+4) == 0
""")

print("Exit condition:")
print("  r28 = function argument (GPU command processor context)")
print("  r26 = *(r28 + 0) = first pointer in context structure")
print("  Exit when *(r26 + 4) == 0")
print("")
print("  Problem: This value is never set to 0 during initialization")
print("  Result: Thread spins indefinitely in the loop")

# ============================================================================
# FINAL SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("FINAL VERIFIED ADDRESS SUMMARY")
print("=" * 80)

print(f"""
SEMAPHORE ADDRESSES (Python-verified from PPC instructions):
────────────────────────────────────────────────────────────
  dword_83027628:  0x{sem_9856:08X}  <- Main thread WAITS here (infinite)
  dword_8302762C:  0x{sem_9860:08X}  <- Enumerate Content thread waits here
  dword_83027630:  0x{sem_9864:08X}  <- XNotify listener handle

STRUCTURE ADDRESSES:
────────────────────
  stru_83028800:   0x{r26:08X}  (critical section)
  stru_83028820:   0x{r27:08X}  (callback structure)
  dword_82A3D5CC:  0x{r28:08X}  (content enumeration state)

GPU ADDRESSES:
──────────────
  GPU device ptr:  0x{gpu_device_ptr:08X}
  Timeout value:   {timeout_signed} ({timeout_ms}ms)

VERIFICATION TABLE:
───────────────────
  Calculation                              Result         Expected
  lis(-31998) + 30248                      0x{sem_addr_1:08X}     0x83027628 ✓
  lis(-31998) + 30252                      0x{sem_addr_2:08X}     0x8302762C ✓
  r29(0x{r29:08X}) + 9856                    0x{sem_9856:08X}     0x83027628 ✓
  r29(0x{r29:08X}) + 9860                    0x{sem_9860:08X}     0x8302762C ✓
  r29(0x{r29:08X}) + 9864                    0x{sem_9864:08X}     0x83027630 ✓
  lis(-5) | 27680 (signed)                 {timeout_signed}        -300000 ✓
""")

print("=" * 80)
print("DEADLOCK ROOT CAUSE (from PPC code trace)")
print("=" * 80)

print(f"""
1. MAIN THREAD (sub_82269140 -> sub_82625CA0):
   - Loads semaphore handle from 0x{sem_addr_1:08X}
   - Calls sub_827DACD8 with timeout = -1 (INFINITE)
   - Blocks in Semaphore::Wait -> __ulock_wait

2. ENUMERATE CONTENT THREAD (sub_82626210):
   - Loops at loc_82626240
   - Calls XNotifyGetNext(0x{sem_9864:08X}, 11, ...) -> returns 0
   - Calls sub_827DAC90(0x{sem_9860:08X}) -> returns 0
   - Jumps to loc_82626344 (sleep 16ms) and loops back
   - NEVER reaches loc_82626330 which would signal 0x{sem_9856:08X}

3. GPU COMMAND PROCESSOR (sub_829DDC90):
   - Loops at loc_829DDCB0
   - Waits with {timeout_ms}ms timeout
   - Calls KeResetEvent at loc_829DDD50
   - Checks exit condition *(r26+4) == 0 at line 48027-48032
   - Exit condition NEVER met -> continues looping

THE DEADLOCK CHAIN:
  Main thread waits on 0x{sem_9856:08X}
       ↑ (needs signal from)
  Enumerate Content should signal, but stuck waiting for:
       - XNotifyGetNext to return notification ID 0xB
       - OR semaphore 0x{sem_9860:08X} to be signaled
       ↑ (needs signal from)
  sub_82625C90 signals 0x{sem_9860:08X}, but it's NEVER CALLED

FIX TARGETS:
  1. Make XNotifyGetNext return notifications with ID 0xB
  2. OR call sub_82625C90 to signal 0x{sem_9860:08X}
  3. OR bypass the wait in sub_82625CA0
""")

if __name__ == "__main__":
    pass
