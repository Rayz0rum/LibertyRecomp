#!/usr/bin/env python3
"""
GPU Memory Corruption Analysis for LibertyRecomp
Investigates how uninitialized texture/surface data leads to 1.1GB memory corruption.

HYPOTHESIS: GPU uses garbage addresses from uninitialized GuestTexture/GuestSurface
            fields, causing massive memory writes to wrong locations.
"""

import struct

print("=" * 80)
print("GPU MEMORY CORRUPTION ANALYSIS")
print("=" * 80)

# =============================================================================
# MEMORY LAYOUT CONSTANTS
# =============================================================================

# Physical heap range (from heap.cpp)
PHYS_HEAP_START = 0xA0000000
PHYS_HEAP_END = 0x100000000
PHYS_HEAP_SIZE = PHYS_HEAP_END - PHYS_HEAP_START

# Observed corruption parameters
CORRUPTION_DEST = 0xBA000000
CORRUPTION_PATTERN = 0xEA7060FF
CORRUPTION_SIZE_BYTES = int(1.1 * 1024 * 1024 * 1024)  # 1.1 GB
BUMP_USED_BYTES = 406 * 1024 * 1024  # 406 MB

print(f"\n--- Memory Layout ---")
print(f"Physical heap: 0x{PHYS_HEAP_START:08X} - 0x{PHYS_HEAP_END:08X} ({PHYS_HEAP_SIZE / (1024**3):.2f} GB)")
print(f"Corruption destination: 0x{CORRUPTION_DEST:08X}")
print(f"Corruption pattern: 0x{CORRUPTION_PATTERN:08X}")
print(f"Corruption size: {CORRUPTION_SIZE_BYTES / (1024**3):.2f} GB")
print(f"Bump allocator used: {BUMP_USED_BYTES / (1024**2):.1f} MB")

# =============================================================================
# GUESTTEXTURE STRUCTURE ANALYSIS
# =============================================================================

print("\n" + "=" * 80)
print("GUESTTEXTURE STRUCTURE ANALYSIS")
print("=" * 80)

# GuestTexture inherits from GuestBaseTexture which inherits from GuestResource
# Based on video.h analysis

# GuestResource (base)
GUEST_RESOURCE_SIZE = 12  # unused(4) + refCount(4) + type(4)

# GuestBaseTexture fields (after GuestResource)
GUEST_BASE_TEXTURE_FIELDS = {
    'textureHolder': ('unique_ptr', 8, 'Host pointer to RenderTexture holder'),
    'texture': ('RenderTexture*', 8, 'Host pointer to actual texture'),
    'textureView': ('unique_ptr', 8, 'Host pointer to texture view'),
    'width': ('uint32_t', 4, 'Texture width in pixels'),
    'height': ('uint32_t', 4, 'Texture height in pixels'),
    'format': ('RenderFormat', 4, 'Pixel format enum'),
    'descriptorIndex': ('uint32_t', 4, 'Index into descriptor set'),
    'layout': ('RenderTextureLayout', 4, 'Current texture layout'),
}

# GuestTexture additional fields
GUEST_TEXTURE_FIELDS = {
    'depth': ('uint32_t', 4, 'Texture depth (for 3D textures)'),
    'mipLevels': ('uint32_t', 4, 'Number of mip levels'),
    'viewDimension': ('enum', 4, 'Texture view dimension'),
    'mappedMemory': ('void*', 8, 'Pointer to mapped memory'),
    # Plus containers (framebuffers map, views vector, etc.)
}

print("\nGuestResource base:")
print(f"  +0x00: unused (4 bytes)")
print(f"  +0x04: refCount (4 bytes)")
print(f"  +0x08: type (4 bytes)")

offset = GUEST_RESOURCE_SIZE
print(f"\nGuestBaseTexture fields (offset {offset}):")
for name, (typ, size, desc) in GUEST_BASE_TEXTURE_FIELDS.items():
    print(f"  +0x{offset:02X}: {name} ({size} bytes) - {desc}")
    offset += size

print(f"\nGuestTexture fields (offset {offset}):")
for name, (typ, size, desc) in GUEST_TEXTURE_FIELDS.items():
    print(f"  +0x{offset:02X}: {name} ({size} bytes) - {desc}")
    offset += size

# =============================================================================
# WHAT HAPPENS WITH UNINITIALIZED FIELDS
# =============================================================================

print("\n" + "=" * 80)
print("UNINITIALIZED FIELD CONSEQUENCES")
print("=" * 80)

# If width/height are garbage (0xEA7060FF)
garbage_dim = CORRUPTION_PATTERN
pixels = garbage_dim * garbage_dim
bytes_per_pixel = 4  # RGBA
total_texture_bytes = pixels * bytes_per_pixel

print(f"\nScenario 1: width/height = 0x{garbage_dim:08X}")
print(f"  Pixels: {garbage_dim} x {garbage_dim} = {pixels:,}")
print(f"  At 4 bytes/pixel: {total_texture_bytes:,} bytes")
print(f"  That's {total_texture_bytes / (1024**4):.2f} TB of texture data!")
print(f"  GPU would attempt to read/write this massive region")

# If descriptorIndex is garbage
print(f"\nScenario 2: descriptorIndex = 0x{garbage_dim:08X}")
print(f"  Would index into descriptor set at position {garbage_dim}")
print(f"  Likely causes out-of-bounds access or binds wrong texture")

# If texture pointer is garbage pointing to physical heap
if PHYS_HEAP_START <= CORRUPTION_PATTERN < PHYS_HEAP_END:
    offset_into_heap = CORRUPTION_PATTERN - PHYS_HEAP_START
    print(f"\nScenario 3: texture ptr = 0x{CORRUPTION_PATTERN:08X}")
    print(f"  Points to physical heap offset: {offset_into_heap / (1024**2):.1f} MB")
    print(f"  GPU would use this as source/destination for operations")

# =============================================================================
# GPU RESOLVE/COPY OPERATION ANALYSIS
# =============================================================================

print("\n" + "=" * 80)
print("GPU RESOLVE/COPY OPERATION ANALYSIS")
print("=" * 80)

print("""
GPU operations that can cause massive memory writes:

1. TEXTURE RESOLVE (MSAA → single sample)
   - Reads from multisampled source texture
   - Writes to destination texture
   - If destination address is garbage → writes to wrong location

2. TEXTURE COPY (blit/stretch)
   - Copies pixels from source to destination
   - Size determined by texture dimensions
   - If dimensions are garbage → copies massive amount

3. RENDER TARGET CLEAR
   - Fills entire texture with color
   - If texture dimensions are garbage → clears huge region

4. FRAMEBUFFER RESOLVE
   - Xbox 360 EDRAM → main memory resolve
   - Destination determined by texture address
   - If address is garbage → resolves to wrong location
""")

# =============================================================================
# CORRUPTION SIZE CALCULATION
# =============================================================================

print("\n" + "=" * 80)
print("CORRUPTION SIZE VERIFICATION")
print("=" * 80)

# Calculate what texture dimensions would produce 1.1 GB
corruption_bytes = CORRUPTION_SIZE_BYTES
bytes_per_pixel = 4

# For a square texture: width * height * 4 = 1.1 GB
# width = height = sqrt(1.1 GB / 4)
import math
side_length = int(math.sqrt(corruption_bytes / bytes_per_pixel))
print(f"\nTo produce {corruption_bytes / (1024**3):.2f} GB of writes:")
print(f"  Square texture: {side_length} x {side_length} pixels")
print(f"  = {side_length * side_length * 4:,} bytes")

# What if only width is garbage?
# Assume height is valid (e.g., 1080)
valid_height = 1080
garbage_width = corruption_bytes // (valid_height * bytes_per_pixel)
print(f"\n  Or: width={garbage_width:,} x height={valid_height}")
print(f"  = {garbage_width * valid_height * 4:,} bytes")

# The pattern 0xEA7060FF as dimension
pattern_as_width = CORRUPTION_PATTERN
normal_height = 720  # 720p
resulting_bytes = pattern_as_width * normal_height * bytes_per_pixel
print(f"\n  Or: width=0x{pattern_as_width:X} ({pattern_as_width:,}) x height={normal_height}")
print(f"  = {resulting_bytes:,} bytes ({resulting_bytes / (1024**3):.2f} GB)")

# =============================================================================
# WHERE CORRUPTION HAPPENS IN PHYSICAL HEAP
# =============================================================================

print("\n" + "=" * 80)
print("PHYSICAL HEAP CORRUPTION MAPPING")
print("=" * 80)

corruption_start = CORRUPTION_DEST
corruption_end = corruption_start + CORRUPTION_SIZE_BYTES

print(f"\nCorruption region:")
print(f"  Start: 0x{corruption_start:08X} ({(corruption_start - PHYS_HEAP_START) / (1024**2):.1f} MB into heap)")
print(f"  End:   0x{corruption_end:08X} ({(corruption_end - PHYS_HEAP_START) / (1024**2):.1f} MB into heap)")
print(f"  Size:  {CORRUPTION_SIZE_BYTES / (1024**3):.2f} GB")

# Does corruption overflow heap?
if corruption_end > PHYS_HEAP_END:
    overflow = corruption_end - PHYS_HEAP_END
    print(f"\n  WARNING: Corruption OVERFLOWS physical heap by {overflow / (1024**2):.1f} MB!")
    print(f"  This would corrupt memory beyond physical heap range")
else:
    remaining = PHYS_HEAP_END - corruption_end
    print(f"\n  Corruption stays within heap, {remaining / (1024**2):.1f} MB remaining")

# What's at the pattern address?
pattern_addr = CORRUPTION_PATTERN
if PHYS_HEAP_START <= pattern_addr < PHYS_HEAP_END:
    pattern_offset = pattern_addr - PHYS_HEAP_START
    print(f"\nPattern as address (0x{pattern_addr:08X}):")
    print(f"  Offset into heap: {pattern_offset / (1024**2):.1f} MB")
    
    # If this is where hash table nodes are...
    if pattern_offset > BUMP_USED_BYTES:
        print(f"  This is BEYOND bump allocator usage ({BUMP_USED_BYTES / (1024**2):.1f} MB)")
        print(f"  Memory here is UNALLOCATED - could be used by normal heap")
    else:
        print(f"  This is WITHIN bump allocator range")

# =============================================================================
# TIMELINE RECONSTRUCTION
# =============================================================================

print("\n" + "=" * 80)
print("CORRUPTION TIMELINE RECONSTRUCTION")
print("=" * 80)

print("""
T+0: Game initializes, physical heap created at 0xA0000000
     Bump allocator ptr = 0xA0000000, used = 0

T+1..N: Normal allocations via AllocPhysical()
     GuestDevice allocated and ZEROED (correct)
     GuestTextures allocated but NOT zeroed (BUG)
     GuestSurfaces allocated but NOT zeroed (BUG)
     Bump allocator advances: used ≈ 406 MB

T+X: Specific GuestTexture allocated with garbage in fields
     texture->width = 0xEA7060FF (garbage from previous memory use)
     texture->height = ??? (may also be garbage)
     texture->texture = ??? (may point to garbage address)

T+X+1: GPU operation uses this texture
     - Could be resolve, copy, clear, or render
     - Operation calculates destination from garbage fields
     - Destination = 0xBA000000 (416 MB into heap)
     - Size = based on garbage dimensions

T+X+2: GPU writes 1.1 GB of data starting at 0xBA000000
     - Fills memory with 0xEA7060FF pattern
     - Overwrites:
       * Later bump allocator memory
       * Possibly hash table nodes
       * Possibly game data structures

T+X+3: Game code accesses corrupted hash table
     - sub_82802540 follows node->next pointers
     - node->next = 0xEA7060FF (corrupted)
     - That address also contains 0xEA7060FF
     - Infinite loop → beach ball
""")

# =============================================================================
# KEY EVIDENCE NEEDED
# =============================================================================

print("\n" + "=" * 80)
print("LLDB VERIFICATION CHECKLIST")
print("=" * 80)

print("""
To VERIFY this hypothesis with LLDB:

1. BEFORE memset fix - Confirm uninitialized memory:
   (lldb) b Heap::AllocPhysical
   (lldb) c
   # When hit at return (line 263):
   (lldb) p/x ptr
   (lldb) memory read ptr ptr+64
   # Should show NON-ZERO garbage if hypothesis correct

2. Catch the GPU operation that corrupts:
   (lldb) p g_memory.Translate(0xBA000000)
   # Get host address for guest 0xBA000000
   (lldb) watchpoint set expression -w write -- *(uint32_t*)<host_addr>
   # When triggered:
   (lldb) bt
   # Should show GPU resolve/copy operation

3. Check GuestTexture fields when allocated:
   (lldb) b video.cpp:3929
   # After AllocPhysical<GuestTexture>:
   (lldb) p/x texture->width
   (lldb) p/x texture->height
   (lldb) p/x texture->texture
   # Before constructor, may show garbage

4. Verify pattern in corrupted memory:
   (lldb) memory read -c 32 <host_addr_of_0xBA000000>
   # Should show 0xEA7060FF pattern repeating

5. Catch infinite loop:
   # When beach ball appears:
   (lldb) process interrupt
   (lldb) bt
   # Should show sub_82802540 or similar hash lookup
   (lldb) p/x v7
   # Should be 0xEA7060FF or similar garbage
""")

# =============================================================================
# CONCLUSION
# =============================================================================

print("\n" + "=" * 80)
print("HYPOTHESIS SUMMARY")
print("=" * 80)

print("""
HYPOTHESIS: GPU uses garbage → 1.1GB corruption

MECHANISM:
1. AllocPhysical returns uninitialized memory
2. GuestTexture/GuestSurface allocated without zeroing
3. Fields like width, height, or destination address contain garbage
4. GPU resolve/copy operation reads these garbage values
5. GPU writes massive amount (1.1 GB) to wrong location (0xBA000000)
6. Write fills memory with repeating pattern (0xEA7060FF)
7. Hash table nodes at affected addresses get overwritten
8. Hash lookup follows garbage pointers → infinite loop

EVIDENCE SUPPORTING:
✓ AllocPhysical doesn't zero memory (confirmed in heap.cpp:244)
✓ GuestDevice IS zeroed but GuestTexture/GuestSurface are NOT
✓ Pattern 0xEA7060FF is valid physical heap address
✓ Corruption destination 0xBA000000 is within physical heap
✓ sub_82802540 has infinite loop following node->next pointers

EVIDENCE NEEDED:
○ LLDB capture of uninitialized memory at allocation time
○ LLDB watchpoint showing GPU write to 0xBA000000
○ Stack trace showing which GPU operation causes write
○ GuestTexture field values at moment of GPU operation
""")
