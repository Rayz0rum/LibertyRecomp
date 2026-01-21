#include "heap.h"
#include "function.h"
#include "memory.h"
#include "xdm.h"
#include <stdafx.h>

// Memory layout from MarathonRecomp (modified for GTA IV):
// | Region        | Start      | End        | Purpose              |
// |---------------|------------|------------|----------------------|
// | Null guard    | 0x00000000 | 0x00001000 | Catch null ptr access|
// | Low memory    | 0x00001000 | 0x00300000 | Texture/resource buf |
// | Normal heap   | 0x00300000 | 0x7FEA0000 | General allocations  |
// | Reserved      | 0x7FEA0000 | 0xA0000000 | XMA I/O, system      |
// | Physical heap | 0xA0000000 | 0xFFFFFFFF | GPU/DMA memory       |

constexpr size_t RESERVED_BEGIN = 0x7FEA0000;
constexpr size_t RESERVED_END = 0xA0000000;

void Heap::Init() {
  // Normal heap: 0x300000 to 0x7FEA0000 (using o1heap)
  // NOTE: Heap base moved from 0x20000 to 0x300000 to avoid corruption.
  // The texture loader (sub_8286ABF0) writes to guest addr 0x80 for 0x20040
  // bytes, covering up to 0x200C0, which overlapped with the old heap base at
  // 0x20000.
  constexpr size_t HEAP_BASE =
      0x300000; // 3MB offset - safe from low memory writes

  void *heapBase = g_memory.Translate(HEAP_BASE);
  size_t heapSize = RESERVED_BEGIN - HEAP_BASE;

  std::fprintf(
      stderr,
      "[Heap::Init] Normal heap base=%p size=%zu (0x%zx) align_check=%zu\n",
      heapBase, heapSize, heapSize, ((size_t)heapBase) % O1HEAP_ALIGNMENT);

  heap = o1heapInit(heapBase, heapSize);

  if (heap) {
    O1HeapDiagnostics diag = o1heapGetDiagnostics(heap);
    std::fprintf(stderr,
                 "[Heap::Init] Normal heap init SUCCESS: capacity=%zu\n",
                 diag.capacity);
  } else {
    std::fprintf(
        stderr,
        "[Heap::Init] Normal heap init FAILED! o1heapInit returned NULL\n");
  }

  // Physical heap: 0xA0000000 to 0x100000000 (using o1heap for proper free
  // support)
  void *physBase = g_memory.Translate(RESERVED_END);
  size_t physSize = 0x100000000 - RESERVED_END;

  std::fprintf(
      stderr,
      "[Heap::Init] Physical heap base=%p size=%zu (0x%zx) align_check=%zu\n",
      physBase, physSize, physSize, ((size_t)physBase) % O1HEAP_ALIGNMENT);

  physicalHeap = o1heapInit(physBase, physSize);

  if (physicalHeap) {
    O1HeapDiagnostics diag = o1heapGetDiagnostics(physicalHeap);
    std::fprintf(stderr,
                 "[Heap::Init] Physical heap init SUCCESS: capacity=%zu\n",
                 diag.capacity);
  } else {
    std::fprintf(stderr, "[Heap::Init] Physical heap init FAILED!\n");
  }

  std::fprintf(stderr, "[Heap::Init] heap=%p physicalHeap=%p\n", (void *)heap,
               (void *)physicalHeap);
  std::fflush(stderr);
}

void *Heap::Alloc(size_t size) {
  std::lock_guard lock(mutex);

  return o1heapAllocate(heap, std::max<size_t>(1, size));
}

void *Heap::AllocPhysical(size_t size, size_t alignment) {
  size = std::max<size_t>(1, size);
  alignment = alignment == 0 ? 0x1000 : std::max<size_t>(16, alignment);

  std::lock_guard lock(physicalMutex);

  void *ptr = o1heapAllocate(physicalHeap, size + alignment);
  
  // FIX: Check for allocation failure before dereferencing
  if (!ptr) {
    std::fprintf(stderr,
                 "[Heap::AllocPhysical] FAILED: size=%zu alignment=%zu (physical heap exhausted)\n",
                 size, alignment);
    std::fflush(stderr);
    return nullptr;
  }
  
  size_t aligned = ((size_t)ptr + alignment) & ~(alignment - 1);

  // Store original pointer and size for Free() to work correctly
  *((void **)aligned - 1) = ptr;
  *((size_t *)aligned - 2) = size + O1HEAP_ALIGNMENT;

  return (void *)aligned;
}

void Heap::Free(void *ptr) {
  if (ptr >= physicalHeap) {
    std::lock_guard lock(physicalMutex);
    o1heapFree(physicalHeap, *((void **)ptr - 1));
  } else {
    std::lock_guard lock(mutex);
    o1heapFree(heap, ptr);
  }
}

size_t Heap::Size(void *ptr) {
  if (ptr)
    return *((size_t *)ptr - 2) -
           O1HEAP_ALIGNMENT; // relies on fragment header in o1heap.c

  return 0;
}

// =============================================================================
// Rtl Heap Functions (from MarathonRecomp)
// =============================================================================

uint32_t RtlAllocateHeap(uint32_t heapHandle, uint32_t flags, uint32_t size) {
  void *ptr = g_userHeap.Alloc(size);

  // FIX: Return 0 on allocation failure instead of asserting
  if (!ptr) {
    std::fprintf(stderr,
                 "[ALLOC] RtlAllocateHeap FAILED: size=%u flags=0x%08X\n", size,
                 flags);
    std::fflush(stderr);
    return 0;
  }

  if ((flags & 0x8) != 0) // HEAP_ZERO_MEMORY
    memset(ptr, 0, size);

  return g_memory.MapVirtual(ptr);
}

uint32_t RtlReAllocateHeap(uint32_t heapHandle, uint32_t flags,
                           uint32_t memoryPointer, uint32_t size) {
  void *ptr = g_userHeap.Alloc(size);

  // FIX: Return 0 on allocation failure instead of asserting
  if (!ptr) {
    std::fprintf(
        stderr,
        "[ALLOC] RtlReAllocateHeap FAILED: size=%u flags=0x%08X old=0x%08X\n",
        size, flags, memoryPointer);
    std::fflush(stderr);
    return 0;
  }

  if ((flags & 0x8) != 0) // HEAP_ZERO_MEMORY
    memset(ptr, 0, size);

  if (memoryPointer != 0) {
    void *oldPtr = g_memory.Translate(memoryPointer);
    memcpy(ptr, oldPtr, std::min<size_t>(size, g_userHeap.Size(oldPtr)));
    g_userHeap.Free(oldPtr);
  }

  return g_memory.MapVirtual(ptr);
}

uint32_t RtlFreeHeap(uint32_t heapHandle, uint32_t flags,
                     uint32_t memoryPointer) {
  if (memoryPointer != NULL)
    g_userHeap.Free(g_memory.Translate(memoryPointer));

  return true;
}

uint32_t RtlSizeHeap(uint32_t heapHandle, uint32_t flags,
                     uint32_t memoryPointer) {
  if (memoryPointer != NULL)
    return (uint32_t)g_userHeap.Size(g_memory.Translate(memoryPointer));

  return 0;
}

// =============================================================================
// X Memory Functions
// =============================================================================

uint32_t XAllocMem(uint32_t size, uint32_t flags) {
  bool isPhysical = (flags & 0x80000000) != 0;
  size_t alignment = isPhysical ? (1ull << ((flags >> 24) & 0xF)) : 0;

  void *ptr = isPhysical ? g_userHeap.AllocPhysical(size, alignment)
                         : g_userHeap.Alloc(size);

  // FIX: Return 0 (guest NULL) on allocation failure instead of asserting
  // The game code checks for NULL after allocation and handles it gracefully
  if (!ptr) {
    // Get heap diagnostics to understand why allocation failed
    O1HeapDiagnostics diag = o1heapGetDiagnostics(
        isPhysical ? g_userHeap.physicalHeap : g_userHeap.heap);
    static int failCount = 0;
    ++failCount;
    if (failCount <= 10 ||
        (failCount % 100 == 0)) { // Log first 10 and every 100th
      std::fprintf(stderr,
                   "[ALLOC] XAllocMem FAILED #%d: size=%u flags=0x%08X "
                   "physical=%d align=%zu\n",
                   failCount, size, flags, isPhysical ? 1 : 0, alignment);
      std::fprintf(stderr,
                   "[ALLOC]   Heap stats: capacity=%zu allocated=%zu peak=%zu "
                   "oom=%llu\n",
                   diag.capacity, diag.allocated, diag.peak_allocated,
                   diag.oom_count);
      std::fflush(stderr);
    }
    return 0; // Return guest NULL - game should handle this
  }

  if ((flags & 0x40000000) != 0)
    memset(ptr, 0, size);

  // Log large allocations for debugging
  static int s_allocCount = 0;
  ++s_allocCount;
  if (size > 1024 * 1024 ||
      s_allocCount <= 20) { // Log first 20 or large (>1MB)
    std::fprintf(
        stderr,
        "[ALLOC] XAllocMem #%d: size=%u flags=0x%08X result=%p -> 0x%08X\n",
        s_allocCount, size, flags, ptr, g_memory.MapVirtual(ptr));
    std::fflush(stderr);
  }

  return g_memory.MapVirtual(ptr);
}

void XFreeMem(uint32_t baseAddress, uint32_t flags) {
  if (baseAddress != NULL)
    g_userHeap.Free(g_memory.Translate(baseAddress));
}

uint32_t XVirtualAlloc(void *lpAddress, unsigned int dwSize,
                       unsigned int flAllocationType, unsigned int flProtect) {
  assert(!lpAddress);
  return g_memory.MapVirtual(g_userHeap.Alloc(dwSize));
}

uint32_t XVirtualFree(uint32_t lpAddress, unsigned int dwSize,
                      unsigned int dwFreeType) {
  if ((dwFreeType & 0x8000) != 0 && dwSize)
    return FALSE;

  if (lpAddress)
    g_userHeap.Free(g_memory.Translate(lpAddress));

  return TRUE;
}

// =============================================================================
// GTA IV CRT Heap Hooks
// =============================================================================
// NOTE: The actual heap hooks are in imports.cpp using PPC_FUNC macro.
// GUEST_FUNCTION_HOOK doesn't work for game functions (only kernel imports).
// The hooks are: sub_82993298 (malloc), sub_82993360 (free), sub_82993848
// (realloc), sub_829A64C0 (low-level alloc), sub_829A7090 (low-level realloc)
// =============================================================================
// sub_8218BF20 (malloc-like) -> XAllocMem
GUEST_FUNCTION_HOOK(sub_8218BF20, XAllocMem);
