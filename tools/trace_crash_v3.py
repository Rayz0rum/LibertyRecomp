#!/usr/bin/env python3
"""
Final trace: Find dword_83137CA8 address and understand crash flow.
"""

print("=== Address Calculation for dword_83137CA8 ===")
print()

# From PPC code:
# lis r11,-31981  -> loads -31981 << 16 into r11
# In Python: -31981 as signed 16-bit, then shifted left 16

lis_value = -31981
r11_after_lis = (lis_value << 16) & 0xFFFFFFFF  # 32-bit
print(f"lis r11,-31981:")
print(f"  -31981 << 16 = {lis_value << 16}")
print(f"  as 32-bit unsigned = 0x{r11_after_lis:08X}")

# lwz r30,31912(r11)
offset = 31912
global_addr = (r11_after_lis + offset) & 0xFFFFFFFF
print(f"lwz r30,31912(r11):")
print(f"  0x{r11_after_lis:08X} + {offset} = 0x{global_addr:08X}")
print()

print(f"=== dword_83137CA8 = 0x{global_addr:08X} ===")
print()

print("Call chain:")
print("  1. sub_82169B00 loads r30 = *(uint32_t*)0x83137CA8")
print("  2. sub_82169B00 calls sub_82169C58(r30, ...)")
print("  3. sub_82169C58 saves r3->r31, then calls sub_8216A288(r31, r31+80)")
print("  4. sub_8216A288 crashes when computing: a1 + (cpu_index + 36) * 4")
print()

print("=== Root cause hypothesis ===")
print()
print("The value at address 0x83137CA8 is either:")
print("  a) NULL (0x00000000) - would crash at low address")
print("  b) Garbage/uninitialized - would crash at high address like 0xFFFFFFFF")
print("  c) Not yet set by initialization code")
print()

# Let's calculate what values would cause crash at 0xFFFFFFFF
print("=== Reverse calculation ===")
print()
print("Crash address: 0xFFFFFFFF")
print("Formula: addr = a1 + (cpu_index + 36) * 4")
print()

for cpu in range(6):
    offset = (cpu + 36) * 4
    a1_needed = (0xFFFFFFFF - offset) & 0xFFFFFFFF
    print(f"  cpu_index={cpu}: offset=0x{offset:04X}, a1=0x{a1_needed:08X}")

print()
print("All these a1 values are near 0xFFFFFF6F-0xFFFFFF5B")
print("These are NOT valid heap addresses (typically 0xC9XXXXXX or 0xA0XXXXXX)")
print()

print("=== LLDB commands to inspect ===")
print()
print("# Check what's at dword_83137CA8:")
print("memory read --size 4 --format x 0x300000000+0x83137CA8")
print()
print("# Check PCR+268 (current_cpu):")
print("# Need r13 value from a guest thread context")
print()

print("=== Key insight from backtrace ===")
print()
print("Thread #29 crashed in sub_8216A288")
print("Called from sub_82169C58")
print("Called from sub_82169B00")  
print("Called from sub_8298E700")
print("Called from sub_827DAE40 (streaming worker)")
print()
print("The streaming worker is executing before the audio/streaming")
print("manager object at 0x83137CA8 has been properly initialized.")
print()
print("This is a RACE CONDITION or INITIALIZATION ORDER issue.")
