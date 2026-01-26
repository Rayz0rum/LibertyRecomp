#include "xenon_memory.h"
#include "xex_header_data.h"
#include <os/logger.h>
#include <cstring>

// =============================================================================
// MEMORY INITIALIZATION - OPTION C (Hybrid)
// =============================================================================
// Performance comparison (from binary analysis):
//   Option A (zero all):     1.79 ms - DESTROYS 3,729 function pointers!
//   Option B (copy all):     1.67 ms - Requires 17.9 MB embedded data
//   Option C (hybrid):       0.26 ms - 6.9x faster, 128 KB data
//
// The XEX data section (0x82000000) contains:
//   - 3,729 function pointers in header
//   - 13,876-byte delegate/vtable array at 0xa20 (read by 2000+ functions!)
//   - Import ordinal table at 0x700-0x7E0
//   - Float constants and other initialized data
//
// Zeroing this destroys critical runtime data. We must preserve it.
// =============================================================================

void InitializeXenonMemoryRegions(uint8_t* base) {
    LOG_WARNING("[Xenon] Initializing Xbox 360 memory regions (Option C - Hybrid)");
    
    // =========================================================================
    // STEP 1: Copy XEX header data (128 KB) - preserves function tables
    // =========================================================================
    // This header contains:
    //   - 3,729 function pointers (0x954-0x4054)
    //   - Delegate table at 0xa20 (13,876 bytes, 432 unique functions)
    //   - Import ordinals at 0x700-0x7E0
    //   - Initialized constants and floats
    //
    // Without this, calls through the delegate table crash or misbehave!
    LOG_WARNING("[Xenon] Copying XEX header data: 0x82000000-0x82020000 (128 KB)");
    memcpy(base + 0x82000000, xex_header_data, sizeof(xex_header_data));
    
    // =========================================================================
    // STEP 2: Zero BSS and runtime regions only
    // =========================================================================
    // These regions are true uninitialized data (BSS) that should be zeroed:
    //   - 0x82020000-0x83000000: XEX data, code data, game globals
    //   - 0x83000000-0x831F0000: Static data/BSS
    //
    // Size: 0x831F0000 - 0x82020000 = 0x11D0000 = 18,677,760 bytes
    LOG_WARNING("[Xenon] Zeroing BSS regions: 0x82020000-0x831F0000 (17.8 MB)");
    memset(base + 0x82020000, 0, 0x11D0000);
    
    // =========================================================================
    // STEP 3: Initialize runtime globals (if any still needed)
    // =========================================================================
    // With proper header data, most runtime values are already correct.
    // The GPU context GOT entry (0x82000768) contains import ordinal 446
    // in the original XEX. If the loader doesn't resolve imports, we may
    // still need to patch specific addresses.
    //
    // For now, keep the GPU context patch as it was working:
    constexpr uint32_t GOT_GPU_CONTEXT = 0x82000768;
    constexpr uint32_t GPU_CONTEXT_GLOBAL = 0x83124900;
    
    uint32_t* gotEntry = reinterpret_cast<uint32_t*>(base + GOT_GPU_CONTEXT);
    *gotEntry = __builtin_bswap32(GPU_CONTEXT_GLOBAL);
    printf("[Xenon] GPU GOT entry 0x82000768 -> 0x%08X\n", GPU_CONTEXT_GLOBAL);
    
    // =========================================================================
    // VERIFICATION
    // =========================================================================
    // Check that critical data was preserved:
    uint32_t* delegate_start = reinterpret_cast<uint32_t*>(base + 0x82000a20);
    uint32_t delegate_val = __builtin_bswap32(*delegate_start);
    printf("[Xenon] Delegate table check: 0x82000a20 = 0x%08X (expected 0x3F800000)\n", delegate_val);
    
    uint32_t* func_ptr = reinterpret_cast<uint32_t*>(base + 0x82000954);
    uint32_t func_val = __builtin_bswap32(*func_ptr);
    printf("[Xenon] Function table check: 0x82000954 = 0x%08X (expected 0x822E58C0)\n", func_val);
    
    LOG_WARNING("[Xenon] Memory initialization complete (Option C - Hybrid)");
    LOG_WARNING("[Xenon] Header: 128 KB copied, BSS: 17.8 MB zeroed");
}
