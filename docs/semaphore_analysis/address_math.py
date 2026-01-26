#!/usr/bin/env python3
"""Address math for sub_82192C28 semaphore analysis"""

print("=" * 60)
print("Address Math for sub_82192C28 Blocking Analysis")
print("=" * 60)

# byte_82AA3DD8 structure analysis
base_addr = 0x82AA3DD8
print(f"\nStructure: byte_82AA3DD8 at 0x{base_addr:08X}")
print("-" * 40)

# Key offsets from PPC code
offsets = {
    "semaphore_4012": 4012,  # sub_827DAC78(0) - semaphore created with count=0
    "semaphore_4016": 4016,  # sub_827DAC78(0)
    "semaphore_4020": 4020,  # sub_827DAC78(0)
    "semaphore_4024": 4024,  # sub_827DAC78(1) - THE BLOCKING SEMAPHORE (wait)
    "counter_4032": 4032,    # Counter
    "counter_4036": 4036,    # Counter
    "flag_4040": 4040,       # Flag checked before semaphore wait!
    "flag_4041": 4041,       # Flag
    "flag_4042": 4042,       # Thread running flag
    "flag_4044": 4044,       # Flag
    "struct_4048": 4048,     # 16-byte structure
    "struct_4064": 4064,     # 16-byte structure
    "marker_4080": 4080,     # Magic marker 0xABCDABCD
    "marker_4084": 4084,     # Pointer to 3996
}

for name, offset in offsets.items():
    addr = base_addr + offset
    print(f"  {name}: 0x{base_addr:08X} + {offset} = 0x{addr:08X}")

print()
print("=" * 60)
print("Key Blocking Logic (from sub_82192C28)")
print("=" * 60)
print("""
1. Load flag at r30+4040 (byte_82AA3DD8+4040 = 0x82AA4D90):
   lbz r11,4040(r30)
   cmplwi cr6,r11,0
   bne cr6,loc_82192C50  ; Skip wait if flag != 0

2. If flag == 0, wait on semaphore at r30+4024 (0x82AA4D80):
   lwz r3,4024(r30)
   bl sub_827DACD8  ; Semaphore wait (infinite)

3. Semaphore created at r30+4024 with initial count = 1:
   sub_827DAC78(1)  ; KeInitializeSemaphore with count=1
   
4. After processing, checks flag again at r30+4040
   If set, waits on semaphore again
""")

# Calculate specific addresses
main_struct = 0x82AA3DD8
sem_4024_addr = main_struct + 4024
flag_4040_addr = main_struct + 4040

print()
print("=" * 60)
print("Critical Addresses to Inspect")
print("=" * 60)
print(f"  Main structure:     0x{main_struct:08X}")
print(f"  Blocking semaphore: 0x{sem_4024_addr:08X} (r30+4024)")
print(f"  Wait skip flag:     0x{flag_4040_addr:08X} (r30+4040)")
print()

# Guest address translation (for LLDB)
guest_base = 0x100000000  # Typical guest base offset
print("LLDB Commands to inspect at runtime:")
print(f"  memory read 0x{guest_base + sem_4024_addr:X}  # Semaphore handle")
print(f"  memory read 0x{guest_base + flag_4040_addr:X}  # Wait skip flag")
print(f"  memory read 0x{guest_base + main_struct:X} -c 128  # First 128 bytes of structure")

print()
print("=" * 60)
print("Call Chain Analysis")
print("=" * 60)
print("""
_xstart
  → sub_8218BEA8 (Main entry?)
    → sub_827D89B8 (Thread entry?)
      → sub_8218BEB0
        → sub_821200D0
          → sub_82121E80 (Main menu/game loop?)
            → sub_821221A8 
              → sub_82192C28(byte_82AA3DD8)
                → sub_827DACD8(semaphore at +4024) [BLOCKS HERE]
                  → sub_829A2380
                    → sub_829A9738
                      → KeWaitForSingleObject (infinite)
""")

print()
print("=" * 60)  
print("Semaphore Signal Path (What should wake it up)")
print("=" * 60)
print("""
Signal function: sub_827DAD60 (KeReleaseSemaphore)
  → sub_829A2290
    → __imp__NtReleaseSemaphore
    
Who calls sub_827DAD60 (to signal the semaphore at +4024)?
Need to find callers that pass semaphore handle from r30+4024
""")

# dword_82AA3DAC analysis - linked list of structures
print()
print("=" * 60)
print("Global Pointers")
print("=" * 60)
dword_82AA3DA8 = main_struct + 3996
dword_82AA3DAC = main_struct + 4084
print(f"  dword_82AA3DA8: points to main_struct + 3996 = 0x{dword_82AA3DA8:08X}")
print(f"  dword_82AA3DAC: points to main_struct + 4084 = 0x{dword_82AA3DAC:08X}")
print(f"  These form a linked list: [3996] <-> [main] <-> [4084] <-> [end]")
