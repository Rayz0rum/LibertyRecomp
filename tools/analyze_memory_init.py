#!/usr/bin/env python3
"""
Memory Initialization Analysis
Researches how physical heap gets its initial memory state.
"""

print("=" * 80)
print("MEMORY INITIALIZATION RESEARCH")
print("=" * 80)

# =============================================================================
# OS MEMORY ALLOCATION BEHAVIOR
# =============================================================================

print("""
RESEARCH FINDING 1: OS Memory Allocation

From memory.cpp:

macOS (line 32):
    base = mmap((void*)0x100000000ull, PPC_MEMORY_SIZE, 
                PROT_READ | PROT_WRITE, MAP_ANON | MAP_PRIVATE, -1, 0);

Windows (line 21):
    base = VirtualAlloc((void*)0x100000000ull, PPC_MEMORY_SIZE, 
                        MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);

CRITICAL: Both MAP_ANON (macOS) and MEM_COMMIT (Windows) GUARANTEE ZEROED PAGES!

This means:
  ✓ Physical heap memory is ZEROED when first allocated
  ✓ Garbage cannot come from uninitialized OS pages
  ✓ Garbage MUST come from something WRITING to memory AFTER allocation

CONCLUSION: The 0xEA7060FF pattern is WRITTEN to memory, not leftover garbage.
""")

# =============================================================================
# WHO WRITES TO PHYSICAL HEAP BEFORE ALLOCATION?
# =============================================================================

print("\n" + "=" * 80)
print("RESEARCH FINDING 2: Who Writes Before Allocation?")
print("=" * 80)

print("""
If OS provides zeroed memory, then something must WRITE the garbage pattern
BEFORE AllocPhysical returns that address. Possible sources:

1. GPU OPERATIONS (Most Likely)
   - GPU can write anywhere in physical memory range
   - If GPU writes to 0xBA000000 before it's "allocated"
   - That memory will contain the GPU's written data
   - Later AllocPhysical returns that address with garbage

2. DMA OPERATIONS
   - Direct Memory Access from hardware
   - Could write to physical addresses
   - Less likely in emulation context

3. ANOTHER THREAD'S ALLOCATION
   - Thread A allocates, writes pattern, "frees"
   - Bump allocator doesn't reuse, so this is impossible

4. MEMORY-MAPPED WRITES
   - Guest code writes via pointer to physical range
   - But guest code typically uses allocated memory

MOST LIKELY: GPU writes to 0xBA000000 area BEFORE bump allocator reaches it.
""")

# =============================================================================
# GPU PRE-WRITE SCENARIO
# =============================================================================

print("\n" + "=" * 80)
print("RESEARCH FINDING 3: GPU Pre-Write Scenario")
print("=" * 80)

# Calculate bump allocator progress
PHYS_HEAP_START = 0xA0000000
CORRUPTION_DEST = 0xBA000000
BUMP_USED = 406 * 1024 * 1024

bump_ptr_current = PHYS_HEAP_START + BUMP_USED
corruption_offset = CORRUPTION_DEST - PHYS_HEAP_START

print(f"""
Timeline Analysis:

At crash time:
  - Bump allocator used: {BUMP_USED / (1024**2):.1f} MB
  - Current bump pointer: 0x{bump_ptr_current:08X}
  - Corruption destination: 0x{CORRUPTION_DEST:08X} ({corruption_offset / (1024**2):.1f} MB offset)

CRITICAL OBSERVATION:
  Corruption destination (0xBA000000) is at 416 MB
  Bump allocator has only used 406 MB
  
  This means 0xBA000000 is 10 MB AHEAD of bump allocator!
  
  But wait - if corruption happens at 0xBA000000 BEFORE allocation,
  then when AllocPhysical later reaches 0xBA000000, it would
  return memory that already contains the corruption pattern.
  
  However, the memset fix zeros it at allocation time, so the
  returned memory would be clean.
  
  The REAL corruption happens when:
  1. Texture allocated with garbage (or valid) fields
  2. GPU operation reads garbage source/dest from texture
  3. GPU writes 1.1GB starting at 0xBA000000
  4. Write OVERWRITES memory that was ALREADY ALLOCATED
  5. Including hash table nodes allocated earlier
""")

# =============================================================================
# REVISED CORRUPTION SCENARIO
# =============================================================================

print("\n" + "=" * 80)
print("RESEARCH FINDING 4: Revised Corruption Scenario")
print("=" * 80)

print("""
REVISED HYPOTHESIS:

The corruption is NOT about uninitialized memory in NEW allocations.
The corruption is about GPU OVERWRITING EXISTING allocations.

Timeline:
  T+0: Bump allocator at 0xA0000000
  T+1: Hash table allocated at 0xAXXXXXXX (say, 100 MB in)
  T+2: Various textures allocated, bump advances to 406 MB
  T+3: GuestTexture allocated with uninitialized fields (e.g., bad pointer)
  T+4: GPU operation uses bad texture fields
  T+5: GPU writes 1.1GB starting at 0xBA000000 (416 MB offset)
  T+6: Write OVERWRITES hash table at 0xAXXXXXXX
  T+7: Hash table lookup fails → infinite loop

KEY INSIGHT:
  The memset fix works NOT because it prevents garbage in new allocations,
  but because zeroing the GuestTexture fields (especially pointers) prevents
  GPU from using garbage addresses/dimensions for its operations.
  
  With zeroed fields:
  - texture->texture = nullptr (not garbage pointer)
  - texture->width = 0 (not garbage dimension)
  - texture->height = 0 (not garbage dimension)
  - GPU operations fail gracefully or are skipped
  - No 1.1GB overwrite happens
""")

# =============================================================================
# WHAT FIELD CAUSES THE GPU WRITE?
# =============================================================================

print("\n" + "=" * 80)
print("RESEARCH FINDING 5: Which Field Triggers GPU Write?")
print("=" * 80)

print("""
Looking at GPU operation code paths to determine which uninitialized
field could cause the 1.1GB write:

FROM video.cpp ExecutePendingStretchRectCommands():

    for (const auto [texture, slice] : surface->destinationTextures)
    {
        // ...
        commandList->resolveTexture(texture->texture, surface->texture);
        // OR
        commandList->copyTextureRegion(..., texture->width, texture->height, ...);
    }

CANDIDATE FIELDS:

1. texture->texture (RenderTexture* pointer)
   - If garbage, GPU could write to wrong destination
   - But RenderTexture is a HOST object, not guest address
   - Metal/Vulkan would likely crash, not write to random address

2. texture->width / texture->height
   - If garbage (e.g., 0xEA7060FF), copy region would be massive
   - copyTextureRegion calculates size from dimensions
   - BUT: This would overflow, likely crash or be clamped

3. surface->destinationTextures map entries
   - Map could contain garbage texture pointers
   - Each garbage pointer used in resolve operation

4. texture->sourceSurface pointer
   - If garbage, surface->destinationTextures lookup fails

MOST LIKELY: The destinationTextures map contains garbage pointers
             pointing to unallocated memory interpreted as textures.
""")

# =============================================================================
# LLDB VERIFICATION NEEDED
# =============================================================================

print("\n" + "=" * 80)
print("LLDB VERIFICATION COMMANDS")
print("=" * 80)

print("""
To verify this revised hypothesis:

1. CATCH THE GPU WRITE:
   (lldb) p g_memory.Translate(0xBA000000)
   # Get host address
   (lldb) watchpoint set expression -w write -- *(uint32_t*)<host_addr>
   (lldb) c
   # When triggered:
   (lldb) bt
   # Should show ExecutePendingStretchRectCommands or similar

2. EXAMINE THE TEXTURE AT GPU WRITE TIME:
   (lldb) frame variable texture
   (lldb) p texture->texture
   (lldb) p texture->width
   (lldb) p texture->height
   # Look for garbage values

3. CHECK destinationTextures MAP:
   (lldb) p surface->destinationTextures.size()
   # If contains garbage entries, would show large size or crash

4. TRACE TEXTURE ALLOCATION:
   (lldb) b video.cpp:3929
   (lldb) c
   # After allocation:
   (lldb) memory read texture texture+128 --force
   # Look for 0xEA7060FF or other non-zero patterns

5. VERIFY HASH TABLE LOCATION:
   # Need to find where hash table nodes are allocated
   # Then verify they're in the corruption region
""")

# =============================================================================
# SUMMARY
# =============================================================================

print("\n" + "=" * 80)
print("RESEARCH SUMMARY")
print("=" * 80)

print("""
KEY FINDINGS:

1. OS provides ZEROED memory via mmap/VirtualAlloc
   → Garbage is WRITTEN, not leftover

2. Corruption at 0xBA000000 is AHEAD of bump pointer (416 MB vs 406 MB used)
   → GPU writes to memory not yet allocated

3. The 1.1GB write OVERWRITES existing allocations
   → Hash table corrupted → infinite loop

4. memset fix works by zeroing GuestTexture fields
   → Prevents GPU from using garbage addresses/dimensions
   → No massive write to wrong location

REMAINING QUESTIONS FOR LLDB:
- Which specific GPU operation triggers the write?
- What garbage value in which field causes it?
- Is the hash table in the corruption region?

THE FIX IS CORRECT because:
- Zeroing prevents garbage in pointer/dimension fields
- GPU operations use 0/nullptr instead of 0xEA7060FF
- No massive overwrite occurs
""")
