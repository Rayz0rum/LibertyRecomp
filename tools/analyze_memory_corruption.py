#!/usr/bin/env python3
"""
Memory Corruption Analysis Script for LibertyRecomp
Analyzes the relationship between bump allocator uninitialized memory and GPU corruption.
"""

# =============================================================================
# ADDRESS SPACE ANALYSIS
# =============================================================================

# Physical heap range (from heap.cpp)
PHYS_HEAP_START = 0xA0000000
PHYS_HEAP_END = 0x100000000
PHYS_HEAP_SIZE = PHYS_HEAP_END - PHYS_HEAP_START

print("=" * 70)
print("MEMORY LAYOUT ANALYSIS")
print("=" * 70)

print(f"\nPhysical heap range: 0x{PHYS_HEAP_START:08X} - 0x{PHYS_HEAP_END:08X}")
print(f"Physical heap size:  {PHYS_HEAP_SIZE:,} bytes ({PHYS_HEAP_SIZE / (1024**3):.2f} GB)")

# =============================================================================
# CORRUPTION PATTERN ANALYSIS
# =============================================================================

print("\n" + "=" * 70)
print("CORRUPTION PATTERN ANALYSIS")
print("=" * 70)

# The observed corruption pattern
CORRUPTION_PATTERN = 0xEA7060FF
CORRUPTION_DEST = 0xBA000000
CORRUPTION_SIZE_GB = 1.1
BUMP_USED_MB = 406

print(f"\nCorruption destination: 0x{CORRUPTION_DEST:08X}")
print(f"Corruption pattern:     0x{CORRUPTION_PATTERN:08X}")
print(f"Corruption size:        ~{CORRUPTION_SIZE_GB} GB")
print(f"Bump allocator used:    ~{BUMP_USED_MB} MB")

# Calculate offset into physical heap
dest_offset = CORRUPTION_DEST - PHYS_HEAP_START
print(f"\nDestination offset into physical heap: 0x{dest_offset:08X} ({dest_offset / (1024**2):.1f} MB)")

# Analyze the pattern as different data types
print("\n--- Pattern Interpretation ---")

# As ABGR color (common GPU format)
a = (CORRUPTION_PATTERN >> 24) & 0xFF
b = (CORRUPTION_PATTERN >> 16) & 0xFF  
g = (CORRUPTION_PATTERN >> 8) & 0xFF
r = CORRUPTION_PATTERN & 0xFF
print(f"As ABGR color: A={a}, B={b}, G={g}, R={r}")
print(f"  -> Opaque (A=255) with pinkish/purple color")

# As RGBA color
r2 = (CORRUPTION_PATTERN >> 24) & 0xFF
g2 = (CORRUPTION_PATTERN >> 16) & 0xFF
b2 = (CORRUPTION_PATTERN >> 8) & 0xFF
a2 = CORRUPTION_PATTERN & 0xFF
print(f"As RGBA color: R={r2}, G={g2}, B={b2}, A={a2}")

# As guest memory address
print(f"As guest address: 0x{CORRUPTION_PATTERN:08X}")
if PHYS_HEAP_START <= CORRUPTION_PATTERN < PHYS_HEAP_END:
    offset_mb = (CORRUPTION_PATTERN - PHYS_HEAP_START) / (1024**2)
    print(f"  -> Valid physical heap address! Offset: {offset_mb:.1f} MB into heap")
else:
    print(f"  -> Outside physical heap range")

# As float (IEEE 754)
import struct
pattern_bytes = struct.pack('>I', CORRUPTION_PATTERN)  # Big-endian (Xbox 360)
pattern_float_be = struct.unpack('>f', pattern_bytes)[0]
pattern_bytes_le = struct.pack('<I', CORRUPTION_PATTERN)  # Little-endian
pattern_float_le = struct.unpack('<f', pattern_bytes_le)[0]
print(f"As float (BE): {pattern_float_be:.6e}")
print(f"As float (LE): {pattern_float_le:.6e}")

# =============================================================================
# HASH TABLE ANALYSIS (sub_82802540)
# =============================================================================

print("\n" + "=" * 70)
print("HASH TABLE CORRUPTION ANALYSIS (sub_82802540)")
print("=" * 70)

print("""
The hash table lookup function sub_82802540 does:
1. Calculate hash: v4 = sub_827E9598(*a2)
2. Get bucket: v7 = *(ptr**)(4 * (v4 % v5) + v6)
3. Walk chain: while(1) { ... v7 = *(ptr**)(v7 + 8) ... }

If v7 contains garbage (0xEA7060FF), the function follows this as a pointer.
This creates an infinite loop because:
- The garbage "pointer" may point to memory filled with the same pattern
- Each iteration reads another garbage pointer
- The loop never terminates (no NULL found)
""")

# Calculate what happens if hash table node is at corruption address
print("--- If hash node pointer corrupted to 0xEA7060FF ---")
garbage_addr = CORRUPTION_PATTERN
if PHYS_HEAP_START <= garbage_addr < PHYS_HEAP_END:
    print(f"Address 0x{garbage_addr:08X} is within physical heap")
    print(f"If that memory also contains 0x{CORRUPTION_PATTERN:08X}, chain continues forever")
else:
    print(f"Address 0x{garbage_addr:08X} is OUTSIDE physical heap")
    print(f"Could cause access violation or read from normal heap")

# =============================================================================
# GUESTTEXTURE/GUESTSURFACE ANALYSIS
# =============================================================================

print("\n" + "=" * 70)
print("GUESTTEXTURE/GUESTSURFACE FIELD ANALYSIS")
print("=" * 70)

print("""
GuestTexture inherits from GuestBaseTexture which inherits from GuestResource.

GuestResource fields:
  uint32_t unused = 0;           // +0x00
  be<uint32_t> refCount = 1;     // +0x04
  ResourceType type;              // +0x08

GuestBaseTexture fields:
  unique_ptr textureHolder;       // +0x10 (host pointer)
  RenderTexture* texture;         // +0x18 (host pointer)
  unique_ptr textureView;         // +0x20 (host pointer)
  uint32_t width = 0;             // +0x28
  uint32_t height = 0;            // +0x2C
  RenderFormat format;            // +0x30
  uint32_t descriptorIndex = 0;   // +0x34
  RenderTextureLayout layout;     // +0x38

If bump allocator returns uninitialized memory:
- width/height could be garbage -> incorrect texture dimensions
- format could be garbage -> incorrect pixel format interpretation
- descriptorIndex could be garbage -> bind wrong texture to shader
- texture pointer could be garbage -> GPU reads from wrong memory
""")

# What if width/height are garbage?
garbage_dim = CORRUPTION_PATTERN
print(f"If width/height = 0x{garbage_dim:08X}:")
print(f"  -> Texture dimension: {garbage_dim} x {garbage_dim} pixels")
print(f"  -> At 4 bytes/pixel: {garbage_dim * garbage_dim * 4 / (1024**3):.2f} GB texture!")
print(f"  -> GPU would read/write massive memory region")

# =============================================================================
# EVIDENCE CHAIN
# =============================================================================

print("\n" + "=" * 70)
print("EVIDENCE CHAIN SUMMARY")
print("=" * 70)

print("""
1. BUMP ALLOCATOR (heap.cpp:244)
   - AllocPhysical() returns uninitialized memory
   - No memset(ptr, 0, size) after allocation
   - ~406 MB allocated before corruption observed

2. GUESTTEXTURE ALLOCATION (video.cpp:3929)
   - g_userHeap.AllocPhysical<GuestTexture>(resourceType)
   - Template calls placement new: new (obj) T(std::forward<Args>(args)...)
   - Constructor ONLY initializes fields with "= 0" defaults
   - Underlying memory may still contain garbage in padding/uninitialized fields

3. GUESTDEVICE IS ZEROED (video.cpp:2573)
   - auto device = g_userHeap.AllocPhysical<GuestDevice>()
   - memset(device, 0, sizeof(*device))  <-- EXPLICIT ZEROING
   - This is the CORRECT pattern that GuestTexture/GuestSurface lack!

4. GPU USES GARBAGE
   - Texture fields contain garbage from uninitialized memory
   - GPU resolve/copy operations use these garbage values
   - Writes 1.1GB of 0xEA7060FF pattern to 0xBA000000

5. HASH TABLE CORRUPTION
   - Game's hash table nodes at 0xEA7060FF get overwritten
   - sub_82802540 follows garbage pointers in while(1) loop
   - Main thread enters infinite loop -> BEACH BALL
""")

# =============================================================================
# ROOT CAUSE VERIFICATION
# =============================================================================

print("\n" + "=" * 70)
print("ROOT CAUSE VERIFICATION CHECKLIST")
print("=" * 70)

print("""
To verify this hypothesis with LLDB:

1. Set breakpoint at AllocPhysical return:
   (lldb) b heap.cpp:262
   
2. When hit, examine returned memory:
   (lldb) memory read $rax $rax+256

3. Look for non-zero bytes in the returned memory
   - If non-zero: CONFIRMS uninitialized memory returned
   - Pattern should be whatever was there from previous use

4. Set watchpoint on 0xBA000000 (guest address):
   (lldb) watchpoint set expression -- *(uint32_t*)(<translated_0xBA000000>)
   
5. When watchpoint triggers, examine call stack:
   - Should show GPU resolve/copy operation
   - Source texture address should be garbage

6. Compare GuestDevice vs GuestTexture allocation:
   - GuestDevice: memset AFTER AllocPhysical
   - GuestTexture: NO memset after AllocPhysical
""")

print("\n" + "=" * 70)
print("RECOMMENDED FIX")
print("=" * 70)

print("""
Option A: Zero in AllocPhysical (heap.cpp)
  void *ptr = (void*)aligned;
  memset(ptr, 0, size);  // <-- ADD THIS LINE
  s_physBumpUsed += totalNeeded;
  return ptr;

Option B: Zero after each GuestTexture/GuestSurface allocation
  const auto texture = g_userHeap.AllocPhysical<GuestTexture>(resourceType);
  memset(texture, 0, sizeof(GuestTexture));  // <-- ADD THIS

Option A is preferred because:
  - Single point of change
  - Protects ALL physical allocations
  - Matches expected behavior (calloc-like semantics)
  - May impact performance slightly but prevents all such bugs
""")
