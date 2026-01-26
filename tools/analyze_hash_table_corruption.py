#!/usr/bin/env python3
"""
Hash Table Corruption Analysis for sub_82802540
Analyzes how uninitialized memory leads to infinite loops in hash table traversal.
"""

# =============================================================================
# HASH TABLE STRUCTURE ANALYSIS
# =============================================================================

print("=" * 70)
print("HASH TABLE STRUCTURE ANALYSIS (sub_82802540)")
print("=" * 70)

print("""
Based on IDA decompilation at line 2587543-2587582:

Hash Table Structure (dword_83127A24):
  +0x00: Bucket array pointer (v6 = *a1)
  +0x04: Bucket count as uint16 (v5 = *((uint16*)a1 + 2))

Hash Node Structure:
  +0x00: String key pointer (v8 = *(ptr*)v7)
  +0x04: Value pointer (returned as v7 + 4)
  +0x08: Next node pointer (v7 = *((DWORD*)v7 + 2))

Lookup Algorithm:
  1. hash = sub_827E9598(key)
  2. bucket_idx = hash % bucket_count
  3. node = buckets[bucket_idx]
  4. while (node != NULL):
       if (strcmp(node->key, key) == 0):
         return &node->value
       node = node->next
  5. return NULL
""")

# =============================================================================
# CORRUPTION SCENARIO ANALYSIS
# =============================================================================

print("\n" + "=" * 70)
print("CORRUPTION SCENARIO")
print("=" * 70)

CORRUPTION_PATTERN = 0xEA7060FF
PHYS_HEAP_START = 0xA0000000

print(f"""
When GPU writes 0x{CORRUPTION_PATTERN:08X} to hash table memory:

Scenario A: Bucket pointer corrupted
  - buckets[idx] = 0x{CORRUPTION_PATTERN:08X}
  - This is a valid physical heap address ({(CORRUPTION_PATTERN - PHYS_HEAP_START) / (1024**2):.1f} MB offset)
  - Node pointer v7 becomes 0x{CORRUPTION_PATTERN:08X}
  - If memory at that address also contains 0x{CORRUPTION_PATTERN:08X}...

Scenario B: Node->next pointer corrupted  
  - Some node's next pointer becomes 0x{CORRUPTION_PATTERN:08X}
  - Traversal continues to address 0x{CORRUPTION_PATTERN:08X}
  - If that memory contains the same pattern...

INFINITE LOOP MECHANISM:
""")

# Calculate what happens when following corrupted pointers
node_addr = CORRUPTION_PATTERN
iterations = 0
max_iter = 5

print(f"  Iteration 0: v7 = 0x{node_addr:08X}")
print(f"  Reading node->key from 0x{node_addr:08X}...")
print(f"  key_ptr = 0x{CORRUPTION_PATTERN:08X} (garbage)")
print(f"  strcmp fails (key doesn't match)")
print(f"  Reading node->next from 0x{node_addr + 8:08X}...")

# If the memory is filled with the same pattern
next_ptr = CORRUPTION_PATTERN
print(f"  next_ptr = 0x{next_ptr:08X}")
print()

for i in range(1, max_iter + 1):
    print(f"  Iteration {i}: v7 = 0x{next_ptr:08X}")
    if next_ptr == CORRUPTION_PATTERN:
        print(f"    -> Same address! Pattern repeats infinitely")
        break
    next_ptr = CORRUPTION_PATTERN  # Assuming memory filled with pattern

print()
print("  Result: INFINITE LOOP - main thread stuck in while(1)")

# =============================================================================
# MEMORY LAYOUT AT CORRUPTION TIME
# =============================================================================

print("\n" + "=" * 70)
print("MEMORY LAYOUT ANALYSIS")
print("=" * 70)

# Calculate where hash table likely lives
# dword_83127A24 is in the .data section
hash_table_addr = 0x83127A24

print(f"""
Hash table global: 0x{hash_table_addr:08X}
  - This is in .data section (above 0x82000000 code)
  - Contains pointer to bucket array

Physical heap: 0xA0000000 - 0x100000000
  - Hash table buckets/nodes may be allocated here
  - GPU corruption writes to 0xBA000000 (416 MB into heap)
  - Corruption size: ~1.1 GB

Key Question: Are hash table nodes in physical heap?
  - If allocated with XAllocMem/AllocPhysical: YES
  - If allocated with normal heap (Alloc): NO

Based on the corruption pattern reaching hash table nodes,
the nodes must be somewhere the GPU write affected.
""")

# =============================================================================
# TIMING ANALYSIS
# =============================================================================

print("\n" + "=" * 70)
print("TIMING ANALYSIS")
print("=" * 70)

bump_used_mb = 406
corruption_dest_offset_mb = 416

print(f"""
Timeline of events:

1. Game starts, physical heap initialized at 0xA0000000
2. Textures, surfaces, buffers allocated via AllocPhysical
3. Bump allocator advances: ~{bump_used_mb} MB used
4. Uninitialized texture allocation contains garbage addresses
5. GPU resolve/copy operation reads garbage source/dest
6. GPU writes 1.1 GB starting at 0xBA000000 ({corruption_dest_offset_mb} MB offset)
7. Write overwrites:
   - More bump allocator memory
   - Possibly hash table nodes if they're in physical heap
   - Possibly pointers in normal heap if bounds exceeded
8. Next hash table lookup hits corrupted node->next
9. while(1) loop follows 0x{CORRUPTION_PATTERN:08X} pointer forever
10. Main thread stuck -> Beach ball / hang
""")

# =============================================================================
# VERIFICATION STEPS
# =============================================================================

print("\n" + "=" * 70)
print("LLDB VERIFICATION STEPS")
print("=" * 70)

print("""
1. CONFIRM UNINITIALIZED MEMORY:
   (lldb) b Heap::AllocPhysical
   (lldb) c
   # When breakpoint hits, step to return
   (lldb) finish
   # Examine returned memory
   (lldb) memory read $rax $rax+64
   # Look for non-zero bytes (should be garbage if hypothesis correct)

2. FIND HASH TABLE BUCKET ARRAY:
   (lldb) p/x *(uint32_t*)g_memory.Translate(0x83127A24)
   # This gives bucket array guest address
   
3. TRANSLATE AND EXAMINE BUCKETS:
   (lldb) p g_memory.Translate(<bucket_array_addr>)
   (lldb) memory read <host_addr> <host_addr>+64
   
4. SET WATCHPOINT ON CORRUPTION DEST:
   (lldb) p g_memory.Translate(0xBA000000)
   (lldb) watchpoint set expression -w write -- *(uint32_t*)<host_addr>
   # When triggered, examine backtrace for GPU operation

5. CATCH INFINITE LOOP:
   # While running, if beach ball appears:
   (lldb) process interrupt
   (lldb) bt
   # Should show stuck in sub_82802540 or similar hash function
   (lldb) register read
   # Check loop counter / node pointer

6. VERIFY PATTERN IN MEMORY:
   (lldb) memory find -e 0xEA7060FF $rsp-0x1000000 $rsp
   # Search for corruption pattern near current execution
""")

# =============================================================================
# EVIDENCE SUMMARY
# =============================================================================

print("\n" + "=" * 70)
print("EVIDENCE SUMMARY")
print("=" * 70)

print("""
CONFIRMED:
✓ Bump allocator returns uninitialized memory (heap.cpp:244)
✓ GuestTexture/GuestSurface allocations don't zero memory
✓ GuestDevice allocation DOES zero memory (memset at video.cpp:2573)
✓ Pattern 0xEA7060FF is valid physical heap address
✓ sub_82802540 has while(1) that follows node->next pointers
✓ If node->next = 0xEA7060FF and memory there also = 0xEA7060FF, infinite loop

HYPOTHESIS:
- Uninitialized GuestTexture has garbage in width/height or address fields
- GPU operation uses these garbage values
- Large memory write (1.1 GB) corrupts hash table node pointers
- Hash lookup enters infinite loop following corrupted pointers

TO VERIFY:
1. Set breakpoint at AllocPhysical, confirm non-zero return memory
2. Set watchpoint at 0xBA000000, confirm GPU write source
3. When hung, interrupt and check if stuck in hash table loop
""")
