# Semaphore Blocking Analysis: sub_82192C28

## Executive Summary

The main thread blocks indefinitely in `sub_82192C28` waiting on a semaphore at `byte_82AA3DD8 + 4024` (guest address `0x82AA4D90`). This semaphore is initialized with count=1, but after the first iteration of the game loop, it's decremented to 0 and no producer thread releases it.

---

## Key Findings

### 1. Blocking Location
- **Function**: `sub_82192C28` (PPC code at `ppc_recomp.5.cpp:31927`)
- **Called From**: `sub_821221A8` which passes `byte_82AA3DD8` as the structure pointer

### 2. Semaphore Mechanics
The structure at `byte_82AA3DD8` contains multiple synchronization primitives:

| Offset | Address | Type | Initial Value | Purpose |
|--------|---------|------|---------------|---------|
| +4012 | 0x82AA4D84 | Semaphore | count=0 | ? |
| +4016 | 0x82AA4D88 | Semaphore | count=0 | ? |
| +4020 | 0x82AA4D8C | Semaphore | count=0 | Consumer signal |
| +4024 | 0x82AA4D90 | **Semaphore** | **count=1** | **BLOCKING WAIT** |
| +4032 | 0x82AA4D98 | Counter | 0 | Frame counter |
| +4040 | 0x82AA4DA0 | Flag (byte) | 0 | Skip-wait flag |

### 3. Control Flow in sub_82192C28

```
ENTRY:
  1. if (flag_4040 == 0) 
       WAIT(semaphore_4024)  // Blocks here!
  
  2. ... do game loop work (60 Hz timing, subsystems) ...
  
  3. counter_4032 = 1 - counter_4032  // Toggle
  
  4. RELEASE(semaphore_4020)  // Signal consumers
  
EXIT:
  5. if (flag_4040 != 0)
       WAIT(semaphore_4024)  // Block again
```

### 4. Root Cause

**The semaphore at +4024 is initialized with count=1.** This means:
- First loop iteration: wait consumes it (count → 0), proceeds
- After first iteration: wait blocks forever (count = 0)

**No producer releases this semaphore!** Looking at all calls to `sub_827DAD60` in the file:
- Line 31864: Signals semaphore at +4012
- Line 32111: Signals semaphore at +4020
- Line 32287: Signals semaphore at +4024 (but only if flag)
- Line 32684, 32713: From `sub_82193000` (separate function)

### 5. The Missing Producer

The semaphore_4024 should be released by:
- **VBlank callback** or **GPU thread** after each frame
- OR **Worker threads** after completing resource loading

Looking at line 32287 in `sub_82192E00`:
```cpp
// lwz r3,4024(r29)
ctx.r3.u64 = PPC_LOAD_U32(ctx.r29.u32 + 4024);
// bl 0x827dacd8
sub_827DACD8(ctx, base);  // This WAITS, not releases
```

The release should come from `sub_82193000` which runs in a separate thread.

---

## Why This Worked on Xbox 360

On original hardware, timing was slower and the semaphore was likely released by:
1. VBlank interrupt callback
2. GPU completion signal
3. Resource streaming completion

In the recompilation, these async signals may not be firing because:
- VBlank is running but not signaling this specific semaphore
- Worker threads exist but aren't dispatching work
- The audio/streaming initialization failed earlier (dword_83137CA8 = NULL issue)

---

## LLDB Debug Commands

```lldb
# Set breakpoint on sub_82192C28
b sub_82192C28

# Inspect the structure at entry
memory read 0x182AA3DD8 -c 128

# Check the specific semaphore handle
memory read 0x182AA4D90 -c 8

# Check the skip-wait flag
memory read 0x182AA4DA0 -c 4

# Check semaphore count in kernel object
# (need to translate handle to object)
```

---

## Potential Fixes

### Option 1: Force flag_4040 = 1 to skip waits
Set `byte_82AA3DD8 + 4040 = 1` at startup to bypass the semaphore waits entirely. This is a hack but may work for initial boot.

### Option 2: Hook sub_82192C28 with timeout
Replace the infinite semaphore wait with a timed wait that returns after N milliseconds, allowing the loop to continue.

### Option 3: Fix the producer
Find and fix why the producer thread (likely `sub_82193000` or VBlank) isn't signaling the semaphore. This requires understanding what triggers the release.

### Option 4: Kernel FAIL-OPEN enhancement
The kernel already has a `ShouldFailOpenWait()` mechanism for boot phase. Ensure it's active and returning waits as successful during initialization.

---

## Producer Thread: sub_82193000

This function runs in a separate thread and is responsible for releasing the blocking semaphore at +4024.

### Call Chain
```
sub_82193B80 (Thread entry wrapper)
  → sub_82193000(byte_82AA3DD8)
```

### Control Flow (from decompiled pseudo-code)
```c
int __fastcall sub_82193000(int a1) {
    // Release semaphore at +4016 (startup signal)
    sub_827DAD60(*(_DWORD *)(a1 + 4016));
    
    // Main loop - continues until shutdown semaphore +4012 is signaled
    if (!sub_827DAC90(*(void **)(a1 + 4012))) {  // try-acquire shutdown sem
        do {
            // Lock critical section
            sub_827F1350(&stru_82AA5D78);
            
            // Check for pending work at +4048/+4064
            if (!sub_827DB198((a1 + 4048), (a1 + 4064))) {
                // Copy work from +4048 to +4064
            }
            
            sub_827F13B8(&stru_82AA5D78);  // Unlock
            
            if (*v2 || *(_DWORD *)(a1 + 4072))  // Check for work
                v6 = 1;
            else
                v6 = 0;
            
            v7 = *(void **)(a1 + 4020);  // Work semaphore
            
            if (v6) {  // HAS WORK
                v8 = sub_827DAC90(v7);  // Try to acquire work sem
                // Execute callback at +4076
                (*(callback)(a1 + 4076))(a1 + 4064);
                if (v8) {
                    // *** SIGNALS +4024 HERE ***
                    sub_82197050(&unk_82AAB2E0);
                    v9 = *(_DWORD *)(a1 + 4024);
                    counter = 1 - counter;
                    sub_827DAD60(v9);  // <== RELEASE SEMAPHORE +4024
                }
            } else {  // NO WORK
                sub_827DACD8(v7);  // Wait on work semaphore +4020
                sub_821DD3D8();
                sub_82196F60(&unk_82AAB2E0);
                sub_821EB1E0();
                
                // *** ALSO SIGNALS +4024 HERE ***
                v10 = *(_DWORD *)(a1 + 4024);
                counter = 1 - counter;
                sub_827DAD60(v10);  // <== RELEASE SEMAPHORE +4024
                sub_827DAE18(0);
            }
        } while (!sub_827DAC90(*(void **)(a1 + 4012)));
    }
    // Cleanup...
}
```

### Why It's Not Signaling

The producer thread signals +4024 in TWO paths:
1. **Work path (v6 != 0)**: Only if `sub_827DAC90(+4020)` returns non-zero (try-acquire succeeds)
2. **No-work path (v6 == 0)**: After waiting on semaphore +4020

**The Problem**: The producer loop blocks at `sub_827DACD8(+4020)` waiting for work to be submitted. Work is submitted via `sub_82192EB8` which copies data to +4048 and signals. If work is never submitted, the producer never reaches the semaphore release.

### Key Insight

This is a **producer-consumer pattern**:
- Main thread (`sub_82192C28`) waits on +4024
- Producer thread (`sub_82193000`) waits on +4020 OR processes work
- After work completes, producer signals +4024
- Main thread wakes up and continues

But if no work is enqueued initially, the producer thread:
1. Enters the loop
2. Finds no work (v6 == 0)
3. Waits on +4020 forever
4. Never signals +4024
5. Main thread blocks forever on +4024

---

## Related Functions

- `sub_82192A78`: Initializes the structure, creates all semaphores
- `sub_82192BB0`: Cleanup function
- `sub_82192BF8`: Check if busy (reads +4064, +4072)
- `sub_82193000`: Render thread loop (producer)
- `sub_82193B80`: Thread entry wrapper for sub_82193000
- `sub_82192DA0`: Single frame step
- `sub_82192E00`: Multi-frame step (4 iterations)
- `sub_82192EB8`: Submit work to queue (+4048)

---

## File References

- PPC Implementation: `ppc_recomp.5.cpp:31927-32153`
- Producer Thread: `ppc_recomp.5.cpp:32539-32759`  
- Thread Entry: `ppc_recomp.5.cpp:34293-34335`
- Decompiled Pseudo: `default (1).xex.c:1232569-1232620`
- Producer Pseudo: `default (1).xex.c:1232754-1232818`
- Kernel Implementation: `imports.cpp:4503-4620` (KeWaitForSingleObject)
- Semaphore Release: `imports.cpp:5372-5393` (KeReleaseSemaphore)
