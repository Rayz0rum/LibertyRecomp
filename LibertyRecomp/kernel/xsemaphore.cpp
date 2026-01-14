/**
 * XSemaphore - Native OS semaphore implementation
 * 
 * Based on xenia/kernel/xsemaphore.cc
 */

#include <stdafx.h>
#include "xsemaphore.h"

namespace kernel {

XSemaphore::XSemaphore(XKSEMAPHORE* header)
    : count_(header->Header.SignalState),
      maximum_count_(header->Limit) {
}

XSemaphore::XSemaphore(int32_t initial_count, int32_t maximum_count)
    : count_(initial_count),
      maximum_count_(maximum_count) {
}

uint32_t XSemaphore::Wait(uint32_t timeout_ms) {
    std::unique_lock<std::mutex> lock(mutex_);
    
    if (timeout_ms == 0) {
        // Immediate check - try to acquire
        int32_t current = count_.load(std::memory_order_acquire);
        if (current > 0) {
            if (count_.compare_exchange_strong(current, current - 1,
                    std::memory_order_acq_rel)) {
                return STATUS_SUCCESS;
            }
        }
        return STATUS_TIMEOUT;
    }
    
    if (timeout_ms == INFINITE) {
        // Wait forever until we can acquire
        cv_.wait(lock, [this] {
            int32_t current = count_.load(std::memory_order_acquire);
            if (current > 0) {
                return count_.compare_exchange_strong(current, current - 1,
                    std::memory_order_acq_rel);
            }
            return false;
        });
        return STATUS_SUCCESS;
    }
    
    // Timed wait
    auto deadline = std::chrono::steady_clock::now() + 
                    std::chrono::milliseconds(timeout_ms);
    
    bool acquired = cv_.wait_until(lock, deadline, [this] {
        int32_t current = count_.load(std::memory_order_acquire);
        if (current > 0) {
            return count_.compare_exchange_strong(current, current - 1,
                std::memory_order_acq_rel);
        }
        return false;
    });
    
    return acquired ? STATUS_SUCCESS : STATUS_TIMEOUT;
}

int32_t XSemaphore::Release(int32_t release_count, int32_t* previous_count) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    int32_t prev = count_.load(std::memory_order_acquire);
    if (previous_count) {
        *previous_count = prev;
    }
    
    int32_t new_count = prev + release_count;
    if (new_count > maximum_count_) {
        new_count = maximum_count_;
    }
    
    count_.store(new_count, std::memory_order_release);
    
    // Wake up waiters
    if (release_count == 1) {
        cv_.notify_one();
    } else {
        cv_.notify_all();
    }
    
    return prev;
}

} // namespace kernel
