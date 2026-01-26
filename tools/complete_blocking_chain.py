#!/usr/bin/env python3
"""
Complete Blocking Chain Analysis - Startup Hang Root Cause
All calculations verified from actual PPC code in ppc_recomp.*.cpp
"""

def lis(imm16):
    """PPC lis instruction: Load Immediate Shifted"""
    if imm16 & 0x8000:
        imm32 = imm16 | 0xFFFF0000
    else:
        imm32 = imm16
    result = (imm32 << 16) & 0xFFFFFFFF
    if result & 0x80000000:
        result_signed = result - 0x100000000
    else:
        result_signed = result
    return result_signed

def to_u32(val):
    """Convert signed value to unsigned 32-bit"""
    return val & 0xFFFFFFFF

print("=" * 80)
print("COMPLETE BLOCKING CHAIN ANALYSIS")
print("Startup Hang Root Cause - Python Verified from PPC Code")
print("=" * 80)

print("""
THREAD STATE SNAPSHOT (from LLDB):
==================================

Thread #19 (GPU Command Processor):
  Location: sub_829DDC90 -> KeWaitForSingleObject
  Status: BLOCKED on GPU work event with 30ms timeout
  Source: ppc_recomp.135.cpp:48016
  
Thread #20 (Content Enumeration):
  Location: sub_82626210 -> sub_827DAE18 (Sleep 16ms)
  Status: INFINITE LOOP - never signals main thread
  Source: ppc_recomp.71.cpp:26476
  
Main Thread:
  Location: sub_82625CA0 -> sub_827DACD8 (Wait INFINITE)
  Status: BLOCKED waiting for semaphore 0x83027628
  Source: ppc_recomp.71.cpp:25431
""")

print("\n" + "=" * 80)
print("VERIFIED ADDRESS CALCULATIONS")
print("=" * 80)

# Calculate all key addresses
r11_base = lis(-31998)
r29 = to_u32(r11_base + 20392)

sem1 = to_u32(r29 + 9856)  # Main thread waits on this
sem2 = to_u32(r29 + 9860)  # Try-wait semaphore
xnotify = to_u32(r29 + 9864)  # XNotify handle

print(f"""
Semaphore Address Calculations (from ppc_recomp.71.cpp:26310-26326):

  lis r11,-31998          => r11 = 0x{to_u32(r11_base):08X}
  addi r29,r11,20392      => r29 = 0x{r29:08X}
  
  Semaphore 1 (main waits): r29+9856 = 0x{sem1:08X}
  Semaphore 2 (try-wait):   r29+9860 = 0x{sem2:08X}
  XNotify handle:           r29+9864 = 0x{xnotify:08X}
""")

print("\n" + "=" * 80)
print("BLOCKING CHAIN FLOW")
print("=" * 80)

print("""
┌─────────────────────────────────────────────────────────────────────────────┐
│                         BLOCKING CHAIN DIAGRAM                              │
└─────────────────────────────────────────────────────────────────────────────┘

MAIN THREAD                         CONTENT ENUM THREAD (#20)
────────────                        ─────────────────────────
     │                                       │
     ▼                                       ▼
sub_82625CA0(arg=1)                  sub_82626210 (INFINITE LOOP)
     │                                       │
     │  if (arg != 0)                        ├──► XNotifyGetNext(0x83027630, 11)
     │      ▼                                │        │
     │  sub_827DACD8                         │        └──► Returns 0 (no notification)
     │  (Wait INFINITE on                    │
     │   semaphore 0x83027628)               ├──► sub_827DAC90(0x8302762C)
     │      │                                │        │
     │      │  ◄─ BLOCKED FOREVER ─►         │        └──► Returns 0 (not signaled)
     │                                       │
     │                                       ├──► Sleep 16ms
     │                                       │
     │                                       └──► LOOP BACK (never reaches signal)

WHERE THE SIGNAL SHOULD COME FROM:
─────────────────────────────────
sub_82268770 (Content Manager Callback)
     │
     ├──► sub_82672970() - Returns content item
     │        │
     │        └──► sub_82213C48() - Check if content ready
     │                  │
     │                  └──► Returns 0 during startup = NO CONTENT
     │
     ├──► if (result != 0)
     │        │
     │        └──► sub_82625C90() - SIGNAL semaphore 0x8302762C
     │                               (This would unblock content enum)
     │
     └──► NEVER CALLED because sub_82672970 returns 0

THE DEADLOCK:
─────────────
1. Main thread calls sub_82625CA0(1) during init
2. Main thread blocks on semaphore 0x83027628 (INFINITE wait)
3. Content enum thread is supposed to signal 0x83027628 when done
4. Content enum thread is stuck in XNotify/try-wait loop
5. XNotifyGetNext(filter=11) always returns 0 - no Xbox Live notifications
6. sub_827DAC90 try-wait on 0x8302762C always returns 0 - never signaled
7. sub_82625C90 (which signals 0x8302762C) is never called
   - It's only called from sub_82268770 when sub_82672970 returns non-zero
   - sub_82672970 returns 0 when sub_82213C48 returns 0 (no content ready)
""")

print("\n" + "=" * 80)
print("ROOT CAUSE ANALYSIS")
print("=" * 80)

print("""
ROOT CAUSE SUMMARY:
===================

The startup hang is caused by a CHICKEN-AND-EGG DEADLOCK in content enumeration:

1. MISSING XBOX LIVE NOTIFICATION:
   - XNotifyGetNext with filter=11 (XN_LIVE_CONNECTIONCHANGED) returns 0
   - On Xbox 360, this notification fires when Xbox Live connects/disconnects
   - In static recompilation, Xbox Live doesn't exist
   - The content enumeration thread expects this notification to proceed

2. MISSING SEMAPHORE SIGNAL:
   - Semaphore 0x8302762C is never signaled
   - sub_82625C90 (the signal function) is only called from sub_82268770
   - sub_82268770 only signals when sub_82672970 returns non-zero
   - sub_82672970 returns 0 when no content is ready

3. THE DEADLOCK CHAIN:
   - Main thread waits on semaphore 0x83027628 (INFINITE)
   - Content enum thread should signal 0x83027628 when done
   - Content enum thread is stuck waiting for:
     a) XNotify ID 11 (never generated)
     b) Semaphore 0x8302762C (never signaled)
   - Main thread never proceeds, game appears hung

GPU THREAD IS NOT THE ISSUE:
============================
- Thread #19 (GPU Command Processor) is working correctly
- It's waiting on GPU work events with 30ms timeout
- The 30ms timeout loop is NORMAL behavior
- VBlank callbacks fire at 60Hz proving rendering works
""")

print("\n" + "=" * 80)
print("POTENTIAL SOLUTION PATHS")
print("=" * 80)

print("""
POTENTIAL SOLUTIONS (FOR RESEARCH - NOT IMPLEMENTING):

OPTION A: Generate XNotify ID 11 at startup
   - Call XamNotifyEnqueueEvent(11, ...) during initialization
   - This would allow content enum thread to see the notification
   - Risk: May have side effects if game expects specific params

OPTION B: Signal semaphore 0x8302762C during startup  
   - Find where 0x8302762C handle is created
   - Signal it after creation to unblock content enum
   - Risk: May bypass necessary initialization

OPTION C: Make sub_82625CA0 non-blocking when arg=1
   - Hook sub_82625CA0 to not call sub_827DACD8 (infinite wait)
   - Instead call sub_827DAC90 (try-wait) and return immediately
   - Risk: May cause race conditions

OPTION D: Make XNotifyGetNext return true for filter=11
   - Hook XNotifyGetNext to return true when dwMsgFilter == 11
   - Generate a fake "connection changed" notification
   - This is the CLEANEST solution as it emulates Xbox Live behavior

RECOMMENDED APPROACH: Option D
   - Most architecturally correct - emulates missing Xbox Live behavior
   - Content enumeration was designed expecting Xbox Live to exist
   - Faking the "connected" notification allows normal code flow
""")

print("\n" + "=" * 80)
print("SOURCE CODE REFERENCES")
print("=" * 80)

print("""
KEY SOURCE LOCATIONS:
====================

sub_82626210 (Content Enum Loop):
  File: ppc_recomp.71.cpp
  Lines: 26292-26479
  Key: XNotifyGetNext at 26333, try-wait at 26351, signal at 26462

sub_82625CA0 (Main Thread Block):
  File: ppc_recomp.71.cpp  
  Lines: 25408-25454
  Key: Infinite wait at 25431

sub_82625C90 (Signal Semaphore 2):
  File: ppc_recomp.71.cpp
  Lines: 25392-25402
  Key: Signals 0x8302762C via sub_827DAD60

sub_82268770 (Content Callback):
  File: ppc_recomp.17.cpp
  Lines: 11287-11357
  Key: Calls sub_82625C90 only if sub_82672970 != 0

sub_82672970 (Get Content):
  File: ppc_recomp.75.cpp
  Lines: 22467-22566
  Key: Returns 0 if sub_82213C48 returns 0

sub_829DDC90 (GPU Worker):
  File: ppc_recomp.135.cpp
  Lines: 47907-48047
  Key: 30ms timeout loop, NOT the hang cause

XNotifyGetNext Implementation:
  File: LibertyRecomp/kernel/xam.cpp
  Lines: 166-205
  Key: Returns false if no matching notification
""")

print("\n" + "=" * 80)
print("RESEARCH COMPLETE")
print("=" * 80)
