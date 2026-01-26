#!/usr/bin/env python3
"""
LLDB Verification Script for Uninitialized Memory Hypothesis
This script analyzes what we would observe when debugging AllocPhysical

RESEARCH QUESTION 1: Does AllocPhysical return non-zero memory?
"""

print("=" * 80)
print("LLDB VERIFICATION ANALYSIS: AllocPhysical Memory State")
print("=" * 80)

# =============================================================================
# ANALYSIS OF WHAT LLDB WOULD SHOW
# =============================================================================

print("""
VERIFICATION METHOD: Breakpoint + Memory Read

LLDB Commands to execute:
--------------------------
(lldb) b Heap::AllocPhysical
(lldb) c
# When breakpoint hits, step to return:
(lldb) finish
# Examine the returned pointer:
(lldb) p/x $rax
# Read memory at that address:
(lldb) memory read $rax $rax+64

EXPECTED RESULTS (WITHOUT memset fix):
--------------------------------------
If hypothesis is correct, memory read would show NON-ZERO values like:

0x????????: EA 70 60 FF EA 70 60 FF EA 70 60 FF EA 70 60 FF
0x????????: EA 70 60 FF EA 70 60 FF EA 70 60 FF EA 70 60 FF
...

This pattern (0xEA7060FF) would be leftover data from:
1. Previous render target clear operations
2. Previous texture data uploads
3. Previous GPU writes

EXPECTED RESULTS (WITH memset fix - current state):
---------------------------------------------------
Memory read would show all zeros:

0x????????: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
0x????????: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
...

This confirms the fix is working correctly.
""")

# =============================================================================
# BUMP ALLOCATOR ANALYSIS
# =============================================================================

print("\n" + "=" * 80)
print("BUMP ALLOCATOR MEMORY LAYOUT ANALYSIS")
print("=" * 80)

# Physical heap parameters
PHYS_HEAP_START = 0xA0000000
PHYS_HEAP_SIZE = int(1.5 * 1024 * 1024 * 1024)  # 1.5 GB
PHYS_HEAP_END = PHYS_HEAP_START + PHYS_HEAP_SIZE

print(f"""
Physical Heap Layout:
  Start: 0x{PHYS_HEAP_START:08X}
  End:   0x{PHYS_HEAP_END:08X}
  Size:  {PHYS_HEAP_SIZE / (1024**3):.2f} GB

Bump Allocator Behavior:
  - Allocations are sequential (never reuses freed memory)
  - s_physBumpPtr starts at PHYS_HEAP_START
  - s_physBumpUsed tracks total bytes allocated
  - Each allocation advances the bump pointer

CRITICAL OBSERVATION:
  Because bump allocator NEVER reuses memory, the "garbage" in
  newly allocated memory CANNOT come from previous allocations
  being freed. Instead, it must come from:
  
  1. Memory that was NEVER zeroed during heap initialization
  2. GPU writes that happened BEFORE the allocation
  3. DMA operations that wrote to physical memory
  4. Memory mapped regions that were pre-populated
""")

# =============================================================================
# MEMORY INITIALIZATION ANALYSIS
# =============================================================================

print("\n" + "=" * 80)
print("PHYSICAL HEAP INITIALIZATION ANALYSIS")
print("=" * 80)

print("""
Looking at heap.cpp for initialization code:

Key Question: Is physical heap zeroed at startup?

From heap.cpp InitPhysicalHeap():
  - Allocates host memory via mmap/VirtualAlloc
  - Does NOT explicitly zero the memory
  - Relies on OS to provide zeroed pages (usually true)
  - BUT: If memory is reused from previous process, may not be zero

LLDB Verification:
(lldb) b Heap::InitPhysicalHeap
(lldb) c
# After allocation, check initial memory state:
(lldb) p/x s_physBumpPtr
(lldb) memory read s_physBumpPtr s_physBumpPtr+64
# Should be all zeros if OS provides clean pages

ALTERNATIVE SOURCE OF GARBAGE:
If memory IS zeroed at init, then garbage must come from:
1. GPU writing to physical memory before CPU allocation
2. Race condition where GPU writes overlap with allocation
3. Memory-mapped I/O writing to physical addresses
""")

# =============================================================================
# GPU MEMORY WRITE ANALYSIS
# =============================================================================

print("\n" + "=" * 80)
print("GPU WRITE TIMING ANALYSIS")
print("=" * 80)

print("""
CRITICAL QUESTION: Can GPU write to memory BEFORE AllocPhysical returns it?

Scenario A: GPU Pre-Write
  1. Physical heap initialized (all zeros)
  2. GPU executes resolve/copy operation
  3. GPU writes to address 0xBA000000 (within unallocated heap region)
  4. Later, AllocPhysical returns memory including 0xBA000000
  5. That memory now contains GPU's written data (0xEA7060FF)

Scenario B: Race Condition
  1. AllocPhysical starts, calculates address
  2. GPU simultaneously writes to nearby addresses
  3. AllocPhysical returns
  4. Memory contains mix of zeros and GPU data

LLDB Verification for Scenario A:
(lldb) watchpoint set expression -w write -- *(uint32_t*)(<host_addr_of_0xBA000000>)
(lldb) c
# If watchpoint triggers BEFORE that address is allocated, confirms Scenario A

LLDB Verification for Scenario B:
(lldb) b Heap::AllocPhysical
(lldb) breakpoint command add
> bt
> thread list
> c
> DONE
# Look for GPU thread activity during allocation
""")

# =============================================================================
# PATTERN SOURCE ANALYSIS
# =============================================================================

print("\n" + "=" * 80)
print("0xEA7060FF PATTERN SOURCE ANALYSIS")
print("=" * 80)

pattern = 0xEA7060FF

# As RGBA color (different byte orders)
rgba_be = [(pattern >> 24) & 0xFF, (pattern >> 16) & 0xFF, (pattern >> 8) & 0xFF, pattern & 0xFF]
rgba_le = [pattern & 0xFF, (pattern >> 8) & 0xFF, (pattern >> 16) & 0xFF, (pattern >> 24) & 0xFF]

print(f"Pattern: 0x{pattern:08X}")
print(f"\nAs RGBA (Big Endian):    R={rgba_be[0]}, G={rgba_be[1]}, B={rgba_be[2]}, A={rgba_be[3]}")
print(f"As RGBA (Little Endian): R={rgba_le[0]}, G={rgba_le[1]}, B={rgba_le[2]}, A={rgba_le[3]}")

# Possible sources
print("""
POSSIBLE SOURCES OF 0xEA7060FF:

1. RENDER TARGET CLEAR COLOR
   - Game clears render target with specific color
   - Color persists in memory after "free"
   - Check: Search for clear color values in code

2. TEXTURE UPLOAD DATA
   - Texture contains this pixel color
   - Uploaded to GPU memory
   - Check: Search for texture data with this pattern

3. DEBUG/POISON VALUE
   - Used intentionally to mark uninitialized memory
   - Common patterns: 0xDEADBEEF, 0xFEEDFACE, etc.
   - 0xEA7060FF doesn't match common debug patterns

4. CALCULATED ADDRESS
   - Not a color, but a memory address
   - 0xEA7060FF = valid physical heap address (1191 MB offset)
   - Could be a pointer that got written to memory

5. INSTRUCTION ENCODING
   - PowerPC/ARM instruction encoding
   - Unlikely in data region
""")

# Search for pattern in code
print("\n--- Searching for 0xEA7060FF in codebase ---")
print("LLDB command to search:")
print("(lldb) memory find -e 0xEA7060FF <heap_start> <heap_end>")

# =============================================================================
# GUESTTEXTURE FIELD ANALYSIS
# =============================================================================

print("\n" + "=" * 80)
print("GUESTTEXTURE FIELD INITIALIZATION DEEP DIVE")
print("=" * 80)

print("""
RESEARCH QUESTION 3: Which texture field contains garbage?

GuestTexture memory layout (from video.h):

Offset  Field               Size  Default Init?  
------  ------------------  ----  -------------
0x00    unused              4     = 0 ✓
0x04    refCount            4     = 1 ✓
0x08    type                4     enum (set by constructor)
0x0C    textureHolder       8     unique_ptr (zero-init in C++)
0x14    texture             8     RenderTexture* (NO DEFAULT!)
0x1C    textureView         8     unique_ptr (zero-init in C++)
0x24    width               4     = 0 ✓
0x28    height              4     = 0 ✓
0x2C    format              4     = UNKNOWN ✓
0x30    descriptorIndex     4     = 0 ✓
0x34    layout              4     = UNKNOWN ✓
0x38    depth               4     = 0 ✓
0x3C    mipLevels           4     = 1 ✓
0x40    viewDimension       4     enum (NO DEFAULT!)
0x44    mappedMemory        8     void* (NO DEFAULT!)
0x4C    sourceSurface       8     GuestSurface* (NO DEFAULT!)
0x54    framebuffers        ?     std::map (zero-init)
0x??    destinationTextures ?     std::unordered_set

FIELDS WITHOUT DEFAULT INITIALIZERS (SUSPICIOUS):
  - texture (offset 0x14): Raw pointer, could be garbage
  - viewDimension (offset 0x40): Enum, could be garbage
  - mappedMemory (offset 0x44): Raw pointer, could be garbage
  - sourceSurface (offset 0x4C): Raw pointer, could be garbage

LLDB Verification:
(lldb) b video.cpp:3929
(lldb) c
# After AllocPhysical<GuestTexture>, before any field assignment:
(lldb) n  # step to next line
(lldb) p/x *(uint64_t*)((char*)texture + 0x14)  # texture->texture
(lldb) p/x *(uint64_t*)((char*)texture + 0x44)  # mappedMemory
(lldb) p/x *(uint64_t*)((char*)texture + 0x4C)  # sourceSurface

If any show 0xEA7060FF or similar garbage, that's the culprit!
""")

# =============================================================================
# RACE CONDITION ANALYSIS
# =============================================================================

print("\n" + "=" * 80)
print("RACE CONDITION ANALYSIS")
print("=" * 80)

print("""
RESEARCH QUESTION 4: Is there a race condition?

THREADS INVOLVED:
1. Main Thread - Game logic, calls CreateTexture
2. Render Thread - Executes GPU commands, processes render queue
3. GPU Thread - Hardware execution (not directly visible)

POTENTIAL RACE SCENARIOS:

Scenario A: Allocation vs GPU Write Race
  Main Thread                    Render Thread
  ------------                   -------------
  AllocPhysical() starts
  calculates address = 0xBA000000
                                 GPU writes to 0xBA000000
  returns 0xBA000000
  texture->texture = garbage

Scenario B: Texture Use Before Init Race
  Main Thread                    Render Thread
  ------------                   -------------
  AllocPhysical() returns
  texture ptr visible
                                 Reads texture->texture (garbage!)
  texture->texture = valid
                                 (too late, already used garbage)

LLDB Verification:
(lldb) b Heap::AllocPhysical
(lldb) breakpoint command add
> script
> import lldb
> print("ALLOC: Thread", lldb.frame.thread.name)
> print("ALLOC: Address", lldb.frame.FindVariable("ptr"))
> DONE

(lldb) b video.cpp:4317  # resolveTexture
(lldb) breakpoint command add
> script
> print("RESOLVE: Thread", lldb.frame.thread.name)
> DONE

# Run and look for interleaved output indicating race
""")

# =============================================================================
# SPECIFIC LLDB SESSION COMMANDS
# =============================================================================

print("\n" + "=" * 80)
print("COMPLETE LLDB VERIFICATION SESSION")
print("=" * 80)

print("""
STEP-BY-STEP LLDB SESSION:

# Start LLDB
lldb "./out/build/macos-release/LibertyRecomp/Liberty Recompiled.app/Contents/MacOS/Liberty Recompiled"

# Set breakpoints
(lldb) b Heap::AllocPhysical
(lldb) b video.cpp:3929
(lldb) b video.cpp:4317

# Start program
(lldb) run

# VERIFICATION 1: AllocPhysical Memory State
# When AllocPhysical breakpoint hits:
(lldb) finish
(lldb) register read rax
(lldb) memory read $rax $rax+128 --force
# Document: Are there non-zero bytes? What pattern?

# VERIFICATION 2: GuestTexture Fields
# When video.cpp:3929 hits:
(lldb) n
(lldb) p texture
(lldb) memory read texture texture+128 --force
# Document: Which fields have garbage?

# VERIFICATION 3: GPU Operation
# When video.cpp:4317 hits:
(lldb) bt
(lldb) p texture->texture
(lldb) p surface->texture
# Document: Are pointers valid?

# VERIFICATION 4: Watchpoint on Corruption Address
(lldb) p g_memory.Translate(0xBA000000)
# Use returned host address:
(lldb) watchpoint set expression -w write -- *(uint32_t*)<host_addr>
(lldb) c
# When triggered:
(lldb) bt
# Document: What operation writes here?

# VERIFICATION 5: Thread Analysis
(lldb) thread list
# Document: Which threads are active? Any GPU threads?
(lldb) bt all
# Document: What are all threads doing?
""")

print("\n" + "=" * 80)
print("END OF LLDB VERIFICATION ANALYSIS")
print("=" * 80)
