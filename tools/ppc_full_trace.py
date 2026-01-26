#!/usr/bin/env python3
"""
COMPLETE PPC RECOMPILED CODE TRACE
===================================
Traces execution through the ACTUAL binary code in LibertyRecompLib/ppc
All address calculations verified with Python
"""

def lis_instruction(value):
    """
    Simulate PPC 'lis' (Load Immediate Shifted) instruction
    lis rD, imm => rD = imm << 16 (sign extended)
    """
    if value < 0:
        result = (value & 0xFFFF) << 16
        if result & 0x80000000:
            result = result | 0xFFFFFFFF00000000
        return result & 0xFFFFFFFF
    else:
        return (value & 0xFFFF) << 16

def addi_instruction(base_val, offset):
    """
    Simulate PPC 'addi' instruction
    addi rD, rA, imm => rD = rA + imm (sign extended)
    """
    # offset is signed 16-bit
    if offset < 0:
        signed_offset = offset
    elif offset > 32767:
        signed_offset = offset - 65536
    else:
        signed_offset = offset
    return (base_val + signed_offset) & 0xFFFFFFFF

def calculate_address(lis_value, offset):
    """Calculate effective address from lis + addi/lwz offset"""
    base = lis_instruction(lis_value)
    return addi_instruction(base, offset)

print("=" * 80)
print("COMPLETE PPC RECOMPILED CODE TRACE")
print("=" * 80)

# ============================================================================
# TRACE: sub_82626210 - Enumerate Content Thread
# ============================================================================
print("\n" + "=" * 80)
print("TRACE: sub_82626210 - Enumerate Content Thread (THE STUCK LOOP)")
print("Source: ppc_recomp.71.cpp lines 26292-26479")
print("=" * 80)

# Calculate all the addresses used in this function
print("\n--- Address Calculations from PPC Instructions ---\n")

# r27: lis r11,-31997; addi r27,r11,-30688
lis_31997 = lis_instruction(-31997)
r27_addr = addi_instruction(lis_31997, -30688)
print(f"r27 (stru_83028820 - callback struct):")
print(f"  lis r11, -31997 = 0x{lis_31997:08X}")
print(f"  addi r27, r11, -30688 = 0x{lis_31997:08X} + {-30688}")
print(f"  r27 = 0x{r27_addr:08X}")

# r29: lis r11,-31998; addi r29,r11,20392
lis_31998 = lis_instruction(-31998)
r29_addr = addi_instruction(lis_31998, 20392)
print(f"\nr29 (base for semaphore/notification handles):")
print(f"  lis r11, -31998 = 0x{lis_31998:08X}")
print(f"  addi r29, r11, 20392 = 0x{lis_31998:08X} + {20392}")
print(f"  r29 = 0x{r29_addr:08X}")

# r28: lis r11,-32092; addi r28,r11,-10804
lis_32092 = lis_instruction(-32092)
r28_addr = addi_instruction(lis_32092, -10804)
print(f"\nr28 (dword_82A3D5CC - content enumeration state):")
print(f"  lis r11, -32092 = 0x{lis_32092:08X}")
print(f"  addi r28, r11, -10804 = 0x{lis_32092:08X} + {-10804}")
print(f"  r28 = 0x{r28_addr:08X}")

# r26: lis r11,-31997; addi r26,r11,-30720
r26_addr = addi_instruction(lis_31997, -30720)
print(f"\nr26 (stru_83028800 - critical section):")
print(f"  lis r11, -31997 = 0x{lis_31997:08X}")
print(f"  addi r26, r11, -30720 = 0x{lis_31997:08X} + {-30720}")
print(f"  r26 = 0x{r26_addr:08X}")

# Semaphore/notification handles (loaded via r29 + offset)
sem_9864 = r29_addr + 9864  # dword_83027630 - XNotify listener
sem_9860 = r29_addr + 9860  # dword_8302762C - semaphore 2
sem_9856 = r29_addr + 9856  # dword_83027628 - semaphore 1

print(f"\n--- Semaphore/Notification Handle Addresses ---")
print(f"dword_83027630 (XNotify listener): r29 + 9864 = 0x{r29_addr:08X} + 0x{9864:04X} = 0x{sem_9864:08X}")
print(f"dword_8302762C (semaphore 2):      r29 + 9860 = 0x{r29_addr:08X} + 0x{9860:04X} = 0x{sem_9860:08X}")
print(f"dword_83027628 (semaphore 1):      r29 + 9856 = 0x{r29_addr:08X} + 0x{9856:04X} = 0x{sem_9856:08X}")

print("\n--- Execution Flow Analysis ---")
print("""
LOOP START (loc_82626240):
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. Load XNotify handle from 0x{sem_9864:08X}                               │
│    lwz r3, 9864(r29)   => r3 = *(0x{sem_9864:08X})                         │
│                                                                             │
│ 2. Call XNotifyGetNext with dwMsgFilter = 11 (0xB)                         │
│    li r4, 11           => r4 = 11                                          │
│    bl __imp__XNotifyGetNext                                                │
│                                                                             │
│ 3. If XNotifyGetNext returns non-zero, set r31 = 1                        │
│    cmpwi cr6, r3, 0                                                        │
│    beq cr6, loc_82626260  (skip if returned 0)                            │
│    li r31, 1           => r31 = 1 (notification received)                  │
│                                                                             │
│ 4. Check if r31 (r30 = r31 & 0xFF) is non-zero                            │
│    clrlwi r30, r31, 24 => r30 = r31 & 0xFF                                │
│    cmplwi cr6, r30, 0                                                      │
│    bne cr6, loc_82626280  (skip wait if notification received)            │
│                                                                             │
│ 5. If no notification, try-wait on semaphore at 0x{sem_9860:08X}          │
│    lwz r3, 9860(r29)   => r3 = *(0x{sem_9860:08X})                        │
│    bl sub_827DAC90     => try-wait (non-blocking)                         │
│                                                                             │
│ 6. If try-wait failed (r3 == 0), jump to SLEEP                            │
│    clrlwi r11, r3, 24                                                      │
│    cmplwi cr6, r11, 0                                                      │
│    beq cr6, loc_82626344  => GOTO SLEEP                                   │
│                                                                             │
│ ... content enumeration logic ...                                          │
│                                                                             │
│ 7. AT loc_82626330: Signal semaphore at 0x{sem_9856:08X}                  │
│    lwz r3, 9856(r29)   => r3 = *(0x{sem_9856:08X})                        │
│    bl sub_827DAD60     => SIGNAL SEMAPHORE (this would unblock main!)     │
│                                                                             │
│ 8. SLEEP (loc_82626344):                                                   │
│    li r3, 16           => r3 = 16 (milliseconds)                          │
│    bl sub_827DAE18     => sleep 16ms                                      │
│    b loc_82626240      => LOOP BACK                                       │
└─────────────────────────────────────────────────────────────────────────────┘

THE PROBLEM:
- XNotifyGetNext with filter 0xB returns 0 (no notifications)
- Try-wait on 0x{sem_9860:08X} returns 0 (not signaled)
- Code jumps to loc_82626344 (sleep) and loops back
- NEVER reaches loc_82626330 where it would signal 0x{sem_9856:08X}
- Main thread waiting on 0x{sem_9856:08X} blocks forever
""".format(sem_9864=sem_9864, sem_9860=sem_9860, sem_9856=sem_9856))

# ============================================================================
# TRACE: sub_829DDC90 - GPU Command Processor
# ============================================================================
print("\n" + "=" * 80)
print("TRACE: sub_829DDC90 - GPU Command Processor (SPINNING)")
print("Source: ppc_recomp.135.cpp lines 47907-48048")
print("=" * 80)

# Calculate timeout value
lis_minus5 = lis_instruction(-5)
timeout_val = lis_minus5 | 27680
if timeout_val & 0x80000000:
    timeout_signed = timeout_val - 0x100000000
else:
    timeout_signed = timeout_val

print(f"\n--- Timeout Calculation ---")
print(f"lis r11, -5:          0x{lis_minus5:08X}")
print(f"ori r11, r11, 27680:  0x{lis_minus5:08X} | 0x{27680:04X} = 0x{timeout_val:08X}")
print(f"As signed 32-bit:     {timeout_signed}")
print(f"In milliseconds:      {abs(timeout_signed) / 10000} ms")

# Calculate the r25 address (MEMORY[0x101BE] equivalent)
lis_32256 = lis_instruction(-32256)
r25_val = lis_32256  # This is the base for GPU state access
print(f"\n--- GPU State Base Address ---")
print(f"lis r25, -32256:      0x{lis_32256:08X}")
print(f"This is used as base for GPU device state access")

print("""
--- Execution Flow ---

LOOP START (loc_829DDCB0):
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. Setup timeout: -300000 (30ms in 100ns units)                            │
│    lis r11, -5                                                              │
│    ori r11, r11, 27680                                                      │
│    std r11, 80(r1)     => store timeout on stack                           │
│                                                                             │
│ 2. Load current state from structure                                       │
│    lwz r26, 0(r28)     => r26 = *(structure + 0)                          │
│                                                                             │
│ 3. Check if work queue empty: compare offsets 60 and 56                   │
│    lwz r11, 60(r28)    => r11 = queue tail                                │
│    lwz r10, 56(r28)    => r10 = queue head                                │
│    cmplw cr6, r11, r10                                                     │
│    bne cr6, loc_829DDD50  (skip wait if work pending)                     │
│                                                                             │
│ 4. Wait for event with timeout                                            │
│    addi r29, r28, 32   => r29 = event address                             │
│    bl __imp__KeWaitForSingleObject                                        │
│    cmplwi cr6, r3, 258 => check if timeout (STATUS_TIMEOUT = 258)         │
│    beq cr6, loc_829DDCF0  (if timeout, do GPU processing)                 │
│                                                                             │
│ 5. Reset event                                                             │
│    addi r3, r28, 32                                                        │
│    bl __imp__KeResetEvent  => 408 samples here (heavy contention!)        │
│                                                                             │
│ 6. Check exit condition: *(r26 + 4) == 0                                  │
│    lwz r11, 4(r26)     => r11 = *(r26 + 4)                                │
│    cmplwi cr6, r11, 0                                                      │
│    beq cr6, loc_829DDD70  (EXIT if zero)                                  │
│                                                                             │
│ 7. Process commands and loop                                               │
│    mr r3, r28                                                              │
│    bl sub_829DD978     => process GPU commands                            │
│    b loc_829DDCB0      => LOOP BACK                                       │
└─────────────────────────────────────────────────────────────────────────────┘

THE PROBLEM:
- Exit condition *(r26 + 4) is never 0 during init
- Thread spins in loop, consuming CPU
- 725+ samples in this function, 408 in KeResetEvent
- Contributes to beachball but not root cause of hang
""")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("VERIFIED ADDRESS SUMMARY (from actual PPC binary code)")
print("=" * 80)

print(f"""
SEMAPHORE ADDRESSES (verified via PPC instruction trace):
─────────────────────────────────────────────────────────
  dword_83027628:  0x{sem_9856:08X}  (main thread waits on this)
  dword_8302762C:  0x{sem_9860:08X}  (Enumerate Content waits on this)
  dword_83027630:  0x{sem_9864:08X}  (XNotify listener handle)

STRUCTURE ADDRESSES:
────────────────────
  stru_83028800:   0x{r26_addr:08X}  (critical section)
  stru_83028820:   0x{r27_addr:08X}  (callback structure)
  dword_82A3D5CC:  0x{r28_addr:08X}  (content enumeration state)

CALCULATION VERIFICATION:
─────────────────────────
  r29 base:        0x{r29_addr:08X}
  + 9856 =         0x{sem_9856:08X}  ✓ dword_83027628
  + 9860 =         0x{sem_9860:08X}  ✓ dword_8302762C  
  + 9864 =         0x{sem_9864:08X}  ✓ dword_83027630

GPU TIMEOUT:
────────────
  Value:           {timeout_signed} (100ns units)
  Milliseconds:    {abs(timeout_signed) / 10000} ms
  Calculation:     lis(-5) | 27680 = 0x{timeout_val:08X}
""")

print("=" * 80)
print("ROOT CAUSE (from PPC code trace)")
print("=" * 80)
print(f"""
1. MAIN THREAD blocks in sub_82269140:
   - Checks *(r31 + 349) != 0, then calls sub_82625CA0(r4)
   - sub_82625CA0 loads semaphore from 0x{sem_9856:08X}
   - Calls sub_827DACD8 with timeout = -1 (INFINITE)
   - Thread blocks in Semaphore::Wait

2. ENUMERATE CONTENT THREAD stuck in sub_82626210:
   - Calls XNotifyGetNext(0x{sem_9864:08X}, 11, ...) => returns 0
   - Calls sub_827DAC90(0x{sem_9860:08X}) => returns 0 (not signaled)
   - Jumps to loc_82626344, sleeps 16ms, loops back
   - NEVER reaches loc_82626330 which would signal 0x{sem_9856:08X}

3. GPU COMMAND PROCESSOR spinning in sub_829DDC90:
   - Waits 30ms, resets events, checks exit condition
   - Exit condition *(r26 + 4) != 0, so loops indefinitely
   - 725+ samples consuming CPU

THE FIX SHOULD TARGET:
- Why XNotifyGetNext never returns notifications with ID 0xB
- OR why semaphore at 0x{sem_9860:08X} is never signaled
- sub_82625C90 (signals 0x{sem_9860:08X}) is never called
""")

if __name__ == "__main__":
    pass
