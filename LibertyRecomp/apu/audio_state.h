#pragma once

#include <cstdint>
#include <mutex>
#include <unordered_map>
#include <atomic>

// Forward declaration
struct XmaPlayback;

/**
 * AudioStateManager - Tracks audio playback states for proper Xbox audio state emulation
 * 
 * On Xbox 360, the XMA hardware sets playback state flags that the game checks
 * via sub_822FA4E8. Since we use FFmpeg for decoding instead of XMA hardware,
 * we need to track these states ourselves.
 * 
 * This replaces the timeout-based hack that forced sub_822FA4E8 to return 1
 * after N calls.
 */
class AudioStateManager {
public:
    // Playback states matching Xbox hardware states
    enum class PlaybackState : uint16_t {
        INACTIVE = 0,
        LOADING = 1,
        PLAYING = 2,   // The state sub_822FA4E8 checks for
        STOPPED = 3,
        ERROR = 4
    };

    static AudioStateManager& Instance();
    
    // State tracking for guest audio objects
    void SetPlaybackState(uint32_t objectAddr, PlaybackState state);
    PlaybackState GetPlaybackState(uint32_t objectAddr) const;
    
    // Called from XMAPlayback functions to update state
    void OnPlaybackCreated(XmaPlayback* playback, uint32_t guestAddr);
    void OnPlaybackStarted(XmaPlayback* playback);
    void OnPlaybackStopped(XmaPlayback* playback);
    void OnDataSubmitted(XmaPlayback* playback, uint32_t dataSize);
    void OnDataConsumed(XmaPlayback* playback, uint32_t samples);
    void OnPlaybackDestroyed(XmaPlayback* playback);
    
    // Check if audio is ready (used by sub_822FA4E8 replacement)
    // Returns true if any playback context is in PLAYING state
    bool IsAudioReady() const;
    
    // Check if a specific audio object at (a1+16)+6 has state == 2
    // This is the exact check sub_822FA4E8 performs
    bool IsAudioObjectReady(uint32_t a1) const;
    
    // Get count of active playback contexts
    uint32_t GetActivePlaybackCount() const;
    
    // Register a guest audio object address for tracking
    void RegisterAudioObject(uint32_t objectAddr);
    
    // Debug: print all tracked states
    void DumpState() const;
    
private:
    AudioStateManager() = default;
    AudioStateManager(const AudioStateManager&) = delete;
    AudioStateManager& operator=(const AudioStateManager&) = delete;
    
    mutable std::mutex m_mutex;
    
    // Map from guest audio object address to playback state
    std::unordered_map<uint32_t, PlaybackState> m_objectStates;
    
    // Map from XmaPlayback pointer to guest address
    std::unordered_map<XmaPlayback*, uint32_t> m_playbackToGuest;
    
    // Count of contexts with data submitted (considered "ready")
    std::atomic<uint32_t> m_activeContexts{0};
    
    // Global audio ready flag (set when first audio starts playing)
    std::atomic<bool> m_globalAudioReady{false};
    
    // Total data submitted across all contexts (heuristic for "audio is ready")
    std::atomic<uint64_t> m_totalDataSubmitted{0};
};

// Volume category management for XAudioGetVoiceCategoryVolume
class AudioVolumeManager {
public:
    // Standard Xbox audio categories
    enum class VoiceCategory : uint32_t {
        Default = 0,
        Music = 1,
        SFX = 2,
        Voice = 3,
        Ambient = 4,
        UI = 5,
        Radio = 6,
        NumCategories
    };

    static AudioVolumeManager& Instance();
    
    // Get/set volume for a category (0.0 to 1.0)
    float GetCategoryVolume(uint32_t category) const;
    void SetCategoryVolume(uint32_t category, float volume);
    
    // Get the change mask (bitmask of categories that changed since last query)
    uint32_t GetChangeMask() const;
    void ClearChangeMask();
    
private:
    AudioVolumeManager();
    AudioVolumeManager(const AudioVolumeManager&) = delete;
    AudioVolumeManager& operator=(const AudioVolumeManager&) = delete;
    
    static constexpr size_t MAX_CATEGORIES = 16;
    
    mutable std::mutex m_mutex;
    std::array<float, MAX_CATEGORIES> m_volumes;
    mutable std::atomic<uint32_t> m_changeMask{0};
};
