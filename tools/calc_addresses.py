#!/usr/bin/env python3
"""
Calculate the global pointer address used by sub_822EF850
"""
import ctypes

print("=" * 70)
print("Global Pointer Address Calculation")
print("=" * 70)

# lis r31, -32050
# This loads (-32050 & 0xFFFF) << 16 into r31
val = -32050
high16 = val & 0xFFFF  # 0x82CE (32462 as unsigned)
lis_result = high16 << 16  # 0x82CE0000

print(f"lis r31, -32050:")
print(f"  -32050 & 0xFFFF = 0x{high16:04X}")
print(f"  0x{high16:04X} << 16 = 0x{lis_result:08X}")

# lwz r3, -9924(r31)
# This loads from r31 + (-9924)
offset = -9924
ptr_addr = (lis_result + offset) & 0xFFFFFFFF
print(f"\nlwz r3, -9924(r31):")
print(f"  r31 = 0x{lis_result:08X}")
print(f"  offset = {offset} = 0x{offset & 0xFFFF:04X}")
print(f"  address = 0x{lis_result:08X} + ({offset}) = 0x{ptr_addr:08X}")

print(f"\nSo the global pointer is at: 0x{ptr_addr:08X}")
print(f"This is dword_82CDD93C in the game's data section")

# Now trace the chain inside sub_822EF570
print("\n" + "=" * 70)
print("Inside sub_822EF570, r27 is set to:")
print("=" * 70)

# lis r11,-32050; addi r27,r11,-9952
offset2 = -9952
r27_addr = (lis_result + offset2) & 0xFFFFFFFF
print(f"  lis r11, -32050 = 0x{lis_result:08X}")
print(f"  addi r27, r11, -9952 = 0x{lis_result:08X} + ({offset2}) = 0x{r27_addr:08X}")

# The crash comes from *(*(r27+32)+4)+192 and +196
print(f"\nPointer chain:")
print(f"  r27 = 0x{r27_addr:08X}")
print(f"  *(r27 + 32) = *(0x{r27_addr + 32:08X}) -> ptr1 (profile object)")
print(f"  *(ptr1 + 4) -> ptr2 (settings buffer)")
print(f"  *(ptr2 + 192) -> loop count (should be 0)")
print(f"  *(ptr2 + 196) -> data array pointer")

# The dword_82CDD93C is at -9924
# The dword at r27+32 is at 0x82CDD920 + 32 = 0x82CDD940
config_ptr_addr = r27_addr + 32
print(f"\nKey addresses:")
print(f"  Global object pointer: 0x{ptr_addr:08X} (dword_82CDD93C)")
print(f"  Config pointer location: 0x{config_ptr_addr:08X}")

# Wait, these addresses are close but different!
print(f"\nWait - let me verify the addresses:")
print(f"  dword_82CDD93C = 0x{ptr_addr:08X}  (object pointer passed to sub_822EF850)")
print(f"  dword_82CDD940 = 0x{config_ptr_addr:08X} (config pointer read in sub_822EF570)")
print(f"  Difference: {config_ptr_addr - ptr_addr} bytes")

# They're only 4 bytes apart - this is the same structure!
# [0x82CDD93C] = object pointer
# [0x82CDD940] = something else

print("""
These are adjacent globals! The structure is:
  0x82CDD920: base address (r27)
  0x82CDD93C: object pointer (r27 + 28)
  0x82CDD940: config pointer (r27 + 32)
  
But wait, -9924 from 0x82CE0000:
""")

# Let me recalculate more carefully
val = 0x82CE0000
print(f"r31 = 0x{val:08X}")
print(f"r31 - 9924 = 0x{val - 9924:08X}")
print(f"r31 - 9952 = 0x{val - 9952:08X}")

# These look wrong. Let me check the signed arithmetic
print("\nActually, in PPC:")
print("lis r31, -32050 loads the upper 16 bits")

# -32050 in 16-bit is 0x82CE (two's complement)
print(f"-32050 as 16-bit: 0x{(-32050) & 0xFFFF:04X}")

# So r31 = 0x82CE0000 (with sign extension it's 0xFFFFFFFF82CE0000 in 64-bit)
# But as 32-bit: 0x82CE0000

r31 = 0x82CE0000
print(f"r31 = 0x{r31:08X}")
print(f"r31 - 9924 = 0x{(r31 - 9924) & 0xFFFFFFFF:08X}")
print(f"r31 - 9952 = 0x{(r31 - 9952) & 0xFFFFFFFF:08X}")

# So:
# dword_82CDD93C = *(0x82CE0000 - 9924) = *(0x82CDD93C)
# r27 = 0x82CE0000 - 9952 = 0x82CDD920

print(f"\nFinal addresses:")
print(f"  Object pointer at: 0x82CDD93C")
print(f"  r27 base at: 0x82CDD920")
print(f"  Config at r27+32: 0x82CDD940")
