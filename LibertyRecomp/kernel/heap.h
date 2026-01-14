#pragma once

#include "mutex.h"

struct Heap
{
    Mutex mutex;
    O1HeapInstance* heap;

    Mutex physicalMutex;
    O1HeapInstance* physicalHeap;

    void Init();

    void* Alloc(size_t size);
    void* AllocPhysical(size_t size, size_t alignment);
    void Free(void* ptr);

    size_t Size(void* ptr);

    template<typename T, typename... Args>
    T* Alloc(Args&&... args)
    {
        T* obj = (T*)Alloc(sizeof(T));
        new (obj) T(std::forward<Args>(args)...);
        return obj;
    }

    template<typename T, typename... Args>
    T* AllocPhysical(Args&&... args)
    {
        T* obj = (T*)AllocPhysical(sizeof(T), alignof(T));
        new (obj) T(std::forward<Args>(args)...);
        return obj;
    }
};

extern Heap g_userHeap;

// Rtl Heap Functions (from MarathonRecomp)
uint32_t RtlAllocateHeap(uint32_t heapHandle, uint32_t flags, uint32_t size);
uint32_t RtlReAllocateHeap(uint32_t heapHandle, uint32_t flags, uint32_t memoryPointer, uint32_t size);
uint32_t RtlFreeHeap(uint32_t heapHandle, uint32_t flags, uint32_t memoryPointer);
uint32_t RtlSizeHeap(uint32_t heapHandle, uint32_t flags, uint32_t memoryPointer);

// X Memory Functions
uint32_t XAllocMem(uint32_t size, uint32_t flags);
void XFreeMem(uint32_t baseAddress, uint32_t flags);
uint32_t XVirtualAlloc(void *lpAddress, unsigned int dwSize, unsigned int flAllocationType, unsigned int flProtect);
uint32_t XVirtualFree(uint32_t lpAddress, unsigned int dwSize, unsigned int dwFreeType);
