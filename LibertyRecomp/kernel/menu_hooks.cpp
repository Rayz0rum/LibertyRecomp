// =============================================================================
// NATIVE MENU HOOKS - GTA IV Recompiled
// =============================================================================
// Implementation of native pause menu integration hooks.
// See menu_hooks.h for detailed documentation.
// =============================================================================

#include "menu_hooks.h"
#include <stdafx.h>
#include <cpu/ppc_context.h>
#include <user/config.h>
#include <os/logger.h>
#include <cstring>
#include <mutex>
#include <unordered_set>

// =============================================================================
// Big-endian helpers for guest memory access
// =============================================================================
namespace {

inline void WriteU32BE(uint8_t* base, uint32_t addr, uint32_t value) {
    uint32_t* ptr = reinterpret_cast<uint32_t*>(base + addr);
    *ptr = __builtin_bswap32(value);
}

inline uint32_t ReadU32BE(uint8_t* base, uint32_t addr) {
    uint32_t* ptr = reinterpret_cast<uint32_t*>(base + addr);
    return __builtin_bswap32(*ptr);
}

inline void WriteS32BE(uint8_t* base, uint32_t addr, int32_t value) {
    WriteU32BE(base, addr, static_cast<uint32_t>(value));
}

inline int32_t ReadS32BE(uint8_t* base, uint32_t addr) {
    return static_cast<int32_t>(ReadU32BE(base, addr));
}

inline void WriteU16BE(uint8_t* base, uint32_t addr, uint16_t value) {
    uint16_t* ptr = reinterpret_cast<uint16_t*>(base + addr);
    *ptr = __builtin_bswap16(value);
}

inline uint16_t ReadU16BE(uint8_t* base, uint32_t addr) {
    uint16_t* ptr = reinterpret_cast<uint16_t*>(base + addr);
    return __builtin_bswap16(*ptr);
}

// =============================================================================
// Module State
// =============================================================================

static uint8_t* g_guestBase = nullptr;
static bool g_initialized = false;
static bool g_verboseLogging = true;  // Enable for debugging
static bool g_menuOpen = false;
static std::mutex g_mutex;

// Custom GXT strings for menu items
static std::unordered_map<std::string, std::string> g_customStrings;

// =============================================================================
// Value Translation Helpers
// =============================================================================

// Convert Config::ResolutionScale (0.25-2.0) to menu value (25-200)
inline int32_t ResolutionScaleToMenu(float scale) {
    return static_cast<int32_t>(scale * 100.0f);
}

// Convert menu value (25-200) to Config::ResolutionScale (0.25-2.0)
inline float MenuToResolutionScale(int32_t value) {
    return static_cast<float>(value) / 100.0f;
}

// Convert Config multipliers (0.5-3.0) to menu value (50-300)
inline int32_t MultiplierToMenu(float mult) {
    return static_cast<int32_t>(mult * 100.0f);
}

// Convert menu value (50-300) to multiplier (0.5-3.0)
inline float MenuToMultiplier(int32_t value) {
    return static_cast<float>(value) / 100.0f;
}

} // anonymous namespace

// =============================================================================
// MenuHooks Implementation
// =============================================================================

namespace MenuHooks {

void Initialize(uint8_t* base) {
    std::lock_guard<std::mutex> lock(g_mutex);
    
    g_guestBase = base;
    g_initialized = true;
    
    LOG_INFO("[MENU_HOOKS] Initializing native menu hooks system");
    LOGF_INFO("[MENU_HOOKS] Guest base address: {:p}", (void*)base);
    
    // Register default custom GXT strings for menu items
    RegisterCustomString("FE_RES_SCALE", "Resolution Scale");
    RegisterCustomString("FE_VSYNC", "VSync");
    RegisterCustomString("FE_FPS_LIMIT", "FPS Limit");
    RegisterCustomString("FE_MSAA", "Anti-Aliasing (MSAA)");
    RegisterCustomString("FE_MODERN_AA", "Modern AA");
    RegisterCustomString("FE_UPSCALER", "Upscaler");
    RegisterCustomString("FE_UPSCALE_Q", "Upscale Quality");
    RegisterCustomString("FE_FRAMEGEN", "Frame Generation");
    RegisterCustomString("FE_DOF", "Depth of Field");
    RegisterCustomString("FE_MOTION_BLUR", "Motion Blur");
    RegisterCustomString("FE_FILM_GRAIN", "Film Grain");
    RegisterCustomString("FE_CHROM_AB", "Chromatic Aberration");
    RegisterCustomString("FE_SHADOW_RES", "Shadow Resolution");
    RegisterCustomString("FE_SHADOW_FILT", "Shadow Filter");
    RegisterCustomString("FE_SSAO", "Ambient Occlusion");
    RegisterCustomString("FE_RENDER_DIST", "Render Distance");
    RegisterCustomString("FE_LOD_DIST", "LOD Distance");
    
    // Value strings
    RegisterCustomString("FE_OFF", "Off");
    RegisterCustomString("FE_ON", "On");
    RegisterCustomString("FE_LOW", "Low");
    RegisterCustomString("FE_MEDIUM", "Medium");
    RegisterCustomString("FE_HIGH", "High");
    RegisterCustomString("FE_ULTRA", "Ultra");
    RegisterCustomString("FE_TAA", "TAA");
    RegisterCustomString("FE_SMAA", "SMAA");
    RegisterCustomString("FE_FSR1", "FSR 1.0");
    RegisterCustomString("FE_FSR3", "FSR 3");
    RegisterCustomString("FE_DLSS", "DLSS");
    RegisterCustomString("FE_XESS", "XeSS");
    RegisterCustomString("FE_METALFX", "MetalFX");
    
    LOGF_INFO("[MENU_HOOKS] Registered {} custom GXT strings", g_customStrings.size());
    LOG_INFO("[MENU_HOOKS] Initialization complete");
}

void ApplyMenuPatches(uint8_t* base) {
    if (!base) base = g_guestBase;
    if (!base) {
        LOG_ERROR("[MENU_HOOKS] Cannot apply patches - base address not set");
        return;
    }
    
    // Phase 2: Menu item array extension would go here
    // For now, we rely on value hooks (Phase 1) which work with existing menu items
    LOG_INFO("[MENU_HOOKS] Menu patches applied (Phase 1 - value hooks active)");
}

// =============================================================================
// Value Translation - Config <-> Menu
// =============================================================================

int32_t GetCustomValue(int32_t index) {
    switch (static_cast<CustomValueIndex>(index)) {
        case CustomValueIndex::ResolutionScale:
            return ResolutionScaleToMenu(Config::ResolutionScale);
            
        case CustomValueIndex::VSync:
            return Config::VSync ? 1 : 0;
            
        case CustomValueIndex::FPS:
            return Config::FPS;
            
        case CustomValueIndex::MSAA:
            // Map EAntiAliasing enum to 0/1/2/3 (Off/2x/4x/8x)
            switch (Config::AntiAliasing.Value) {
                case EAntiAliasing::Off:    return 0;
                case EAntiAliasing::MSAA2x: return 1;
                case EAntiAliasing::MSAA4x: return 2;
                case EAntiAliasing::MSAA8x: return 3;
                default: return 0;
            }
            
        case CustomValueIndex::ModernAA:
            // Map EModernAA enum
            switch (Config::ModernAA.Value) {
                case EModernAA::Off:  return 0;
                case EModernAA::TAA:  return 1;
                case EModernAA::SMAA: return 2;
                case EModernAA::FSR1: return 3;
                default: return 0;
            }
            
        case CustomValueIndex::Upscaler:
            // Map EUpscaler enum
            switch (Config::Upscaler.Value) {
                case EUpscaler::Off:     return 0;
                case EUpscaler::FSR1:    return 1;
                case EUpscaler::FSR3:    return 2;
                case EUpscaler::DLSS:    return 3;
                case EUpscaler::XeSS:    return 4;
                case EUpscaler::MetalFX: return 5;
                default: return 0;
            }
            
        case CustomValueIndex::UpscaleQuality:
            // Map EUpscaleQuality enum
            switch (Config::UpscaleQuality.Value) {
                case EUpscaleQuality::UltraQuality:      return 0;
                case EUpscaleQuality::Quality:           return 1;
                case EUpscaleQuality::Balanced:          return 2;
                case EUpscaleQuality::Performance:       return 3;
                case EUpscaleQuality::UltraPerformance:  return 4;
                default: return 1;
            }
            
        case CustomValueIndex::FrameGeneration:
            // Map EFrameGeneration enum
            switch (Config::FrameGeneration.Value) {
                case EFrameGeneration::Off:     return 0;
                case EFrameGeneration::FSR3FG:  return 1;
                case EFrameGeneration::DLSSFG:  return 2;
                default: return 0;
            }
            
        case CustomValueIndex::DepthOfField:
            // Map EDepthOfField enum
            switch (Config::DepthOfField.Value) {
                case EDepthOfField::Off:    return 0;
                case EDepthOfField::Low:    return 1;
                case EDepthOfField::Medium: return 2;
                case EDepthOfField::High:   return 3;
                case EDepthOfField::Ultra:  return 4;
                default: return 0;
            }
            
        case CustomValueIndex::MotionBlur:
            // Map EMotionBlur enum
            switch (Config::MotionBlur.Value) {
                case EMotionBlur::Off:      return 0;
                case EMotionBlur::Camera:   return 1;
                case EMotionBlur::Enhanced: return 2;
                default: return 0;
            }
            
        case CustomValueIndex::FilmGrain:
            // Map EFilmGrain enum
            switch (Config::FilmGrain.Value) {
                case EFilmGrain::Off:    return 0;
                case EFilmGrain::Light:  return 1;
                case EFilmGrain::Medium: return 2;
                case EFilmGrain::Heavy:  return 3;
                default: return 0;
            }
            
        case CustomValueIndex::ChromaticAberration:
            // Map EChromaticAberration enum
            switch (Config::ChromaticAberration.Value) {
                case EChromaticAberration::Off:    return 0;
                case EChromaticAberration::Subtle: return 1;
                case EChromaticAberration::Normal: return 2;
                case EChromaticAberration::Strong: return 3;
                default: return 0;
            }
            
        case CustomValueIndex::ShadowResolution:
            // Map EShadowResolution enum
            switch (Config::ShadowResolution.Value) {
                case EShadowResolution::x512:  return 0;
                case EShadowResolution::x1024: return 1;
                case EShadowResolution::x2048: return 2;
                case EShadowResolution::x4096: return 3;
                case EShadowResolution::x8192: return 4;
                default: return 2;
            }
            
        case CustomValueIndex::ShadowFilter:
            // Map EShadowFilter enum
            switch (Config::ShadowFilter.Value) {
                case EShadowFilter::Off:     return 0;
                case EShadowFilter::PCF3x3:  return 1;
                case EShadowFilter::PCF5x5:  return 2;
                case EShadowFilter::PCF7x7:  return 3;
                case EShadowFilter::PCSS:    return 4;
                default: return 1;
            }
            
        case CustomValueIndex::SSAO:
            // Map ESSAO enum
            switch (Config::SSAO.Value) {
                case ESSAO::Off:    return 0;
                case ESSAO::Low:    return 1;
                case ESSAO::Medium: return 2;
                case ESSAO::High:   return 3;
                case ESSAO::Ultra:  return 4;
                default: return 0;
            }
            
        case CustomValueIndex::RenderDistanceMultiplier:
            return MultiplierToMenu(Config::RenderDistanceMultiplier);
            
        case CustomValueIndex::LODDistanceMultiplier:
            return MultiplierToMenu(Config::LODDistanceMultiplier);
            
        default:
            if (g_verboseLogging) {
                LOGF_WARNING("[MENU_HOOKS] GetCustomValue: unhandled index {}", index);
            }
            return 0;
    }
}

void SetCustomValue(int32_t index, int32_t value) {
    if (g_verboseLogging) {
        LOGF_INFO("[MENU_HOOKS] SetCustomValue: index={}, value={}", index, value);
    }
    
    switch (static_cast<CustomValueIndex>(index)) {
        case CustomValueIndex::ResolutionScale:
            Config::ResolutionScale = MenuToResolutionScale(value);
            break;
            
        case CustomValueIndex::VSync:
            Config::VSync = (value != 0);
            break;
            
        case CustomValueIndex::FPS:
            Config::FPS = value;
            break;
            
        case CustomValueIndex::MSAA:
            switch (value) {
                case 0: Config::AntiAliasing = EAntiAliasing::Off;    break;
                case 1: Config::AntiAliasing = EAntiAliasing::MSAA2x; break;
                case 2: Config::AntiAliasing = EAntiAliasing::MSAA4x; break;
                case 3: Config::AntiAliasing = EAntiAliasing::MSAA8x; break;
            }
            break;
            
        case CustomValueIndex::ModernAA:
            switch (value) {
                case 0: Config::ModernAA = EModernAA::Off;  break;
                case 1: Config::ModernAA = EModernAA::TAA;  break;
                case 2: Config::ModernAA = EModernAA::SMAA; break;
                case 3: Config::ModernAA = EModernAA::FSR1; break;
            }
            break;
            
        case CustomValueIndex::Upscaler:
            switch (value) {
                case 0: Config::Upscaler = EUpscaler::Off;     break;
                case 1: Config::Upscaler = EUpscaler::FSR1;    break;
                case 2: Config::Upscaler = EUpscaler::FSR3;    break;
                case 3: Config::Upscaler = EUpscaler::DLSS;    break;
                case 4: Config::Upscaler = EUpscaler::XeSS;    break;
                case 5: Config::Upscaler = EUpscaler::MetalFX; break;
            }
            break;
            
        case CustomValueIndex::UpscaleQuality:
            switch (value) {
                case 0: Config::UpscaleQuality = EUpscaleQuality::UltraQuality;     break;
                case 1: Config::UpscaleQuality = EUpscaleQuality::Quality;          break;
                case 2: Config::UpscaleQuality = EUpscaleQuality::Balanced;         break;
                case 3: Config::UpscaleQuality = EUpscaleQuality::Performance;      break;
                case 4: Config::UpscaleQuality = EUpscaleQuality::UltraPerformance; break;
            }
            break;
            
        case CustomValueIndex::FrameGeneration:
            switch (value) {
                case 0: Config::FrameGeneration = EFrameGeneration::Off;    break;
                case 1: Config::FrameGeneration = EFrameGeneration::FSR3FG; break;
                case 2: Config::FrameGeneration = EFrameGeneration::DLSSFG; break;
            }
            break;
            
        case CustomValueIndex::DepthOfField:
            switch (value) {
                case 0: Config::DepthOfField = EDepthOfField::Off;    break;
                case 1: Config::DepthOfField = EDepthOfField::Low;    break;
                case 2: Config::DepthOfField = EDepthOfField::Medium; break;
                case 3: Config::DepthOfField = EDepthOfField::High;   break;
                case 4: Config::DepthOfField = EDepthOfField::Ultra;  break;
            }
            break;
            
        case CustomValueIndex::MotionBlur:
            switch (value) {
                case 0: Config::MotionBlur = EMotionBlur::Off;      break;
                case 1: Config::MotionBlur = EMotionBlur::Camera;   break;
                case 2: Config::MotionBlur = EMotionBlur::Enhanced; break;
            }
            break;
            
        case CustomValueIndex::FilmGrain:
            switch (value) {
                case 0: Config::FilmGrain = EFilmGrain::Off;    break;
                case 1: Config::FilmGrain = EFilmGrain::Light;  break;
                case 2: Config::FilmGrain = EFilmGrain::Medium; break;
                case 3: Config::FilmGrain = EFilmGrain::Heavy;  break;
            }
            break;
            
        case CustomValueIndex::ChromaticAberration:
            switch (value) {
                case 0: Config::ChromaticAberration = EChromaticAberration::Off;    break;
                case 1: Config::ChromaticAberration = EChromaticAberration::Subtle; break;
                case 2: Config::ChromaticAberration = EChromaticAberration::Normal; break;
                case 3: Config::ChromaticAberration = EChromaticAberration::Strong; break;
            }
            break;
            
        case CustomValueIndex::ShadowResolution:
            switch (value) {
                case 0: Config::ShadowResolution = EShadowResolution::x512;  break;
                case 1: Config::ShadowResolution = EShadowResolution::x1024; break;
                case 2: Config::ShadowResolution = EShadowResolution::x2048; break;
                case 3: Config::ShadowResolution = EShadowResolution::x4096; break;
                case 4: Config::ShadowResolution = EShadowResolution::x8192; break;
            }
            break;
            
        case CustomValueIndex::ShadowFilter:
            switch (value) {
                case 0: Config::ShadowFilter = EShadowFilter::Off;    break;
                case 1: Config::ShadowFilter = EShadowFilter::PCF3x3; break;
                case 2: Config::ShadowFilter = EShadowFilter::PCF5x5; break;
                case 3: Config::ShadowFilter = EShadowFilter::PCF7x7; break;
                case 4: Config::ShadowFilter = EShadowFilter::PCSS;   break;
            }
            break;
            
        case CustomValueIndex::SSAO:
            switch (value) {
                case 0: Config::SSAO = ESSAO::Off;    break;
                case 1: Config::SSAO = ESSAO::Low;    break;
                case 2: Config::SSAO = ESSAO::Medium; break;
                case 3: Config::SSAO = ESSAO::High;   break;
                case 4: Config::SSAO = ESSAO::Ultra;  break;
            }
            break;
            
        case CustomValueIndex::RenderDistanceMultiplier:
            Config::RenderDistanceMultiplier = MenuToMultiplier(value);
            break;
            
        case CustomValueIndex::LODDistanceMultiplier:
            Config::LODDistanceMultiplier = MenuToMultiplier(value);
            break;
            
        default:
            if (g_verboseLogging) {
                LOGF_WARNING("[MENU_HOOKS] SetCustomValue: unhandled index {}", index);
            }
            break;
    }
}

// =============================================================================
// Menu State Management
// =============================================================================

void OnMenuOpened() {
    std::lock_guard<std::mutex> lock(g_mutex);
    
    if (g_verboseLogging) {
        LOG_INFO("[MENU_HOOKS] Menu opened - syncing Config to menu values");
    }
    
    g_menuOpen = true;
    
    if (g_guestBase) {
        SyncConfigToMenu(g_guestBase);
    }
}

void OnMenuClosed() {
    std::lock_guard<std::mutex> lock(g_mutex);
    
    if (g_verboseLogging) {
        LOG_INFO("[MENU_HOOKS] Menu closed - syncing menu values to Config");
    }
    
    g_menuOpen = false;
    
    if (g_guestBase) {
        SyncMenuToConfig(g_guestBase);
        Config::Save();
    }
}

void SyncConfigToMenu(uint8_t* base) {
    if (!base) return;
    
    // Write custom values to the menu value array at indices 100-124
    // This ensures the menu displays current Config values
    for (int i = static_cast<int>(CustomValueIndex::First); 
         i <= static_cast<int>(CustomValueIndex::Last); i++) {
        uint32_t addr = Addresses::MENU_VALUES_ARRAY + (i * 4);
        int32_t value = GetCustomValue(i);
        WriteS32BE(base, addr, value);
    }
    
    if (g_verboseLogging) {
        LOG_INFO("[MENU_HOOKS] Synced Config values to menu array [100-124]");
    }
}

void SyncMenuToConfig(uint8_t* base) {
    if (!base) return;
    
    // Read values from menu array and update Config
    for (int i = static_cast<int>(CustomValueIndex::First); 
         i <= static_cast<int>(CustomValueIndex::Last); i++) {
        uint32_t addr = Addresses::MENU_VALUES_ARRAY + (i * 4);
        int32_t value = ReadS32BE(base, addr);
        SetCustomValue(i, value);
    }
    
    if (g_verboseLogging) {
        LOG_INFO("[MENU_HOOKS] Synced menu array values to Config");
    }
}

// =============================================================================
// GXT String Injection
// =============================================================================

const char* GetCustomString(const char* key) {
    if (!key) return nullptr;
    
    auto it = g_customStrings.find(key);
    if (it != g_customStrings.end()) {
        return it->second.c_str();
    }
    return nullptr;
}

void RegisterCustomString(const std::string& key, const std::string& value) {
    g_customStrings[key] = value;
}

// =============================================================================
// Debug/Logging
// =============================================================================

void SetVerboseLogging(bool enabled) {
    g_verboseLogging = enabled;
}

void DumpMenuState(uint8_t* base) {
    if (!base) {
        base = g_guestBase;
    }
    if (!base) {
        LOG_ERROR("[MENU_HOOKS] Cannot dump state - base address not set");
        return;
    }
    
    LOG_INFO("[MENU_HOOKS] === Menu State Dump ===");
    
    // Read current screen index
    int32_t screenIndex = ReadS32BE(base, Addresses::CURRENT_SCREEN_INDEX);
    LOGF_INFO("[MENU_HOOKS] Current screen index: {}", screenIndex);
    
    // Dump custom value indices
    LOG_INFO("[MENU_HOOKS] Custom values (indices 100-116):");
    for (int i = 100; i <= 116; i++) {
        uint32_t addr = Addresses::MENU_VALUES_ARRAY + (i * 4);
        int32_t value = ReadS32BE(base, addr);
        LOGF_INFO("[MENU_HOOKS]   [{}] = {} (Config: {})", 
                  i, value, GetCustomValue(i));
    }
    
    LOG_INFO("[MENU_HOOKS] === End Dump ===");
}

} // namespace MenuHooks

// =============================================================================
// PPC Function Hooks
// =============================================================================
// These hooks monitor menu state via byte_82BEC62A and sync Config values
// to/from the menu value array (dword_82BEC638[]).
//
// IMPORTANT: sub_8213B268/B350 are lookup helpers, NOT value accessors!
// Values are accessed DIRECTLY from dword_82BEC638[] via array indexing.
//
// NOTE: We use _hook suffix and extern "C" to match the forward declarations
// in imports.cpp for PatchFuncMapping compatibility on macOS.

// Forward declarations of original functions (from PPC recompiled code)
extern "C" void __imp__sub_8212FCC8(PPCContext &ctx, uint8_t *base);  // Menu frame update
extern "C" void __imp__sub_821485D8(PPCContext &ctx, uint8_t *base);  // Menu XML parser
extern "C" void __imp__sub_82273620(PPCContext &ctx, uint8_t *base);  // GXT string lookup

// =============================================================================
// sub_8212FCC8 - Menu Frame Update
// =============================================================================
// VERIFIED FROM PPC (ultimate truth):
//   - byte_82BEC62A = 1 is SET at PPC line 38433 (inside this function)
//   - byte_82BEC62A = 0 is SET at PPC line 39336 (also inside this function)
//   - Address verified: 0x82BF0000 + (-14806) = 0x82BEC62A
//
// We track state AFTER the function completes using a static variable.
extern "C" void sub_8212FCC8_hook(PPCContext &ctx, uint8_t *base) {
    // Track previous state across calls
    static uint8_t s_previousMenuState = 0;
    static bool s_initialized = false;
    
    // Call original function first (this may set or clear byte_82BEC62A)
    __imp__sub_8212FCC8(ctx, base);
    
    // Read menu state AFTER the call completes
    uint8_t currentMenuState = *(base + MenuHooks::Addresses::MENU_ACTIVE_FLAG);
    
    // Initialize on first call
    if (!s_initialized) {
        s_previousMenuState = currentMenuState;
        s_initialized = true;
        if (currentMenuState) {
            LOG_INFO("[MENU_HOOKS] Initialized with menu already open");
        }
        return;
    }
    
    // Detect state transitions
    if (s_previousMenuState == 0 && currentMenuState == 1) {
        // Menu just opened (0 -> 1)
        LOG_INFO("[MENU_HOOKS] Menu OPENED (byte_82BEC62A: 0->1)");
        MenuHooks::OnMenuOpened();
    }
    else if (s_previousMenuState == 1 && currentMenuState == 0) {
        // Menu just closed (1 -> 0)
        LOG_INFO("[MENU_HOOKS] Menu CLOSED (byte_82BEC62A: 1->0)");
        MenuHooks::OnMenuClosed();
    }
    
    // Update tracked state
    s_previousMenuState = currentMenuState;
}

// =============================================================================
// Phase 2: sub_821485D8 - Menu XML parser/loader
// =============================================================================
// This function is called when the menu system loads its XML configuration.
// We hook it to inject custom menu items after the native items are loaded.
//
// Post-hook approach:
// 1. Let original function parse XML and populate menu structures
// 2. After completion, extend the Display screen's item array
// 3. Inject custom menu items for LibertyRecomp settings
extern "C" void sub_821485D8_hook(PPCContext &ctx, uint8_t *base) {
    static bool s_injectionDone = false;
    static int s_callCount = 0;
    s_callCount++;
    
    // Call original first - let it parse the XML
    __imp__sub_821485D8(ctx, base);
    
    // Only inject once after first successful parse
    if (!s_injectionDone) {
        LOGF_INFO("[MENU_HOOKS] sub_821485D8 (Menu XML parser) called #{}", s_callCount);
        
        // Phase 2 injection would happen here:
        // 1. Read Display screen item pointer from unk_83142B10 + (DISPLAY_SCREEN * 24)
        // 2. Read item count from unk_83142B14 + (DISPLAY_SCREEN * 24)
        // 3. Allocate new array with space for custom items
        // 4. Copy existing items and append custom items
        // 5. Update pointer and count
        
        // For now, we log that injection would occur and mark as done
        // Full implementation requires runtime verification of:
        // - Correct Display screen index
        // - Menu item structure layout (22 bytes confirmed from pseudocode)
        // - Guest memory allocation function
        
        LOG_INFO("[MENU_HOOKS] Menu XML parsed - Phase 2 injection point ready");
        LOGF_INFO("[MENU_HOOKS] Screen item pointers at: 0x{:08X}", MenuHooks::Addresses::SCREEN_ITEM_PTRS);
        LOGF_INFO("[MENU_HOOKS] Screen item counts at: 0x{:08X}", MenuHooks::Addresses::SCREEN_ITEM_COUNTS);
        
        // Initialize MenuHooks with base pointer if not done yet
        MenuHooks::Initialize(base);
        
        s_injectionDone = true;
    }
}

// =============================================================================
// Phase 3: sub_82273620 - GXT string lookup
// =============================================================================
// This function looks up localized strings from GXT files.
// We hook it to return custom strings for our injected menu items.
//
// Parameters: r3 = string key (e.g., "FE_UPSCALER")
// Returns: r3 = pointer to localized string
extern "C" void sub_82273620_hook(PPCContext &ctx, uint8_t *base) {
    uint32_t keyAddr = ctx.r3.u32;
    
    // Read the key string from guest memory
    if (keyAddr != 0 && keyAddr < 0x90000000) {
        const char* key = reinterpret_cast<const char*>(base + keyAddr);
        
        // Check if this is one of our custom keys
        const char* customString = MenuHooks::GetCustomString(key);
        if (customString != nullptr) {
            // Return pointer to our custom string
            // Note: This is a host pointer, which may not work directly
            // A proper implementation would need to:
            // 1. Allocate guest memory for the string
            // 2. Copy our string there
            // 3. Return the guest address
            
            // For now, log the lookup and fall through to original
            static std::unordered_set<std::string> s_loggedKeys;
            if (s_loggedKeys.find(key) == s_loggedKeys.end()) {
                LOGF_INFO("[MENU_HOOKS] GXT lookup for custom key '{}' -> '{}'", key, customString);
                s_loggedKeys.insert(key);
            }
        }
    }
    
    // Call original for all lookups (custom string injection needs guest memory allocation)
    __imp__sub_82273620(ctx, base);
}
