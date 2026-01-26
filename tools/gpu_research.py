#!/usr/bin/env python3
"""
GPU Context Research - Option B Implementation Analysis
=======================================================

This script documents the complete research findings for fixing the
GPU context NULL pointer crash in LibertyRecomp.

ROOT CAUSE:
  Force-start at imports.cpp:14139-14140 sets interruptUserData = 0,
  but sub_829D7368 expects r4 to be the GPU context pointer.

SOLUTION (Option B):
  Read GPU context dynamically from global variable at *[*[0x82000768]]
  instead of relying on the (incorrect) interruptUserData.

VERIFICATION:
  All calculations verified against actual PPC recompiled code in
  LibertyRecompLib/ppc/ppc_recomp.135.cpp and ppc_recomp.136.cpp.
"""

def main():
    print("=" * 70)
    print("GPU CONTEXT STRUCTURE OFFSETS")
    print("=" * 70)

    offsets = {
        'spinlock': 16696,
        'frame_counter': 16532,
        'timestamp': 16536,
        'fence_read_index': 16684,
        'fence_write_index': 16688,
        'completion_callback': 16528,
        'state_ptr': 10900
    }

    for name, offset in offsets.items():
        word_index = offset // 4
        print(f"  {name:25} = {offset:6} (0x{offset:04X}) word[{word_index}]")

    print("\n" + "=" * 70)
    print("KEY MEMORY ADDRESSES")
    print("=" * 70)

    addresses = {
        'GPU_CONTEXT_GLOBAL_GOT': 0x82000768,
        'GPU_FENCE_REGISTER': 0x7FC86110,
        'GPU_INTERRUPT_STATUS': 0x7FC86544,
        'VBLANK_CALLBACK': 0x829D7368,
        'GPU_FENCE_HANDLER': 0x829D4C48,
        'VdSetGraphicsInterruptCallback': 0x829DF358,
        'GPU_INIT_FUNCTION': 0x829DF440,
    }

    for name, addr in addresses.items():
        print(f"  {name:30} = 0x{addr:08X}")

    print("\n" + "=" * 70)
    print("CRASH ANALYSIS")
    print("=" * 70)

    null_context = 0
    spinlock_offset = 16696
    crash_addr = null_context + spinlock_offset
    print(f"  NULL context (r3=0) + spinlock offset ({spinlock_offset})")
    print(f"  = 0x{crash_addr:08X}")
    print(f"  Crash happens reading from low memory address 0x{crash_addr:04X}")

    print("\n" + "=" * 70)
    print("GOT ENTRY CALCULATION")
    print("=" * 70)
    
    got_base = 0x82000000
    got_entry = 0x82000768
    got_offset = got_entry - got_base
    print(f"  GOT base:        0x{got_base:08X}")
    print(f"  GOT entry addr:  0x{got_entry:08X}")
    print(f"  Offset:          {got_offset} bytes (0x{got_offset:04X})")

    print("\n" + "=" * 70)
    print("DOUBLE-DEREFERENCE PATTERN ANALYSIS (PPC Assembly)")
    print("=" * 70)

    # PPC instruction analysis for: lis r11, -32256
    lis_val = -32256
    print(f"\n  Step 1: lis r11, {lis_val}")
    
    # lis loads 16-bit signed immediate into upper 16 bits
    # -32256 as 16-bit signed = 0x8200
    lis_immediate = lis_val & 0xFFFF  # Get 16-bit representation
    upper_half = lis_immediate << 16
    print(f"    {lis_val} as 16-bit signed = 0x{lis_immediate:04X}")
    print(f"    Shifted left 16 bits = 0x{upper_half:08X}")
    
    # Step 2: lwz r11, 1896(r11)
    lwz_offset = 1896
    final_addr = upper_half + lwz_offset
    print(f"\n  Step 2: lwz r11, {lwz_offset}(r11)")
    print(f"    0x{upper_half:08X} + {lwz_offset} = 0x{final_addr:08X}")
    print(f"    This loads GOT entry pointer from 0x{final_addr:08X}")
    
    # Step 3: lwz rX, 0(r11)
    print(f"\n  Step 3: lwz rX, 0(r11)")
    print(f"    Loads the GPU context pointer from the address in GOT entry")
    
    print("\n  Summary of double-dereference:")
    print(f"    *[0x{got_entry:08X}] -> address of global variable")
    print(f"    *[global_addr] -> GPU context pointer")

    print("\n" + "=" * 70)
    print("TIMELINE ANALYSIS: WHY THE BUG OCCURS")
    print("=" * 70)
    
    print("""
  1. FORCE-START (imports.cpp ~line 14139-14140):
     g_gpuRingBuffer.interruptCallback = 0x829D7368;
     g_gpuRingBuffer.interruptUserData = 0;   <-- THE BUG!
     
  2. VBLANK TIMER FIRES (before GPU init completes):
     Calls callback(r3=interruptType, r4=interruptUserData)
     r4 = 0 because force-start set it to 0
     
  3. sub_829D7368 RECEIVES (r3=0, r4=0):
     Stores r4 into r30 for later use
     Checks MEMORY[0x7FC86544] & 1 (GPU interrupt status)
     If set, calls sub_829D4C48(r3=r30=0)  <-- NULL pointer!
     
  4. sub_829D4C48 CRASHES:
     Computes spinlock addr = r3 + 16696 = 0 + 16696 = 16696
     KfAcquireSpinLock(16696) reads from low memory -> CRASH!
     
  5. GPU INIT COMPLETES (TOO LATE):
     sub_829DF440 stores GPU context to global at *[*[0x82000768]]
     sub_829DF358 calls VdSetGraphicsInterruptCallback
     This WOULD set proper userData, but timer already crashed
""")

    print("\n" + "=" * 70)
    print("OPTION B SOLUTION: READ GPU CONTEXT FROM GLOBAL")
    print("=" * 70)
    
    print("""
  Instead of relying on interruptUserData passed via r4,
  read the GPU context dynamically from the global variable.
  
  Implementation pattern:
  
    uint32_t ReadGpuContextFromGlobal() {
        // Step 1: Read pointer from GOT entry at 0x82000768
        uint32_t* gotEntry = (uint32_t*)g_memory.Translate(0x82000768);
        if (!gotEntry) return 0;
        
        // Step 2: Read the address stored in GOT (big-endian)
        uint32_t globalAddr = byteswap(*gotEntry);
        if (globalAddr == 0) return 0;
        
        // Step 3: Read the GPU context pointer from that global
        uint32_t* gpuContextPtr = (uint32_t*)g_memory.Translate(globalAddr);
        if (!gpuContextPtr) return 0;
        
        // Step 4: Return the GPU context (big-endian)
        return byteswap(*gpuContextPtr);
    }
  
  Usage in VBlank callback hook:
  
    uint32_t gpuContext = ReadGpuContextFromGlobal();
    if (gpuContext == 0) return;  // GPU not ready, skip
    ctx.r4.u32 = gpuContext;      // Set proper context
    // Now call original function
""")

    print("\n" + "=" * 70)
    print("MEMORY TRANSLATION VERIFICATION")
    print("=" * 70)
    
    # Verify the GOT entry is within valid Xbox 360 memory range
    xbox_mem_base = 0x82000000
    xbox_mem_end = 0x90000000
    
    print(f"  Xbox 360 memory range: 0x{xbox_mem_base:08X} - 0x{xbox_mem_end:08X}")
    print(f"  GOT entry address: 0x{got_entry:08X}")
    
    if xbox_mem_base <= got_entry < xbox_mem_end:
        print(f"  Status: VALID (within Xbox memory range)")
        relative_offset = got_entry - xbox_mem_base
        print(f"  Relative offset from base: {relative_offset} bytes (0x{relative_offset:08X})")
    else:
        print(f"  Status: INVALID!")

    print("\n" + "=" * 70)
    print("FUNCTIONS USING GPU CONTEXT GLOBAL (via 0x82000768)")
    print("=" * 70)
    
    # These functions were identified from grep search
    functions_using_global = [
        "ppc_recomp.135.cpp:25965 (read)",
        "ppc_recomp.136.cpp:1847  (store)",
        "And 17+ other locations"
    ]
    
    for func in functions_using_global:
        print(f"  - {func}")

    print("\n" + "=" * 70)
    print("IMPLEMENTATION PLAN SUMMARY")  
    print("=" * 70)
    
    print("""
  Phase 1: Add helper function to read GPU context from global
    - Location: imports.cpp or gpu.cpp
    - Function: ReadGpuContextFromGlobal()
    - Returns: GPU context pointer (or 0 if not initialized)
    
  Phase 2: Hook sub_829D7368 to use dynamic context
    - If r4 == 0, call ReadGpuContextFromGlobal()
    - If still 0, return early (GPU not ready)
    - Otherwise, set ctx.r4.u32 = gpuContext
    - Call original implementation
    
  Phase 3: Optionally remove force-start
    - The force-start at line 14139-14140 may no longer be needed
    - Can be removed once dynamic context reading is verified working
    
  Risks:
    - If the global is not yet initialized when VBlank fires,
      we still need to handle the 0 case gracefully
    - Threading considerations: global may be written by another thread
    - Big-endian/little-endian conversion must be correct
""")

if __name__ == "__main__":
    main()
