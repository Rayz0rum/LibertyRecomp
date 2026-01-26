#!/usr/bin/env python3
"""
GPU Command Processor Address Analysis for LibertyRecomp
Performs all address calculations using Python for verification
"""

def lis(value):
    """
    PowerPC LIS instruction - Load Immediate Shifted
    lis rD, SIMM => rD = SIMM << 16 (sign-extended)
    """
    # Sign-extend the 16-bit value and shift left by 16
    if value < 0:
        # Handle negative values (sign-extended)
        return (value << 16) & 0xFFFFFFFF
    else:
        return (value << 16) & 0xFFFFFFFF

def signed_32(value):
    """Convert unsigned 32-bit to signed"""
    if value >= 0x80000000:
        return value - 0x100000000
    return value

def unsigned_32(value):
    """Convert signed to unsigned 32-bit"""
    if value < 0:
        return value + 0x100000000
    return value

print("=" * 70)
print("GPU Command Processor Address Analysis")
print("=" * 70)

# ============================================================================
# sub_829DDC90 Analysis (GPU Command Processor Worker)
# ============================================================================
print("\n## sub_829DDC90 - GPU Command Processor Worker Thread")
print("-" * 70)

# From ppc_recomp.135.cpp line 47931-47938:
# lis r11,-5
# ori r11,r11,27680
r11_lis = lis(-5)
print(f"lis(-5) = 0x{r11_lis:08X}")
r11_ori = r11_lis | 27680
print(f"0x{r11_lis:08X} | 27680 = 0x{r11_ori:08X}")
signed_timeout = signed_32(r11_ori)
print(f"As signed 32-bit: {signed_timeout}")
print(f"Timeout in 100ns units: {signed_timeout} => {abs(signed_timeout) / 10000:.1f}ms")

# From ppc_recomp.135.cpp line 47928-47929:
# lis r25,-32256
r25_lis = lis(-32256)
print(f"\nlis(-32256) = 0x{r25_lis:08X} = {signed_32(r25_lis)}")

# ============================================================================
# sub_829DD978 Analysis (GPU Command Buffer Processing)
# ============================================================================
print("\n## sub_829DD978 - GPU Command Buffer Processing")
print("-" * 70)

# From ppc_recomp.135.cpp line 47466-47469:
# lis r3,-17477
# ori r3,r3,48059
r3_lis = lis(-17477)
print(f"lis(-17477) = 0x{r3_lis:08X}")
r3_ori = r3_lis | 48059
print(f"0x{r3_lis:08X} | 48059 = 0x{r3_ori:08X}")

# From ppc_recomp.135.cpp line 47475-47476:
# lis r29,256
r29_lis = lis(256)
print(f"\nlis(256) = 0x{r29_lis:08X} = {r29_lis}")
print(f"This is 0x1000000 = {r29_lis} (bitmask for GPU worker ID)")

# ============================================================================
# sub_829D8568 Analysis (GPU Command Buffer Flush)
# ============================================================================
print("\n## sub_829D8568 - GPU Command Buffer Flush")
print("-" * 70)

# Key observation: This function is called FREQUENTLY to flush GPU commands
# It compares write pointer (offset 48) vs read pointer (offset 56)
# If write > read, it needs to wait for GPU to catch up

print("Key structure offsets:")
print("  offset 48 (0x30): Write pointer (cmdWritePtr)")
print("  offset 56 (0x38): Read pointer (cmdReadPtr)")
print("  offset 60 (0x3C): Queue index")
print("")
print("Blocking condition: write_ptr > read_ptr")
print("The function spins waiting for GPU to consume commands")

# ============================================================================
# Critical Memory Addresses
# ============================================================================
print("\n## Critical Memory Addresses")
print("-" * 70)

# From research: MEMORY[0x101BE] appears in decompiled code
# This is likely a global pointer to the D3D device structure
print("MEMORY[0x101BE]:")
print(f"  0x101BE = {0x101BE}")
print(f"  This appears to be a pointer read, not actual address")

# Device structure offsets
print("\nD3D Device Structure Offsets (from decompiled code):")
print("  +10942 (0x2ABE): Flags byte (bitfield)")
print("  +14828 (0x39EC): Some buffer/context")
print("  +14928 (0x3A50): Critical section")

# ============================================================================
# Semaphore/Event Addresses from Previous Research
# ============================================================================
print("\n## Semaphore/Event Addresses (from ppc_recomp.71.cpp)")
print("-" * 70)

# From user's refined research:
# lis(-31998) = 0x83020000
# 0x83020000 + 30248 = 0x83027628
r_lis = lis(-31998)
print(f"lis(-31998) = 0x{r_lis:08X}")
addr1 = r_lis + 30248
print(f"0x{r_lis:08X} + 30248 = 0x{addr1:08X} (dword_83027628 - main thread semaphore)")
addr2 = r_lis + 30252
print(f"0x{r_lis:08X} + 30252 = 0x{addr2:08X} (dword_8302762C - semaphore 2)")

# r29 calculation
r29_base = r_lis + 20392
print(f"\nr29 = lis(-31998) + 20392 = 0x{r_lis:08X} + 0x{20392:04X} = 0x{r29_base:08X}")
print(f"r29 + 9864 = 0x{r29_base + 9864:08X} (XNotify handle)")
print(f"r29 + 9860 = 0x{r29_base + 9860:08X} (semaphore 2)")
print(f"r29 + 9856 = 0x{r29_base + 9856:08X} (semaphore 1)")

# ============================================================================
# GPU Command Processor Loop Analysis
# ============================================================================
print("\n## GPU Command Processor Loop (sub_829DDC90)")
print("-" * 70)
print("""
EXECUTION FLOW:
1. sub_829A0B50(-2, event) - Set thread priority
2. LOOP (loc_829DDCB0):
   a. Load timeout = -300000 (30ms in 100ns units)
   b. Check if signalState != context+368
   c. KeWaitForSingleObject with 30ms timeout
   d. If timeout (258), check flags and possibly call VdSwap
   e. KeResetEvent
   f. Check exit flag at context+4
   g. If not exit, call sub_829DD978 (process commands)
   h. Loop back to loc_829DDCB0

EXIT CONDITION:
  *(context + 4) == 0  => Break loop and return 0

BLOCKING POINTS:
  1. KeWaitForSingleObject - waits for event with 30ms timeout
  2. sub_829DD978 - processes GPU commands (can block internally)
""")

# ============================================================================
# sub_829DD978 Internal Flow
# ============================================================================
print("\n## sub_829DD978 Internal Flow (Command Processing)")
print("-" * 70)
print("""
1. Load context pointer from a1[0]
2. While loop checking context[13] and worker bitmask
3. Atomic compare-exchange on context[0] (lock acquisition)
4. Compare a1[15] vs a1[14] (queue positions)
5. If equal, return (no commands to process)
6. Otherwise, increment context[13] and process commands

COMMAND TYPES (from decompiled):
  - 0x8C000000 (-1929379840): Set context[88]
  - 0x8B000000 (-1946157056): Set context[4], context[5]
  - 0xC0000000+ : Jump/call commands
  - Others: Literal GPU commands

BLOCKING POINT:
  The while loop at line 3005827 spins waiting for GPU worker bit
""")

# ============================================================================
# Key Finding Summary
# ============================================================================
print("\n" + "=" * 70)
print("KEY FINDINGS")
print("=" * 70)
print("""
1. GPU Command Processor (sub_829DDC90) runs as a worker thread
   - Created via sub_829A24F0 (Xbox thread creation)
   - Loops indefinitely processing GPU commands
   - Uses 30ms timeout on KeWaitForSingleObject

2. Command Processing (sub_829DD978) is the actual work:
   - Acquires spinlock on context[0]
   - Processes PM4-style command packets
   - Can block waiting for GPU worker bitmask

3. Command Buffer Flush (sub_829D8568) called frequently:
   - Compares write_ptr vs read_ptr
   - Blocks if write ahead of read (waiting for GPU)

4. Current Implementation Status:
   - sub_829DD978 is STUBBED in imports.cpp (returns 0)
   - sub_829D8568 is HOOKED to skip ring buffer wait
   - sub_827DE858 (pgStreamer::Worker) is STUBBED
   - VdSwap handles frame presentation

5. PROBLEM: The stub approach may not fully prevent blocking because:
   - Other functions may still reference GPU command state
   - Event/semaphore synchronization may still block
   - The game expects GPU commands to complete
""")

print("\n" + "=" * 70)
print("RECOMMENDED INVESTIGATION")
print("=" * 70)
print("""
Use LLDB to:
1. Set breakpoint on KeWaitForSingleObject
2. Check which event handles are being waited on
3. Trace back to see which code path is blocking
4. Verify sub_829DD978 stub is actually being called

Key functions to trace:
- sub_829DDC90 (GPU command processor loop)
- sub_829DD978 (command processing)  
- sub_829D8568 (command buffer flush)
- KeWaitForSingleObject (kernel wait)
- NtWaitForSingleObject (NT wait)
""")
