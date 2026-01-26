#!/usr/bin/env python3
"""
CONSOLIDATED LLDB VERIFICATION FINDINGS
Final research summary for GPU memory corruption hypothesis.
"""

print("=" * 80)
print("CONSOLIDATED LLDB VERIFICATION FINDINGS")
print("=" * 80)

# =============================================================================
# RESEARCH QUESTION 1: Does AllocPhysical return non-zero memory?
# =============================================================================

print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║ QUESTION 1: Does AllocPhysical return non-zero memory?                       ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║ FINDING: OS GUARANTEES ZEROED MEMORY                                         ║
║                                                                              ║
║ Evidence from memory.cpp:                                                    ║
║   • macOS: mmap() with MAP_ANON → OS provides zeroed pages                   ║
║   • Windows: VirtualAlloc() with MEM_COMMIT → OS provides zeroed pages       ║
║                                                                              ║
║ CONCLUSION:                                                                  ║
║   Initial physical heap memory IS zeroed by the OS.                          ║
║   Any garbage pattern (0xEA7060FF) must be WRITTEN to memory AFTER           ║
║   OS allocation, not leftover from uninitialized pages.                      ║
║                                                                              ║
║ LLDB VERIFICATION:                                                           ║
║   (lldb) b Heap::InitPhysicalHeap                                            ║
║   (lldb) finish                                                              ║
║   (lldb) memory read s_physBumpPtr s_physBumpPtr+64                          ║
║   Expected: All zeros (00 00 00 00 ...)                                      ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")

# =============================================================================
# RESEARCH QUESTION 2: Which GPU operation writes to 0xBA000000?
# =============================================================================

print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║ QUESTION 2: Which GPU operation writes to 0xBA000000?                        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║ FINDING: ExecutePendingStretchRectCommands IS THE LIKELY CULPRIT             ║
║                                                                              ║
║ Evidence from video.cpp:4297-4458:                                           ║
║   • Iterates surface->destinationTextures map                                ║
║   • Calls resolveTexture() or copyTextureRegion() for each texture           ║
║   • Uses texture->texture pointer for GPU destination                        ║
║   • Uses texture->width/height for copy dimensions                           ║
║                                                                              ║
║ CORRUPTION MECHANISM:                                                        ║
║   1. Bad texture pointer in destinationTextures map                          ║
║   2. GPU operation reads garbage from that pointer                           ║
║   3. GPU writes massive amount to wrong destination (0xBA000000)             ║
║   4. Write overwrites hash table nodes → infinite loop                       ║
║                                                                              ║
║ LLDB VERIFICATION:                                                           ║
║   (lldb) p g_memory.Translate(0xBA000000)                                    ║
║   (lldb) watchpoint set expression -w write -- *(uint32_t*)<host_addr>       ║
║   (lldb) c                                                                   ║
║   # When triggered:                                                          ║
║   (lldb) bt                                                                  ║
║   Expected: ExecutePendingStretchRectCommands in backtrace                   ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")

# =============================================================================
# RESEARCH QUESTION 3: Which texture field contains garbage?
# =============================================================================

print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║ QUESTION 3: Which texture field contains garbage?                            ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║ FINDING: ALL GuestTexture FIELDS HAVE DEFAULT INITIALIZERS!                  ║
║                                                                              ║
║ Evidence from video.h:                                                       ║
║   • texture = nullptr (explicitly initialized)                               ║
║   • width = 0 (explicitly initialized)                                       ║
║   • height = 0 (explicitly initialized)                                      ║
║   • All containers default-construct to empty                                ║
║   • All unique_ptr default to nullptr                                        ║
║                                                                              ║
║ EXCEPTION: GuestResource.unused has NO initializer                           ║
║   But this field is marked "unused" and likely not read                      ║
║                                                                              ║
║ REVISED HYPOTHESIS:                                                          ║
║   The problem is NOT uninitialized GuestTexture fields.                      ║
║   C++ constructors properly initialize all fields.                           ║
║                                                                              ║
║   More likely:                                                               ║
║   A) Guest code passes invalid/freed pointer to StretchRect                  ║
║   B) Use-after-free: texture freed but pointer reused                        ║
║   C) Guest code reads memory BEFORE constructor runs                         ║
║                                                                              ║
║ LLDB VERIFICATION:                                                           ║
║   (lldb) b video.cpp:4132  # StretchRect                                     ║
║   (lldb) c                                                                   ║
║   (lldb) p texture->texture                                                  ║
║   (lldb) p texture->width                                                    ║
║   Expected: Valid values (if constructor ran) or garbage (if UAF)            ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")

# =============================================================================
# RESEARCH QUESTION 4: Is there a race condition?
# =============================================================================

print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║ QUESTION 4: Is there a race condition?                                       ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║ FINDING: UNLIKELY FOR NORMAL CODE PATH                                       ║
║                                                                              ║
║ Thread Analysis:                                                             ║
║   • Main Thread: Allocates texture, fully initializes, THEN calls StretchRect║
║   • Render Thread: Processes commands AFTER they're queued                   ║
║   • Queue acts as synchronization barrier                                    ║
║                                                                              ║
║ Code Flow:                                                                   ║
║   1. CreateTexture() fully initializes texture                               ║
║   2. Game code receives fully initialized texture                            ║
║   3. Game code calls StretchRect(texture)                                    ║
║   4. Command queued with valid texture pointer                               ║
║   5. Render thread processes command                                         ║
║                                                                              ║
║ POTENTIAL RACE SCENARIOS:                                                    ║
║   • Game frees texture while render thread still has reference               ║
║   • Multiple threads call StretchRect with same texture                      ║
║   • Texture modified while queued command pending                            ║
║                                                                              ║
║ LLDB VERIFICATION:                                                           ║
║   (lldb) thread list                                                         ║
║   (lldb) bt all                                                              ║
║   Check for multiple threads accessing same texture                          ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")

# =============================================================================
# FINAL RESEARCH CONCLUSIONS
# =============================================================================

print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                        FINAL RESEARCH CONCLUSIONS                            ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║ KEY FINDINGS:                                                                ║
║                                                                              ║
║ 1. OS Memory: ZEROED at allocation (mmap/VirtualAlloc guarantee)             ║
║    → Garbage is WRITTEN, not leftover                                        ║
║                                                                              ║
║ 2. GuestTexture Fields: ALL have default initializers                        ║
║    → C++ constructor properly initializes fields                             ║
║    → Uninitialized field hypothesis is WEAK                                  ║
║                                                                              ║
║ 3. Race Condition: UNLIKELY for normal code path                             ║
║    → Texture fully initialized before StretchRect                            ║
║    → Queue provides synchronization                                          ║
║                                                                              ║
║ 4. GPU Write: ExecutePendingStretchRectCommands most likely source           ║
║    → Uses texture pointers from destinationTextures map                      ║
║    → Bad pointer → wrong GPU write destination                               ║
║                                                                              ║
║ MOST PROBABLE ROOT CAUSE:                                                    ║
║                                                                              ║
║   USE-AFTER-FREE or GUEST CODE BUG                                           ║
║                                                                              ║
║   1. Guest code (game) obtains texture pointer                               ║
║   2. Guest code "frees" texture (decrements refcount, etc.)                  ║
║   3. Memory potentially reused for other allocation                          ║
║   4. Guest code STILL holds old pointer                                      ║
║   5. Guest code calls StretchRect with stale pointer                         ║
║   6. Stale pointer added to destinationTextures                              ║
║   7. GPU operation uses stale pointer → corruption                           ║
║                                                                              ║
║ WHY MEMSET FIX WORKS:                                                        ║
║                                                                              ║
║   The memset doesn't fix uninitialized C++ fields (they're initialized).     ║
║   Instead, it zeros the ENTIRE allocation including:                         ║
║   • Padding bytes between struct fields                                      ║
║   • Memory that guest code might read before our constructor                 ║
║   • Any bytes that Xbox 360 code expects to be zero                          ║
║                                                                              ║
║   Xbox 360 physical memory allocations were likely zeroed.                   ║
║   Guest code may rely on this behavior.                                      ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")

# =============================================================================
# LLDB VERIFICATION SESSION COMMANDS
# =============================================================================

print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                      LLDB VERIFICATION SESSION                               ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║ To fully verify these findings, run WITHOUT the memset fix:                  ║
║                                                                              ║
║ 1. REMOVE MEMSET (temporarily):                                              ║
║    In heap.cpp:245, comment out: // memset(ptr, 0, size);                    ║
║    Rebuild project                                                           ║
║                                                                              ║
║ 2. START LLDB:                                                               ║
║    lldb "./out/build/macos-release/LibertyRecomp/Liberty Recompiled.app/     ║
║          Contents/MacOS/Liberty Recompiled"                                  ║
║                                                                              ║
║ 3. SET WATCHPOINT ON CORRUPTION DESTINATION:                                 ║
║    (lldb) b main                                                             ║
║    (lldb) run                                                                ║
║    # After init:                                                             ║
║    (lldb) p g_memory.Translate(0xBA000000)                                   ║
║    (lldb) watchpoint set expression -w write -- *(uint32_t*)<host_addr>      ║
║    (lldb) c                                                                  ║
║                                                                              ║
║ 4. WHEN WATCHPOINT TRIGGERS:                                                 ║
║    (lldb) bt                                                                 ║
║    (lldb) frame variable                                                     ║
║    (lldb) thread list                                                        ║
║                                                                              ║
║ 5. RESTORE MEMSET after verification                                         ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")

print("=" * 80)
print("END OF VERIFICATION FINDINGS")
print("=" * 80)
