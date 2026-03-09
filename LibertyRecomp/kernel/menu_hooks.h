// =============================================================================
// NATIVE MENU HOOKS - GTA IV Recompiled
// =============================================================================
// This module provides hooks to inject custom options into GTA IV's native
// pause menu (Display tab) and redirect value read/write to the Config system.
//
// Architecture:
//   - Values stored directly in dword_82BEC638[] (125-element array)
//   - Menu state flag: byte_82BEC62A (1=active, 0=inactive)
//   - Sync Config values to array on menu open, read back on close
//
// Key data structures:
//   0x82BEC62A - byte_82BEC62A    - Menu active flag (1=open, 0=closed)
//   0x82BEC638 - dword_82BEC638[] - 125-element value array (menu option values)
//   0x82BEC844 - dword_82BEC844   - Current menu screen index
//   0x83142B10 - unk_83142B10     - Pointer array to menu screen item arrays
//   0x83142B14 - unk_83142B14     - Item count array per screen
//
// Key functions hooked:
//   sub_8212FCC8 - Menu frame update (monitors byte_82BEC62A transitions)
//   sub_821485D8 - Menu XML parser/loader (Phase 2 - item injection)
//   sub_82273620 - GXT string lookup (Phase 3 - custom strings)
//
// NOTE: sub_8213B268/B350 are lookup helpers, NOT value accessors!
//       sub_8259AFF8/B018 are script commands, not internal menu events!
// =============================================================================

#pragma once

#include <cstdint>
#include <string>
#include <unordered_map>
#include <cpu/ppc_context.h>

namespace MenuHooks {

// =============================================================================
// Custom Value Index Allocation (100-124 reserved for LibertyRecomp)
// =============================================================================
// These indices map into dword_82BEC638[] but are intercepted by our hooks
// to redirect to the Config system instead of the game's native storage.

enum class CustomValueIndex : int32_t {
    // Video/Display Core
    ResolutionScale         = 100,  // Slider: 0.25x-2.0x (stored as 25-200)
    VSync                   = 101,  // Toggle: On/Off
    FPS                     = 102,  // Slider: 15-241
    MSAA                    = 103,  // Enum: Off/2x/4x/8x
    
    // Modern Anti-Aliasing
    ModernAA                = 104,  // Enum: Off/TAA/SMAA/FSR1
    
    // Upscaling
    Upscaler                = 105,  // Enum: Off/FSR1/FSR3/DLSS/XeSS/MetalFX
    UpscaleQuality          = 106,  // Enum: UltraQuality/Quality/Balanced/Performance/UltraPerformance
    FrameGeneration         = 107,  // Enum: Off/FSR3FG/DLSSFG
    
    // Post-Processing
    DepthOfField            = 108,  // Enum: Off/Low/Medium/High/Ultra
    MotionBlur              = 109,  // Enum: Off/Camera/Enhanced
    FilmGrain               = 110,  // Enum: Off/Light/Medium/Heavy
    ChromaticAberration     = 111,  // Enum: Off/Subtle/Normal/Strong
    
    // Quality Settings
    ShadowResolution        = 112,  // Enum: 512/1024/2048/4096/8192
    ShadowFilter            = 113,  // Enum: Off/PCF3x3/PCF5x5/PCF7x7/PCSS
    SSAO                    = 114,  // Enum: Off/Low/Medium/High/Ultra
    
    // Distance/LOD
    RenderDistanceMultiplier = 115, // Slider: 50-300 (0.5x-3.0x)
    LODDistanceMultiplier   = 116,  // Slider: 50-300 (0.5x-3.0x)
    
    // Reserved for future use
    Reserved117             = 117,
    Reserved118             = 118,
    Reserved119             = 119,
    Reserved120             = 120,
    Reserved121             = 121,
    Reserved122             = 122,
    Reserved123             = 123,
    Reserved124             = 124,
    
    // Bounds
    First = ResolutionScale,
    Last  = Reserved124
};

// =============================================================================
// Menu Screen Indices
// =============================================================================
enum class MenuScreen : int32_t {
    Unknown         = -1,
    // These need runtime verification - indices may vary
    Game            = 0,
    Display         = 1,  // Primary target for video options
    Audio           = 2,
    Controls        = 3,
    // Add more as discovered
};

// =============================================================================
// Display Value Types (from dword_8314295C[])
// =============================================================================
enum class DisplayValueType : uint8_t {
    None            = 100,  // No value display
    Slider          = 101,  // Brightness/Contrast style slider
    OnOff           = 102,  // On/Off toggle (MENU_DISPLAY_ON_OFF)
    // Add more as discovered from runtime analysis
};

// =============================================================================
// Menu Item Structure (22 bytes per item)
// =============================================================================
#pragma pack(push, 1)
struct MenuItemDef {
    uint8_t  type;           // Offset 0: Item behavior type
    uint8_t  reserved[17];   // Offsets 1-17: Various fields (flags, callbacks, etc.)
    int16_t  valueIndex;     // Offset 18: Index into dword_82BEC638[]
    uint8_t  displayMode;    // Offset 20: Display flags
    uint8_t  displayType;    // Offset 21: Value type index (101=slider, etc.)
};
#pragma pack(pop)
static_assert(sizeof(MenuItemDef) == 22, "MenuItemDef must be 22 bytes");

// =============================================================================
// Memory Address Constants (Xbox 360 guest addresses)
// =============================================================================
// VERIFIED FROM PPC CODE (ultimate truth) - ppc_recomp.0.cpp
//
// Address calculation pattern in PPC:
//   lis rX, -32065     ; rX = 0x82BF0000
//   lbz/stb rY, offset(rX)
//
// Verified addresses:
//   0x82BF0000 + (-14806) = 0x82BEC62A  (byte_82BEC62A - menu active flag)
//   0x82BF0000 + (-14792) = 0x82BEC638  (dword_82BEC638 - values array)
//   0x82BF0000 + (-14798) = 0x82BEC632  (byte_82BEC632)
//   0x82BF0000 + (-14796) = 0x82BEC634  (byte_82BEC634)
//   0x82BF0000 + (-14795) = 0x82BEC635  (byte_82BEC635)
// =============================================================================
namespace Addresses {

// Menu state and value storage (VERIFIED from PPC)
constexpr uint32_t MENU_ACTIVE_FLAG      = 0x82BEC62A;  // byte_82BEC62A (1=open, 0=closed)
constexpr uint32_t MENU_VALUES_ARRAY     = 0x82BEC638;  // dword_82BEC638[125]
constexpr uint32_t MENU_VALUES_COUNT     = 125;         // Original array size
constexpr uint32_t CURRENT_SCREEN_INDEX  = 0x82BEC844;  // dword_82BEC844

// Menu screen item arrays (24-byte stride per screen)
constexpr uint32_t SCREEN_ITEM_PTRS      = 0x83142B10;  // unk_83142B10 - pointers
constexpr uint32_t SCREEN_ITEM_COUNTS    = 0x83142B14;  // unk_83142B14 - counts (+4)
constexpr uint32_t SCREEN_STRUCT_STRIDE  = 24;          // 6 DWORDs per screen

// Display value type definitions
constexpr uint32_t DISPLAY_VALUE_TYPES   = 0x8314295C;  // dword_8314295C[]
constexpr uint32_t DISPLAY_VALUE_LOOKUP  = 0x83142958;  // unk_83142958

// Function addresses (for reference - actual hooks use PPC_FUNC)
constexpr uint32_t FN_MENU_FRAME_UPDATE  = 0x8212FCC8;  // sub_8212FCC8 - sets byte_82BEC62A
constexpr uint32_t FN_MENU_XML_PARSER    = 0x821485D8;  // sub_821485D8
constexpr uint32_t FN_PROCESS_SELECTION  = 0x8224EAA0;  // sub_8224EAA0
constexpr uint32_t FN_GXT_STRING_LOOKUP  = 0x82273620;  // sub_82273620

// Script command handlers (fallback - not always called)
constexpr uint32_t FN_ACTIVATE_FRONTEND  = 0x8259AFF8;  // sub_8259AFF8 (script cmd)
constexpr uint32_t FN_DEACTIVATE_FRONTEND= 0x8259B018;  // sub_8259B018 (script cmd)

// NOTE: These are lookup helpers, NOT value accessors - do not hook:
// constexpr uint32_t FN_GET_SETTING_V1  = 0x8213B268;  // sub_8213B268 - lookup helper
// constexpr uint32_t FN_GET_SETTING_V2  = 0x8213B350;  // sub_8213B350 - lookup helper
// constexpr uint32_t FN_APPLY_SETTING   = 0x8213AF40;  // sub_8213AF40 - not needed

} // namespace Addresses

// =============================================================================
// Initialization
// =============================================================================

/// Initialize menu hooks system
/// Call this during game initialization (after memory regions are set up)
void Initialize(uint8_t* base);

/// Apply runtime patches to inject menu items (Phase 2)
/// Called after menu XML is parsed
void ApplyMenuPatches(uint8_t* base);

// =============================================================================
// Value Translation (Config <-> Menu)
// =============================================================================

/// Get custom value for menu display (called by hooked sub_8213B268/B350)
/// Returns the value that should be displayed in the menu
int32_t GetCustomValue(int32_t index);

/// Set custom value from menu interaction (called by hooked sub_8213AF40)
/// Syncs the menu value to the Config system
void SetCustomValue(int32_t index, int32_t value);

/// Check if an index is a custom (LibertyRecomp) index
inline bool IsCustomIndex(int32_t index) {
    return index >= static_cast<int32_t>(CustomValueIndex::First) &&
           index <= static_cast<int32_t>(CustomValueIndex::Last);
}

// =============================================================================
// Menu State Management
// =============================================================================

/// Called when frontend (pause menu) is activated
void OnMenuOpened();

/// Called when frontend is deactivated
void OnMenuClosed();

/// Sync all Config values to menu value array
/// Call on menu open to ensure menu shows current Config state
void SyncConfigToMenu(uint8_t* base);

/// Sync all menu values to Config system
/// Call on menu close to persist changes
void SyncMenuToConfig(uint8_t* base);

// =============================================================================
// GXT String Injection (Phase 3)
// =============================================================================

/// Get custom string for a GXT key
/// Returns nullptr if key is not a custom key
const char* GetCustomString(const char* key);

/// Register a custom GXT string
void RegisterCustomString(const std::string& key, const std::string& value);

// =============================================================================
// Debug/Logging
// =============================================================================

/// Enable verbose logging of menu hook activity
void SetVerboseLogging(bool enabled);

/// Dump current menu state to log
void DumpMenuState(uint8_t* base);

} // namespace MenuHooks
