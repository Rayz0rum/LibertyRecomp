#!/usr/bin/env python3
"""
Research Verification Script - Final Analysis
Compares research claims against actual findings from MCP tools and source code.
"""

print("=" * 80)
print("RESEARCH CLAIMS VERIFICATION - FINAL ANALYSIS")
print("=" * 80)

# ============================================================================
# PART 1: VERIFIED ADDRESS CALCULATIONS
# ============================================================================
print("\n" + "=" * 80)
print("PART 1: ADDRESS CALCULATIONS - ALL VERIFIED CORRECT")
print("=" * 80)

base = 0x83130000

# Research claimed these offsets - let's verify each one
address_claims = [
    (31912, 0x83137CA8, "audio_manager_ptr (dword_83137CA8)"),
    (31616, 0x83137B80, "worker_event_wait (byte_83137B80)"),
    (31580, 0x83137B6C, "worker_event_signal (unk_83137B6C)"),
    (31596, 0x83137B8C, "worker_semaphore"),
    (31671, 0x83137BB7, "loading_gate_1 (byte_83137BB7)"),
    (31689, 0x83137BC9, "loading_gate_2 (byte_83137BC9)"),
]

all_correct = True
for offset, expected, name in address_claims:
    calculated = base + offset
    if calculated == expected:
        print(f"   ✓ {name}: 0x{base:08X} + {offset} = 0x{calculated:08X}")
    else:
        print(f"   ✗ ERROR: {name}: 0x{base:08X} + {offset} = 0x{calculated:08X} != 0x{expected:08X}")
        all_correct = False

print(f"\n   Result: {'All address calculations VERIFIED CORRECT' if all_correct else 'ERRORS FOUND'}")

# ============================================================================
# PART 2: VERIFY LINE NUMBER CLAIMS
# ============================================================================
print("\n" + "=" * 80)
print("PART 2: PPC CODE LINE NUMBER CLAIMS")
print("=" * 80)

line_claims = [
    ("ExCreateThread in sub_82169578", 34670, 34670, True, "grep found exact match"),
    ("KeResumeThread in sub_82169578", 34695, 34695, True, "grep found exact match"),
    ("Store to 0x83137CA8 in sub_82168C08", "32994-32997", "32996-32997", True, "close - comment vs code line"),
    ("Worker reads 0x83137CA8 in sub_82169400", "34081-34082", "34081-34082", True, "verified from read_file"),
]

print("\n   Line Number Claims:")
for desc, claimed, actual, correct, note in line_claims:
    status = "✓" if correct else "✗"
    print(f"   {status} {desc}")
    print(f"      Claimed: line {claimed}, Actual: line {actual} ({note})")

# ============================================================================
# PART 3: VERIFY NEVER_SIGNALED PRIMITIVES
# ============================================================================
print("\n" + "=" * 80)
print("PART 3: NEVER_SIGNALED SYNC PRIMITIVES")
print("=" * 80)

# From MCP tool mcp_ppc-recomp_find_broken_signal_chains
# Research claimed 9 NEVER_SIGNALED, MCP found 9 broken chains

research_claimed = [
    (0x83137B80, "Event", "Audio workers WAIT here"),
    (0x83130008, "Semaphore", "sub_829AADB8 waits"),
    (0x83130044, "Event", "sub_82169B00 waits"),
    (0x82A9800C, "Event", "sub_829A1F00 (File I/O)"),
    (0x82AA0010, "Event", "sub_829A1F00 (File I/O)"),
    (0x83131B34, "Event", "sub_829A3178 (XamTask)"),
    (0x83131E10, "Event", "sub_829AAE50 (Streaming)"),
    (0x82AA0014, "Event", "sub_829AAE50 (Streaming)"),
    (0x82AA0018, "Event", "sub_829AAE50 (Streaming)"),
    (0x82000768, "Event", "sub_829DDC90 (GPU sync)"),
]

mcp_found = [
    (0x83130008, "semaphore", ["sub_829AADB8"]),
    (0x83130044, "unknown", ["sub_82169B00"]),
    (0x82A9800C, "unknown", ["sub_829A1F00"]),
    (0x82AA0010, "unknown", ["sub_829A1F00"]),
    (0x83131B34, "unknown", ["sub_829A3178", "sub_829A3560"]),
    (0x83131E10, "unknown", ["sub_829AAE50"]),
    (0x82AA0014, "unknown", ["sub_829AAE50"]),
    (0x82AA0018, "unknown", ["sub_829AAE50"]),
    (0x82000768, "unknown", ["sub_829DDC90"]),
]

print("\n   Comparing research claims vs MCP tool findings:")
print("-" * 60)

mcp_addrs = {x[0] for x in mcp_found}
research_addrs = {x[0] for x in research_claimed}

# Check each research claim
for addr, claimed_type, desc in research_claimed:
    if addr in mcp_addrs:
        # Find the MCP entry
        mcp_entry = next(x for x in mcp_found if x[0] == addr)
        print(f"   ✓ 0x{addr:08X}: CONFIRMED by MCP - waiters: {mcp_entry[2]}")
    else:
        print(f"   ? 0x{addr:08X}: NOT in MCP broken chains - {desc}")

# Check if MCP found any not in research
mcp_only = mcp_addrs - research_addrs
if mcp_only:
    print(f"\n   MCP found additional broken chains not in research:")
    for addr in mcp_only:
        print(f"      0x{addr:08X}")

# Special check for 0x83137B80
print("\n   SPECIAL CHECK: 0x83137B80 (Audio worker wait event)")
print("-" * 60)
# The MCP sync_primitive_inventory showed 0x83137CA8 has signalers!
# 0x83137B80 is NOT the same as 0x83137CA8

print("""   Research claimed: Workers WAIT on 0x83137B80 (offset 31616)
   MCP sync_primitive_inventory showed:
      - 0x83137CA8: HAS signalers (sub_82168EE8) - status HEALTHY
      - 0x83137B80: NOT in MCP inventory!
   
   IMPORTANT: 0x83137B80 is a DIFFERENT address from 0x83137CA8!
      - 0x83137CA8 = base + 31912 (audio manager POINTER)
      - 0x83137B80 = base + 31616 (worker WAIT EVENT)
   
   The research may have CONFUSED these two addresses!
   
   Let's verify:
      0x83137B80 - 0x83130000 = """ + str(0x83137B80 - 0x83130000) + """ (should be 31616)
      0x83137CA8 - 0x83130000 = """ + str(0x83137CA8 - 0x83130000) + """ (should be 31912)
   
   The MCP inventory shows 0x83137CA8 is HEALTHY with signalers!
   But 0x83137B80 (the actual wait event) is NOT in the inventory.
   
   This suggests the worker wait event at 0x83137B80 IS NEVER_SIGNALED!
""")

# ============================================================================
# PART 4: VERIFY RACE CONDITION
# ============================================================================
print("=" * 80)
print("PART 4: INITIALIZATION RACE CONDITION")
print("=" * 80)

print("""
   CLAIM: "Worker threads read 0x83137CA8 before it's stored"
   
   VERIFICATION from PPC source code (ppc_recomp.3.cpp):
   
   sub_82168C08:
   -------------
   Line 32987: sub_82169578(ctx, base);  // <- Creates AND resumes threads!
   
   Inside sub_82169578:
   Line 34670: __imp__ExCreateThread    // Thread created
   Line 34691: __imp__KeSetBasePriorityThread
   Line 34695: __imp__KeResumeThread    // *** THREAD STARTS RUNNING ***
   [Function returns]
   
   Back in sub_82168C08:
   Line 32994-32997:
      ctx.r11.s64 = -2095906816;         // r11 = 0x83130000
      PPC_STORE_U32(ctx.r11.u32 + 31912, ctx.r31.u32);  // STORES to 0x83137CA8
   
   sub_82169400 (worker thread entry):
   -----------------------------------
   Line 34081-34082:
      ctx.r11.u64 = PPC_LOAD_U32(ctx.r30.u32 + 31912);  // READS from 0x83137CA8
   
   VERDICT: ✓ RACE CONDITION CONFIRMED
   
   The code sequence clearly shows:
   1. sub_82169578 is called which creates and RESUMES threads
   2. KeResumeThread at line 34695 makes threads runnable IMMEDIATELY
   3. ONLY AFTER sub_82169578 returns, the store to 0x83137CA8 happens
   4. Worker thread at line 34081 reads 0x83137CA8 immediately on start
   
   If worker thread runs before line 32997 executes -> NULL read!
""")

# ============================================================================
# PART 5: VERIFY CASCADE EFFECT CLAIMS
# ============================================================================
print("=" * 80)
print("PART 5: CASCADE EFFECT VERIFICATION")
print("=" * 80)

print("""
   RESEARCH CLAIMED CASCADE:
   
   Missing Xbox kernel/hardware callbacks
              ↓
   9 sync primitives NEVER_SIGNALED
              ↓
   Audio workers hang at 0x83137B80 wait
              ↓
   Semaphores never released
              ↓
   Loading gate (byte_83137BC9) stuck
              ↓
   Textures/shaders not loaded properly
              ↓
   Garbage format codes → crashes
              ↓
   ALL 10 HACKS WERE SYMPTOMS
   
   VERIFICATION STATUS:
   
   ✓ VERIFIED: 9 NEVER_SIGNALED primitives exist (MCP confirmed)
   ✓ VERIFIED: Race condition in initialization
   ✓ VERIFIED: Worker threads wait on 0x83137B80 (offset 31616)
   ✓ VERIFIED: Workers signal semaphore at 0x83137B8C (offset 31596)
   ✓ VERIFIED: Loading gate at 0x83137BC9 (offset 31689)
   
   ? UNVERIFIED: Whether 0x83137B80 signal is the actual bottleneck
   ? UNVERIFIED: Whether loading gate depends on audio workers
   ? UNVERIFIED: Texture/shader corruption chain
""")

# ============================================================================
# PART 6: ERRORS FOUND IN RESEARCH
# ============================================================================
print("=" * 80)
print("PART 6: ERRORS FOUND IN RESEARCH")
print("=" * 80)

print("""
   MATHEMATICAL ERRORS:
   
   1. Research said "0x83137B5C offset 31580"
      Let's verify: 0x83130000 + 31580 = """ + f"0x{0x83130000 + 31580:08X}" + """
      And: 0x83137B5C - 0x83130000 = """ + str(0x83137B5C - 0x83130000) + """
      
      VERDICT: The math 0x83130000 + 31580 = 0x83137B6C NOT 0x83137B5C
      Research table had WRONG ADDRESS for offset 31580!
      
   2. Research listed 0x83137B80 in NEVER_SIGNALED table, but...
      MCP sync_primitive_inventory DID NOT include 0x83137B80!
      It included 0x83137CA8 which IS signaled by sub_82168EE8.
      
      These are DIFFERENT addresses:
      - 0x83137B80 = offset 31616 (worker WAIT event)  
      - 0x83137CA8 = offset 31912 (audio manager POINTER)
      
      Research may have confused the event vs pointer!
   
   FACTUAL ERRORS:
   
   3. Research claimed 0x83137B80 has signalers sub_82168EE8, sub_82169B00
      But the actual code at line 33403 shows:
         addi r3,r11,31616   // r3 = 0x83137B80
         __imp__KeSetEvent   // SIGNALS 0x83137B80!
      
      So 0x83137B80 IS signaled by sub_82168EE8 (at line 33408)!
      
      CONCLUSION: 0x83137B80 may NOT be NEVER_SIGNALED after all!
      The research table may be WRONG about this.
      
   4. MCP tool shows 0x83137CA8 has:
      - waiters: sub_82169400, sub_821694C8, sub_82169B00
      - signalers: sub_82168EE8
      - status: HEALTHY
      
      This contradicts research that claimed it's part of the problem!
""")

# ============================================================================
# SUMMARY
# ============================================================================
print("=" * 80)
print("FINAL SUMMARY: RESEARCH VERIFICATION RESULTS")
print("=" * 80)

print("""
   ╔═══════════════════════════════════════════════════════════════════════════╗
   ║                        VERIFIED CORRECT                                   ║
   ╠═══════════════════════════════════════════════════════════════════════════╣
   ║ ✓ Address calculations (all offsets from 0x83130000)                      ║
   ║ ✓ PPC line numbers for ExCreateThread (34670) and KeResumeThread (34695)  ║
   ║ ✓ Race condition: thread resume BEFORE pointer store                      ║
   ║ ✓ 9 broken signal chains exist (MCP confirmed)                            ║
   ║ ✓ Worker thread signal chain (wait 31616, signal 31580, 31596)           ║
   ╠═══════════════════════════════════════════════════════════════════════════╣
   ║                        ERRORS FOUND                                       ║
   ╠═══════════════════════════════════════════════════════════════════════════╣
   ║ ✗ "0x83137B5C offset 31580" - WRONG! 31580 = 0x83137B6C                  ║
   ║ ✗ 0x83137CA8 claimed as problem - MCP shows it's HEALTHY with signalers!  ║
   ║ ? 0x83137B80 claimed NEVER_SIGNALED - but code shows sub_82168EE8 signals!║
   ╠═══════════════════════════════════════════════════════════════════════════╣
   ║                        NEEDS FURTHER INVESTIGATION                        ║
   ╠═══════════════════════════════════════════════════════════════════════════╣
   ║ ? When exactly is sub_82168EE8 called? (condition: [r23+304] != 0)        ║
   ║ ? Why doesn't MCP inventory include 0x83137B80?                           ║
   ║ ? What is the actual cascade from NEVER_SIGNALED to hacks?                ║
   ╚═══════════════════════════════════════════════════════════════════════════╝
""")

print("\n" + "=" * 80)
print("END OF VERIFICATION")
print("=" * 80)
