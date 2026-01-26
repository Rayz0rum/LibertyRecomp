# Semaphore Signal Accumulation Root Cause Analysis

## Issue Summary

After the kernel phase transition from Init → Runtime, semaphore signals accumulate on handle `0xC285A450` with counts increasing (3→4→5→6) and "nothing else happening" between releases.

## Key Log Evidence

```
[KernelPhase_EnterRuntime] [KERNEL_PHASE] Init -> Runtime
[sub_821200D0] [KERNEL_PHASE] Forced Init -> Runtime at sub_821200D0 (main loop entry)
[sub_827DAD60] [SEM_SIGNAL] sub_827DAD60 #14 SYNC_TABLE handle=0xC285A450 release=1 caller=0x82196774
[NtReleaseSemaphore] #16 handle=0xC285A450 release=1 count=3/32767
[NtReleaseSemaphore] #17 handle=0xC285A450 release=1 count=4/32767
[NtReleaseSemaphore] #18 handle=0xC285A450 release=1 count=5/32767
[NtReleaseSemaphore] #19 handle=0xC285A450 release=1 count=6/32767
```

**Critical observation**: Count starts at 3, not 1 — indicating pre-existing signals from Init phase.

---

## RMPTFX Synchronization Pattern

### Semaphore Structure (RMPTFX object at base ~0xC2854F94)

| Offset | Name | Purpose |
|--------|------|---------|
| +21684 | thread_handle | RMPTFX worker thread |
| +21688 | wait_sem | RMPTFX waits on this before starting work |
| +21692 | signal_sem (0xC285A450) | RMPTFX signals when work is complete |
| +21696 | termination_marker | Set to -999.0 to stop thread |
| +21748 | active_flag | Controls whether consumer waits |

### Thread Roles

**RMPTFX Update Thread (`sub_821966D0` at 0x821966D0)**:
```c
for (i = result; *(float*)(i + 21696) != -999.0; 
     result = sub_827DAD60(*(DWORD*)(i + 21692)))  // Signal signal_sem
{
    sub_827DACD8(*(void**)(i + 21688));  // WAIT on wait_sem
    // ... do particle effects work ...
}
```

**Main Loop Producer (`sub_82195588` via render path)**:
- Sets `byte[+21748] = 1` (active flag)
- Signals `wait_sem` (+21688) to wake RMPTFX thread

**Main Loop Consumer (`sub_821948F0` via `sub_82192C28`)**:
```c
if (*(_BYTE*)(a1 + 21748))           // If active flag set
    sub_827DACD8(*(void**)(a1 + 21692));  // WAIT on signal_sem
*(_BYTE*)(a1 + 21748) = 0;           // Clear active flag
```

### Expected Flow (Per Frame)

1. Main loop: `sub_82195588` sets flag=1, signals wait_sem
2. RMPTFX: wakes on wait_sem, does work, signals signal_sem
3. Main loop: `sub_821948F0` sees flag=1, waits on signal_sem
4. Main loop: consumes signal, clears flag=0
5. **Result**: signal_sem count balanced (1 → 0)

---

## Root Cause: Fail-Open Pre-Signaling

### Location
`@/Users/Ozordi/Downloads/LibertyRecomp/LibertyRecomp/kernel/imports.cpp:6174-6187`

```cpp
// CASE 2: Blocking wait during Init/Boot phase
if (ShouldFailOpenWait()) {
    if (handle != 0) {
        SyncObject *syncObj = SyncTable_GetOrCreate(handle, SyncType::Semaphore, callerLR);
        if (syncObj) {
            syncObj->Signal(1);  // PRE-SIGNAL to prevent init hangs
        }
    }
    ctx.r3.u32 = 1;
    return;
}
```

### Mechanism

1. **During Init Phase**: Every semaphore WAIT attempt triggers `syncObj->Signal(1)`
2. **Effect on wait_sem (+21688)**: Accumulates N signals from N wait attempts
3. **When Runtime Starts**: RMPTFX thread has N queued signals to process
4. **Result**: Thread runs N iterations rapidly, each signaling signal_sem

### Why Signals Accumulate

1. RMPTFX processes backlog of wait_sem signals (from Init phase pre-signaling)
2. Each iteration signals signal_sem (+21692)
3. Main loop either:
   - Not running yet (still in transition)
   - `byte[+21748] == 0` so consumer skips wait
4. **signal_sem count increases unchecked**: 3 → 4 → 5 → 6 → ...

---

## Call Chain Analysis

### Render Path (sets active flag, signals wait_sem)
```
sub_821200D0 (main loop)
  └─ if (byte_83137BB5)
       └─ sub_8222ADE0 (render)
            └─ sub_82223568
                 └─ sub_821B9148
                      └─ sub_82195588  ← Sets byte[+21748]=1, signals wait_sem
```

### Consumer Path (waits on signal_sem)
```
sub_821200D0 (main loop)
  └─ sub_82192C28 (end of each iteration)
       └─ sub_821948F0  ← IF byte[+21748]==1: waits on signal_sem
```

### Producer Thread
```
sub_821966D0 (RMPTFX Update thread)
  └─ Loop:
       ├─ sub_827DACD8(wait_sem)   ← WAIT
       ├─ ... work ...
       └─ sub_827DAD60(signal_sem) ← SIGNAL (caller 0x82196774)
```

---

## Why "Nothing Else Happening"

The logs show rapid semaphore releases with no interleaved activity. This indicates:

1. **Main loop is NOT running or is blocked**
   - If running, we'd see other function calls between releases
   
2. **RMPTFX thread running in tight loop**
   - Processing backlog of pre-signaled wait_sem
   - No actual blocking waits occurring

3. **Possible blockers for main loop**:
   - `sub_8218C2C0()` returning non-zero (exit condition)
   - Render thread synchronization issue
   - Lock contention with another subsystem

---

## Summary

| Factor | Status |
|--------|--------|
| Root cause identified | ✅ Fail-open pre-signaling during Init |
| Signal source | RMPTFX thread (`sub_821966D0`) |
| Signal target | `0xC285A450` (signal_sem at +21692) |
| Consumer | `sub_821948F0` (not running or skipping wait) |
| Caller address | `0x82196774` (within `sub_821966D0`) |

**The fundamental issue is a synchronization mismatch**: The fail-open logic creates a backlog of signals during Init, but the Runtime phase consumer expectations assume 1:1 signal-to-consume ratio. The RMPTFX thread drains its wait_sem backlog faster than the main loop can consume signal_sem signals.
