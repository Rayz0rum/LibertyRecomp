#!/usr/bin/env python3
"""
Race Condition Analysis for dword_83137CA8 NULL Pointer Crash

This script traces the address calculations in the crash chain:
  sub_8216A288 (CRASH) <- sub_82169C58 <- sub_82169B00 <- worker thread

The race condition: Worker threads start in sub_82169578, but dword_83137CA8
is only set AFTER sub_82169578 returns in sub_82168C08.
"""

import struct

# Guest address constants (Xbox 360 addresses)
DWORD_83137CA8 = 0x83137CA8  # Global audio manager pointer
BASE_OFFSET = 0x83000000     # Typical base for guest memory

# PPC register calculations from ppc_recomp.3.cpp
def analyze_sub_82169B00_load():
    """
    Analyze how sub_82169B00 loads dword_83137CA8
    
    From ppc_recomp.3.cpp lines 35086-35093:
        // lis r11,-31981
        ctx.r11.s64 = -2095906816;
        // ...
        // lwz r30,31912(r11)
        ctx.r30.u64 = PPC_LOAD_U32(ctx.r11.u32 + 31912);
    """
    # lis r11,-31981 sets r11 to (-31981 << 16) = -2095906816
    r11_value = -31981 << 16  # = -2095906816 = 0x83140000 (as unsigned 32-bit)
    r11_unsigned = r11_value & 0xFFFFFFFF
    
    # lwz r30,31912(r11) loads from r11 + 31912
    load_offset = 31912  # = 0x7CA8
    load_address = (r11_unsigned + load_offset) & 0xFFFFFFFF
    
    print("=" * 60)
    print("sub_82169B00: Loading dword_83137CA8")
    print("=" * 60)
    print(f"  lis r11,-31981:")
    print(f"    r11 (signed)   = {r11_value}")
    print(f"    r11 (unsigned) = 0x{r11_unsigned:08X}")
    print(f"  lwz r30,31912(r11):")
    print(f"    offset = {load_offset} = 0x{load_offset:04X}")
    print(f"    load_address = 0x{load_address:08X}")
    print(f"  Expected: 0x{DWORD_83137CA8:08X} (dword_83137CA8)")
    print(f"  Match: {load_address == DWORD_83137CA8}")
    print()
    
    return load_address

def analyze_sub_82168C08_store():
    """
    Analyze how sub_82168C08 stores to dword_83137CA8
    
    From ppc_recomp.3.cpp lines 32994-32997:
        // lis r11,-31981
        ctx.r11.s64 = -2095906816;
        // stw r31,31912(r11)
        PPC_STORE_U32(ctx.r11.u32 + 31912, ctx.r31.u32);
    """
    r11_value = -31981 << 16
    r11_unsigned = r11_value & 0xFFFFFFFF
    store_offset = 31912
    store_address = (r11_unsigned + store_offset) & 0xFFFFFFFF
    
    print("=" * 60)
    print("sub_82168C08: Storing to dword_83137CA8")
    print("=" * 60)
    print(f"  lis r11,-31981:")
    print(f"    r11 (unsigned) = 0x{r11_unsigned:08X}")
    print(f"  stw r31,31912(r11):")
    print(f"    store_address = 0x{store_address:08X}")
    print(f"  This stores the audio manager object pointer")
    print()
    
    return store_address

def analyze_sub_82169400_access():
    """
    Analyze the crash access in sub_82169400 (worker thread entry)
    
    From decompiled code line 1197283:
        *(_DWORD *)(4 * (*(unsigned __int8 *)(v0 + 268) + 83) + dword_83137CA8) = ...
    
    If dword_83137CA8 is NULL (0), this becomes:
        *(_DWORD *)(4 * (thread_index + 83) + 0) = ...
        = *(_DWORD *)(4 * 83 + ...) = access to low memory = CRASH
    """
    print("=" * 60)
    print("sub_82169400: Worker Thread Access Pattern")
    print("=" * 60)
    print("  Code: *(_DWORD *)(4 * (thread_index + 83) + dword_83137CA8)")
    print()
    print("  If dword_83137CA8 = valid_object (e.g., 0x12345678):")
    for thread_idx in range(6):
        offset = 4 * (thread_idx + 83)
        print(f"    Thread {thread_idx}: offset = {offset} (0x{offset:X})")
    print()
    print("  If dword_83137CA8 = 0 (NULL - race condition):")
    for thread_idx in range(6):
        offset = 4 * (thread_idx + 83)
        crash_addr = offset  # base is 0
        print(f"    Thread {thread_idx}: access 0x{crash_addr:08X} -> CRASH (low memory)")
    print()

def analyze_sub_8216A288_crash():
    """
    Analyze the crash in sub_8216A288
    
    From decompiled code lines 1198058-1059:
        v13 = *(char ***)(a2 + 36);
        v14 = *v13;
    
    If a1 (from dword_83137CA8) is NULL:
        a2 = a1 + 80 = 80
        v13 = *(char ***)(80 + 36) = *(char ***)116
        This dereferences address 116 = CRASH
    """
    print("=" * 60)
    print("sub_8216A288: Crash Analysis")
    print("=" * 60)
    print("  Called as: sub_8216A288(a1, a1 + 80)")
    print("  where a1 = dword_83137CA8")
    print()
    print("  If a1 = valid_object:")
    print("    a2 = valid_object + 80")
    print("    v13 = *(a2 + 36) = valid pointer")
    print("    v14 = *v13 = valid dereference")
    print()
    print("  If a1 = 0 (NULL - race condition):")
    a1 = 0
    a2 = a1 + 80
    v13_addr = a2 + 36
    print(f"    a2 = 0 + 80 = {a2}")
    print(f"    v13 = *(char ***){v13_addr}")
    print(f"    Dereferencing address {v13_addr} (0x{v13_addr:08X}) -> CRASH")
    print()

def analyze_race_condition():
    """
    Analyze the complete race condition timeline
    """
    print("=" * 60)
    print("RACE CONDITION TIMELINE")
    print("=" * 60)
    print("""
MAIN THREAD                          WORKER THREADS
-----------                          --------------
sub_82168C08() called
  |
  v
sub_82169578() called
  |
  +-- Creates threads with                
  |   ExCreateThread(sub_82169400)   sub_82169400 starts running!
  |   ExCreateThread(sub_821694C8)   sub_821694C8 starts running!
  |                                        |
  +-- KeResumeThread() resumes them        v
  |                                  Reads dword_83137CA8
  |                                  IT'S STILL NULL!
  |                                        |
  v                                        v
sub_82169578() returns               *(_DWORD *)(... + dword_83137CA8)
  |                                  = *(_DWORD *)(... + 0)
  v                                        |
dword_83137CA8 = v23;  <-- TOO LATE!       v
  |                                  CRASH: NULL pointer dereference
  v
sub_82168C08() returns

SOLUTION: Either:
1. Set dword_83137CA8 BEFORE creating threads in sub_82169578
2. Have worker threads wait for dword_83137CA8 to be non-NULL
3. Don't resume threads until after dword_83137CA8 is set
""")

def print_lldb_commands():
    """
    Print LLDB commands for debugging this issue
    """
    print("=" * 60)
    print("LLDB DEBUG COMMANDS")
    print("=" * 60)
    print("""
# Set breakpoint on sub_82169578 (thread creation)
b sub_82169578

# Set breakpoint on sub_82168C08 (initialization) 
b sub_82168C08

# Set breakpoint on sub_82169400 (worker thread entry)
b sub_82169400

# Set breakpoint on sub_82169B00 (audio callback)
b sub_82169B00

# Watch dword_83137CA8 for writes (need to calculate host address)
# Guest address: 0x83137CA8
# Host address: base + 0x83137CA8 (where base is the guest memory base)
# In LLDB: watchpoint set expression -w write -- (uint32_t*)(base + 0x83137CA8)

# When stopped, examine the global:
# memory read 0x383137CA8   (if base is 0x300000000)
# or: p *(uint32_t*)(base + 0x83137CA8)

# Check thread states:
thread list
thread backtrace all
""")

def main():
    print("\n" + "=" * 60)
    print("RACE CONDITION ANALYSIS: dword_83137CA8 NULL POINTER CRASH")
    print("=" * 60 + "\n")
    
    # Verify address calculations
    load_addr = analyze_sub_82169B00_load()
    store_addr = analyze_sub_82168C08_store()
    
    assert load_addr == store_addr == DWORD_83137CA8, "Address mismatch!"
    
    # Analyze access patterns
    analyze_sub_82169400_access()
    analyze_sub_8216A288_crash()
    
    # Show timeline
    analyze_race_condition()
    
    # Show LLDB commands
    print_lldb_commands()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"""
Root Cause: Initialization order race condition

Key Address: dword_83137CA8 = 0x{DWORD_83137CA8:08X}
  - Set by: sub_82168C08 line 1196881
  - Read by: sub_82169400, sub_821694C8, sub_82169B00

Problem: Worker threads are created and resumed in sub_82169578,
but dword_83137CA8 is set AFTER sub_82169578 returns.

On Xbox 360: Implicit timing/scheduling prevented this race.
In recompiled: Threads start faster, exposing the bug.

Evidence:
  - memory read 0x383137CA8 shows 0x00000000 at crash time
  - Worker thread backtrace shows access to NULL-derived address
""")

if __name__ == "__main__":
    main()
