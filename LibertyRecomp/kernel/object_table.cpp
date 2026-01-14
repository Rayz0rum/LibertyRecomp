/**
 * ObjectTable - Xenia-style kernel object handle management
 * 
 * Based on xenia/kernel/util/object_table.cc
 */

#include <stdafx.h>
#include "object_table.h"
#include <os/logger.h>

namespace kernel {

// Global object table instance
ObjectTable g_objectTable;

ObjectTable::ObjectTable() {
    // Pre-allocate some slots
    table_.resize(64);
    table_capacity_ = 64;
}

ObjectTable::~ObjectTable() {
    Reset();
}

void ObjectTable::Reset() {
    std::lock_guard<std::mutex> lock(mutex_);
    
    // Delete all objects
    for (auto& entry : table_) {
        if (entry.object) {
            delete entry.object;
            entry.object = nullptr;
        }
        entry.ref_count = 0;
    }
    
    last_free_slot_ = 0;
}

uint32_t ObjectTable::FindFreeSlot() {
    // Start from last free slot for O(1) amortized allocation
    uint32_t slot = last_free_slot_;
    uint32_t checked = 0;
    
    while (checked < table_capacity_) {
        if (table_[slot].object == nullptr && table_[slot].ref_count == 0) {
            last_free_slot_ = (slot + 1) % table_capacity_;
            return slot;
        }
        slot = (slot + 1) % table_capacity_;
        checked++;
    }
    
    // Table full - expand it
    uint32_t old_capacity = table_capacity_;
    uint32_t new_capacity = table_capacity_ * 2;
    table_.resize(new_capacity);
    table_capacity_ = new_capacity;
    
    // Return first slot in new region
    last_free_slot_ = old_capacity + 1;
    return old_capacity;
}

uint32_t ObjectTable::AddHandle(KernelObject* object) {
    if (!object) {
        return GUEST_INVALID_HANDLE_VALUE;
    }
    
    std::lock_guard<std::mutex> lock(mutex_);
    
    uint32_t slot = FindFreeSlot();
    table_[slot].object = object;
    table_[slot].ref_count = 1;
    
    uint32_t handle = HandleFromSlot(slot);
    
    return handle;
}

uint32_t ObjectTable::DuplicateHandle(uint32_t handle) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto* entry = GetEntry(handle);
    if (!entry || !entry->object) {
        return GUEST_INVALID_HANDLE_VALUE;
    }
    
    entry->ref_count++;
    return handle;
}

bool ObjectTable::ReleaseHandle(uint32_t handle) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto* entry = GetEntry(handle);
    if (!entry || !entry->object) {
        return false;
    }
    
    entry->ref_count--;
    
    if (entry->ref_count <= 0) {
        delete entry->object;
        entry->object = nullptr;
        entry->ref_count = 0;
    }
    
    return true;
}

KernelObject* ObjectTable::LookupObject(uint32_t handle) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto* entry = GetEntry(handle);
    if (!entry) {
        return nullptr;
    }
    
    return entry->object;
}

bool ObjectTable::IsValidHandle(uint32_t handle) const {
    if (handle == GUEST_INVALID_HANDLE_VALUE) {
        return false;
    }
    
    if (handle < kHandleBase) {
        return false;
    }
    
    uint32_t slot = SlotFromHandle(handle);
    
    std::lock_guard<std::mutex> lock(mutex_);
    if (slot >= table_capacity_) {
        return false;
    }
    
    return table_[slot].object != nullptr;
}

ObjectTable::TableEntry* ObjectTable::GetEntry(uint32_t handle) {
    if (handle == GUEST_INVALID_HANDLE_VALUE) {
        return nullptr;
    }
    
    if (handle < kHandleBase) {
        return nullptr;
    }
    
    uint32_t slot = SlotFromHandle(handle);
    if (slot >= table_capacity_) {
        return nullptr;
    }
    
    return &table_[slot];
}

} // namespace kernel
