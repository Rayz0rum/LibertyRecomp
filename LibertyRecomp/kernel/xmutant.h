/**
 * XMutant - Native OS mutex wrapper for Xbox 360 kernel mutants
 * 
 * Based on xenia/kernel/xmutant.h
 * Uses native OS primitives for proper synchronization.
 */

#pragma once

#include <stdafx.h>
#include <cstdint>
#include <atomic>
#include <mutex>
#include <thread>
#include <chrono>

#include "xdm.h"

namespace kernel {

/**
 * XMutant wraps native OS recursive mutex.
 * 
 * Supports recursive acquisition by the same thread.
 */
class XMutant final : public KernelObject {
public:
    // Create directly with parameters
    XMutant(bool initial_owner);
    
    ~XMutant() override = default;

    // KernelObject interface
    uint32_t Wait(uint32_t timeout_ms) override;

    // Mutex operations
    bool Release();
    
    // State query
    std::thread::id GetOwner() const { return owner_thread_; }
    int32_t GetRecursionCount() const { return recursion_count_.load(); }

private:
    std::recursive_mutex mutex_;
    std::thread::id owner_thread_;
    std::atomic<int32_t> recursion_count_{0};
};

} // namespace kernel
