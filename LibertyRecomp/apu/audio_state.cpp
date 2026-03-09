#include "audio_state.h"
#include <os/logger.h>
#include <kernel/memory.h>
#include <algorithm>

// =============================================================================
// AudioStateManager Implementation
// =============================================================================

AudioStateManager& AudioStateManager::Instance() {
    static AudioStateManager instance;
    return instance;
}

void AudioStateManager::SetPlaybackState(uint32_t objectAddr, PlaybackState state) {
    std::lock_guard<std::mutex> lock(m_mutex);
    
    auto it = m_objectStates.find(objectAddr);
    PlaybackState oldState = (it != m_objectStates.end()) ? it->second : PlaybackState::INACTIVE;
    
    m_objectStates[objectAddr] = state;
    
    // Update active context count
    if (oldState != PlaybackState::PLAYING && state == PlaybackState::PLAYING) {
        m_activeContexts++;
        m_globalAudioReady = true;
        LOGF_WARNING("[AUDIO_STATE] Object 0x{:08X} -> PLAYING (active={})", 
                     objectAddr, m_activeContexts.load());
    } else if (oldState == PlaybackState::PLAYING && state != PlaybackState::PLAYING) {
        if (m_activeContexts > 0) m_activeContexts--;
        LOGF_WARNING("[AUDIO_STATE] Object 0x{:08X} -> {} (active={})", 
                     objectAddr, static_cast<int>(state), m_activeContexts.load());
    }
}

AudioStateManager::PlaybackState AudioStateManager::GetPlaybackState(uint32_t objectAddr) const {
    std::lock_guard<std::mutex> lock(m_mutex);
    auto it = m_objectStates.find(objectAddr);
    return (it != m_objectStates.end()) ? it->second : PlaybackState::INACTIVE;
}

void AudioStateManager::OnPlaybackCreated(XmaPlayback* playback, uint32_t guestAddr) {
    std::lock_guard<std::mutex> lock(m_mutex);
    m_playbackToGuest[playback] = guestAddr;
    m_objectStates[guestAddr] = PlaybackState::LOADING;
    
    LOGF_WARNING("[AUDIO_STATE] Playback created: host={:p} guest=0x{:08X}", 
                 (void*)playback, guestAddr);
}

void AudioStateManager::OnPlaybackStarted(XmaPlayback* playback) {
    std::lock_guard<std::mutex> lock(m_mutex);
    
    auto it = m_playbackToGuest.find(playback);
    if (it != m_playbackToGuest.end()) {
        uint32_t guestAddr = it->second;
        m_objectStates[guestAddr] = PlaybackState::PLAYING;
        m_activeContexts++;
        m_globalAudioReady = true;
        
        LOGF_WARNING("[AUDIO_STATE] Playback started: guest=0x{:08X} (active={})", 
                     guestAddr, m_activeContexts.load());
    }
}

void AudioStateManager::OnPlaybackStopped(XmaPlayback* playback) {
    std::lock_guard<std::mutex> lock(m_mutex);
    
    auto it = m_playbackToGuest.find(playback);
    if (it != m_playbackToGuest.end()) {
        uint32_t guestAddr = it->second;
        PlaybackState oldState = m_objectStates[guestAddr];
        m_objectStates[guestAddr] = PlaybackState::STOPPED;
        
        if (oldState == PlaybackState::PLAYING && m_activeContexts > 0) {
            m_activeContexts--;
        }
        
        LOGF_WARNING("[AUDIO_STATE] Playback stopped: guest=0x{:08X} (active={})", 
                     guestAddr, m_activeContexts.load());
    }
}

void AudioStateManager::OnDataSubmitted(XmaPlayback* playback, uint32_t dataSize) {
    m_totalDataSubmitted += dataSize;
    
    // After sufficient data is submitted, audio is considered ready
    // This is a heuristic - Xbox hardware would set state when buffers are filled
    if (m_totalDataSubmitted >= 8192 && !m_globalAudioReady) {
        m_globalAudioReady = true;
        LOGF_WARNING("[AUDIO_STATE] Global audio ready (total data: {})", 
                     m_totalDataSubmitted.load());
    }
    
    // Also update the playback state to PLAYING if it was LOADING
    std::lock_guard<std::mutex> lock(m_mutex);
    auto it = m_playbackToGuest.find(playback);
    if (it != m_playbackToGuest.end()) {
        uint32_t guestAddr = it->second;
        if (m_objectStates[guestAddr] == PlaybackState::LOADING) {
            m_objectStates[guestAddr] = PlaybackState::PLAYING;
            m_activeContexts++;
            LOGF_WARNING("[AUDIO_STATE] Data submitted -> PLAYING: guest=0x{:08X}", guestAddr);
        }
    }
}

void AudioStateManager::OnDataConsumed(XmaPlayback* playback, uint32_t samples) {
    // Consuming data confirms audio is actively playing
    if (!m_globalAudioReady && samples > 0) {
        m_globalAudioReady = true;
    }
}

void AudioStateManager::OnPlaybackDestroyed(XmaPlayback* playback) {
    std::lock_guard<std::mutex> lock(m_mutex);
    
    auto it = m_playbackToGuest.find(playback);
    if (it != m_playbackToGuest.end()) {
        uint32_t guestAddr = it->second;
        
        if (m_objectStates[guestAddr] == PlaybackState::PLAYING && m_activeContexts > 0) {
            m_activeContexts--;
        }
        
        m_objectStates.erase(guestAddr);
        m_playbackToGuest.erase(it);
        
        LOGF_WARNING("[AUDIO_STATE] Playback destroyed: guest=0x{:08X} (active={})", 
                     guestAddr, m_activeContexts.load());
    }
}

bool AudioStateManager::IsAudioReady() const {
    // Audio is ready if:
    // 1. We have active playing contexts, OR
    // 2. Sufficient data has been submitted (global flag set)
    return m_globalAudioReady.load() || m_activeContexts.load() > 0;
}

bool AudioStateManager::IsAudioObjectReady(uint32_t a1) const {
    // This mirrors sub_822FA4E8's logic:
    // int v1 = *(DWORD*)(a1 + 16);
    // if (!v1) return 0;
    // if (*(uint16_t*)(v1 + 6) == 2) return 1;
    // return 0;
    
    // For now, use the global ready state as a heuristic
    // In the future, could track specific object states if needed
    return IsAudioReady();
}

uint32_t AudioStateManager::GetActivePlaybackCount() const {
    return m_activeContexts.load();
}

void AudioStateManager::RegisterAudioObject(uint32_t objectAddr) {
    std::lock_guard<std::mutex> lock(m_mutex);
    if (m_objectStates.find(objectAddr) == m_objectStates.end()) {
        m_objectStates[objectAddr] = PlaybackState::INACTIVE;
    }
}

void AudioStateManager::DumpState() const {
    std::lock_guard<std::mutex> lock(m_mutex);
    
    LOG_WARNING("[AUDIO_STATE] === State Dump ===");
    LOGF_WARNING("  Global ready: {}", m_globalAudioReady.load());
    LOGF_WARNING("  Active contexts: {}", m_activeContexts.load());
    LOGF_WARNING("  Total data submitted: {}", m_totalDataSubmitted.load());
    LOGF_WARNING("  Tracked objects: {}", m_objectStates.size());
    
    for (const auto& [addr, state] : m_objectStates) {
        LOGF_WARNING("    0x{:08X} -> {}", addr, static_cast<int>(state));
    }
    LOG_WARNING("[AUDIO_STATE] === End Dump ===");
}

// =============================================================================
// AudioVolumeManager Implementation
// =============================================================================

AudioVolumeManager& AudioVolumeManager::Instance() {
    static AudioVolumeManager instance;
    return instance;
}

AudioVolumeManager::AudioVolumeManager() {
    // Initialize all volumes to 1.0 (full volume)
    m_volumes.fill(1.0f);
}

float AudioVolumeManager::GetCategoryVolume(uint32_t category) const {
    std::lock_guard<std::mutex> lock(m_mutex);
    
    if (category >= MAX_CATEGORIES) {
        return 1.0f;
    }
    
    return m_volumes[category];
}

void AudioVolumeManager::SetCategoryVolume(uint32_t category, float volume) {
    std::lock_guard<std::mutex> lock(m_mutex);
    
    if (category >= MAX_CATEGORIES) {
        return;
    }
    
    // Clamp volume to valid range
    volume = std::clamp(volume, 0.0f, 1.0f);
    
    if (m_volumes[category] != volume) {
        m_volumes[category] = volume;
        m_changeMask |= (1u << category);
        
        LOGF_WARNING("[AUDIO_VOLUME] Category {} volume set to {:.2f}", category, volume);
    }
}

uint32_t AudioVolumeManager::GetChangeMask() const {
    return m_changeMask.load();
}

void AudioVolumeManager::ClearChangeMask() {
    m_changeMask = 0;
}
