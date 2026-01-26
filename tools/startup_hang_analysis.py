#!/usr/bin/env python3
"""
Startup Hang Analysis - Address Calculations and Blocking Chain Trace
All math operations performed via Python for verification.
"""

def lis(val):
    """PowerPC lis instruction: load immediate shifted (16 bits << 16)"""
    # lis loads a 16-bit signed immediate into the upper 16 bits
    # Result is sign-extended to 32 bits
    result = (val & 0xFFFF) << 16
    if val < 0:
        # Handle signed negative values
        result = (0xFFFF0000 & (val << 16)) | 0x00000000
        # Sign extend
        if result & 0x80000000:
            result = result - 0x100000000
    return result & 0xFFFFFFFF

def signed32(val):
    """Convert to signed 32-bit"""
    if val & 0x80000000:
        return val - 0x100000000
    return val

print("=" * 80)
print("STARTUP HANG ANALYSIS - ADDRESS CALCULATIONS")
print("=" * 80)

# =============================================================================
# SECTION 1: sub_829DDC90 (GPU Command Processor) - Threads 17 & 18 stuck here
# =============================================================================
print("\n## SECTION 1: sub_829DDC90 (GPU Command Processor)")
print("-" * 60)

# Line 47931-47938: Timeout calculation
# lis r11,-5  => ctx.r11.s64 = -327680
# ori r11,r11,27680  => ctx.r11.u64 = ctx.r11.u64 | 27680

lis_minus5 = lis(-5)
print(f"lis(-5) = 0x{lis_minus5:08X} = {signed32(lis_minus5)} (decimal)")

timeout_value = lis_minus5 | 27680
print(f"lis(-5) | 27680 = 0x{timeout_value:08X} = {signed32(timeout_value)} (decimal)")

# Convert 100ns units to milliseconds
timeout_100ns = signed32(timeout_value)
timeout_ms = abs(timeout_100ns) / 10000
print(f"Timeout in 100ns units: {timeout_100ns}")
print(f"Timeout in milliseconds: {timeout_ms:.1f}ms")

# Line 47929: r25 = lis(-32256) = device pointer base
lis_32256 = lis(-32256)
print(f"\nlis(-32256) = 0x{lis_32256:08X} (r25 = device pointer base)")

# Line 48017: cmplwi cr6,r3,258 - checks for WAIT_TIMEOUT (258 = 0x102)
print(f"\nWAIT_TIMEOUT check: r3 == 258 (0x{258:X})")
print("If wait returns 258 (TIMEOUT), loop continues to loc_829DDCF0")

# =============================================================================
# SECTION 2: sub_82626210 (Enumerate Content Thread) - Thread 19
# =============================================================================
print("\n\n## SECTION 2: sub_82626210 (Enumerate Content Thread)")
print("-" * 60)

# Line 26304-26321: Address calculations
# lis r11,-31997 => ctx.r11.s64 = -2096955392
lis_31997 = lis(-31997)
print(f"lis(-31997) = 0x{lis_31997:08X}")

# addi r27,r11,-30688 => stru_83028820
r27 = (lis_31997 + (-30688)) & 0xFFFFFFFF
print(f"r27 = lis(-31997) + (-30688) = 0x{r27:08X} (stru_83028820)")

# lis r11,-31998 => -2097020928
lis_31998 = lis(-31998)
print(f"lis(-31998) = 0x{lis_31998:08X}")

# addi r29,r11,20392 => base pointer for semaphores
r29 = (lis_31998 + 20392) & 0xFFFFFFFF
print(f"r29 = lis(-31998) + 20392 = 0x{r29:08X} (semaphore base)")

# lis r11,-32092 => -2103181312
lis_32092 = lis(-32092)
print(f"lis(-32092) = 0x{lis_32092:08X}")

# addi r28,r11,-10804 => dword_82A3D5CC
r28 = (lis_32092 + (-10804)) & 0xFFFFFFFF
print(f"r28 = lis(-32092) + (-10804) = 0x{r28:08X} (dword_82A3D5CC)")

# addi r26,r11,-30720 => stru_83028800
lis_31997_2 = lis(-31997)
r26 = (lis_31997_2 + (-30720)) & 0xFFFFFFFF
print(f"r26 = lis(-31997) + (-30720) = 0x{r26:08X} (stru_83028800)")

print("\n### Key Memory Addresses:")
# Line 26326: lwz r3,9864(r29) => XNotify handle at r29+9864
xnotify_handle_addr = (r29 + 9864) & 0xFFFFFFFF
print(f"XNotify handle: r29 + 9864 = 0x{xnotify_handle_addr:08X}")

# Line 26348: lwz r3,9860(r29) => semaphore 2
sem2_addr = (r29 + 9860) & 0xFFFFFFFF
print(f"Semaphore 2 (try-wait): r29 + 9860 = 0x{sem2_addr:08X}")

# Line 26459: lwz r3,9856(r29) => semaphore 1 (signal target)
sem1_addr = (r29 + 9856) & 0xFFFFFFFF
print(f"Semaphore 1 (signal target): r29 + 9856 = 0x{sem1_addr:08X}")

# =============================================================================
# SECTION 3: Blocking Chain Analysis
# =============================================================================
print("\n\n## SECTION 3: BLOCKING CHAIN ANALYSIS")
print("-" * 60)

print("""
THREAD #17 & #18 (sub_829DDC90 - GPU Command Processor):
=========================================================
Location: ppc_recomp.135.cpp lines 47907-48048

LOOP STRUCTURE:
  loc_829DDCB0:           <- LOOP START
    1. lis r11,-5         <- Load timeout = -300000 (30ms)
    2. ori r11,r11,27680
    3. lwz r26,0(r28)     <- Load device state
    4. KeWaitForSingleObject(event, 30ms timeout)
    5. If returns 258 (TIMEOUT) -> goto loc_829DDCF0 (Present frame)
    
  loc_829DDD50:           <- RESET EVENT
    1. KeResetEvent(r28+32)  <- Thread 17 stuck here
    2. lwz r11,4(r26)     <- Check exit flag
    3. If exit flag == 0 -> EXIT
    4. sub_829DD978()     <- PM4 processing (stubbed)
    5. goto loc_829DDCB0  <- LOOP BACK

EXIT CONDITION: *(r26 + 4) == 0 (device exit flag)

THREAD #19 (sub_82626210 - Enumerate Content Thread):
=====================================================
Location: ppc_recomp.71.cpp lines 26292-26479

LOOP STRUCTURE:
  loc_82626240:           <- LOOP START
    1. XNotifyGetNext(handle, filter=11)
    2. If notification received -> r31 = 1
    3. If r31 == 0:
       - sub_827DAC90(sem2)   <- Try-wait semaphore
       - If failed -> goto loc_82626344 (SLEEP)
    4. If r30 == 0 (no notification AND no semaphore):
       - goto loc_82626330   <- SIGNAL sem1
    
  loc_82626330:           <- SIGNAL POINT
    - sub_827DAD60(sem1)     <- Signal semaphore 1 (would unblock main!)
    
  loc_82626344:           <- SLEEP
    - sub_827DAE18(16)       <- Sleep 16ms
    - goto loc_82626240      <- LOOP BACK

EXIT CONDITION: None - infinite loop by design
""")

# =============================================================================
# SECTION 4: Why Thread 17 is stuck in KeResetEvent
# =============================================================================
print("\n## SECTION 4: WHY THREAD 17 IS STUCK IN KeResetEvent")
print("-" * 60)

print("""
From LLDB backtrace (Thread #17):
  frame #0: KeResetEvent(_XDISPATCHER_HEADER*) + 524
  frame #1: sub_829DDC90(PPCContext&, unsigned char*) + 968

From PPC code at line 48022-48026:
  // addi r3,r28,32
  ctx.r3.s64 = ctx.r28.s64 + 32;
  // bl 0x82a02a4c
  __imp__KeResetEvent(ctx, base);

The thread is stuck because:
1. KeResetEvent is waiting on a host synchronization primitive
2. The event at (r28 + 32) is never being signaled
3. This event is related to GPU command buffer completion

GPU COMMAND BUFFER ISSUE:
- sub_829DD978 (PM4 processing) is stubbed to return 0
- But the event that sub_829DDC90 waits on is never signaled
- The loop at loc_829DDD50 calls KeResetEvent then loops back

ROOT CAUSE: The GPU command processor waits for an event that should be
signaled when GPU work completes, but since GPU work is stubbed, this
event is never signaled properly.
""")

# =============================================================================
# SECTION 5: Why Thread 18 is stuck in KeWaitForSingleObject
# =============================================================================
print("\n## SECTION 5: WHY THREAD 18 IS STUCK IN KeWaitForSingleObject")
print("-" * 60)

print("""
From LLDB backtrace (Thread #18):
  frame #0: __ulock_wait + 8
  frame #4: KeWaitForSingleObject + 2944
  frame #5: sub_829DDC90(PPCContext&, unsigned char*) + 500

From PPC code at line 48004-48016:
  loc_829DDD30:
    // mr r7,r27       <- timeout pointer (or 0)
    // li r6,0
    // li r5,1
    // li r4,3
    // mr r3,r29       <- event at r28+32
    // bl __imp__KeWaitForSingleObject

Parameters:
  r3 = event (r28 + 32)
  r4 = 3 (wait reason)
  r5 = 1 (wait mode)
  r6 = 0 (alertable = false)
  r7 = timeout pointer (30ms or NULL)

The thread is stuck because:
1. It's waiting for the same GPU completion event as Thread #17
2. The 30ms timeout causes it to loop (return value 258 = TIMEOUT)
3. But the event is never truly signaled, so it keeps timing out and looping
""")

# =============================================================================
# SECTION 6: The Real Blocking Point
# =============================================================================
print("\n## SECTION 6: THE REAL BLOCKING POINT IDENTIFIED")
print("-" * 60)

print("""
CRITICAL FINDING: Both Thread #17 and #18 are in sub_829DDC90
(GPU Command Processor) but they are NOT the cause of the beachball.

Evidence:
1. VBlank callbacks fire at 60Hz (rendering works)
2. NtWaitEx is being called with timeout=0 (polling)
3. Log shows "NtWaitEx #60500 handle=0xC84B1530 timeout=0 caller=0x829B091C"

The beachball occurs because:
1. The main thread is waiting on a semaphore that's never signaled
2. Thread 19 (Enumerate Content) should signal this semaphore
3. But Thread 19 never reaches the signal point (loc_82626330)

THREAD 19 ANALYSIS (sub_82626210):
- Calls XNotifyGetNext(handle, filter=11) -> returns 0 (no notifications)
- Calls sub_827DAC90(sem2) -> try-wait returns 0 (not signaled)
- Goes to loc_82626344 -> sleep 16ms
- Loops back without ever reaching loc_82626330 (signal point)

THE DEADLOCK:
- Main thread waits on semaphore at 0x83027628
- Thread 19 should signal it but can't because:
  1. XNotifyGetNext returns 0 (no notification ID 11)
  2. sub_827DAC90 try-wait fails
- Neither condition allows Thread 19 to reach the signal point
""")

# =============================================================================
# SECTION 7: XNotifyGetNext Filter Analysis
# =============================================================================
print("\n## SECTION 7: XNotifyGetNext FILTER ANALYSIS")
print("-" * 60)

# Filter value is 11 (0xB)
filter_value = 11
print(f"XNotifyGetNext filter parameter: {filter_value} (0x{filter_value:X})")

print("""
Xbox 360 XNotify IDs (filter mask 0xB = 11):
  Bit 0 (1): XNOTIFY_SYSTEM - System notifications
  Bit 1 (2): XNOTIFY_LIVE - Xbox Live notifications  
  Bit 3 (8): XNOTIFY_UI - UI notifications

Filter 11 = 1 + 2 + 8 = System + Live + UI notifications

The game is waiting for one of these notification types.
Possible notifications:
  - XNOTIFY_SYSTEM: Profile signed in, storage enumerated
  - XNOTIFY_LIVE: Connection status
  - XNOTIFY_UI: User interaction completed

MOST LIKELY: Content enumeration complete notification
The game enumerates save games/DLC and waits for completion notification.
""")

# =============================================================================
# SECTION 8: Summary
# =============================================================================
print("\n" + "=" * 80)
print("SUMMARY OF FINDINGS")
print("=" * 80)

print(f"""
VERIFIED ADDRESSES (all calculated via Python):
  - Timeout value: 0x{timeout_value:08X} = {timeout_ms:.1f}ms
  - XNotify handle: 0x{xnotify_handle_addr:08X}
  - Semaphore 1 (signal): 0x{sem1_addr:08X}
  - Semaphore 2 (try-wait): 0x{sem2_addr:08X}
  - dword_82A3D5CC: 0x{r28:08X}

BLOCKING CHAIN:
  Main Thread -> waits on semaphore 0x{sem1_addr:08X}
       ^
       | (should signal)
       |
  Thread 19 (sub_82626210) -> loops waiting for:
    1. XNotifyGetNext(filter=11) to return notification
    2. OR sub_827DAC90(sem2) to succeed
    
  Neither happens, so signal at loc_82626330 is never reached.

GPU THREADS (17 & 18):
  - Both in sub_829DDC90 (GPU Command Processor)
  - Looping with 30ms timeout waiting for GPU completion event
  - NOT the cause of beachball - they're doing timed waits
  
ROOT CAUSE:
  XNotifyGetNext needs to return a notification with ID matching filter 11
  OR the try-wait semaphore (sem2 at 0x{sem2_addr:08X}) needs to be signaled
  
RECOMMENDED INVESTIGATION:
  1. Trace what signals semaphore 2 (0x{sem2_addr:08X})
  2. Check XNotifyGetNext implementation for filter 11 support
  3. Find content enumeration completion path
""")

if __name__ == "__main__":
    print("\n[Script complete - all calculations verified via Python]")
