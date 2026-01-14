/**
 * XEvent - Native OS event implementation
 * 
 * Based on xenia/kernel/xevent.cc
 */

#include <stdafx.h>
#include "xevent.h"

namespace kernel {

XEvent::XEvent(XKEVENT* header)
    : manual_reset_(header->Type == 0),  // Type 0 = manual, Type 1 = auto
      signaled_(header->SignalState != 0) {
}

XEvent::XEvent(bool manual_reset, bool initial_state)
    : manual_reset_(manual_reset),
      signaled_(initial_state) {
}

uint32_t XEvent::Wait(uint32_t timeout_ms) {
    std::unique_lock<std::mutex> lock(mutex_);
    
    if (timeout_ms == 0) {
        // Immediate check - no wait
        if (signaled_.load(std::memory_order_acquire)) {
            if (!manual_reset_) {
                signaled_.store(false, std::memory_order_release);
            }
            return STATUS_SUCCESS;
        }
        return STATUS_TIMEOUT;
    }
    
    if (timeout_ms == INFINITE) {
        // Wait forever
        cv_.wait(lock, [this] { 
            return signaled_.load(std::memory_order_acquire); 
        });
        
        if (!manual_reset_) {
            signaled_.store(false, std::memory_order_release);
        }
        return STATUS_SUCCESS;
    }
    
    // Timed wait
    auto deadline = std::chrono::steady_clock::now() + 
                    std::chrono::milliseconds(timeout_ms);
    
    bool signaled = cv_.wait_until(lock, deadline, [this] {
        return signaled_.load(std::memory_order_acquire);
    });
    
    if (signaled) {
        if (!manual_reset_) {
            signaled_.store(false, std::memory_order_release);
        }
        return STATUS_SUCCESS;
    }
    
    return STATUS_TIMEOUT;
}

bool XEvent::Set() {
    {
        std::lock_guard<std::mutex> lock(mutex_);
        signaled_.store(true, std::memory_order_release);
    }
    
    if (manual_reset_) {
        cv_.notify_all();
    } else {
        cv_.notify_one();
    }
    
    return true;
}

bool XEvent::Reset() {
    signaled_.store(false, std::memory_order_release);
    return true;
}

bool XEvent::Pulse() {
    // Pulse: Set then immediately reset
    {
        std::lock_guard<std::mutex> lock(mutex_);
        signaled_.store(true, std::memory_order_release);
    }
    
    if (manual_reset_) {
        cv_.notify_all();
    } else {
        cv_.notify_one();
    }
    
    std::this_thread::yield();
    signaled_.store(false, std::memory_order_release);
    return true;
}

} // namespace kernel
