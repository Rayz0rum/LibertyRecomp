#!/usr/bin/env python3
"""
Deep analysis of the crash in sub_822EF570
Focus on the loop count source
"""

print("=" * 70)
print("LOOP COUNT ANALYSIS")
print("=" * 70)

print("""
In sub_822EF570, the loop count comes from:

1. r27 = 0x82CCD920 (static address from lis/addi)

2. r11 = *(r27 + 32)  = *(0x82CCD940)
   This is a pointer to some configuration/manager object

3. r11 = *(r11 + 4)
   This dereferences the first pointer to get another pointer

4. r10 = *(r11 + 192)
   This reads the "count" field

5. r29 = (r10 >> 3) & 0x1FFFFFFF
   rlwinm r29,r10,29,3,31 = rotate right 3 bits, mask low 29 bits
   This extracts bits 3-31 of r10, effectively dividing by 8

6. If r29 != 0:
   r30 = *(r11 + 196)  -- data array pointer
   Loop r29 times calling sub_827827C8
""")

# The loop ran 1001+ times
loop_count = 1001
# This means r29 >= 1001
# r29 = (r10 >> 3) & 0x1FFFFFFF
# So r10 >= 1001 * 8 = 8008

print(f"\nIf loop ran {loop_count}+ times:")
print(f"  r29 >= {loop_count}")
print(f"  r10 = r29 * 8 >= {loop_count * 8}")
print(f"  r10 = 0x{loop_count * 8:X}")

print("""
The crash happens AFTER the loop completes, when processing the allocated data.

Key insight: The loop itself completed (1001 allocations), but then the
subsequent code crashes because it reads from uninitialized memory.

Let me trace what happens after loc_822EF630:
""")

print("=" * 70)
print("CODE AFTER THE LOOP")
print("=" * 70)
print("""
loc_822EF630:
  lhz r10, 44(r31)      ; Load halfword from r31+44 (counter)
  mr r11, r26           ; r26 was set to 0 earlier
  cmplwi r10, 0         ; if counter == 0
  beq loc_822EF670      ; skip to default handling

  lwz r10, 40(r31)      ; Load pointer from r31+40 (array pointer)

loc_822EF644:
  lwz r9, 0(r10)        ; Load first word from array element
  cmpwi r9, 0           ; Check if entry is 0 (empty)
  beq loc_822EF668      ; if empty, check if index == -1
  
  lhz r9, 44(r31)       ; Reload counter
  addi r11, r11, 1      ; Increment index
  addi r10, r10, 8      ; Move to next array element
  cmpw r11, r9          ; Compare index with counter
  blt loc_822EF644      ; Loop if index < counter
  
  b loc_822EF670        ; Done searching

loc_822EF668:
  cmpwi r11, -1         ; Check if r11 == -1 (which would be 0xFFFFFFFF)
  bne loc_822EF688      ; If not -1, continue to loc_822EF688

The crash is at the instruction that loads r9 from the array!
If the array pointer (r31+40) is garbage, or points to garbage data,
the load will get 0xFFFFFFFF which then causes issues.
""")

print("=" * 70)
print("ROOT CAUSE IDENTIFIED")
print("=" * 70)
print("""
The structure at r31 (which was passed as first parameter) contains:
  [+40] = array pointer
  [+44] = array count

The loop at loc_822EF604 WRITES to r31+40 via sub_827827C8!

Look at the loop:
  addi r28, r31, 40     ; r28 = &(r31+40)
  ...
  mr r3, r28            ; Pass r28 to sub_827827C8
  bl sub_827827C8       ; Returns pointer in r3
  stw r11, 0(r3)        ; Store r11 to returned pointer
  stw r11, 4(r3)        ; Store r11 to returned pointer+4

sub_827827C8 modifies the buffer structure at r31+40!
After 1001 calls, the buffer has been resized multiple times.

BUT - the issue is in the DATA being stored:
  lwz r11, 0(r30)       ; Load from r30 (which came from *(r11+196))
  stw r11, 0(r3)        ; Store to new buffer slot
  lwz r11, 4(r30)       ; Load next word from r30
  addi r30, r30, 8      ; Advance r30
  stw r11, 4(r3)        ; Store to buffer

If the source data at r30 is garbage (e.g., 0xFFFFFFFF), it gets copied
to the buffer. Later when the code reads from this buffer, it crashes.

THE REAL ROOT CAUSE:
  The data at *(*(*(0x82CCD940)+4)+196) contains garbage!
  
This is the "configuration" or "template" data that should have been
initialized but wasn't.
""")

# Let me calculate the exact address
r27 = 0x82CCD920
config_ptr_addr = r27 + 32
print(f"\nAddress chain:")
print(f"  *(0x{config_ptr_addr:08X}) -> ptr1")
print(f"  *(ptr1 + 4) -> ptr2 (config struct)")
print(f"  *(ptr2 + 192) -> count (should be reasonable)")
print(f"  *(ptr2 + 196) -> data array (source of garbage)")

print("\n" + "=" * 70)
print("WHY IS THE DATA GARBAGE?")
print("=" * 70)
print("""
Hypothesis 1: Race condition
  - The configuration is loaded asynchronously
  - The loading thread hasn't finished yet
  - Main thread reads uninitialized data

Hypothesis 2: Missing initialization
  - Some initialization function was skipped/stubbed
  - The data array was never populated

Hypothesis 3: Memory corruption
  - Something else overwrote the configuration data
  - The 1001 allocations may have caused heap corruption

Looking at the log:
  [sub_8218BE28] [ALLOC] sub_8218BE28 #4000 46464 bytes -> 0xD75A00B0

4000 allocations! The heap may be stressed or fragmented.
""")

print("\n" + "=" * 70)
print("LIKELY FIX APPROACH")  
print("=" * 70)
print("""
1. Hook sub_822EF570 to validate the configuration pointer chain
2. If any pointer is NULL or garbage, return early instead of crashing
3. Or find what should initialize the config at 0x82CCD940 and fix that

The address 0x82CCD920 is in the code/rodata region (0x82xxxxxx).
Let me check what's at 0x82CCD920...
""")

# This is calculated from lis r11,-32050; addi r27,r11,-9952
# -32050 as 16-bit is 0x8302, shifted left 16 = 0x83020000
# Wait, that's wrong. Let me recalculate.

val = -32050
# lis loads the value << 16 as a signed 32-bit
high = val & 0xFFFF  # 0x82CE
lis_result = high << 16  # 0x82CE0000

# But Python treats this as positive. We need sign extension.
if lis_result >= 0x80000000:
    lis_result -= 0x100000000

addi_val = -9952  # 0xD920 as 16-bit, but we use signed
result = lis_result + addi_val

print(f"\nRecalculation:")
print(f"  -32050 & 0xFFFF = 0x{val & 0xFFFF:04X}")
print(f"  lis shifts: 0x{(val & 0xFFFF) << 16:08X}")
print(f"  addi -9952 = 0x{-9952 & 0xFFFF:04X}")
print(f"  Final r27 = 0x{result & 0xFFFFFFFF:08X}")
