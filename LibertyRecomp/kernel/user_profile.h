/**
 * LibertyRecomp - User Profile System
 * 
 * Centralized Xbox 360 user profile emulation based on Xenia's implementation.
 * Provides a "Niko Bellic" built-in profile for GTA IV.
 * 
 * Reference: xenia/kernel/xam/user_profile.h
 */

#pragma once

#include <cstdint>
#include <string>
#include <vector>
#include <unordered_map>
#include <memory>
#include <mutex>

namespace Liberty {

/**
 * Xbox 360 Profile Setting Types
 * From XDK documentation and Xenia implementation
 */
enum class ProfileSettingType : uint8_t {
    Content     = 0,
    Int32       = 1,
    Int64       = 2,
    Double      = 3,
    UnicodeStr  = 4,
    Float       = 5,
    Binary      = 6,
    DateTime    = 7,
    Unset       = 0xFF
};

/**
 * Xbox 360 Signin States
 */
enum class SigninState : uint32_t {
    NotSignedIn     = 0,
    SignedInLocally = 1,
    SignedInToLive  = 2
};

/**
 * Xbox Live Membership Tiers
 */
enum class MembershipTier : uint32_t {
    Unknown     = 0,
    Silver      = 3,
    Gold        = 6,
    FamilyGold  = 9
};

/**
 * Profile Setting base class
 */
class ProfileSetting {
public:
    uint32_t settingId;
    ProfileSettingType type;
    bool isSet;
    uint32_t loadedTitleId;

    ProfileSetting(uint32_t id, ProfileSettingType t, bool set = true)
        : settingId(id), type(t), isSet(set), loadedTitleId(0) {}
    virtual ~ProfileSetting() = default;
    
    bool isTitleSpecific() const {
        return (settingId & 0x3F00) == 0x3F00;
    }
    
    virtual std::vector<uint8_t> serialize() const { return {}; }
    virtual void deserialize(const std::vector<uint8_t>& data) {}
};

/**
 * Integer setting (32-bit)
 */
class Int32Setting : public ProfileSetting {
public:
    int32_t value;
    
    Int32Setting(uint32_t id, int32_t val)
        : ProfileSetting(id, ProfileSettingType::Int32), value(val) {}
    
    std::vector<uint8_t> serialize() const override {
        std::vector<uint8_t> data(4);
        *reinterpret_cast<int32_t*>(data.data()) = value;
        return data;
    }
};

/**
 * Integer setting (64-bit)
 */
class Int64Setting : public ProfileSetting {
public:
    int64_t value;
    
    Int64Setting(uint32_t id, int64_t val)
        : ProfileSetting(id, ProfileSettingType::Int64), value(val) {}
};

/**
 * Float setting
 */
class FloatSetting : public ProfileSetting {
public:
    float value;
    
    FloatSetting(uint32_t id, float val)
        : ProfileSetting(id, ProfileSettingType::Float), value(val) {}
};

/**
 * Unicode string setting
 */
class UnicodeSetting : public ProfileSetting {
public:
    std::u16string value;
    
    UnicodeSetting(uint32_t id, const std::u16string& val)
        : ProfileSetting(id, ProfileSettingType::UnicodeStr), value(val) {}
};

/**
 * Binary data setting (used for saves)
 */
class BinarySetting : public ProfileSetting {
public:
    std::vector<uint8_t> value;
    
    BinarySetting(uint32_t id)
        : ProfileSetting(id, ProfileSettingType::Binary, false) {}
    
    BinarySetting(uint32_t id, const std::vector<uint8_t>& val)
        : ProfileSetting(id, ProfileSettingType::Binary), value(val) {}
    
    std::vector<uint8_t> serialize() const override { return value; }
    void deserialize(const std::vector<uint8_t>& data) override {
        value = data;
        isSet = true;
    }
};

/**
 * Xbox 360 User Profile
 * 
 * Emulates a complete Xbox 360 user profile with:
 * - XUID (Xbox User ID)
 * - Gamertag
 * - Profile settings (controller prefs, gamercard, etc.)
 * - Title-specific settings (save data)
 * 
 * Default profile is "Niko" for GTA IV theme.
 */
class UserProfile {
public:
    // Default XUID that passes Xbox validation masks
    // Bit pattern 0x00C0000000000000 (3<<54) must NOT be set
    // This value is used by Xenia and is known to work
    static constexpr uint64_t DEFAULT_XUID = 0xB13EBABEBABEBABE;
    
    // GTA IV themed default name
    static constexpr const char* DEFAULT_NAME = "Niko";
    
    // Singleton access
    static UserProfile& Instance();
    
    // Profile identity
    uint64_t xuid() const { return xuid_; }
    const std::string& name() const { return name_; }
    SigninState signinState() const { return signinState_; }
    MembershipTier membershipTier() const { return membershipTier_; }
    
    // For XamUserGetSigninInfo - returns 1|2 for "local | online profile"
    uint32_t type() const { return 1 | 2; }
    
    // Setters (for future customization)
    void setName(const std::string& name) { name_ = name; }
    void setXuid(uint64_t xuid) { xuid_ = xuid; }
    
    // Settings management
    void addSetting(std::unique_ptr<ProfileSetting> setting);
    ProfileSetting* getSetting(uint32_t settingId);
    const ProfileSetting* getSetting(uint32_t settingId) const;
    
    // Persistence for title-specific settings
    void loadTitleSettings(uint32_t titleId);
    void saveTitleSettings(uint32_t titleId);
    
    // Get all settings
    const std::unordered_map<uint32_t, ProfileSetting*>& settings() const { return settingsMap_; }

private:
    UserProfile();
    ~UserProfile() = default;
    
    // Non-copyable
    UserProfile(const UserProfile&) = delete;
    UserProfile& operator=(const UserProfile&) = delete;
    
    void initializeDefaults();
    
    uint64_t xuid_;
    std::string name_;
    SigninState signinState_;
    MembershipTier membershipTier_;
    
    // Settings storage
    std::vector<std::unique_ptr<ProfileSetting>> settingsList_;
    std::unordered_map<uint32_t, ProfileSetting*> settingsMap_;
    
    mutable std::mutex mutex_;
};

// Convenience accessor
inline UserProfile& GetUserProfile() {
    return UserProfile::Instance();
}

} // namespace Liberty

// ============================================================================
// Xbox 360 Profile Setting IDs
// From XDK documentation and Xenia research
// ============================================================================

namespace XProfileSettingId {

// Controller/Input settings
constexpr uint32_t GAMER_YAXIS_INVERSION            = 0x10040002;
constexpr uint32_t OPTION_CONTROLLER_VIBRATION      = 0x10040003;
constexpr uint32_t GAMER_DIFFICULTY                 = 0x10040015;
constexpr uint32_t GAMER_CONTROL_SENSITIVITY        = 0x10040018;
constexpr uint32_t GAMER_ACTION_AUTO_AIM            = 0x10040022;
constexpr uint32_t GAMER_ACTION_AUTO_CENTER         = 0x10040023;
constexpr uint32_t GAMER_ACTION_MOVEMENT_CONTROL    = 0x10040024;

// Racing game settings (GTA IV uses these!)
constexpr uint32_t GAMER_RACE_TRANSMISSION          = 0x10040026;
constexpr uint32_t GAMER_RACE_CAMERA_LOCATION       = 0x10040027;
constexpr uint32_t GAMER_RACE_BRAKE_CONTROL         = 0x10040028;
constexpr uint32_t GAMER_RACE_ACCELERATOR_CONTROL   = 0x10040029;

// Gamercard settings
constexpr uint32_t GAMERCARD_ZONE                   = 0x10040004;
constexpr uint32_t GAMERCARD_REGION                 = 0x10040005;
constexpr uint32_t GAMERCARD_CRED                   = 0x10040006;  // Gamerscore
constexpr uint32_t GAMERCARD_REP                    = 0x5004000B;  // Float reputation
constexpr uint32_t GAMERCARD_MOTTO                  = 0x402C0011;  // Unicode string
constexpr uint32_t GAMERCARD_TITLES_PLAYED          = 0x10040012;
constexpr uint32_t GAMERCARD_ACHIEVEMENTS_EARNED    = 0x10040013;
constexpr uint32_t GAMERCARD_PICTURE_KEY            = 0x4064000F;  // Unicode string
constexpr uint32_t GAMERCARD_TITLE_CRED_EARNED      = 0x10040038;
constexpr uint32_t GAMERCARD_TITLE_ACHIEVEMENTS     = 0x10040039;

// Voice settings
constexpr uint32_t OPTION_VOICE_MUTED               = 0x1004000C;
constexpr uint32_t OPTION_VOICE_THRU_SPEAKERS       = 0x1004000D;
constexpr uint32_t OPTION_VOICE_VOLUME              = 0x1004000E;

// Color preferences
constexpr uint32_t GAMER_PREFERRED_COLOR_1          = 0x1004001D;
constexpr uint32_t GAMER_PREFERRED_COLOR_2          = 0x1004001E;

// Title-specific settings (used for save data)
constexpr uint32_t TITLE_SPECIFIC1                  = 0x63E83FFF;
constexpr uint32_t TITLE_SPECIFIC2                  = 0x63E83FFE;
constexpr uint32_t TITLE_SPECIFIC3                  = 0x63E83FFD;

} // namespace XProfileSettingId
