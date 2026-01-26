#include "heap.h"
#include "function.h"
#include "memory.h"
#include "xdm.h"
#include <stdafx.h>
#include <patches/player_limit_patches.h>  // For player array expansion

// =============================================================================
// HEAP CORRUPTION DEBUGGING
// =============================================================================
// Memory poisoning: Fill freed memory with pattern to detect use-after-free
// Canary values: Write magic values at allocation boundaries to detect overflow
// =============================================================================
#define HEAP_DEBUG_ENABLED 0  // Disabled - poison pattern interferes with game code

// Heap integrity check - validate o1heap can be used safely
#define HEAP_INTEGRITY_CHECK 1

#if HEAP_INTEGRITY_CHECK
#include <cstdio>
static int s_physAllocNum = 0;
static int s_lastGoodAlloc = 0;
#endif

// =============================================================================
// SAFE PHYSICAL ALLOCATOR - Metadata stored in host memory, not guest memory
// =============================================================================
// The problem: o1heap stores Fragment headers in the same memory that guest
// code can access. When guest code has use-after-free bugs, it corrupts
// o1heap's internal pointers causing crashes.
//
// Solution: Use a simple bump allocator for physical heap that keeps all
// bookkeeping in host memory (std::unordered_map), not in guest memory.
// =============================================================================
#define USE_SAFE_PHYSICAL_ALLOCATOR 1

#if USE_SAFE_PHYSICAL_ALLOCATOR
#include <unordered_map>
#include <mutex>

struct PhysAllocInfo {
  void* basePtr;      // Start of allocation in guest memory
  size_t totalSize;   // Total size including alignment padding
  size_t userSize;    // Requested size
};

static std::unordered_map<void*, PhysAllocInfo> s_physAllocMap;
static std::mutex s_physAllocMapMutex;
static uint8_t* s_physBumpPtr = nullptr;
static uint8_t* s_physBumpEnd = nullptr;
static size_t s_physBumpUsed = 0;
#endif

#if HEAP_DEBUG_ENABLED
constexpr uint8_t POISON_FREE = 0xFE;      // Pattern for freed memory
constexpr uint8_t POISON_ALLOC = 0xCD;     // Pattern for uninitialized alloc
constexpr uint32_t CANARY_HEAD = 0xDEADBEEF; // Magic value before allocation
constexpr uint32_t CANARY_TAIL = 0xCAFEBABE; // Magic value after allocation
constexpr size_t CANARY_SIZE = 16;         // Extra bytes for canaries (8 head + 8 tail)

// Track allocations for debugging
struct AllocRecord {
  void* ptr;
  size_t size;
  uint32_t allocNum;
  bool freed;
};
static std::vector<AllocRecord> s_allocRecords;
static std::mutex s_recordMutex;
static int s_totalAllocNum = 0;

static void RecordAlloc(void* ptr, size_t size) {
  std::lock_guard lock(s_recordMutex);
  s_allocRecords.push_back({ptr, size, (uint32_t)++s_totalAllocNum, false});
  // Keep last 1000 allocations
  if (s_allocRecords.size() > 1000) {
    s_allocRecords.erase(s_allocRecords.begin());
  }
}

static void RecordFree(void* ptr) {
  std::lock_guard lock(s_recordMutex);
  for (auto& rec : s_allocRecords) {
    if (rec.ptr == ptr && !rec.freed) {
      rec.freed = true;
      return;
    }
  }
}

static bool CheckCanaries(void* userPtr, size_t size, const char* context) {
  uint32_t* headCanary = (uint32_t*)((uint8_t*)userPtr - 8);
  uint32_t* tailCanary = (uint32_t*)((uint8_t*)userPtr + size);
  
  bool valid = true;
  if (headCanary[0] != CANARY_HEAD || headCanary[1] != CANARY_HEAD) {
    std::fprintf(stderr, "[HEAP_OVERFLOW] %s: HEAD canary corrupted at %p (was 0x%08X 0x%08X, expected 0x%08X)\n",
                 context, userPtr, headCanary[0], headCanary[1], CANARY_HEAD);
    std::fflush(stderr);
    valid = false;
  }
  if (tailCanary[0] != CANARY_TAIL || tailCanary[1] != CANARY_TAIL) {
    std::fprintf(stderr, "[HEAP_OVERFLOW] %s: TAIL canary corrupted at %p+%zu (was 0x%08X 0x%08X, expected 0x%08X)\n",
                 context, userPtr, size, tailCanary[0], tailCanary[1], CANARY_TAIL);
    std::fflush(stderr);
    valid = false;
  }
  return valid;
}

static void WriteCanaries(void* userPtr, size_t size) {
  uint32_t* headCanary = (uint32_t*)((uint8_t*)userPtr - 8);
  uint32_t* tailCanary = (uint32_t*)((uint8_t*)userPtr + size);
  headCanary[0] = CANARY_HEAD;
  headCanary[1] = CANARY_HEAD;
  tailCanary[0] = CANARY_TAIL;
  tailCanary[1] = CANARY_TAIL;
}

static void PoisonMemory(void* ptr, size_t size, uint8_t pattern) {
  memset(ptr, pattern, size);
}
#endif

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

  // Physical heap: 0xA0000000 to 0x100000000
  void *physBase = g_memory.Translate(RESERVED_END);
  size_t physSize = 0x100000000 - RESERVED_END;

  std::fprintf(
      stderr,
      "[Heap::Init] Physical heap base=%p size=%zu (0x%zx) align_check=%zu\n",
      physBase, physSize, physSize, ((size_t)physBase) % O1HEAP_ALIGNMENT);

#if USE_SAFE_PHYSICAL_ALLOCATOR
  // Safe allocator: Use bump allocator with host-side metadata tracking
  // This prevents guest use-after-free from corrupting allocator internals
  s_physBumpPtr = (uint8_t*)physBase;
  s_physBumpEnd = s_physBumpPtr + physSize;
  s_physBumpUsed = 0;
  physicalHeap = (O1HeapInstance*)physBase;  // Just store base for range check
  
  std::fprintf(stderr,
               "[Heap::Init] Physical heap using SAFE BUMP ALLOCATOR: capacity=%zu\n",
               physSize);
#else
  physicalHeap = o1heapInit(physBase, physSize);

  if (physicalHeap) {
    O1HeapDiagnostics diag = o1heapGetDiagnostics(physicalHeap);
    std::fprintf(stderr,
                 "[Heap::Init] Physical heap init SUCCESS: capacity=%zu\n",
                 diag.capacity);
  } else {
    std::fprintf(stderr, "[Heap::Init] Physical heap init FAILED!\n");
  }
#endif

  std::fprintf(stderr, "[Heap::Init] heap=%p physicalHeap=%p\n", (void *)heap,
               (void *)physicalHeap);
  std::fflush(stderr);
}

void *Heap::Alloc(size_t size) {
  std::lock_guard lock(mutex);
  size = std::max<size_t>(1, size);
  void* ptr = o1heapAllocate(heap, size);
  if (ptr) {
    memset(ptr, 0, size);  // Zero memory - Xbox 360 allocators return zeroed memory
  }
  return ptr;
}

void *Heap::AllocPhysical(size_t size, size_t alignment) {
  size = std::max<size_t>(1, size);
  alignment = alignment == 0 ? 0x1000 : std::max<size_t>(16, alignment);

  std::lock_guard lock(physicalMutex);

  // Track allocation count for debugging
  static int s_allocCount = 0;
  ++s_allocCount;
  
#if HEAP_INTEGRITY_CHECK
  ++s_physAllocNum;
#endif

#if USE_SAFE_PHYSICAL_ALLOCATOR
  // Safe bump allocator: metadata stored in host memory, not guest memory
  // This prevents guest use-after-free from corrupting allocator internals
  
  // Calculate aligned address
  uintptr_t current = (uintptr_t)s_physBumpPtr + s_physBumpUsed;
  uintptr_t aligned = (current + alignment - 1) & ~(alignment - 1);
  size_t padding = aligned - current;
  size_t totalNeeded = padding + size;
  
  // Check if we have enough space
  if (s_physBumpPtr + s_physBumpUsed + totalNeeded > s_physBumpEnd) {
    std::fprintf(stderr,
                 "[Heap::AllocPhysical] FAILED: size=%zu (bump allocator exhausted, used=%zu)\n",
                 size, s_physBumpUsed);
    std::fflush(stderr);
    return nullptr;
  }
  
  void *ptr = (void*)aligned;
  memset(ptr, 0, size);  // Zero memory to prevent GPU corruption from uninitialized data
  s_physBumpUsed += totalNeeded;
  
  // Track allocation in host memory (for potential future free support)
  {
    std::lock_guard mapLock(s_physAllocMapMutex);
    s_physAllocMap[ptr] = {ptr, totalNeeded, size};
  }
  
#if HEAP_INTEGRITY_CHECK
  s_lastGoodAlloc = s_physAllocNum;
  if (s_physAllocNum % 1000 == 0) {
    std::fprintf(stderr, "[HEAP_OK] bump alloc #%d, used=%zu/%zu\n",
                 s_physAllocNum, s_physBumpUsed, (size_t)(s_physBumpEnd - s_physBumpPtr));
    std::fflush(stderr);
  }
#endif
  
  return ptr;
  
#else
  // Original o1heap-based allocator (vulnerable to guest corruption)
#if HEAP_DEBUG_ENABLED
  size_t totalSize = size + alignment + CANARY_SIZE;
#else
  size_t totalSize = size + alignment;
#endif

  void *ptr = o1heapAllocate(physicalHeap, totalSize);
  
  // FIX: Check for allocation failure before dereferencing
  if (!ptr) {
    std::fprintf(stderr,
                 "[Heap::AllocPhysical] FAILED: size=%zu alignment=%zu (physical heap exhausted)\n",
                 size, alignment);
    std::fflush(stderr);
    return nullptr;
  }
  
#if HEAP_INTEGRITY_CHECK
  s_lastGoodAlloc = s_physAllocNum;  // Mark successful allocation
  
  // Log allocations to narrow down crash window
  // Crash happens around alloc 2000-3000 based on previous runs
  if (s_physAllocNum >= 2000 && s_physAllocNum <= 3000) {
    uint32_t guestAddr = g_memory.MapVirtual(ptr);
    std::fprintf(stderr, "[ALLOC] #%d guest=0x%08X size=%zu\n",
                 s_physAllocNum, guestAddr, size);
    std::fflush(stderr);
  } else if (s_physAllocNum % 500 == 0) {
    O1HeapDiagnostics diag = o1heapGetDiagnostics(physicalHeap);
    std::fprintf(stderr, "[HEAP_OK] alloc #%d, allocated=%zu/%zu\n",
                 s_physAllocNum, diag.allocated, diag.capacity);
    std::fflush(stderr);
  }
#endif
  
#if HEAP_DEBUG_ENABLED
  // Leave room for head canary (8 bytes before user data)
  size_t aligned = ((size_t)ptr + alignment + 8) & ~(alignment - 1);
  void* userPtr = (void*)aligned;
  
  // Write canaries
  WriteCanaries(userPtr, size);
  
  // Poison allocated memory with pattern (helps detect uninitialized reads)
  PoisonMemory(userPtr, size, POISON_ALLOC);
  
  // Record allocation
  RecordAlloc(userPtr, size);
  
  // Store original pointer and size for Free() to work correctly
  *((void **)aligned - 1) = ptr;
  *((size_t *)aligned - 2) = size; // Store user size, not total size
  
  return userPtr;
#else
  size_t aligned = ((size_t)ptr + alignment) & ~(alignment - 1);

  // Store original pointer and size for Free() to work correctly
  *((void **)aligned - 1) = ptr;
  *((size_t *)aligned - 2) = size + O1HEAP_ALIGNMENT;

  return (void *)aligned;
#endif
#endif  // USE_SAFE_PHYSICAL_ALLOCATOR else branch
}

void Heap::Free(void *ptr) {
#if USE_SAFE_PHYSICAL_ALLOCATOR
  // Safe bump allocator: Free is a no-op (bump allocator doesn't reclaim)
  // Memory is reclaimed when heap is reset or process exits
  // This trades memory efficiency for corruption resistance
  if (ptr >= (void*)s_physBumpPtr && ptr < (void*)s_physBumpEnd) {
    // Remove from tracking map (optional, for debugging)
    std::lock_guard mapLock(s_physAllocMapMutex);
    s_physAllocMap.erase(ptr);
    return;
  }
  // Fall through to normal heap free
  std::lock_guard lock(mutex);
  o1heapFree(heap, ptr);
#else
  if (ptr >= physicalHeap) {
    std::lock_guard lock(physicalMutex);
    
#if HEAP_DEBUG_ENABLED
    // Get stored size and check canaries before freeing
    size_t userSize = *((size_t *)ptr - 2);
    if (!CheckCanaries(ptr, userSize, "Free")) {
      // Canary corruption detected - dump recent allocations
      std::fprintf(stderr, "[HEAP_DEBUG] Canary corruption at %p, dumping recent allocations:\n", ptr);
      std::lock_guard recLock(s_recordMutex);
      int count = 0;
      for (auto it = s_allocRecords.rbegin(); it != s_allocRecords.rend() && count < 20; ++it, ++count) {
        std::fprintf(stderr, "  [%d] ptr=%p size=%zu alloc#%u freed=%d\n",
                     count, it->ptr, it->size, it->allocNum, it->freed ? 1 : 0);
      }
      std::fflush(stderr);
    }
    
    // Poison freed memory to detect use-after-free
    PoisonMemory(ptr, userSize, POISON_FREE);
    RecordFree(ptr);
#endif
    
    o1heapFree(physicalHeap, *((void **)ptr - 1));
  } else {
    std::lock_guard lock(mutex);
    o1heapFree(heap, ptr);
  }
#endif  // USE_SAFE_PHYSICAL_ALLOCATOR
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
  // Expand player arrays if enabled (16->64 player support)
  uint32_t originalSize = size;
  if (PlayerLimitPatches::IsEnabled() && PlayerLimitPatches::Memory::IsPlayerArraySize(size)) {
    size = PlayerLimitPatches::Memory::GetExpandedSize(size);
  }
  
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
