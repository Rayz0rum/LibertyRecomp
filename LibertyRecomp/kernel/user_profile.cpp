/**
 * LibertyRecomp - User Profile System Implementation
 * 
 * Implements Xbox 360 user profile emulation for GTA IV.
 * Default "Niko" profile with all necessary settings pre-populated.
 */

#include "user_profile.h"
#include <user/paths.h>
#include <filesystem>
#include <fstream>
#include <cstring>

#ifdef _WIN32
#include <windows.h>
#else
#include <sys/stat.h>
#endif

namespace Liberty {

// Singleton instance
UserProfile& UserProfile::Instance() {
    static UserProfile instance;
    return instance;
}

UserProfile::UserProfile()
    : xuid_(DEFAULT_XUID)
    , name_(DEFAULT_NAME)
    , signinState_(SigninState::SignedInLocally)
    , membershipTier_(MembershipTier::Gold)  // Gold for online features
{
    initializeDefaults();
}

void UserProfile::initializeDefaults() {
    // =========================================================================
    // CONTROLLER/INPUT SETTINGS
    // =========================================================================
    
    // Y-Axis Inversion: 0 = normal, 1 = inverted
    addSetting(std::make_unique<Int32Setting>(
        XProfileSettingId::GAMER_YAXIS_INVERSION, 0));
    
    // Controller Vibration: 3 = on (normal pattern)
    addSetting(std::make_unique<Int32Setting>(
        XProfileSettingId::OPTION_CONTROLLER_VIBRATION, 3));
    
    // Difficulty: 0 = default/medium
    addSetting(std::make_unique<Int32Setting>(
        XProfileSettingId::GAMER_DIFFICULTY, 0));
    
    // Control Sensitivity: 0 = default
    addSetting(std::make_unique<Int32Setting>(
        XProfileSettingId::GAMER_CONTROL_SENSITIVITY, 0));
    
    // Auto-Aim: 1 = enabled (important for GTA IV!)
    addSetting(std::make_unique<Int32Setting>(
        XProfileSettingId::GAMER_ACTION_AUTO_AIM, 1));
    
    // Auto-Center: 0 = disabled
    addSetting(std::make_unique<Int32Setting>(
        XProfileSettingId::GAMER_ACTION_AUTO_CENTER, 0));
    
    // Movement Control: 0 = default scheme
    addSetting(std::make_unique<Int32Setting>(
        XProfileSettingId::GAMER_ACTION_MOVEMENT_CONTROL, 0));
    
    // =========================================================================
    // RACING SETTINGS (GTA IV reads these for vehicle controls!)
    // =========================================================================
    
    // Transmission: 0 = automatic
    addSetting(std::make_unique<Int32Setting>(
        XProfileSettingId::GAMER_RACE_TRANSMISSION, 0));
    
    // Camera Location: 0 = default (behind car)
    addSetting(std::make_unique<Int32Setting>(
        XProfileSettingId::GAMER_RACE_CAMERA_LOCATION, 0));
    
    // Brake Control: 0 = default
    addSetting(std::make_unique<Int32Setting>(
        XProfileSettingId::GAMER_RACE_BRAKE_CONTROL, 0));
    
    // Accelerator Control: 0 = default
    addSetting(std::make_unique<Int32Setting>(
        XProfileSettingId::GAMER_RACE_ACCELERATOR_CONTROL, 0));
    
    // =========================================================================
    // GAMERCARD SETTINGS
    // =========================================================================
    
    // Zone: 0 = default
    addSetting(std::make_unique<Int32Setting>(
        XProfileSettingId::GAMERCARD_ZONE, 0));
    
    // Region: 0 = default
    addSetting(std::make_unique<Int32Setting>(
        XProfileSettingId::GAMERCARD_REGION, 0));
    
    // Gamerscore: 1000 (respectable starting score for "Niko")
    addSetting(std::make_unique<Int32Setting>(
        XProfileSettingId::GAMERCARD_CRED, 1000));
    
    // Reputation: 3.0 (good standing)
    addSetting(std::make_unique<FloatSetting>(
        XProfileSettingId::GAMERCARD_REP, 3.0f));
    
    // Motto: Empty by default
    addSetting(std::make_unique<UnicodeSetting>(
        XProfileSettingId::GAMERCARD_MOTTO, u""));
    
    // Titles Played: 1 (GTA IV)
    addSetting(std::make_unique<Int32Setting>(
        XProfileSettingId::GAMERCARD_TITLES_PLAYED, 1));
    
    // Achievements Earned: 0 (fresh start)
    addSetting(std::make_unique<Int32Setting>(
        XProfileSettingId::GAMERCARD_ACHIEVEMENTS_EARNED, 0));
    
    // Picture Key (avatar/gamerpic reference)
    addSetting(std::make_unique<UnicodeSetting>(
        XProfileSettingId::GAMERCARD_PICTURE_KEY, u"gamercard_picture_key"));
    
    // Title-specific gamerscore: 0
    addSetting(std::make_unique<Int32Setting>(
        XProfileSettingId::GAMERCARD_TITLE_CRED_EARNED, 0));
    
    // Title-specific achievements: 0
    addSetting(std::make_unique<Int32Setting>(
        XProfileSettingId::GAMERCARD_TITLE_ACHIEVEMENTS, 0));
    
    // =========================================================================
    // VOICE SETTINGS
    // =========================================================================
    
    // Voice Muted: 0 = not muted
    addSetting(std::make_unique<Int32Setting>(
        XProfileSettingId::OPTION_VOICE_MUTED, 0));
    
    // Voice Through Speakers: 0 = headset only
    addSetting(std::make_unique<Int32Setting>(
        XProfileSettingId::OPTION_VOICE_THRU_SPEAKERS, 0));
    
    // Voice Volume: 100 (max)
    addSetting(std::make_unique<Int32Setting>(
        XProfileSettingId::OPTION_VOICE_VOLUME, 100));
    
    // =========================================================================
    // COLOR PREFERENCES
    // =========================================================================
    
    // Preferred Color 1: Red (0xFFFF0000) - ARGB
    addSetting(std::make_unique<Int32Setting>(
        XProfileSettingId::GAMER_PREFERRED_COLOR_1, 0xFFFF0000));
    
    // Preferred Color 2: Green (0xFF00FF00) - ARGB
    addSetting(std::make_unique<Int32Setting>(
        XProfileSettingId::GAMER_PREFERRED_COLOR_2, 0xFF00FF00));
    
    // =========================================================================
    // TITLE-SPECIFIC SETTINGS (for save data)
    // These are binary blobs that games write their save data to
    // =========================================================================
    
    addSetting(std::make_unique<BinarySetting>(XProfileSettingId::TITLE_SPECIFIC1));
    addSetting(std::make_unique<BinarySetting>(XProfileSettingId::TITLE_SPECIFIC2));
    addSetting(std::make_unique<BinarySetting>(XProfileSettingId::TITLE_SPECIFIC3));
    
    printf("[UserProfile] Initialized \"Niko\" profile with %zu settings\n",
           settingsMap_.size());
    printf("[UserProfile] XUID: 0x%016llX, SigninState: %u, Tier: Gold\n",
           static_cast<unsigned long long>(xuid_),
           static_cast<uint32_t>(signinState_));
}

void UserProfile::addSetting(std::unique_ptr<ProfileSetting> setting) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    uint32_t id = setting->settingId;
    
    // Check if setting already exists
    auto it = settingsMap_.find(id);
    if (it != settingsMap_.end()) {
        // Replace existing setting
        for (auto& stored : settingsList_) {
            if (stored.get() == it->second) {
                stored = std::move(setting);
                settingsMap_[id] = stored.get();
                return;
            }
        }
    }
    
    // Add new setting
    ProfileSetting* ptr = setting.get();
    settingsList_.push_back(std::move(setting));
    settingsMap_[id] = ptr;
}

ProfileSetting* UserProfile::getSetting(uint32_t settingId) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = settingsMap_.find(settingId);
    if (it == settingsMap_.end()) {
        return nullptr;
    }
    
    ProfileSetting* setting = it->second;
    
    // For title-specific settings, check if we need to reload
    // (commented out for now - will implement with save system)
    /*
    if (setting->isTitleSpecific()) {
        if (g_currentTitleId != setting->loadedTitleId) {
            loadTitleSetting(setting);
        }
    }
    */
    
    return setting;
}

const ProfileSetting* UserProfile::getSetting(uint32_t settingId) const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = settingsMap_.find(settingId);
    return (it != settingsMap_.end()) ? it->second : nullptr;
}

void UserProfile::loadTitleSettings(uint32_t titleId) {
    // Build path: <save_dir>/content/<xuid>/<title_id>/
    auto savePath = GetSavePath(false);
    char pathBuf[512];
    snprintf(pathBuf, sizeof(pathBuf), 
             "%s/content/%016llX/%08X/",
             savePath.string().c_str(),
             static_cast<unsigned long long>(xuid_),
             titleId);
    
    std::filesystem::path contentPath(pathBuf);
    
    if (!std::filesystem::exists(contentPath)) {
        return;
    }
    
    // Load each title-specific setting
    for (auto& setting : settingsList_) {
        if (setting->isTitleSpecific()) {
            char settingFile[32];
            snprintf(settingFile, sizeof(settingFile), "%08X", setting->settingId);
            
            auto filePath = contentPath / settingFile;
            
            if (std::filesystem::exists(filePath)) {
                std::ifstream file(filePath, std::ios::binary);
                if (file.is_open()) {
                    file.seekg(0, std::ios::end);
                    size_t size = file.tellg();
                    file.seekg(0, std::ios::beg);
                    
                    std::vector<uint8_t> data(size);
                    file.read(reinterpret_cast<char*>(data.data()), size);
                    
                    setting->deserialize(data);
                    setting->loadedTitleId = titleId;
                    
                    printf("[UserProfile] Loaded setting %08X from disk (%zu bytes)\n",
                           setting->settingId, size);
                }
            }
        }
    }
}

void UserProfile::saveTitleSettings(uint32_t titleId) {
    // Build path: <save_dir>/content/<xuid>/<title_id>/
    auto savePath = GetSavePath(false);
    char pathBuf[512];
    snprintf(pathBuf, sizeof(pathBuf), 
             "%s/content/%016llX/%08X/",
             savePath.string().c_str(),
             static_cast<unsigned long long>(xuid_),
             titleId);
    
    std::filesystem::path contentPath(pathBuf);
    
    // Create directories
    std::error_code ec;
    std::filesystem::create_directories(contentPath, ec);
    
    // Save each title-specific setting that has data
    for (auto& setting : settingsList_) {
        if (setting->isTitleSpecific() && setting->isSet) {
            char settingFile[32];
            snprintf(settingFile, sizeof(settingFile), "%08X", setting->settingId);
            
            auto filePath = contentPath / settingFile;
            
            auto data = setting->serialize();
            if (!data.empty()) {
                std::ofstream file(filePath, std::ios::binary);
                if (file.is_open()) {
                    file.write(reinterpret_cast<const char*>(data.data()), data.size());
                    
                    printf("[UserProfile] Saved setting %08X to disk (%zu bytes)\n",
                           setting->settingId, data.size());
                }
            }
        }
    }
}

} // namespace Liberty
