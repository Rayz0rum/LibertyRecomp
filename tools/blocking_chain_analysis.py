#!/usr/bin/env python3
"""
Complete Blocking Chain Analysis for GTA IV Static Recompilation
All address calculations performed via Python for verification.
"""

def lis(val):
    """PowerPC lis instruction: load immediate shifted (16 bits << 16)"""
    result = (val & 0xFFFF) << 16
    if val < 0:
        result = (0xFFFF0000 & (val << 16)) | 0x00000000
        if result & 0x80000000:
            result = result - 0x100000000
    return result & 0xFFFFFFFF

def signed32(val):
    """Convert to signed 32-bit"""
    if val & 0x80000000:
        return val - 0x100000000
    return val

print("=" * 80)
print("COMPLETE BLOCKING CHAIN ANALYSIS")
print("GTA IV Static Recompilation - Startup Hang Investigation")
print("=" * 80)

# =============================================================================
# SECTION 1: Address Calculations from PPC Code
# =============================================================================
print("\n## SECTION 1: ADDRESS CALCULATIONS (Python Verified)")
print("-" * 60)

# From ppc_recomp.71.cpp sub_82626210 (Enumerate Content Thread)
lis_31997 = lis(-31997)
lis_31998 = lis(-31998)
lis_32092 = lis(-32092)

r27_stru_83028820 = (lis_31997 + (-30688)) & 0xFFFFFFFF
r29_semaphore_base = (lis_31998 + 20392) & 0xFFFFFFFF
r28_dword_82A3D5CC = (lis_32092 + (-10804)) & 0xFFFFFFFF
r26_stru_83028800 = (lis_31997 + (-30720)) & 0xFFFFFFFF

xnotify_handle = (r29_semaphore_base + 9864) & 0xFFFFFFFF
semaphore_2_trywait = (r29_semaphore_base + 9860) & 0xFFFFFFFF
semaphore_1_signal = (r29_semaphore_base + 9856) & 0xFFFFFFFF

print(f"lis(-31997) = 0x{lis_31997:08X}")
print(f"lis(-31998) = 0x{lis_31998:08X}")
print(f"lis(-32092) = 0x{lis_32092:08X}")
print()
print(f"r27 (stru_83028820) = 0x{r27_stru_83028820:08X}")
print(f"r29 (semaphore base) = 0x{r29_semaphore_base:08X}")
print(f"r28 (dword_82A3D5CC) = 0x{r28_dword_82A3D5CC:08X}")
print(f"r26 (stru_83028800) = 0x{r26_stru_83028800:08X}")
print()
print(f"XNotify handle (dword_83027630) = r29 + 9864 = 0x{xnotify_handle:08X}")
print(f"Semaphore 2 (dword_8302762C) = r29 + 9860 = 0x{semaphore_2_trywait:08X}")
print(f"Semaphore 1 (dword_83027628) = r29 + 9856 = 0x{semaphore_1_signal:08X}")

# =============================================================================
# SECTION 2: Complete Blocking Chain from IDA Pseudo-code
# =============================================================================
print("\n\n## SECTION 2: COMPLETE BLOCKING CHAIN (IDA Pseudo-code Verified)")
print("-" * 60)

print("""
THREAD HIERARCHY AND BLOCKING RELATIONSHIPS:

┌─────────────────────────────────────────────────────────────────────────┐
│ MAIN THREAD                                                             │
│ ─────────────────────────────────────────────────────────────────────── │
│ sub_82269140(a1, 1) called from many game functions                     │
│       ↓                                                                 │
│ sub_82625CA0(a1=1)                                                      │
│       ↓                                                                 │
│ sub_827DACD8(dword_83027628)  ← INFINITE WAIT on semaphore 1           │
│       ↓                                                                 │
│ BLOCKED - waiting for semaphore 1 (0x83027628) to be signaled          │
└───────────────────────────┬─────────────────────────────────────────────┘
                            │
                            │ (should be signaled by)
                            ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ THREAD 19: "Enumerate Content" (sub_82626210)                           │
│ ─────────────────────────────────────────────────────────────────────── │
│ while(1) {                                                              │
│   // Step 1: Check for XNotify with filter 0xB (11)                     │
│   if (XNotifyGetNext(dword_83027630, 0xB, &v4, &v3))                    │
│     v0 = 1;  // notification received                                  │
│                                                                         │
│   // Step 2: Check conditions to proceed                                │
│   if (v0 || sub_827DAC90(dword_8302762C))  // notify OR sem2 signaled  │
│     break;  // proceed to content enumeration                          │
│                                                                         │
│   // Step 3: Neither condition met - SLEEP AND LOOP                     │
│   sub_827DAE18(16);  // sleep 16ms                                     │
│   goto while(1);     // loop back                                       │
│ }                                                                       │
│                                                                         │
│ // Content enumeration code (NEVER REACHED in current state)            │
│ ...                                                                     │
│ sub_827DAD60(dword_83027628);  // SIGNAL semaphore 1 (would unblock!)  │
│ ...                                                                     │
└───────────────────────────┬─────────────────────────────────────────────┘
                            │
                            │ (needs one of)
                            ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ TWO POSSIBLE UNBLOCK CONDITIONS:                                        │
│ ─────────────────────────────────────────────────────────────────────── │
│                                                                         │
│ CONDITION A: XNotifyGetNext returns notification with filter 0xB        │
│   - Filter 0xB = 11 = bits 0,1,3 = System + Live + UI notifications    │
│   - Currently: XNotifyGetNext returns 0 (no notifications)              │
│   - WHY: No code is calling XamNotifyEnqueueEvent with matching ID      │
│                                                                         │
│ CONDITION B: sub_82625C90() is called (signals semaphore 2)             │
│   - sub_82625C90() calls sub_827DAD60(dword_8302762C)                  │
│   - Called from: sub_82268770() when sub_82672970() returns valid ptr   │
│   - sub_82672970() returns dword_83051378 (content device pointer)      │
│   - Currently: sub_82672970() returns NULL or invalid                   │
│   - WHY: Content device not initialized before thread checks it         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

GPU THREADS (17 & 18) - sub_829DDC90:
=====================================
NOT blocking the startup - doing 30ms timed waits in GPU command processor.
VBlank fires at 60Hz, proving rendering pipeline works.
""")

# =============================================================================
# SECTION 3: The Missing Link - Content Device Initialization
# =============================================================================
print("\n## SECTION 3: THE MISSING LINK - CONTENT DEVICE INITIALIZATION")
print("-" * 60)

print("""
sub_82672970() returns dword_83051378 (content device pointer).

CALL CHAIN TO SIGNAL SEMAPHORE 2:
  sub_82268770(a1) 
    ↓
  result = sub_82672970()   // Get content device
    ↓
  if (result != NULL) {
    sub_82625C80(sub_8296C148(result))
    sub_82625C90()          // ← SIGNALS SEMAPHORE 2!
    ...
  }

sub_82268770 IS CALLED FROM:
  1. sub_82268898(a1) - directly calls sub_82268770
  2. sub_822688D0(a1, a2) - calls when content comparison succeeds

THESE ARE CALLED WHEN:
  - Game tries to access content (save files, DLC)
  - Content enumeration finds matching content
  - User profile is signed in and content is mounted

THE PROBLEM:
  - sub_82672970() checks dword_82A22D04 against signed-in user index
  - If check fails or content device not initialized, returns NULL
  - sub_82268770 exits early, sub_82625C90 never called
  - Semaphore 2 never signaled
  - Thread 19 loops forever
  - Semaphore 1 never signaled
  - Main thread blocks forever
""")

# =============================================================================
# SECTION 4: XNotifyGetNext Filter Analysis
# =============================================================================
print("\n## SECTION 4: XNotifyGetNext FILTER ANALYSIS")
print("-" * 60)

filter_value = 0xB
print(f"Filter parameter: 0x{filter_value:X} = {filter_value}")
print()
print("Xbox 360 XNotify Message Areas (from XDK):")
print("  Bit 0 (1): XNOTIFY_SYSTEM")
print("  Bit 1 (2): XNOTIFY_LIVE") 
print("  Bit 3 (8): XNOTIFY_PARTY (or UI in some contexts)")
print()
print(f"Filter 0xB = {0xB} = 1 + 2 + 8 = System + Live + Party/UI")
print()
print("Relevant XNotify IDs the game may be waiting for:")
print("  0x00000009 - XN_SYS_PROFILESETTINGCHANGED (area 0)")
print("  0x0000000A - XN_SYS_STORAGEDEVICESCHANGED (area 0)")
print("  0x0000000B - XN_SYS_SIGNINCHANGED (area 0)")
print("  0x00000019 - XN_LIVE_CONNECTIONCHANGED (area 1)")
print()
print("CURRENT IMPLEMENTATION (xam.cpp:166-205):")
print("  XNotifyGetNext checks for exact match of dwMsgFilter against dwId")
print("  Filter 11 means: look for notification with ID == 11 (0xB)")
print("  This is XN_SYS_SIGNINCHANGED - profile sign-in state changed")

# =============================================================================
# SECTION 5: Root Cause Analysis
# =============================================================================
print("\n\n## SECTION 5: ROOT CAUSE ANALYSIS")
print("-" * 60)

print("""
IDENTIFIED ROOT CAUSES:

1. CONTENT DEVICE NOT INITIALIZED BEFORE ENUMERATE THREAD RUNS
   ─────────────────────────────────────────────────────────────
   The "Enumerate Content" thread (sub_82626210) starts before the
   content device (dword_83051378) is properly initialized.
   
   sub_82672970() returns NULL because:
   - dword_82A22D04 (expected user index) check fails, OR
   - dword_83051378 hasn't been set yet
   
   This prevents sub_82268770 from being called, which would signal
   semaphore 2 via sub_82625C90().

2. NO XNOTIFY NOTIFICATION MATCHING FILTER 0xB IS ENQUEUED
   ─────────────────────────────────────────────────────────────
   The game expects XN_SYS_SIGNINCHANGED (ID 0xB) to be sent when
   a user profile is signed in and ready.
   
   Current code only calls XamNotifyEnqueueEvent in:
   - XamContentFlush (ID 9)
   - Various XDM functions
   
   No code sends notification ID 11 (0xB) at startup.

3. CHICKEN-AND-EGG PROBLEM
   ─────────────────────────────────────────────────────────────
   - Main thread waits for semaphore 1 before accessing content
   - Thread 19 should signal semaphore 1 after content enumeration
   - Thread 19 waits for semaphore 2 OR XNotify before enumerating
   - Semaphore 2 is signaled when content is accessed successfully
   - Content can't be accessed until main thread continues
   - DEADLOCK
""")

# =============================================================================
# SECTION 6: Summary and Investigation Targets
# =============================================================================
print("\n## SECTION 6: SUMMARY AND INVESTIGATION TARGETS")
print("-" * 60)

print(f"""
VERIFIED ADDRESSES (Python calculated):
  Semaphore 1 (main thread waits): 0x{semaphore_1_signal:08X}
  Semaphore 2 (thread 19 checks):  0x{semaphore_2_trywait:08X}
  XNotify handle:                  0x{xnotify_handle:08X}
  Content device pointer:          0x83051378 (dword_83051378)
  User index check:                0x82A22D04 (dword_82A22D04)

BLOCKING CHAIN:
  Main Thread → waits on semaphore 1 (0x{semaphore_1_signal:08X})
       ↑
       │ (should be signaled by Thread 19)
       │
  Thread 19 → loops waiting for:
    - XNotifyGetNext(filter=0xB) to return notification, OR
    - sub_827DAC90(semaphore 2) to succeed
       ↑
       │ (semaphore 2 should be signaled by)
       │
  sub_82625C90() → called from sub_82268770() when:
    - sub_82672970() returns valid content device pointer
       ↑
       │ (requires)
       │
  Content device initialization → dword_83051378 must be set

INVESTIGATION TARGETS:
  1. Trace when/how dword_83051378 gets set
  2. Find what should call XamNotifyEnqueueEvent with ID 0xB (11)
  3. Trace sub_82672970() initialization path
  4. Check if sub_82268770 is being called and why it exits early
  
POTENTIAL FIX APPROACHES (for research, not implementation):
  A. Make XNotifyGetNext return notification ID 11 at startup
  B. Signal semaphore 2 after content initialization
  C. Initialize content device before "Enumerate Content" thread starts
  D. Trace actual Xbox 360 behavior for sign-in sequence
""")

if __name__ == "__main__":
    print("\n[Analysis complete - all calculations verified via Python]")
