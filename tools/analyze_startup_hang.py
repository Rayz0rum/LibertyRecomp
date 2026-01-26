#!/usr/bin/env python3
"""
Analysis of LibertyRecomp Startup Hang/Beachball Issue
Based on LLDB sampling and decompiled source analysis
"""

# Key addresses from decompiled source
ADDRESSES = {
    "dword_83027628": 0x83027628,  # Semaphore - main thread waits on this
    "dword_8302762C": 0x8302762C,  # Semaphore - Enumerate Content thread waits on this
    "dword_83027630": 0x83027630,  # XNotify listener handle
    "dword_83137CA8": 0x83137CA8,  # Audio manager pointer (NULL causing timeout)
}

# Key functions involved in the deadlock
FUNCTIONS = {
    "sub_829DDC90": {
        "address": 0x829DDC90,
        "description": "GPU Command Processor Thread - loops waiting for events",
        "samples": 725,
        "issue": "Spinning in tight loop resetting events, calling KeResetEvent repeatedly"
    },
    "sub_82626210": {
        "address": 0x82626210,
        "description": "Enumerate Content Thread - waits for notifications",
        "issue": "Never signals dword_83027628 because XNotifyGetNext returns false"
    },
    "sub_82625CA0": {
        "address": 0x82625CA0,
        "description": "Semaphore wait wrapper - main thread blocks here",
        "issue": "Waits on dword_83027628 which is never signaled"
    },
    "sub_827DACD8": {
        "address": 0x827DACD8,
        "description": "Wait on semaphore with infinite timeout (-1)",
        "calls": "sub_829A2380(semaphore, -1)"
    },
    "sub_827DAD60": {
        "address": 0x827DAD60,
        "description": "Signal semaphore (release)",
        "calls": "sub_829A2290()"
    },
    "sub_82625C90": {
        "address": 0x82625C90,
        "description": "Signals dword_8302762C - would wake Enumerate Content thread",
        "calls": "sub_827DAD60(dword_8302762C)"
    },
}

# Thread analysis from sample
THREADS = {
    "Main Thread (Thread_9221316)": {
        "state": "BLOCKED",
        "location": "Semaphore::Wait -> __ulock_wait",
        "call_stack": [
            "main",
            "GuestThread::Start",
            "_xstart",
            "sub_8218BEA8",
            "sub_827D89B8",
            "sub_8218BEB0",
            "sub_821200D0",  # Main loop entry
            "sub_82121E80",
            "sub_82121C10",
            "sub_82121548",
            "sub_8220E700",
            "sub_8226A178",
            "sub_82269140",
            "sub_82625CA0",  # BLOCKS HERE - waits on dword_83027628
            "sub_827DACD8",
            "NtWaitForSingleObjectEx",
            "Semaphore::Wait",
        ],
        "waiting_for": "dword_83027628 to be signaled"
    },
    "GPU Command Processor (multiple threads)": {
        "state": "SPINNING/WAITING",
        "location": "sub_829DDC90 -> KeResetEvent/KeWaitForSingleObject",
        "samples": 1561 + 725,  # Combined samples
        "issue": "Tight loop: waits with 30ms timeout, resets event, repeats",
        "exit_condition": "*(r26 + 4) == 0 - never becomes 0"
    },
    "Enumerate Content (Thread in sub_82626210)": {
        "state": "SLEEPING",
        "location": "KeDelayExecutionThread (via sub_827DAE18)",
        "loop_condition": "XNotifyGetNext returns false, dword_8302762C not signaled",
        "issue": "Never reaches code that signals dword_83027628"
    },
}

# Calculate timeout values
def analyze_timeout():
    """Analyze the timeout value in sub_829DDC90"""
    timeout_100ns = -300000  # From decompiled code
    timeout_ms = abs(timeout_100ns) / 10000
    print(f"GPU Command Processor timeout: {timeout_100ns} (100ns units)")
    print(f"  = {timeout_ms} ms")
    print(f"  = {timeout_ms / 1000} seconds")
    return timeout_ms

# Calculate semaphore addresses
def analyze_addresses():
    """Calculate and verify key memory addresses"""
    print("\n=== Key Memory Addresses ===")
    for name, addr in ADDRESSES.items():
        print(f"{name}: 0x{addr:08X}")
    
    # Calculate offset between semaphores
    diff = ADDRESSES["dword_8302762C"] - ADDRESSES["dword_83027628"]
    print(f"\nOffset between semaphores: {diff} bytes")

# Analyze the deadlock chain
def analyze_deadlock():
    """Document the deadlock chain"""
    print("\n=== DEADLOCK CHAIN ANALYSIS ===")
    print("""
    MAIN THREAD                         ENUMERATE CONTENT THREAD
    -----------                         ------------------------
         |                                       |
         v                                       v
    sub_82625CA0(a1=1)                   sub_82626210() [infinite loop]
         |                                       |
         v                                       v
    sub_827DACD8(dword_83027628)         while(1) {
         |                                   XNotifyGetNext() -> returns FALSE
         v                                   sub_827DAC90(dword_8302762C) -> FALSE
    sub_829A2380(sem, -1)                    sub_827DAE18(16) // sleep 16ms
         |                                   [loop back]
         v                               }
    NtWaitForSingleObjectEx                  |
         |                               [NEVER reaches sub_827DAD60(dword_83027628)]
         v
    Semaphore::Wait
         |
         v
    __ulock_wait  [BLOCKED FOREVER]
    
    
    ROOT CAUSE: The Enumerate Content thread is stuck in its loop because:
    1. XNotifyGetNext(dword_83027630, 0xB, ...) returns FALSE - no notifications queued
    2. sub_827DAC90(dword_8302762C) returns FALSE - semaphore not signaled
    
    The semaphore dword_8302762C should be signaled by sub_82625C90(),
    which is called from sub_82268770() during content initialization.
    
    sub_82268770() is called when:
    - Content enumeration succeeds (sub_82672970 returns non-NULL)
    - Save game loading proceeds
    
    The issue: Content enumeration may be failing or never being triggered,
    causing the Enumerate Content thread to loop forever without signaling
    dword_83027628 that the main thread is waiting on.
    """)

def analyze_gpu_spin():
    """Analyze the GPU command processor spin"""
    print("\n=== GPU COMMAND PROCESSOR SPIN ANALYSIS ===")
    print("""
    sub_829DDC90 is a GPU command buffer processor thread that:
    
    1. Calls sub_829A0B50(-2, SignalState) - wait with infinite timeout
    2. Enters infinite while(1) loop at loc_829DDCB0
    3. Sets up timeout: -300000 (30ms in 100ns units)
    4. Checks if work pending: a1[60] != a1[56]
    5. If equal (no work), calls KeWaitForSingleObject with timeout
    6. If timeout (returns 258), enters critical section, does GPU work
    7. Resets event with KeResetEvent
    8. Checks exit condition: *(r26 + 4) == 0
    9. If not 0, calls sub_829DD978 and loops back
    
    EXIT CONDITION NEVER MET:
    - r26 = *(r28 + 0) at start of each loop
    - Exit requires *(r26 + 4) == 0
    - This value is never set to 0 during normal init
    
    SAMPLES: 725 directly in sub_829DDC90, 1561+ in the loop
    - Heavy mutex contention in KeResetEvent (408 samples)
    - This is CPU spinning, causing beachball
    """)

def main():
    print("=" * 60)
    print("LIBERTYRECOMP STARTUP HANG ANALYSIS")
    print("=" * 60)
    
    timeout = analyze_timeout()
    analyze_addresses()
    analyze_deadlock()
    analyze_gpu_spin()
    
    print("\n" + "=" * 60)
    print("SUMMARY OF FINDINGS")
    print("=" * 60)
    print("""
    PRIMARY BLOCKING POINT:
    - Main thread blocked on semaphore at 0x83027628
    - Waiting for Enumerate Content thread to signal it
    
    SECONDARY ISSUE (CPU SPIN):
    - GPU Command Processor threads (sub_829DDC90) spinning
    - 725+ samples in tight loop with KeResetEvent
    - Exit condition (*(r26+4)==0) never satisfied
    
    ROOT CAUSE HYPOTHESIS:
    1. Content enumeration not completing (XNotifyGetNext returns false)
    2. No notifications being enqueued to the listener
    3. dword_8302762C semaphore never signaled
    4. Therefore dword_83027628 never signaled
    5. Main thread blocked forever
    
    RELATED ISSUE:
    - Audio manager pointer at 0x83137CA8 is NULL
    - Causing 5-second timeouts in sub_82169B00
    - This may be symptom of same initialization failure
    
    POTENTIAL FIX AREAS:
    1. Check why XNotifyGetNext never returns notifications
    2. Check why sub_82625C90() is never called to signal dword_8302762C
    3. Check if sub_82268770() / content enumeration is failing
    4. Consider if GPU command processor exit condition is broken
    """)

if __name__ == "__main__":
    main()
