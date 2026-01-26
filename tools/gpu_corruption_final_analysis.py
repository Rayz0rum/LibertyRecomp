#!/usr/bin/env python3
"""
FINAL GPU CORRUPTION ANALYSIS
Consolidates all research findings on the 1.1GB memory corruption hypothesis.
"""

print("=" * 80)
print("FINAL GPU CORRUPTION ANALYSIS - RESEARCH FINDINGS")
print("=" * 80)

# =============================================================================
# MEMORY CALCULATIONS
# =============================================================================

# Physical heap constants
PHYS_HEAP_START = 0xA0000000
PHYS_HEAP_END = 0x100000000
PHYS_HEAP_SIZE = PHYS_HEAP_END - PHYS_HEAP_START

# Observed corruption values
CORRUPTION_DEST = 0xBA000000
CORRUPTION_PATTERN = 0xEA7060FF
CORRUPTION_SIZE = int(1.1 * 1024 * 1024 * 1024)
BUMP_USED = 406 * 1024 * 1024

# Calculate key offsets
dest_offset = CORRUPTION_DEST - PHYS_HEAP_START
pattern_offset = CORRUPTION_PATTERN - PHYS_HEAP_START
corruption_end = CORRUPTION_DEST + CORRUPTION_SIZE
heap_overflow = max(0, corruption_end - PHYS_HEAP_END)

print("\n--- KEY CALCULATIONS ---")
print(f"Physical heap size: {PHYS_HEAP_SIZE / (1024**3):.2f} GB")
print(f"Corruption destination offset: {dest_offset / (1024**2):.1f} MB into heap")
print(f"Pattern as address offset: {pattern_offset / (1024**2):.1f} MB into heap")
print(f"Corruption end: 0x{corruption_end:08X}")
print(f"Heap overflow: {heap_overflow / (1024**2):.1f} MB beyond heap end")

# =============================================================================
# GPU OPERATION ANALYSIS
# =============================================================================

print("\n" + "=" * 80)
print("GPU OPERATION CODE PATHS")
print("=" * 80)

gpu_operations = [
    {
        "name": "StretchRect",
        "file": "video.cpp",
        "line": 4132,
        "description": "Queues texture resolve/copy command",
        "risk": "If texture has garbage fields, command uses bad data"
    },
    {
        "name": "ExecutePendingStretchRectCommands",
        "file": "video.cpp", 
        "line": 4297,
        "description": "Executes queued resolve/copy operations",
        "risk": "GPU writes based on texture->texture pointer and dimensions"
    },
    {
        "name": "resolveTexture",
        "file": "video.cpp",
        "line": 4319,
        "description": "Hardware MSAA resolve operation",
        "risk": "GPU writes entire framebuffer to destination"
    },
    {
        "name": "copyTextureRegion",
        "file": "video.cpp",
        "line": 2669,
        "description": "Copies texture data using width/height",
        "risk": "If width/height garbage, copies massive amount"
    }
]

print("\nCritical GPU operations that could cause corruption:\n")
for op in gpu_operations:
    print(f"  {op['name']} ({op['file']}:{op['line']})")
    print(f"    - {op['description']}")
    print(f"    - RISK: {op['risk']}")
    print()

# =============================================================================
# TEXTURE ALLOCATION ANALYSIS  
# =============================================================================

print("=" * 80)
print("TEXTURE ALLOCATION SITES")
print("=" * 80)

allocation_sites = [
    {"file": "video.cpp", "line": 3929, "type": "GuestTexture", "zeroed": False},
    {"file": "video.cpp", "line": 4068, "type": "GuestSurface", "zeroed": False},
    {"file": "video.cpp", "line": 4002, "type": "GuestBuffer", "zeroed": False},
    {"file": "video.cpp", "line": 6201, "type": "GuestShader", "zeroed": False},
    {"file": "video.cpp", "line": 2572, "type": "GuestDevice", "zeroed": True},
    {"file": "video.cpp", "line": 9061, "type": "GuestTexture (GTAIV)", "zeroed": False},
]

print("\nAllocPhysical call sites:\n")
for site in allocation_sites:
    status = "✅ ZEROED" if site["zeroed"] else "❌ NOT ZEROED"
    print(f"  {site['file']}:{site['line']} - {site['type']} - {status}")

# =============================================================================
# GUESTTEXTURE FIELD ANALYSIS
# =============================================================================

print("\n" + "=" * 80)
print("GUESTTEXTURE FIELD INITIALIZATION")
print("=" * 80)

print("""
GuestTexture inherits GuestBaseTexture inherits GuestResource

Fields with default initializers (= 0):
  ✅ unused = 0
  ✅ refCount = 1 (actually initialized to 1)
  ✅ width = 0
  ✅ height = 0
  ✅ depth = 0
  ✅ mipLevels = 1
  ✅ descriptorIndex = 0
  ✅ format = UNKNOWN
  ✅ layout = UNKNOWN

Fields WITHOUT default initializers (rely on memory being zero):
  ❓ textureHolder (unique_ptr - should zero construct)
  ❓ texture (RenderTexture* - MAY NOT BE ZEROED)
  ❓ textureView (unique_ptr - should zero construct)
  ❓ mappedMemory (void* - MAY NOT BE ZEROED)
  ❓ viewDimension (enum - MAY NOT BE ZEROED)

CRITICAL: The 'texture' pointer (RenderTexture*) is NOT explicitly initialized!
If underlying memory contains garbage, this pointer could be garbage.
""")

# =============================================================================
# CORRUPTION MECHANISM ANALYSIS
# =============================================================================

print("=" * 80)
print("CORRUPTION MECHANISM - DETAILED ANALYSIS")
print("=" * 80)

print("""
THEORY: GPU uses garbage texture pointer → writes to wrong address

STEP 1: AllocPhysical returns uninitialized memory
  - Memory at returned address contains old data
  - Pattern 0xEA7060FF may be from previous render target clear
  - Or from previous texture upload

STEP 2: GuestTexture placement new runs
  - Constructor initializes SOME fields via default initializers
  - BUT: Fields without '= 0' may retain garbage
  - texture->texture could be 0xEA7060FF (garbage pointer)

STEP 3: CreateTexture assigns proper values
  - texture->textureHolder = g_device->createTexture(desc)
  - texture->texture = texture->textureHolder.get()
  - These OVERWRITE the garbage... usually

STEP 4: RACE or TIMING ISSUE?
  - Between allocation and proper initialization
  - Another thread reads texture->texture?
  - GPU command queued before texture fully initialized?

ALTERNATIVE: The garbage is in a DIFFERENT field
  - destinationTextures map could have garbage pointers
  - framebuffers map could have garbage
  - sourceSurface pointer could be garbage
""")

# =============================================================================
# WHY 0xBA000000 DESTINATION?
# =============================================================================

print("\n" + "=" * 80)
print("WHY DESTINATION 0xBA000000?")
print("=" * 80)

# Calculate where 0xBA000000 would come from
dest_as_pattern = CORRUPTION_DEST
print(f"\n0x{CORRUPTION_DEST:08X} analysis:")

# As RGBA color
r = (dest_as_pattern >> 24) & 0xFF
g = (dest_as_pattern >> 16) & 0xFF  
b = (dest_as_pattern >> 8) & 0xFF
a = dest_as_pattern & 0xFF
print(f"  As RGBA: R={r}, G={g}, B={b}, A={a}")

# Could it be calculated from something?
print(f"\n  Offset into physical heap: {dest_offset / (1024**2):.1f} MB")
print(f"  This is 10 MB AFTER bump allocator usage ({BUMP_USED / (1024**2):.1f} MB)")

# Possible sources
print("""
POSSIBLE SOURCES OF 0xBA000000:
1. Calculated from texture base + offset
   - Base = 0xA0000000 (phys heap start)
   - Offset = 0x1A000000 (416 MB)
   
2. From a GuestSurface allocation
   - Surfaces are in physical heap
   - Address could be valid allocation

3. From garbage width/height calculation
   - GPU calculates destination from dimensions
   - Garbage dimensions → garbage destination
""")

# =============================================================================
# EVIDENCE SUMMARY
# =============================================================================

print("\n" + "=" * 80)
print("EVIDENCE SUMMARY")
print("=" * 80)

evidence_for = [
    "AllocPhysical does NOT zero memory (heap.cpp:244 - confirmed)",
    "GuestDevice IS zeroed after allocation (video.cpp:2573)",
    "GuestTexture/GuestSurface are NOT zeroed after allocation",
    "Pattern 0xEA7060FF is valid physical heap address (1191 MB offset)",
    "Corruption destination 0xBA000000 is in physical heap (416 MB offset)",
    "Corruption size (~1.1GB) would overflow heap by 6.4 MB",
    "sub_82802540 has infinite loop following linked list pointers",
    "If list node contains 0xEA7060FF, loop follows to that address",
]

evidence_against = [
    "C++ default member initializers should zero most fields",
    "unique_ptr should zero-construct even without explicit init",
    "texture->texture is assigned immediately after allocation in CreateTexture",
    "Would need race condition for texture pointer to be used before init",
]

evidence_needed = [
    "LLDB capture showing non-zero memory at AllocPhysical return",
    "LLDB watchpoint catching write to 0xBA000000",
    "Stack trace showing which GPU operation causes the write",
    "Memory dump showing 0xEA7060FF pattern at corruption destination",
]

print("\nEVIDENCE SUPPORTING HYPOTHESIS:")
for e in evidence_for:
    print(f"  ✓ {e}")

print("\nEVIDENCE AGAINST (or needs explanation):")
for e in evidence_against:
    print(f"  ? {e}")

print("\nEVIDENCE STILL NEEDED:")
for e in evidence_needed:
    print(f"  ○ {e}")

# =============================================================================
# LLDB VERIFICATION COMMANDS
# =============================================================================

print("\n" + "=" * 80)
print("LLDB VERIFICATION COMMANDS")
print("=" * 80)

print("""
To verify with LLDB (BEFORE the memset fix):

1. CATCH UNINITIALIZED MEMORY:
   (lldb) b Heap::AllocPhysical
   (lldb) breakpoint modify --condition "size > 100"
   (lldb) c
   # At return:
   (lldb) finish
   (lldb) memory read $rax $rax+64
   
2. CHECK GUESTTEXTURE FIELDS BEFORE INIT:
   (lldb) b video.cpp:3929
   (lldb) c
   # After AllocPhysical, before constructor:
   (lldb) n
   (lldb) p/x *(uint64_t*)((char*)texture + 0x18)  # texture->texture offset
   
3. CATCH GPU WRITE:
   # First translate guest address:
   (lldb) p g_memory.Translate(0xBA000000)
   # Then set watchpoint:
   (lldb) watchpoint set expression -w write -- *(uint32_t*)<host_addr>
   (lldb) c
   # When triggered:
   (lldb) bt
   (lldb) frame select 0
   (lldb) p/x texture->texture
   
4. VERIFY CORRUPTION PATTERN:
   (lldb) memory read <host_addr_of_0xBA000000> <host_addr>+64
   # Should show 0xEA7060FF repeating
   
5. CATCH INFINITE LOOP:
   # When hung (beach ball):
   (lldb) process interrupt
   (lldb) bt all
   # Look for sub_82802540 or similar
   (lldb) frame variable v7
   # Should be 0xEA7060FF or similar
""")

# =============================================================================
# FINAL CONCLUSION
# =============================================================================

print("\n" + "=" * 80)
print("FINAL CONCLUSION")
print("=" * 80)

print("""
HYPOTHESIS STATUS: PARTIALLY VERIFIED

The hypothesis "GPU uses garbage → 1.1GB corruption" is SUPPORTED by:
- Code analysis showing uninitialized memory in AllocPhysical
- Inconsistent zeroing (GuestDevice yes, GuestTexture no)
- Valid physical heap addresses in corruption pattern
- GPU operations that use texture dimensions/pointers for writes

REMAINING QUESTIONS:
1. Which specific GPU operation triggers the corruption?
2. Which texture field contains the garbage (texture ptr? dimensions?)
3. Is there a race condition involved?
4. Why does corruption write 0xEA7060FF specifically?

RECOMMENDED VERIFICATION:
1. Run with LLDB watchpoint on 0xBA000000 (BEFORE memset fix)
2. Capture stack trace when watchpoint triggers
3. Examine texture fields at that moment
4. This will definitively confirm or refute the hypothesis

THE FIX (memset in AllocPhysical) SHOULD WORK because:
- Zeroing all physical allocations prevents garbage in any field
- Even if some fields aren't explicitly initialized, memory is zero
- GPU operations will see zeros instead of garbage
- No more 1.1GB writes to wrong addresses
""")

print("\n" + "=" * 80)
print("END OF ANALYSIS")
print("=" * 80)
