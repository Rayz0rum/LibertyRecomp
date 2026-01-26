#!/usr/bin/env python3
"""
Research Verification Script
Verifies all address calculations and claims from the previous research.
"""

print("=" * 80)
print("RESEARCH VERIFICATION: Address Calculations")
print("=" * 80)

# Base addresses from the research
BASE_AUDIO_MANAGER = 0x83130000  # Claimed base address for audio system

# Claimed offsets from the research
OFFSETS = {
    "audio_manager_ptr": 31912,   # dword_83137CA8
    "worker_event_wait": 31616,   # byte_83137B80 - event workers WAIT on
    "worker_event_signal": 31580, # unk_83137B6C - event workers SIGNAL
    "worker_semaphore": 31596,    # unk_83137B8C - semaphore workers SIGNAL
    "loading_gate_1": 31671,      # byte_83137BB7
    "loading_gate_2": 31689,      # byte_83137BC9
}

print("\n1. Verifying Audio Manager Address Calculations")
print("-" * 60)
for name, offset in OFFSETS.items():
    calculated_addr = BASE_AUDIO_MANAGER + offset
    print(f"   {name:25} offset={offset:5} -> 0x{calculated_addr:08X}")

# Now verify the claimed addresses match
CLAIMED_ADDRESSES = {
    "dword_83137CA8": 0x83137CA8,
    "byte_83137B80": 0x83137B80,
    "unk_83137B6C": 0x83137B6C,  # Actually should be 31580
    "unk_83137B8C": 0x83137B8C,
    "byte_83137BB7": 0x83137BB7,
    "byte_83137BC9": 0x83137BC9,
}

print("\n2. Verifying Claimed Addresses Match Calculations")
print("-" * 60)

errors_found = []

# Check audio_manager_ptr (31912)
calc = BASE_AUDIO_MANAGER + 31912
claimed = 0x83137CA8
if calc == claimed:
    print(f"   ✓ audio_manager_ptr: 0x83130000 + 31912 = 0x{calc:08X} == 0x{claimed:08X}")
else:
    err = f"   ✗ MISMATCH: 0x83130000 + 31912 = 0x{calc:08X} != 0x{claimed:08X}"
    print(err)
    errors_found.append(err)

# Check worker_event_wait (31616)
calc = BASE_AUDIO_MANAGER + 31616
claimed = 0x83137B80
if calc == claimed:
    print(f"   ✓ worker_event_wait: 0x83130000 + 31616 = 0x{calc:08X} == 0x{claimed:08X}")
else:
    err = f"   ✗ MISMATCH: 0x83130000 + 31616 = 0x{calc:08X} != 0x{claimed:08X}"
    print(err)
    errors_found.append(err)

# Check worker_event_signal (31580)
calc = BASE_AUDIO_MANAGER + 31580
claimed = 0x83137B6C
if calc == claimed:
    print(f"   ✓ worker_event_signal: 0x83130000 + 31580 = 0x{calc:08X} == 0x{claimed:08X}")
else:
    err = f"   ✗ MISMATCH: 0x83130000 + 31580 = 0x{calc:08X} != 0x{claimed:08X}"
    print(err)
    errors_found.append(err)
    # Calculate the correct offset
    correct_offset = claimed - BASE_AUDIO_MANAGER
    print(f"      CORRECT: 0x{claimed:08X} - 0x83130000 = {correct_offset} (offset)")

# Check worker_semaphore (31596)
calc = BASE_AUDIO_MANAGER + 31596
claimed = 0x83137B8C
if calc == claimed:
    print(f"   ✓ worker_semaphore: 0x83130000 + 31596 = 0x{calc:08X} == 0x{claimed:08X}")
else:
    err = f"   ✗ MISMATCH: 0x83130000 + 31596 = 0x{calc:08X} != 0x{claimed:08X}"
    print(err)
    errors_found.append(err)
    correct_offset = claimed - BASE_AUDIO_MANAGER
    print(f"      CORRECT: 0x{claimed:08X} - 0x83130000 = {correct_offset} (offset)")

# Check loading_gate_1 (31671)
calc = BASE_AUDIO_MANAGER + 31671
claimed = 0x83137BB7
if calc == claimed:
    print(f"   ✓ loading_gate_1: 0x83130000 + 31671 = 0x{calc:08X} == 0x{claimed:08X}")
else:
    err = f"   ✗ MISMATCH: 0x83130000 + 31671 = 0x{calc:08X} != 0x{claimed:08X}"
    print(err)
    errors_found.append(err)

# Check loading_gate_2 (31689)
calc = BASE_AUDIO_MANAGER + 31689
claimed = 0x83137BC9
if calc == claimed:
    print(f"   ✓ loading_gate_2: 0x83130000 + 31689 = 0x{calc:08X} == 0x{claimed:08X}")
else:
    err = f"   ✗ MISMATCH: 0x83130000 + 31689 = 0x{calc:08X} != 0x{claimed:08X}"
    print(err)
    errors_found.append(err)

print("\n3. Verifying PPC Address Encoding")
print("-" * 60)
# The research claims: "lis r11,-31981 = 0x83130000"
# lis instruction loads a 16-bit signed immediate into upper 16 bits
# -31981 as signed 16-bit = 0x831F in twos complement? Let's verify.

lis_immediate = -31981
# Convert to unsigned 16-bit
if lis_immediate < 0:
    lis_unsigned = lis_immediate & 0xFFFF
else:
    lis_unsigned = lis_immediate

# lis shifts by 16 bits
calculated_base = (lis_unsigned << 16) & 0xFFFFFFFF
print(f"   lis r11, {lis_immediate}")
print(f"   Immediate as unsigned 16-bit: 0x{lis_unsigned:04X}")
print(f"   After shift left 16: 0x{calculated_base:08X}")
print(f"   Expected: 0x83130000")
if calculated_base == 0x83130000:
    print(f"   ✓ CORRECT: lis -31981 produces 0x83130000")
else:
    print(f"   ✗ MISMATCH: lis -31981 produces 0x{calculated_base:08X}")
    # What value should lis use?
    correct_lis = 0x83130000 >> 16
    correct_signed = correct_lis if correct_lis < 0x8000 else correct_lis - 0x10000
    print(f"      CORRECT lis value needed: {correct_signed} (0x{correct_lis:04X})")

print("\n4. Cross-checking NEVER_SIGNALED Primitives")
print("-" * 60)

NEVER_SIGNALED = [
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

for addr, ptype, desc in NEVER_SIGNALED:
    region = "UNKNOWN"
    if 0x82000000 <= addr < 0x82FFFFFF:
        region = "PPC Image/Code"
    elif 0x83130000 <= addr < 0x83140000:
        offset = addr - 0x83130000
        region = f"Audio Manager (offset {offset})"
    elif 0x82A90000 <= addr < 0x82AB0000:
        region = "File/Stream Data"
    print(f"   0x{addr:08X} - {ptype:10} - {region:30} - {desc}")

print("\n5. Verifying PPC Line Number Claims")
print("-" * 60)
print("   Research claims:")
print("   - Line 32985-32987: sub_82169578() called at 0x82168CB4")
print("   - Line 34670: ExCreateThread() at 0x8216984C")
print("   - Line 34695: KeResumeThread() at 0x82169878")
print("   - Line 32994-32997: stw r31,31912(r11) at 0x82168CC4")
print("   (These need manual verification against ppc_recomp.3.cpp)")

# Calculate address offsets to verify line claims
print("\n   Address Verification:")
base_func = 0x82168C08  # sub_82168C08 start address
addr_call_sub = 0x82168CB4
addr_create_thread = 0x8216984C
addr_resume = 0x82169878
addr_store = 0x82168CC8  # Note: research says 0x82168CC4

print(f"   sub_82168C08 base:       0x{base_func:08X}")
print(f"   Call to sub_82169578:    0x{addr_call_sub:08X} (offset +{addr_call_sub - base_func})")
print(f"   ExCreateThread:          0x{addr_create_thread:08X}")
print(f"   KeResumeThread:          0x{addr_resume:08X}")
print(f"   Store to 0x83137CA8:     0x{addr_store:08X} (offset +{addr_store - base_func})")

print("\n6. Summary")
print("-" * 60)
if errors_found:
    print(f"   ERRORS FOUND: {len(errors_found)}")
    for err in errors_found:
        print(f"   {err}")
else:
    print("   ✓ All address calculations verified correct!")

print("\n" + "=" * 80)
