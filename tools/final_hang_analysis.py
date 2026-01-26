#!/usr/bin/env python3
"""
FINAL ANALYSIS: LibertyRecomp Startup Hang/Beachball Issue
============================================================
Based on extensive LLDB sampling and decompiled source analysis
"""

def calculate_semaphore_address():
    """
    Calculate the semaphore address from PPC code in ppc_recomp.71.cpp:
    lis r11,-31998  => r11 = -31998 << 16 = 0x83020000
    lwz r3,30248(r11) => load from r11 + 30248 = 0x83020000 + 0x7628
    """
    lis_value = -31998
    offset = 30248
    
    # lis loads into upper 16 bits (shifted left 16)
    base = (lis_value & 0xFFFF) << 16
    # Sign extend if negative
    if lis_value < 0:
        base = 0x100000000 + (lis_value << 16)
    
    address = (base + offset) & 0xFFFFFFFF
    
    print(f"=== Semaphore Address Calculation ===")
    print(f"lis r11, -31998:")
    print(f"  -31998 in hex = 0x{(-31998 & 0xFFFF):04X}")
    print(f"  Shifted left 16 = 0x{base:08X}")
    print(f"Offset = {offset} = 0x{offset:04X}")
    print(f"Final address = 0x{base:08X} + 0x{offset:04X} = 0x{address:08X}")
    return address

def calculate_timeout():
    """Calculate GPU command processor timeout"""
    timeout_100ns = -300000
    timeout_ms = abs(timeout_100ns) / 10000
    timeout_sec = timeout_ms / 1000
    
    print(f"\n=== GPU Command Processor Timeout ===")
    print(f"Raw value: {timeout_100ns} (100ns units)")
    print(f"In milliseconds: {timeout_ms} ms")
    print(f"In seconds: {timeout_sec} sec")
    return timeout_ms

def analyze_sample_counts():
    """Analyze sample counts from LLDB sampling"""
    samples = {
        "sub_829DDC90 (GPU Cmd Proc)": 725,
        "KeResetEvent": 408,
        "pthread_mutex_lock": 562,
        "semaphore_wait_trap": 9380,
        "__workq_kernreturn": 9360,
        "__ulock_wait": 4690,
        "__semwait_signal": 4630,
    }
    
    total = sum(samples.values())
    
    print(f"\n=== Sample Counts from LLDB ===")
    print(f"{'Function':<35} {'Samples':>10} {'%':>8}")
    print("-" * 55)
    for func, count in sorted(samples.items(), key=lambda x: -x[1]):
        pct = (count / total) * 100
        print(f"{func:<35} {count:>10} {pct:>7.1f}%")
    print("-" * 55)
    print(f"{'TOTAL':<35} {total:>10}")

def print_deadlock_chain():
    """Print the complete deadlock chain"""
    print("""
================================================================================
DEADLOCK CHAIN ANALYSIS
================================================================================

THREAD 1: MAIN THREAD (Thread_9221316)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Call Stack:
  main
    └─ GuestThread::Start
        └─ _xstart
            └─ sub_8218BEA8
                └─ sub_827D89B8
                    └─ sub_8218BEB0
                        └─ sub_821200D0 (Main loop entry)
                            └─ sub_82121E80
                                └─ sub_82121C10
                                    └─ sub_82121548
                                        └─ sub_8220E700
                                            └─ sub_8226A178
                                                └─ sub_82269140
                                                    └─ sub_82625CA0(a1=1)  ← BLOCKING POINT
                                                        └─ sub_827DACD8(dword_83027628)
                                                            └─ sub_829A2380(sem, -1)
                                                                └─ NtWaitForSingleObjectEx
                                                                    └─ Semaphore::Wait
                                                                        └─ __ulock_wait [BLOCKED]

Status: WAITING for semaphore at 0x83027628 to be signaled


THREAD 2: ENUMERATE CONTENT THREAD (via sub_827DAE40)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Function: sub_82626210 (infinite loop)

    while(1) {
        if (XNotifyGetNext(dword_83027630, 0xB, &v4, &v3))
            v0 = 1;                    // ← Never happens, returns FALSE
        
        if (v0 || sub_827DAC90(dword_8302762C))
            break;                     // ← Never breaks
        
        sub_827DAE18(16);              // ← Sleep 16ms and retry
    }
    
    // NEVER REACHED:
    sub_827DAD60(dword_83027628);      // ← Would signal main thread

Status: STUCK IN LOOP - never signals dword_83027628


THREAD 3+: GPU COMMAND PROCESSOR THREADS (sub_829DDC90)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Function: sub_829DDC90 (GPU command buffer processor)

    while(1) {
        // Wait 30ms for GPU work
        if (KeWaitForSingleObject(..., timeout=-300000) == 258) {
            // Timeout - do GPU processing in critical section
            RtlEnterCriticalSection(...)
            sub_829D5380(...);
            sub_829D5388(...);
            RtlLeaveCriticalSection(...);
        }
        
        KeResetEvent(...);             // ← 408 samples here (heavy contention)
        
        if (*(r26 + 4) == 0)          // ← Exit condition NEVER MET
            break;
        
        sub_829DD978(...);             // Process commands
    }

Status: SPINNING - 725+ samples, exit condition never satisfied
""")

def print_root_cause():
    """Print the root cause analysis"""
    print("""
================================================================================
ROOT CAUSE ANALYSIS
================================================================================

PRIMARY ISSUE: Content Enumeration Never Completes
─────────────────────────────────────────────────
1. Main thread calls sub_82625CA0(a1=1) during initialization
2. This waits on semaphore dword_83027628 with INFINITE timeout
3. Semaphore should be signaled by "Enumerate Content" thread (sub_82626210)
4. But sub_82626210 is stuck in its while(1) loop because:
   
   a) XNotifyGetNext(dword_83027630, 0xB, ...) returns FALSE
      - No notifications with ID 0xB are being enqueued
      - The XamNotifyEnqueueEvent() function is never called with relevant events
   
   b) sub_827DAC90(dword_8302762C) returns FALSE  
      - This semaphore is never signaled
      - It should be signaled by sub_82625C90() 
      - Which is called from sub_82268770() during content init
      - But sub_82268770() requires sub_82672970() to return non-NULL
      - sub_82672970() returns NULL if content system not initialized

SECONDARY ISSUE: GPU Command Processor Spinning
────────────────────────────────────────────────
- sub_829DDC90 threads consuming CPU with tight event reset loops
- Exit condition (*(r26+4)==0) is never met during init phase
- This isn't the cause of the hang, but contributes to beachball


RELATED SYMPTOMS:
─────────────────
- [RACE_FIX] sub_82169B00 timeouts: Audio manager pointer NULL at 0x83137CA8
- VBlank callbacks continuing to fire (system not fully hung)
- NtWaitEx calls progressing normally
""")

def print_key_addresses():
    """Print all key addresses"""
    addresses = {
        "dword_83027628": (0x83027628, "Semaphore - main thread waits here"),
        "dword_8302762C": (0x8302762C, "Semaphore - Enumerate Content waits here"),
        "dword_83027630": (0x83027630, "XNotify listener handle"),
        "dword_83051378": (0x83051378, "Content system state array"),
        "dword_82A22D04": (0x82A22D04, "User index for content"),
        "dword_83137CA8": (0x83137CA8, "Audio manager pointer (NULL)"),
    }
    
    print("\n=== Key Memory Addresses ===")
    print(f"{'Symbol':<20} {'Address':<12} {'Description'}")
    print("-" * 70)
    for name, (addr, desc) in addresses.items():
        print(f"{name:<20} 0x{addr:08X}  {desc}")

def print_functions():
    """Print key functions"""
    functions = [
        ("sub_829DDC90", 0x829DDC90, "GPU Command Processor thread loop"),
        ("sub_82626210", 0x82626210, "Enumerate Content thread loop"),
        ("sub_82625CA0", 0x82625CA0, "Content sync - waits on semaphore"),
        ("sub_827DACD8", 0x827DACD8, "Wait semaphore (infinite timeout)"),
        ("sub_827DAD60", 0x827DAD60, "Signal semaphore (release)"),
        ("sub_827DAC90", 0x827DAC90, "Try-wait semaphore (non-blocking)"),
        ("sub_82625C90", 0x82625C90, "Signals dword_8302762C"),
        ("sub_82268770", 0x82268770, "Content init - calls sub_82625C90"),
        ("sub_82672970", 0x82672970, "Get content object (returns NULL)"),
    ]
    
    print("\n=== Key Functions ===")
    print(f"{'Function':<20} {'Address':<12} {'Description'}")
    print("-" * 70)
    for name, addr, desc in functions:
        print(f"{name:<20} 0x{addr:08X}  {desc}")

def main():
    print("=" * 80)
    print("LIBERTYRECOMP STARTUP HANG - FINAL RESEARCH FINDINGS")
    print("=" * 80)
    
    sem_addr = calculate_semaphore_address()
    calculate_timeout()
    analyze_sample_counts()
    print_key_addresses()
    print_functions()
    print_deadlock_chain()
    print_root_cause()
    
    print("""
================================================================================
SUMMARY
================================================================================

The startup hang is caused by a DEADLOCK between:

1. MAIN THREAD: Blocked waiting on semaphore 0x83027628
   - Location: sub_82625CA0 → sub_827DACD8 → Semaphore::Wait

2. ENUMERATE CONTENT THREAD: Stuck in loop, never signals the semaphore
   - Location: sub_82626210 (while loop)
   - Reason: XNotifyGetNext returns FALSE, dword_8302762C not signaled

3. GPU COMMAND PROCESSOR THREADS: Spinning in event reset loop
   - Location: sub_829DDC90
   - Reason: Exit condition *(r26+4)==0 never met

The content enumeration system (sub_82672970) is returning NULL, preventing
the initialization flow from proceeding and signaling the required semaphores.

================================================================================
""")

if __name__ == "__main__":
    main()
