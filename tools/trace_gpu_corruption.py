#!/usr/bin/env python3
"""
GPU Corruption Trace Analysis
Analyzes the code paths that could lead to GPU using garbage addresses.
"""

print("=" * 80)
print("GPU CORRUPTION CODE PATH ANALYSIS")
print("=" * 80)

# =============================================================================
# KEY CODE PATHS FOR GPU CORRUPTION
# =============================================================================

print("""
CRITICAL CODE PATHS IDENTIFIED:

1. TEXTURE ALLOCATION (video.cpp:3929)
   ```cpp
   const auto texture = g_userHeap.AllocPhysical<GuestTexture>(resourceType);
   // NO memset here - texture fields may contain garbage!
   ```
   
   After allocation, GuestTexture fields are:
   - texture->texture = GARBAGE (could point anywhere)
   - texture->width = GARBAGE (could be 0xEA7060FF)
   - texture->height = GARBAGE (could be 0xEA7060FF)
   
2. STRETCHRECT COMMAND (video.cpp:4132-4140)
   ```cpp
   static void StretchRect(GuestDevice* device, uint32_t flags, uint32_t, 
                           GuestTexture* texture, uint32_t, uint32_t, uint32_t destSliceOrFace)
   {
       RenderCommand cmd;
       cmd.type = RenderCommandType::StretchRect;
       cmd.stretchRect.texture = texture;  // texture may have garbage fields!
       g_renderQueue.enqueue(cmd);
   }
   ```

3. RESOLVE OPERATION (video.cpp:4317-4319)
   ```cpp
   commandList->resolveTextureRegion(texture->texture, 0, 0, surface->texture, ...);
   // OR
   commandList->resolveTexture(texture->texture, surface->texture);
   ```
   
   If texture->texture is garbage (0xEA7060FF interpreted as address):
   - GPU reads from garbage source address
   - GPU writes to destination based on garbage dimensions
   
4. COPY OPERATION (video.cpp:2669-2671)
   ```cpp
   g_commandLists[g_frame]->copyTextureRegion(
       RenderTextureCopyLocation::Subresource(args.texture->texture, 0),
       RenderTextureCopyLocation::PlacedFootprint(allocation.buffer, 
           args.texture->format,
           args.texture->width,    // GARBAGE!
           args.texture->height,   // GARBAGE!
           ...));
   ```
   
   If width/height are garbage:
   - copyTextureRegion calculates massive copy size
   - GPU writes beyond intended destination
""")

# =============================================================================
# SPECIFIC CORRUPTION SCENARIO
# =============================================================================

print("\n" + "=" * 80)
print("CORRUPTION SCENARIO RECONSTRUCTION")
print("=" * 80)

# Calculate what happens with garbage dimensions
GARBAGE = 0xEA7060FF
BYTES_PER_PIXEL = 4

# Scenario: width is garbage, height is valid
width_garbage = GARBAGE
height_valid = 720
copy_size = width_garbage * height_valid * BYTES_PER_PIXEL
print(f"\nScenario A: width=0x{width_garbage:X}, height={height_valid}")
print(f"  Copy size = {width_garbage} * {height_valid} * {BYTES_PER_PIXEL}")
print(f"  = {copy_size:,} bytes")
print(f"  = {copy_size / (1024**3):.2f} GB")

# Scenario: both dimensions garbage
width_garbage = GARBAGE
height_garbage = GARBAGE
copy_size = width_garbage * height_garbage * BYTES_PER_PIXEL
print(f"\nScenario B: width=0x{width_garbage:X}, height=0x{height_garbage:X}")
print(f"  Copy size = {width_garbage} * {height_garbage} * {BYTES_PER_PIXEL}")
print(f"  = {copy_size:,} bytes")
print(f"  = {copy_size / (1024**4):.2f} PB (OVERFLOW!)")

# Scenario: destination address is garbage
dest_garbage = 0xBA000000  # Observed corruption destination
phys_heap_start = 0xA0000000
offset = dest_garbage - phys_heap_start
print(f"\nScenario C: destination address = 0x{dest_garbage:X}")
print(f"  Offset into physical heap: {offset / (1024**2):.1f} MB")
print(f"  GPU writes starting here, corrupting everything after")

# =============================================================================
# WHY 0xEA7060FF PATTERN?
# =============================================================================

print("\n" + "=" * 80)
print("WHY THE 0xEA7060FF PATTERN?")
print("=" * 80)

pattern = 0xEA7060FF
print(f"\nPattern: 0x{pattern:08X}")

# As color
r = (pattern >> 24) & 0xFF
g = (pattern >> 16) & 0xFF
b = (pattern >> 8) & 0xFF
a = pattern & 0xFF
print(f"\nAs RGBA color: R={r}, G={g}, B={b}, A={a}")
print(f"  This is a pinkish/magenta color with full alpha")

# Possible sources
print("""
POSSIBLE SOURCES OF THIS PATTERN:

1. CLEAR COLOR
   - If a render target was cleared with this color
   - Then the memory was "freed" (bump allocator doesn't reuse)
   - New allocation gets that memory with old clear color

2. TEXTURE DATA
   - Some texture was uploaded with this color pattern
   - Memory reused for new allocation

3. MARKER/DEBUG VALUE
   - Some code uses this as a debug marker
   - e.g., to mark uninitialized memory

4. RANDOM GARBAGE
   - Could be coincidental heap data
   - Previous allocation's leftover data
""")

# =============================================================================
# CORRUPTION CHAIN VERIFICATION
# =============================================================================

print("\n" + "=" * 80)
print("FULL CORRUPTION CHAIN")
print("=" * 80)

print("""
STEP-BY-STEP CORRUPTION MECHANISM:

1. ALLOCATION
   AllocPhysical() called for GuestTexture
   └─ Returns pointer to memory containing 0xEA7060FF pattern
   └─ GuestTexture constructor runs, initializes some fields
   └─ But underlying memory still has garbage in uninitialized areas

2. FIELD CONTAMINATION
   texture->texture pointer = 0xEA7060FF (garbage from memory)
   OR texture->width = 0xEA7060FF (garbage)
   OR texture->height = 0xEA7060FF (garbage)
   
   Note: C++ default member initializers (= 0) should prevent this
   BUT: std::unique_ptr and RenderTexture* may not be zero-initialized
        if placement new doesn't zero the underlying memory first

3. GPU COMMAND SUBMISSION
   StretchRect or similar called with this texture
   └─ Command queued with garbage texture pointer/dimensions

4. GPU EXECUTION
   ExecutePendingStretchRectCommands runs
   └─ resolveTexture(texture->texture, surface->texture)
   └─ GPU reads from garbage source address
   └─ OR GPU writes based on garbage dimensions

5. MEMORY CORRUPTION
   GPU writes 1.1GB of data to 0xBA000000
   └─ Pattern 0xEA7060FF fills the region
   └─ Hash table nodes at affected addresses overwritten

6. INFINITE LOOP
   sub_82802540 accesses corrupted hash table
   └─ node->next = 0xEA7060FF (corrupted)
   └─ Follows pointer to 0xEA7060FF
   └─ That memory also contains 0xEA7060FF
   └─ Loop forever → BEACH BALL
""")

# =============================================================================
# VERIFICATION APPROACH
# =============================================================================

print("\n" + "=" * 80)
print("LLDB VERIFICATION APPROACH")
print("=" * 80)

print("""
To verify this hypothesis, we need to catch:

1. THE ALLOCATION with garbage
   - Break at AllocPhysical return
   - Check if memory contains non-zero data
   
2. THE TEXTURE with garbage fields
   - Break at StretchRect
   - Check texture->texture, texture->width, texture->height
   
3. THE GPU WRITE
   - Watchpoint on 0xBA000000 (guest address)
   - Catch the write, get backtrace
   
4. THE CORRUPTION PATTERN
   - After watchpoint triggers, examine memory
   - Verify it contains 0xEA7060FF pattern

LLDB COMMANDS:

# Step 1: Check AllocPhysical returns
(lldb) b Heap::AllocPhysical
(lldb) c
# At return:
(lldb) p/x ptr
(lldb) memory read ptr ptr+64
# Look for 0xEA7060FF or other non-zero data

# Step 2: Check texture at StretchRect
(lldb) b video.cpp:4132
(lldb) c
# When hit:
(lldb) p/x texture->texture
(lldb) p texture->width
(lldb) p texture->height

# Step 3: Catch GPU write
(lldb) p g_memory.Translate(0xBA000000)
# Use returned host address:
(lldb) watchpoint set expression -w write -- *(uint32_t*)<host_addr>
(lldb) c
# When triggered:
(lldb) bt

# Step 4: Verify corruption
(lldb) memory read <host_addr> <host_addr>+64
# Should show 0xEA7060FF pattern
""")

# =============================================================================
# ALTERNATIVE HYPOTHESIS
# =============================================================================

print("\n" + "=" * 80)
print("ALTERNATIVE HYPOTHESES TO CONSIDER")
print("=" * 80)

print("""
While uninitialized memory is the primary hypothesis, consider:

HYPOTHESIS B: Use-After-Free
- Texture freed but pointer still used
- Memory reallocated for something else
- Original texture pointer used, reads garbage

HYPOTHESIS C: Race Condition
- Render thread reads texture while main thread modifies
- Partial update causes inconsistent state
- GPU uses half-updated texture data

HYPOTHESIS D: Integer Overflow
- Texture dimensions multiplied, overflow occurs
- Resulting size wraps around
- GPU writes to unintended region

HYPOTHESIS E: Buffer Overrun
- Some buffer write goes past boundaries
- Corrupts adjacent texture structure
- GPU uses corrupted texture data

EVIDENCE FAVORING HYPOTHESIS A (Uninitialized Memory):
✓ AllocPhysical confirmed to not zero memory
✓ GuestDevice zeroed but GuestTexture not zeroed
✓ Pattern 0xEA7060FF is consistent (not random)
✓ Corruption starts at fixed offset (0xBA000000)
✓ Corruption size consistent (~1.1 GB)
""")
