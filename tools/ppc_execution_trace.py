#!/usr/bin/env python3
"""
PPC Execution Trace - Actual Binary Code Analysis
All math operations performed via Python for verification.
Based on actual ppc_recomp.*.cpp files, NOT IDA pseudo-code.
"""

def lis(val):
    """
    PowerPC lis instruction: Load Immediate Shifted
    lis r11,-31997  =>  ctx.r11.s64 = -2096955392
    
    The value is a signed 16-bit immediate shifted left by 16 bits.
    Result is sign-extended to 64 bits in the PPC context.
    """
    # Sign-extend 16-bit value, then shift left 16
    if val < 0:
        # Negative: val is already sign-extended in Python
        result = val << 16
    else:
        result = val << 16
    
    # Mask to 32 bits for address use
    return result & 0xFFFFFFFF

def signed_extend(val, bits=32):
    """Sign-extend a value to signed integer"""
    mask = (1 << bits) - 1
    val = val & mask
    if val & (1 << (bits - 1)):
        return val - (1 << bits)
    return val

print("=" * 80)
print("PPC EXECUTION TRACE - ACTUAL BINARY CODE ANALYSIS")
print("Based on ppc_recomp.*.cpp files (the ACTUAL compilable code)")
print("=" * 80)

# =============================================================================
# SECTION 1: sub_82626210 - "Enumerate Content" Thread
# Source: ppc_recomp.71.cpp lines 26292-26479
# =============================================================================
print("\n## SECTION 1: sub_82626210 - Enumerate Content Thread")
print("Source: ppc_recomp.71.cpp:26292-26479")
print("-" * 60)

print("\n### Address Calculations from PPC Instructions:")
print()

# Line 26304-26305: lis r11,-31997 => ctx.r11.s64 = -2096955392
r11_lis_31997 = -2096955392
print(f"Line 26304-26305: lis r11,-31997")
print(f"  ctx.r11.s64 = -2096955392")
print(f"  Verification: -31997 * 65536 = {-31997 * 65536}")
print(f"  As unsigned 32-bit: 0x{r11_lis_31997 & 0xFFFFFFFF:08X}")
print()

# Line 26308-26309: addi r27,r11,-30688 => stru_83028820
r27 = (r11_lis_31997 + (-30688)) & 0xFFFFFFFF
print(f"Line 26308-26309: addi r27,r11,-30688")
print(f"  ctx.r27.s64 = ctx.r11.s64 + (-30688)")
print(f"  Calculation: {r11_lis_31997} + (-30688) = {r11_lis_31997 + (-30688)}")
print(f"  As unsigned 32-bit: 0x{r27:08X}")
print(f"  This is: stru_83028820")
print()

# Line 26310-26311: lis r11,-31998 => ctx.r11.s64 = -2097020928
r11_lis_31998 = -2097020928
print(f"Line 26310-26311: lis r11,-31998")
print(f"  ctx.r11.s64 = -2097020928")
print(f"  Verification: -31998 * 65536 = {-31998 * 65536}")
print(f"  As unsigned 32-bit: 0x{r11_lis_31998 & 0xFFFFFFFF:08X}")
print()

# Line 26312-26313: addi r29,r11,20392 => semaphore base
r29 = (r11_lis_31998 + 20392) & 0xFFFFFFFF
print(f"Line 26312-26313: addi r29,r11,20392")
print(f"  ctx.r29.s64 = ctx.r11.s64 + 20392")
print(f"  Calculation: {r11_lis_31998} + 20392 = {r11_lis_31998 + 20392}")
print(f"  As unsigned 32-bit: 0x{r29:08X}")
print(f"  This is the semaphore base pointer")
print()

# Line 26314-26315: lis r11,-32092 => ctx.r11.s64 = -2103181312
r11_lis_32092 = -2103181312
print(f"Line 26314-26315: lis r11,-32092")
print(f"  ctx.r11.s64 = -2103181312")
print(f"  Verification: -32092 * 65536 = {-32092 * 65536}")
print(f"  As unsigned 32-bit: 0x{r11_lis_32092 & 0xFFFFFFFF:08X}")
print()

# Line 26316-26317: addi r28,r11,-10804 => dword_82A3D5CC
r28 = (r11_lis_32092 + (-10804)) & 0xFFFFFFFF
print(f"Line 26316-26317: addi r28,r11,-10804")
print(f"  ctx.r28.s64 = ctx.r11.s64 + (-10804)")
print(f"  Calculation: {r11_lis_32092} + (-10804) = {r11_lis_32092 + (-10804)}")
print(f"  As unsigned 32-bit: 0x{r28:08X}")
print(f"  This is: dword_82A3D5CC")
print()

# Line 26318-26321: addi r26,r11,-30720 => stru_83028800
r11_lis_31997_2 = -2096955392
r26 = (r11_lis_31997_2 + (-30720)) & 0xFFFFFFFF
print(f"Line 26318-26321: lis r11,-31997; addi r26,r11,-30720")
print(f"  ctx.r26.s64 = -2096955392 + (-30720)")
print(f"  Calculation: {r11_lis_31997_2} + (-30720) = {r11_lis_31997_2 + (-30720)}")
print(f"  As unsigned 32-bit: 0x{r26:08X}")
print(f"  This is: stru_83028800")
print()

# =============================================================================
# SECTION 2: Memory Access Addresses
# =============================================================================
print("\n### Memory Access Addresses (from PPC LOAD instructions):")
print()

# Line 26325-26326: lwz r3,9864(r29) => XNotify handle
xnotify_handle = (r29 + 9864) & 0xFFFFFFFF
print(f"Line 26325-26326: lwz r3,9864(r29)")
print(f"  ctx.r3.u64 = PPC_LOAD_U32(ctx.r29.u32 + 9864)")
print(f"  Address: 0x{r29:08X} + 9864 = 0x{xnotify_handle:08X}")
print(f"  This loads: dword_83027630 (XNotify handle)")
print()

# Line 26347-26348: lwz r3,9860(r29) => semaphore 2
sem2_addr = (r29 + 9860) & 0xFFFFFFFF
print(f"Line 26347-26348: lwz r3,9860(r29)")
print(f"  ctx.r3.u64 = PPC_LOAD_U32(ctx.r29.u32 + 9860)")
print(f"  Address: 0x{r29:08X} + 9860 = 0x{sem2_addr:08X}")
print(f"  This loads: dword_8302762C (semaphore 2 - try-wait)")
print()

# Line 26458-26459: lwz r3,9856(r29) => semaphore 1
sem1_addr = (r29 + 9856) & 0xFFFFFFFF
print(f"Line 26458-26459: lwz r3,9856(r29)")
print(f"  ctx.r3.u64 = PPC_LOAD_U32(ctx.r29.u32 + 9856)")
print(f"  Address: 0x{r29:08X} + 9856 = 0x{sem1_addr:08X}")
print(f"  This loads: dword_83027628 (semaphore 1 - signal target)")
print()

# =============================================================================
# SECTION 3: Execution Flow Trace
# =============================================================================
print("\n## SECTION 2: EXECUTION FLOW TRACE")
print("From actual ppc_recomp.71.cpp code")
print("-" * 60)

print("""
loc_82626240 (LOOP START - Line 26322):
  │
  ├─ Line 26325-26326: Load XNotify handle
  │    ctx.r3.u64 = PPC_LOAD_U32(0x83027630)
  │
  ├─ Line 26329-26330: Set filter = 11 (0xB)
  │    ctx.r4.s64 = 11
  │
  ├─ Line 26331-26333: Call XNotifyGetNext
  │    ctx.lr = 0x82626254
  │    __imp__XNotifyGetNext(ctx, base)
  │
  ├─ Line 26334-26339: Check if notification received
  │    if (ctx.r3.s32 != 0) ctx.r31.s64 = 1
  │
  ├─ Line 26340-26346: Check r31 (notification flag)
  │    r30 = r31 & 0xFF
  │    if (r30 != 0) goto loc_82626280  // Proceed to content enum
  │
  ├─ Line 26347-26351: Try-wait on semaphore 2
  │    ctx.r3 = PPC_LOAD_U32(0x8302762C)  // Load sem2 handle
  │    sub_827DAC90(ctx, base)            // Try-wait
  │
  ├─ Line 26352-26357: Check try-wait result
  │    if ((ctx.r3 & 0xFF) == 0)
  │        goto loc_82626344  // SLEEP AND LOOP
  │
  ... (content enumeration code - NOT REACHED) ...
  │
loc_82626330 (SIGNAL POINT - Line 26457):
  │
  ├─ Line 26458-26462: SIGNAL semaphore 1
  │    ctx.r3 = PPC_LOAD_U32(0x83027628)  // Load sem1 handle
  │    sub_827DAD60(ctx, base)            // SIGNAL!
  │
loc_82626344 (SLEEP - Line 26471):
  │
  ├─ Line 26472-26476: Sleep 16ms
  │    ctx.r3.s64 = 16
  │    sub_827DAE18(ctx, base)  // Sleep
  │
  └─ Line 26477-26478: Loop back
       goto loc_82626240
""")

# =============================================================================
# SECTION 4: Semaphore Function Trace
# =============================================================================
print("\n## SECTION 3: SEMAPHORE FUNCTION TRACE")
print("From actual ppc_recomp.102.cpp and ppc_recomp.131/132.cpp")
print("-" * 60)

print("""
### sub_827DAC90 - Try-Wait Semaphore (Non-blocking)
Source: ppc_recomp.102.cpp:26822-26863

  PPC_FUNC_IMPL(__imp__sub_827DAC90):
    if (ctx.r3.u32 == 0) return;  // NULL check
    ctx.r4.s64 = 0;               // timeout = 0 (immediate)
    sub_829A2380(ctx, base);      // -> sub_829A9738 -> NtWaitForSingleObjectEx
    // Return: 1 if acquired, 0 if not

### sub_827DACD8 - Wait Semaphore (Blocking - INFINITE)
Source: ppc_recomp.102.cpp:26869-26910

  PPC_FUNC_IMPL(__imp__sub_827DACD8):
    if (ctx.r3.u32 == 0) return;  // NULL check
    ctx.r4.s64 = -1;              // timeout = -1 (INFINITE)
    sub_829A2380(ctx, base);      // -> sub_829A9738 -> NtWaitForSingleObjectEx
    // BLOCKS FOREVER if semaphore not signaled!

### sub_827DAD60 - Signal Semaphore (Release)
Source: ppc_recomp.102.cpp:26961-27006

  PPC_FUNC_IMPL(__imp__sub_827DAD60):
    if (ctx.r3.u32 == 0) return;  // NULL check
    ctx.r5.s64 = 0;
    ctx.r4.s64 = 1;               // release count = 1
    sub_829A2290(ctx, base);      // -> NtReleaseSemaphore
    // Wakes up one waiting thread

### sub_829A9738 - Semaphore Wait Implementation
Source: ppc_recomp.132.cpp:1682-1745

  PPC_FUNC_IMPL(__imp__sub_829A9738):
    // r3 = semaphore handle, r4 = timeout
    __imp__NtWaitForSingleObjectEx(ctx, base);  // Line 1718
    // If r3 < 0: error
    // If r3 == 257: alerted, loop back
    // Otherwise: success or timeout

### sub_829A2290 - Semaphore Signal Implementation
Source: ppc_recomp.131.cpp:19988-20025

  PPC_FUNC_IMPL(__imp__sub_829A2290):
    __imp__NtReleaseSemaphore(ctx, base);  // Line 20001
    // r3 < 0: error
    // Otherwise: return 1 (success)
""")

# =============================================================================
# SECTION 5: The Deadlock Explained from Actual Code
# =============================================================================
print("\n## SECTION 4: THE DEADLOCK (from actual PPC code)")
print("-" * 60)

print(f"""
VERIFIED ADDRESSES (all Python calculated):
  Semaphore 1 (dword_83027628): 0x{sem1_addr:08X}
  Semaphore 2 (dword_8302762C): 0x{sem2_addr:08X}
  XNotify handle (dword_83027630): 0x{xnotify_handle:08X}
  stru_83028800: 0x{r26:08X}
  stru_83028820: 0x{r27:08X}
  dword_82A3D5CC: 0x{r28:08X}

THE BLOCKING SEQUENCE (from ppc_recomp.71.cpp):
================================================

1. Thread 19 enters sub_82626210 at loc_82626240 (line 26322)

2. Calls __imp__XNotifyGetNext with filter=11 (line 26333)
   - Returns 0 (no notification with ID 11 in queue)
   - ctx.r31 stays 0

3. Checks ctx.r30 (= ctx.r31 & 0xFF) == 0 (line 26343-26346)
   - True, so doesn't jump to loc_82626280

4. Loads semaphore 2 handle from 0x{sem2_addr:08X} (line 26348)
   - Calls sub_827DAC90 (try-wait with timeout=0)
   
5. sub_827DAC90 (ppc_recomp.102.cpp:26822):
   - Sets ctx.r4.s64 = 0 (immediate timeout)
   - Calls sub_829A2380 -> sub_829A9738 -> NtWaitForSingleObjectEx
   - Returns 0 because semaphore not signaled

6. Checks result (line 26352-26357):
   - (ctx.r3 & 0xFF) == 0 is TRUE
   - Jumps to loc_82626344 (SLEEP)

7. At loc_82626344 (line 26471):
   - ctx.r3 = 16 (sleep 16ms)
   - Calls sub_827DAE18 (Sleep)
   - goto loc_82626240 (LOOP BACK)

8. NEVER REACHES loc_82626330 (line 26457) which would:
   - Load semaphore 1 handle from 0x{sem1_addr:08X}
   - Call sub_827DAD60 (signal semaphore 1)
   - UNBLOCK MAIN THREAD!

MAIN THREAD BLOCKING (not shown but traced):
============================================
Main thread calls sub_827DACD8(semaphore 1 handle)
  - Sets ctx.r4.s64 = -1 (INFINITE timeout)
  - Calls NtWaitForSingleObjectEx with INFINITE wait
  - BLOCKS FOREVER because Thread 19 never signals
""")

# =============================================================================
# SECTION 6: Why XNotifyGetNext Returns 0
# =============================================================================
print("\n## SECTION 5: WHY XNotifyGetNext RETURNS 0")
print("-" * 60)

print("""
From the PPC code at line 26329-26330:
  ctx.r4.s64 = 11;  // li r4,11 - filter value

XNotifyGetNext is called with dwMsgFilter = 11 (0xB)

WHAT THIS FILTER MEANS:
  The game looks for a notification with ID == 11
  ID 11 = 0xB = XN_SYS_SIGNINCHANGED (profile sign-in state changed)

CURRENT BEHAVIOR:
  - XamNotifyEnqueueEvent is NOT called with ID 11 at startup
  - XNotifyGetNext searches listener.notifications for ID == 11
  - No match found, returns 0

THE FIX WOULD REQUIRE:
  Someone to call XamNotifyEnqueueEvent(11, param) before or during startup
  This would add a notification with ID 11 to the queue
  XNotifyGetNext would then return 1 (found notification)
  Thread 19 would proceed to content enumeration
  Thread 19 would signal semaphore 1
  Main thread would unblock
""")

# =============================================================================
# SECTION 7: Summary Table
# =============================================================================
print("\n## SECTION 6: SUMMARY TABLE")
print("-" * 60)

print(f"""
┌────────────────────────────────────────────────────────────────────────────┐
│ COMPONENT                │ ADDRESS/VALUE      │ SOURCE FILE                │
├────────────────────────────────────────────────────────────────────────────┤
│ Semaphore 1 (main waits) │ 0x{sem1_addr:08X}      │ ppc_recomp.71.cpp:26459    │
│ Semaphore 2 (try-wait)   │ 0x{sem2_addr:08X}      │ ppc_recomp.71.cpp:26348    │
│ XNotify handle           │ 0x{xnotify_handle:08X}      │ ppc_recomp.71.cpp:26326    │
│ XNotify filter           │ 11 (0xB)           │ ppc_recomp.71.cpp:26330    │
│ Sleep duration           │ 16ms               │ ppc_recomp.71.cpp:26473    │
├────────────────────────────────────────────────────────────────────────────┤
│ sub_827DAC90 (try-wait)  │ timeout=0          │ ppc_recomp.102.cpp:26847   │
│ sub_827DACD8 (wait)      │ timeout=-1 (INF)   │ ppc_recomp.102.cpp:26894   │
│ sub_827DAD60 (signal)    │ count=1            │ ppc_recomp.102.cpp:26988   │
├────────────────────────────────────────────────────────────────────────────┤
│ NtWaitForSingleObjectEx  │ kernel call        │ ppc_recomp.132.cpp:1718    │
│ NtReleaseSemaphore       │ kernel call        │ ppc_recomp.131.cpp:20001   │
└────────────────────────────────────────────────────────────────────────────┘

BLOCKING THREAD: Thread 19 (sub_82626210 "Enumerate Content")
  Location: ppc_recomp.71.cpp lines 26292-26479
  State: Loops between loc_82626240 and loc_82626344
  Never reaches: loc_82626330 (signal point)

BLOCKED THREAD: Main Thread
  Function: sub_827DACD8 (infinite wait on semaphore 1)
  Source: ppc_recomp.102.cpp lines 26869-26910
  State: BLOCKED on NtWaitForSingleObjectEx with timeout=-1
""")

if __name__ == "__main__":
    print("\n[Trace complete - all addresses verified from actual PPC code]")
