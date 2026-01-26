#!/usr/bin/env python3
"""
GuestTexture Field Initialization Analysis
Research which fields could contain garbage and cause GPU corruption.
"""

print("=" * 80)
print("GUESTTEXTURE FIELD INITIALIZATION ANALYSIS")
print("=" * 80)

# =============================================================================
# STRUCT ANALYSIS FROM video.h
# =============================================================================

print("""
FROM video.h - GuestResource (base class):

struct GuestResource {
    uint32_t unused;        // No initializer
    uint32_t refCount = 1;  // ✓ Initialized
    ResourceType type;      // Set by constructor
};

FROM video.h - GuestBaseTexture (inherits GuestResource):

struct GuestBaseTexture : GuestResource {
    std::unique_ptr<RenderTexture> textureHolder;  // ✓ unique_ptr default-init to nullptr
    RenderTexture* texture = nullptr;               // ✓ Explicitly initialized
    std::unique_ptr<RenderTextureView> textureView; // ✓ unique_ptr default-init to nullptr
    uint32_t width = 0;                             // ✓ Explicitly initialized
    uint32_t height = 0;                            // ✓ Explicitly initialized
    RenderFormat format = RenderFormat::UNKNOWN;    // ✓ Explicitly initialized
    uint32_t descriptorIndex = 0;                   // ✓ Explicitly initialized
    RenderTextureLayout layout = RenderTextureLayout::UNKNOWN; // ✓ Explicitly initialized
};

FROM video.h - GuestTexture (inherits GuestBaseTexture):

struct GuestTexture : GuestBaseTexture {
    uint32_t depth = 0;                             // ✓ Explicitly initialized
    uint32_t mipLevels = 1;                         // ✓ Explicitly initialized
    RenderTextureViewDimension viewDimension = RenderTextureViewDimension::UNKNOWN; // ✓ Initialized
    void* mappedMemory = nullptr;                   // ✓ Explicitly initialized
    ankerl::unordered_dense::map<...> framebuffers; // ✓ Default constructed (empty)
    std::vector<...> framebufferViews;              // ✓ Default constructed (empty)
    std::unique_ptr<GuestTexture> patchedTexture;   // ✓ unique_ptr default-init to nullptr
    struct GuestSurface* sourceSurface = nullptr;   // ✓ Explicitly initialized
};

FROM video.h - GuestSurface (inherits GuestBaseTexture):

struct GuestSurface : GuestBaseTexture {
    uint32_t guestFormat = 0;                       // ✓ Explicitly initialized
    ankerl::unordered_dense::map<...> framebuffers; // ✓ Default constructed (empty)
    RenderSampleCounts sampleCount = RenderSampleCount::COUNT_1; // ✓ Initialized
    ankerl::unordered_dense::map<GuestTexture*, uint32_t> destinationTextures; // ✓ Default constructed
    bool wasCached = false;                         // ✓ Explicitly initialized
};
""")

# =============================================================================
# CRITICAL FINDING
# =============================================================================

print("\n" + "=" * 80)
print("CRITICAL FINDING: ALL FIELDS HAVE DEFAULT INITIALIZERS!")
print("=" * 80)

print("""
ANALYSIS:

Looking at video.h, ALL fields in GuestTexture and GuestSurface have either:
1. Explicit default initializers (= 0, = nullptr, = UNKNOWN)
2. Are containers that default-construct to empty state
3. Are unique_ptr which default to nullptr

THIS MEANS:
  - Even with uninitialized memory, C++ constructors SHOULD zero/initialize all fields
  - The memset fix might be REDUNDANT if constructors run correctly

BUT WAIT - PLACEMENT NEW CONSIDERATION:
  When AllocPhysical<T> is called:
  1. Raw memory is returned (potentially garbage)
  2. Placement new constructs T at that address
  3. Constructor runs, initializing fields with default values

  The question is: Does placement new GUARANTEE to overwrite all memory?
  Answer: YES, for fields with initializers, NO for padding bytes.

POTENTIAL ISSUE: PADDING BYTES
  - Struct padding between fields is NOT initialized
  - If sizeof(GuestTexture) > sum of field sizes, padding exists
  - Padding bytes retain garbage from uninitialized memory
  - BUT: Padding bytes shouldn't be read by normal code
""")

# =============================================================================
# ALTERNATIVE HYPOTHESIS
# =============================================================================

print("\n" + "=" * 80)
print("ALTERNATIVE HYPOTHESIS: THE PROBLEM ISN'T GuestTexture")
print("=" * 80)

print("""
Given that all GuestTexture fields have default initializers, the corruption
might NOT be from uninitialized GuestTexture fields.

ALTERNATIVE SOURCES OF CORRUPTION:

1. GuestResource.unused FIELD
   - This field has NO default initializer in the base class
   - If garbage, could be interpreted as something else
   - But it's marked 'unused' so probably not read

2. RENDER COMMAND QUEUE CORRUPTION
   - RenderCommand struct in render queue
   - If queue memory is corrupted, wrong commands execute
   - Could cause arbitrary GPU writes

3. DESCRIPTOR SET CORRUPTION
   - Texture descriptors in GPU descriptor heap
   - If descriptor index is wrong, binds wrong texture
   - GPU reads/writes wrong memory

4. GUEST CODE PASSING BAD POINTER
   - Game code calls StretchRect with garbage texture pointer
   - StretchRect trusts the pointer
   - Garbage pointer added to destinationTextures map

5. MAP CONTAINER CORRUPTION
   - destinationTextures map itself is corrupted
   - Iteration returns garbage texture pointers
   - GPU uses these garbage pointers
""")

# =============================================================================
# EXAMINING GuestResource.unused
# =============================================================================

print("\n" + "=" * 80)
print("EXAMINING GuestResource.unused FIELD")
print("=" * 80)

print("""
FROM video.h:

struct GuestResource {
    uint32_t unused;        // <-- NO INITIALIZER!
    uint32_t refCount = 1;
    ResourceType type;
};

LLDB VERIFICATION:
(lldb) b video.cpp:3929
(lldb) c
# After AllocPhysical:
(lldb) n
(lldb) p texture->unused
# If this shows 0xEA7060FF or similar, we found the issue!

BUT: If 'unused' is truly unused, it shouldn't cause corruption.
Let's search for any code that reads this field...
""")

# =============================================================================
# SEARCH RESULTS
# =============================================================================

print("\n" + "=" * 80)
print("SEARCH: Who reads GuestResource.unused?")
print("=" * 80)

print("""
grep -r "->unused" video.cpp video.h
grep -r "\\.unused" video.cpp video.h

EXPECTED RESULT:
  If truly unused, no code should read this field.
  The corruption must come from elsewhere.

ALTERNATIVE: Check if 'unused' is actually used for something:
  - Xbox 360 D3D resource header
  - Alignment padding
  - Reserved field that game code reads
""")

# =============================================================================
# RACE CONDITION ANALYSIS
# =============================================================================

print("\n" + "=" * 80)
print("RACE CONDITION ANALYSIS")
print("=" * 80)

print("""
RESEARCH QUESTION 4: Is there a race condition?

THREADS IN LIBERTYRECOMP:

1. Main Thread
   - Runs guest game code
   - Calls CreateTexture, StretchRect, etc.
   - Allocates GuestTexture via AllocPhysical

2. Render Thread
   - Processes render command queue
   - Executes GPU commands
   - Calls ExecutePendingStretchRectCommands

3. Audio Thread
   - Separate, shouldn't affect GPU/memory

POTENTIAL RACE:

Main Thread                      Render Thread
-----------                      -------------
texture = AllocPhysical()
                                 (render thread can't see texture yet)
StretchRect(texture)
  cmd.texture = texture
  g_renderQueue.enqueue(cmd)
                                 ProcStretchRect(cmd)
                                   args.texture->sourceSurface  // texture fully initialized?
                                   surface->destinationTextures.emplace(texture, ...)

CRITICAL QUESTION:
  Is texture fully initialized BEFORE StretchRect queues the command?
  If not, render thread could see partially initialized texture.

ANSWER FROM CODE FLOW:
  CreateTexture (video.cpp:3912):
    1. AllocPhysical<GuestTexture>() - memory allocated
    2. Constructor runs - fields initialized to defaults
    3. textureHolder = g_device->createTexture() - RenderTexture created
    4. texture->texture = textureHolder.get() - pointer assigned
    5. texture->textureView = ... - view created
    6. texture->width = width; texture->height = height; - dims set
    7. return texture;
  
  THEN game code calls StretchRect with this texture.
  
  So texture IS fully initialized before StretchRect.
  
  UNLESS: Game code reuses a texture pointer after "freeing" it
          (use-after-free scenario)

LLDB VERIFICATION:
(lldb) b video.cpp:4132  # StretchRect
(lldb) c
# When hit:
(lldb) p texture->texture
(lldb) p texture->width
(lldb) p texture->height
# All should be valid values, not garbage
""")

# =============================================================================
# REVISED CONCLUSION
# =============================================================================

print("\n" + "=" * 80)
print("REVISED RESEARCH CONCLUSION")
print("=" * 80)

print("""
FINDINGS:

1. GuestTexture fields ALL have default initializers
   → Constructor SHOULD zero/init all fields
   → memset fix may be redundant for field initialization

2. GuestResource.unused has NO initializer
   → Could contain garbage
   → But if truly unused, won't cause corruption

3. Race condition analysis shows texture IS initialized before StretchRect
   → Normal code path is safe
   → But use-after-free could cause issues

4. OS provides zeroed memory (mmap/VirtualAlloc)
   → Garbage pattern must be WRITTEN somewhere

MOST LIKELY ROOT CAUSE:

The corruption is probably NOT from uninitialized GuestTexture fields.
Instead, it's likely from:

A) USE-AFTER-FREE
   - Game code reuses freed texture pointer
   - Memory reallocated for something else
   - Old pointer used in StretchRect

B) GUEST CODE BUG
   - Game passes invalid pointer to StretchRect
   - Our code trusts it, adds to destinationTextures
   - Garbage pointer used in GPU operation

C) BUMP ALLOCATOR MEMORY REUSE
   - Wait, bump allocator DOESN'T reuse memory
   - So this isn't possible

THE MEMSET FIX MIGHT WORK BY:
   - Not fixing uninitialized fields (they're already initialized)
   - But zeroing the ENTIRE allocation including padding
   - Which zeros memory that GUEST CODE might read/write
   - Guest code expects zeroed memory (Xbox 360 behavior?)

VERIFICATION NEEDED:
   Run without memset, check if game code reads from allocation
   before our constructor sets values.
""")
