/**
 * XMutant - Native OS mutex implementation
 * 
 * Based on xenia/kernel/xmutant.cc
 */

#include <stdafx.h>
#include "xmutant.h"

namespace kernel {

XMutant::XMutant(bool initial_owner) {
    if (initial_owner) {
        mutex_.lock();
        owner_thread_ = std::this_thread::get_id();
        recursion_count_ = 1;
    }
}

uint32_t XMutant::Wait(uint32_t timeout_ms) {
    if (timeout_ms == 0) {
        // Try to acquire without blocking
        if (mutex_.try_lock()) {
            owner_thread_ = std::this_thread::get_id();
            recursion_count_++;
            return STATUS_SUCCESS;
        }
        return STATUS_TIMEOUT;
    }
    
    if (timeout_ms == INFINITE) {
        mutex_.lock();
        owner_thread_ = std::this_thread::get_id();
        recursion_count_++;
        return STATUS_SUCCESS;
    }
    
    // Timed wait - use try_lock in a loop
    auto deadline = std::chrono::steady_clock::now() + 
                    std::chrono::milliseconds(timeout_ms);
    
    while (std::chrono::steady_clock::now() < deadline) {
        if (mutex_.try_lock()) {
            owner_thread_ = std::this_thread::get_id();
            recursion_count_++;
            return STATUS_SUCCESS;
        }
        std::this_thread::sleep_for(std::chrono::microseconds(100));
    }
    
    return STATUS_TIMEOUT;
}

bool XMutant::Release() {
    if (owner_thread_ != std::this_thread::get_id()) {
        return false;
    }
    
    recursion_count_--;
    if (recursion_count_ <= 0) {
        owner_thread_ = std::thread::id();
        recursion_count_ = 0;
    }
    mutex_.unlock();
    return true;
}

} // namespace kernel
