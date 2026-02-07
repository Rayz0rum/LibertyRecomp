// =============================================================================
// GTA IV Save System PPC Function Hooks
// =============================================================================
// These hooks intercept GTA IV's save wrapper functions to provide visibility
// into save operations and ensure proper integration with host filesystem.
//
// Based on REWRITE_PLAYBOOK.md section 14.1:
// - sub_829A1C38: Content creation wrapper (calls XamContentCreateEx)
// - sub_829A1CA0: Content close wrapper (calls XamContentClose)
// - sub_829A1CB8: Enumeration wrapper (calls XamContentCreateEnumerator)
// - sub_8297A930: Save manager (orchestrates save operations)
// =============================================================================

#include <stdafx.h>
#include <cpu/ppc_context.h>
#include "function.h"
#include "memory.h"
#include <cstdio>
#include <thread>
#include <chrono>
#include <atomic>
#include <os/logger.h>

// =============================================================================
// KERNEL PHASE - extern declarations from imports.cpp
// =============================================================================
enum class KernelPhase { Boot, Init, Runtime };
extern std::atomic<KernelPhase> g_kernelPhase;
extern void KernelPhase_EnterRuntime();

// Debug logging control
#define SAVE_HOOKS_DEBUG_LOGGING 1

// =============================================================================
// sub_829A1C38 - Content Creation Wrapper
// Location: ppc_recomp.79.cpp:37654
// Calls XamContentCreateEx to create/open save containers
// =============================================================================
extern "C" void __imp__sub_829A1C38(PPCContext& ctx, uint8_t* base);
PPC_FUNC(sub_829A1C38)
{
    static int s_count = 0;
    ++s_count;
    
#if SAVE_HOOKS_DEBUG_LOGGING
    printf("[SaveHook] ========================================\n");
    printf("[SaveHook] sub_829A1C38 (Content Creation) #%d\n", s_count);
    printf("[SaveHook] r3=0x%08X r4=0x%08X r5=0x%08X\n", ctx.r3.u32, ctx.r4.u32, ctx.r5.u32);
#endif
    
    // Call original implementation
    __imp__sub_829A1C38(ctx, base);
    
#if SAVE_HOOKS_DEBUG_LOGGING
    printf("[SaveHook] sub_829A1C38 returned r3=0x%08X\n", ctx.r3.u32);
    printf("[SaveHook] ========================================\n");
#endif
}

// =============================================================================
// sub_829A1CA0 - Content Close Wrapper
// Location: ppc_recomp.79.cpp:37723
// Direct jump to XamContentClose
// =============================================================================
extern "C" void __imp__sub_829A1CA0(PPCContext& ctx, uint8_t* base);
PPC_FUNC(sub_829A1CA0)
{
    static int s_count = 0;
    ++s_count;
    
#if SAVE_HOOKS_DEBUG_LOGGING
    printf("[SaveHook] sub_829A1CA0 (Content Close) #%d r3=0x%08X\n", s_count, ctx.r3.u32);
#endif
    
    // Call original implementation
    __imp__sub_829A1CA0(ctx, base);
    
#if SAVE_HOOKS_DEBUG_LOGGING
    printf("[SaveHook] sub_829A1CA0 returned r3=0x%08X\n", ctx.r3.u32);
#endif
}

// =============================================================================
// sub_829A1CB8 - Enumeration Wrapper
// Location: ppc_recomp.79.cpp:37756
// Calls XamContentCreateEnumerator to list save files
// =============================================================================
extern "C" void __imp__sub_829A1CB8(PPCContext& ctx, uint8_t* base);
PPC_FUNC(sub_829A1CB8)
{
    static int s_count = 0;
    ++s_count;
    
#if SAVE_HOOKS_DEBUG_LOGGING
    printf("[SaveHook] ========================================\n");
    printf("[SaveHook] sub_829A1CB8 (Content Enumeration) #%d\n", s_count);
    printf("[SaveHook] r3=0x%08X r4=0x%08X r5=0x%08X r6=0x%08X\n", 
           ctx.r3.u32, ctx.r4.u32, ctx.r5.u32, ctx.r6.u32);
#endif
    
    // Call original implementation
    __imp__sub_829A1CB8(ctx, base);
    
#if SAVE_HOOKS_DEBUG_LOGGING
    printf("[SaveHook] sub_829A1CB8 returned r3=0x%08X\n", ctx.r3.u32);
    printf("[SaveHook] ========================================\n");
#endif
}

// =============================================================================
// sub_8297A930 - Save Manager
// Location: ppc_recomp.77.cpp:7308
// Orchestrates save operations, calls sub_829A1878
// =============================================================================
extern "C" void __imp__sub_8297A930(PPCContext& ctx, uint8_t* base);
PPC_FUNC(sub_8297A930)
{
    static int s_count = 0;
    ++s_count;
    
#if SAVE_HOOKS_DEBUG_LOGGING
    if (s_count <= 10) {
        printf("[SaveHook] ========================================\n");
        printf("[SaveHook] sub_8297A930 (Save Manager) #%d\n", s_count);
        printf("[SaveHook] r3=0x%08X (context+208)\n", ctx.r3.u32);
        printf("[SaveHook] ========================================\n");
    }
#endif
    
    // Call original implementation
    __imp__sub_8297A930(ctx, base);
    
#if SAVE_HOOKS_DEBUG_LOGGING
    if (s_count <= 10) {
        printf("[SaveHook] sub_8297A930 returned\n");
    }
#endif
}

// =============================================================================
// sub_82122CA0 - Save System Init
// Location: ppc_recomp.0.cpp:7117
// Initializes save system with 3 save slot contexts (Profile, Game, Autosave)
// =============================================================================
extern "C" void __imp__sub_82122CA0(PPCContext& ctx, uint8_t* base);
PPC_FUNC(sub_82122CA0)
{
    static int s_count = 0;
    ++s_count;
    
    printf("[SaveHook] ========================================\n");
    printf("[SaveHook] sub_82122CA0 (Save System Init) #%d\n", s_count);
    printf("[SaveHook] Initializing 3 save slot contexts:\n");
    printf("[SaveHook]   - Profile Save (vtable: 0x81209104)\n");
    printf("[SaveHook]   - Game Save (vtable: 0x81209064)\n");
    printf("[SaveHook]   - Autosave (vtable: 0x81209028)\n");
    printf("[SaveHook] ========================================\n");
    
    // Call original implementation
    __imp__sub_82122CA0(ctx, base);
    
    printf("[SaveHook] sub_82122CA0 completed\n");
}

// =============================================================================
// sub_821200D0 - Post-Init (Profiles/Saves)
// Location: ppc_recomp.0.cpp:134
// Loads profile and enumerates/opens save files
// =============================================================================
extern "C" void __imp__sub_821200D0(PPCContext& ctx, uint8_t* base);
// sub_821238D0 is declared in ppc_recomp_shared.h via PPC_EXTERN_FUNC
extern void ShutdownAllWorkers();  // From imports.cpp - sets exit flags and signals workers

// Memory addresses for loading screen state (Python-verified from PPC source)
// Base: lis r11,-31981 = 0x83130000
// byte_83137BB7 = base + 31671 = 0x83137BB7 (loading in progress flag)
// byte_83137BC9 = base + 31689 = 0x83137BC9 (loading step - exit when 0)
constexpr uint32_t LOADING_FLAG_ADDR = 0x83137BB7;  // Loading in progress flag
constexpr uint32_t LOADING_STEP_ADDR = 0x83137BC9;  // Loading step (non-zero = still loading)

// sub_821200D0_hook - Main game loop entry point (extern "C" for PatchFuncMapping)
// This is the correct point to enter Runtime phase:
// - All 63 subsystems initialized
// - GPU device created, shaders loaded
// - About to start main render loop
// 
// CRITICAL FIX: Force Runtime phase HERE to break circular dependency:
//   Runtime Phase requires Proper Sync requires Render Loop requires VdSwap requires Runtime Phase
// By forcing Runtime at main loop entry, semaphore waits become real waits instead of fail-open bypasses.
//
// LOADING SCREEN FIX (Issue 2): Call sub_821238D0 (loading screen render) when loading is active.
// Root cause: sub_821238D0 is defined but NEVER called in the actual PPC code.
// This function handles timer updates, fade effects, and sets byte_83137BC9 = 0 to exit loading.
//
// CRITICAL: Named `sub_821200D0` (not `sub_821200D0_hook`) to OVERRIDE the weak symbol in ppc_recomp.0.cpp!
// PatchFuncMapping only redirects function TABLE lookups, not direct bl (branch) calls.
// By defining a strong symbol, we intercept ALL calls including direct bl instructions.
PPC_FUNC(sub_821200D0)
{
    static int s_count = 0;
    static bool s_runtimeForced = false;
    ++s_count;
    
    printf("[821200D0] #%d ENTER\n", s_count); fflush(stdout);
    
    // PHASE 1 FIX: Force Runtime phase at main loop entry to break circular dependency
    if (!s_runtimeForced) {
        s_runtimeForced = true;
        if (g_kernelPhase.load(std::memory_order_acquire) != KernelPhase::Runtime) {
            KernelPhase_EnterRuntime();
            LOG_WARNING("[KERNEL_PHASE] Forced Init -> Runtime at sub_821200D0 (main loop entry)");
        }
    }
    
    // LOADING SCREEN FIX (Issue 2): Invoke the missing render function
    // The loading screen state machine is stuck because sub_821238D0 is never called.
    // This function advances the loading timer and transitions states.
    uint8_t loadingActive = PPC_LOAD_U8(LOADING_FLAG_ADDR);
    if (loadingActive) {
        // Call the loading screen render function to advance the state machine
        sub_821238D0(ctx, base);
        
        // Log state for debugging (first 50 calls only to avoid spam)
        if (s_count <= 50) {
            uint8_t loadingStep = PPC_LOAD_U8(LOADING_STEP_ADDR);
            printf("[821200D0] Loading active: flag=%d step=%d, called sub_821238D0\n", 
                   loadingActive, loadingStep);
            fflush(stdout);
        }
    }
    
    // Run the actual function
    __imp__sub_821200D0(ctx, base);
    
    printf("[821200D0] #%d EXIT r3=%d\n", s_count, ctx.r3.s32); fflush(stdout);
}
