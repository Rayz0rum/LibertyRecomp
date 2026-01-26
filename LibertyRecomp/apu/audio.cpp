#include <stdafx.h>

#include <bit>
#include <atomic>

#include "audio.h"
#include <cpu/guest_thread.h>
#include <kernel/heap.h>
#include <kernel/memory.h>
#include <os/logger.h>

#define AUDIO_DRIVER_KEY (uint32_t)('DAUD')

// Use to dump raw audio captures to the game folder.
//#define AUDIO_DUMP_SAMPLES_PATH "audio.pcm"

#ifdef AUDIO_DUMP_SAMPLES_PATH
std::ofstream g_audioDumpStream;
#endif

// =============================================================================
// Audio Manager Initialization
// =============================================================================
// sub_82168C08 initializes the audio manager and stores pointer at 0x83137CA8.
// This function is ORPHANED in the static call graph - never called by game code.
// We must call it here before starting the SDL2 audio thread, otherwise
// sub_82172BE8 -> sub_82169B00 will crash reading NULL from 0x83137CA8.
// =============================================================================
constexpr uint32_t AUDIO_MANAGER_PTR_ADDR = 0x83137CA8;

// sub_82168C08 is declared via PPC_EXTERN_FUNC in ppc_recomp_shared.h
// We access it directly since it's already linked

static std::atomic<bool> s_audioManagerInitialized{false};

static void InitializeAudioManager(uint32_t callbackParam) {
    // Only initialize once
    if (s_audioManagerInitialized.exchange(true)) {
        LOG_WARNING("[AUDIO] Audio manager already initialized, skipping");
        return;
    }
    
    // Check if already initialized by game code (unlikely but possible)
    uint8_t* base = g_memory.base;
    uint32_t existingPtr = __builtin_bswap32(*(volatile uint32_t*)(base + AUDIO_MANAGER_PTR_ADDR));
    if (existingPtr != 0) {
        LOGF_WARNING("[AUDIO] Audio manager already set to 0x{:08X}, skipping init", existingPtr);
        return;
    }
    
    LOG_WARNING("[AUDIO] Initializing audio manager (sub_82168C08)...");
    
    // Allocate a minimal audio config structure in guest memory
    // sub_82168D10 reads from this structure at offsets 0, 1, 2, 4
    // Structure layout (inferred from sub_82168D10):
    //   offset 0: byte - channel count (compared with 6, min 6)
    //   offset 1: byte - some multiplier (multiplied by 44)
    //   offset 2: byte - passed to sub_821699E8
    //   offset 4: pointer - audio format table (NULL uses default 0x820ADC70)
    struct AudioConfig {
        uint8_t channelCount;     // offset 0
        uint8_t multiplier;       // offset 1  
        uint8_t formatIndex;      // offset 2
        uint8_t padding;          // offset 3
        be<uint32_t> formatTable; // offset 4 (NULL = use default)
    };
    
    auto* config = static_cast<AudioConfig*>(g_userHeap.Alloc(sizeof(AudioConfig)));
    if (!config) {
        LOG_ERROR("[AUDIO] Failed to allocate audio config structure");
        s_audioManagerInitialized = false;
        return;
    }
    
    // Set up minimal config - 6 channels, use defaults
    config->channelCount = 6;     // Xbox 360 typically uses 6 channels (5.1)
    config->multiplier = 0;       // No extra buffers
    config->formatIndex = 0;      // Default format
    config->padding = 0;
    config->formatTable = 0;      // NULL = use default table at 0x820ADC70
    
    uint32_t configAddr = g_memory.MapVirtual(config);
    LOGF_WARNING("[AUDIO] Audio config allocated at 0x{:08X}", configAddr);
    
    // Create guest thread context for calling PPC function
    GuestThreadContext guestCtx(0);
    
    // Set up parameters for sub_82168C08:
    // r3 = config pointer
    // r4 = callback parameter (from XAudioRegisterRenderDriverClient)
    guestCtx.ppcContext.r3.u32 = configAddr;
    guestCtx.ppcContext.r4.u32 = callbackParam;
    
    LOGF_WARNING("[AUDIO] Calling sub_82168C08(config=0x{:08X}, param=0x{:08X})", 
                 configAddr, callbackParam);
    
    // Call the audio manager initialization function
    // Use g_memory.FindFunction to get the hooked version
    auto audioInitFunc = g_memory.FindFunction(0x82168C08);
    if (audioInitFunc) {
        audioInitFunc(guestCtx.ppcContext, g_memory.base);
    } else {
        LOG_ERROR("[AUDIO] Could not find sub_82168C08 function!");
        s_audioManagerInitialized = false;
        return;
    }
    
    // Check if initialization succeeded
    uint32_t audioMgrPtr = __builtin_bswap32(*(volatile uint32_t*)(base + AUDIO_MANAGER_PTR_ADDR));
    if (audioMgrPtr != 0) {
        LOGF_WARNING("[AUDIO] Audio manager initialized successfully! Pointer=0x{:08X}", audioMgrPtr);
    } else {
        LOG_ERROR("[AUDIO] Audio manager initialization FAILED - pointer still NULL");
        // Don't reset the flag - we tried, don't try again
    }
}

uint32_t XAudioRegisterRenderDriverClient(be<uint32_t>* callback, be<uint32_t>* driver)
{
    LOGF_WARNING("[AUDIO] XAudioRegisterRenderDriverClient CALLED! callback=0x{:08X} param=0x{:08X}", 
                 (uint32_t)*callback, (uint32_t)callback[1]);

#ifdef AUDIO_DUMP_SAMPLES_PATH
    g_audioDumpStream.open(AUDIO_DUMP_SAMPLES_PATH, std::ios::binary);
#endif

    // CRITICAL: Initialize audio manager BEFORE starting SDL2 audio thread
    // This ensures 0x83137CA8 is valid when sub_82172BE8 is invoked
    InitializeAudioManager((uint32_t)callback[1]);

    *driver = AUDIO_DRIVER_KEY;
    XAudioRegisterClient(g_memory.FindFunction(*callback), callback[1]);
    
    LOG_WARNING("[AUDIO] XAudioRegisterRenderDriverClient SUCCESS - audio thread started!");
    return 0;
}

uint32_t XAudioUnregisterRenderDriverClient(uint32_t driver)
{
    return 0;
}

uint32_t XAudioSubmitRenderDriverFrame(uint32_t driver, void* samples)
{
#ifdef AUDIO_DUMP_SAMPLES_PATH
    static uint32_t xaudioSamplesBuffer[XAUDIO_NUM_SAMPLES * XAUDIO_NUM_CHANNELS];
    for (size_t i = 0; i < XAUDIO_NUM_SAMPLES; i++)
    {
        for (size_t j = 0; j < XAUDIO_NUM_CHANNELS; j++)
        {
            xaudioSamplesBuffer[i * XAUDIO_NUM_CHANNELS + j] = ByteSwap(((uint32_t *)samples)[j * XAUDIO_NUM_SAMPLES + i]);
        }
    }

    g_audioDumpStream.write((const char *)(xaudioSamplesBuffer), sizeof(xaudioSamplesBuffer));
#endif

    XAudioSubmitFrame(samples);
    return 0;
}
