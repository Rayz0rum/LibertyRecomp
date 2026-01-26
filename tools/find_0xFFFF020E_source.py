#!/usr/bin/env python3
"""
Find what buffer values could produce 0xFFFF020E in sub_828A58C8.
We work backwards from the known bad value to find the source.
"""
import struct

TARGET = 0xFFFF020E
URL_SIZE = 65010

print("=" * 70)
print("REVERSE ENGINEERING: WHAT PRODUCES 0xFFFF020E?")
print("=" * 70)

print(f"""
Target value: 0x{TARGET:08X}
As signed int32: {struct.unpack('>i', struct.pack('>I', TARGET))[0]}
URL size parameter: {URL_SIZE}

The calculation is:
  r5 = (r26 * 10) + r21

So either:
  1. r26 * 10 = 0xFFFF020E and r21 = 0, OR
  2. r21 = 0xFFFF020E and r26 = 0, OR
  3. Some combination
""")

print("=" * 70)
print("SCENARIO A: r26 * 10 = 0xFFFF020E")
print("=" * 70)

# If r26 * 10 = 0xFFFF020E
# Then r26 = 0xFFFF020E / 10
r26_scenario_a = TARGET // 10
remainder = TARGET % 10
print(f"If r26 * 10 = 0x{TARGET:08X}:")
print(f"  r26 = {TARGET} / 10 = {r26_scenario_a} remainder {remainder}")
print(f"  r26 = 0x{r26_scenario_a:08X}")
print(f"  Verify: {r26_scenario_a} * 10 = {r26_scenario_a * 10} = 0x{(r26_scenario_a * 10) & 0xFFFFFFFF:08X}")
print(f"  Doesn't divide evenly, so r26 alone can't produce exact value")

print("\n" + "=" * 70)
print("SCENARIO B: r21 = 0xFFFF020E (r26 = 0)")
print("=" * 70)

# If r21 = 0xFFFF020E, trace back r21
# r21 = r11 + 4 where r11 = (r10 * 14) + r20
# So r21 = (r10 * 14) + r20 + 4

print("""
If r26 = 0, then r5 = r21.
r21 = 0xFFFF020E

r21 = r11 + 4  (line 10476-10477)
So r11 = 0xFFFF020A

r11 = (r10 * 14) + r20  (lines 10470-10473)

Possibilities:
  1. r10 = 0 and r20 = 0xFFFF020A
  2. r10 = some value and r20 = corresponding value
""")

r21_target = TARGET
r11_target = r21_target - 4
print(f"r11 must be: 0x{r11_target:08X}")

# Check if r20 could be 0xFFFF020A
print(f"\nIf r10 = 0, then r20 = 0x{r11_target:08X}")
print("But r20 is supposed to be a pointer (r11 + 4 from earlier)")
print("r20 can't be 0xFFFF020A because that's not a valid pointer!")

# What if r20 is valid and r10 is large?
# r11 = r10 * 14 + r20
# 0xFFFF020A = r10 * 14 + r20
# If r20 = 0xB9528388 (typical), then:
r20_typical = 0xB9528388
r10_needed = (r11_target - r20_typical) // 14
print(f"\nIf r20 = 0x{r20_typical:08X} (typical buffer pointer):")
print(f"  r10 * 14 = 0x{r11_target:08X} - 0x{r20_typical:08X}")
print(f"           = {r11_target - r20_typical} (negative!)")
print(f"  This would require r10 to be negative, which is unusual")

print("\n" + "=" * 70)
print("SCENARIO C: THE rlwinm CORRUPTION")
print("=" * 70)

print("""
Looking at the rlwinm operations more carefully:

Line 10480-10481:
  ctx.r11.u64 = __builtin_rotateleft64(ctx.r26.u32 | (ctx.r26.u64 << 32), 2) & 0xFFFFFFFC;

This creates a 64-bit value by:
  1. Taking r26.u32 (lower 32 bits)
  2. OR with (r26.u64 << 32) - shifts the FULL 64-bit value left 32!
  3. Rotate left by 2
  4. Mask with 0xFFFFFFFC

The key issue: (r26.u64 << 32) uses the FULL r26.u64!
If r26.u64 has garbage in upper 32 bits, this gets shifted and ORed!
""")

def simulate_rlwinm_with_garbage(r26_u32, r26_upper32):
    """Simulate rlwinm with potential garbage in upper 32 bits."""
    r26_u64 = (r26_upper32 << 32) | r26_u32
    
    print(f"\nr26.u32 = 0x{r26_u32:08X}")
    print(f"r26 upper 32 = 0x{r26_upper32:08X}")
    print(f"r26.u64 = 0x{r26_u64:016X}")
    
    # The rlwinm operation
    combined = r26_u32 | (r26_u64 << 32)
    combined = combined & 0xFFFFFFFFFFFFFFFF  # Ensure 64-bit
    print(f"r26.u32 | (r26.u64 << 32) = 0x{combined:016X}")
    
    # Rotate left by 2
    def rotl64(val, n):
        val = val & 0xFFFFFFFFFFFFFFFF
        return ((val << n) | (val >> (64 - n))) & 0xFFFFFFFFFFFFFFFF
    
    rotated = rotl64(combined, 2)
    print(f"rotateleft64(..., 2) = 0x{rotated:016X}")
    
    masked = rotated & 0xFFFFFFFC
    print(f"& 0xFFFFFFFC = 0x{masked:016X}")
    
    return masked

# Test with clean r26
print("\n--- Clean r26 (no garbage) ---")
r11_clean = simulate_rlwinm_with_garbage(0x21, 0x00000000)

# Test with garbage in upper bits
print("\n--- r26 with garbage in upper 32 bits ---")
r11_garbage = simulate_rlwinm_with_garbage(0x21, 0xFFFFFFFF)

print("\n" + "=" * 70)
print("SCENARIO D: NEGATIVE r22 (FILE SIZE)")
print("=" * 70)

print("""
Looking at lines 10498-10499:
  ctx.r11.u64 = ctx.r11.u64 + ctx.r22.u64;

r22 is the file size from sub_827E7FA8.
If r22 has garbage upper bits, it could affect the calculation.
""")

# What if r22 = -65010 (the size as negative)?
r22_negative = (-65010) & 0xFFFFFFFFFFFFFFFF
print(f"\nIf r22 = -65010 = 0x{r22_negative:016X}")

print("\n" + "=" * 70)
print("SCENARIO E: THE subf INSTRUCTION")
print("=" * 70)

print("""
Lines 10494-10495:
  ctx.r11.s64 = ctx.r27.s64 - ctx.r29.s64;  // subf = subtract FROM

Lines 10502-10503:
  ctx.r11.s64 = ctx.r27.s64 - ctx.r28.s64;

These are SIGNED subtractions!

If r27 (buffer) is 0xB9528380 and r28/r29 is larger,
the result would be NEGATIVE!
""")

r27 = 0xB9528380
# r29 = r5 + 4 where r5 is calculated from earlier
# If r5 is a valid pointer, r29 would be valid too

# But what if r28 > r27?
# r28 = r10 + r29 where r10 = rlwinm(r11, 2)

# Let's say r28 = 0xC0000000 (larger than r27)
r28_large = 0xC0000000
r11_subf = r27 - r28_large  # Signed subtraction
print(f"r27 = 0x{r27:08X}")
print(f"r28 (hypothetical large) = 0x{r28_large:08X}")
print(f"r11 = r27 - r28 = {r27 - r28_large}")
print(f"r11 as unsigned 64-bit = 0x{(r27 - r28_large) & 0xFFFFFFFFFFFFFFFF:016X}")

print("\n" + "=" * 70)
print("FINAL ANALYSIS: MOST LIKELY SOURCE")
print("=" * 70)

print("""
The subf instruction at line 10502-10503 computes:
  r11 = r27 - r28

Where:
  r27 = buffer pointer (~0xB9XXXXXX)
  r28 = calculated offset into buffer

If r28 > r27, the result is NEGATIVE!

Then at line 10506-10507:
  r19 = r11 + r22

r22 is the file size (~544432 = 0x84EB0)

If r11 is a small negative number like -65010:
  r19 = -65010 + 544432 = 479422 = 0x750FE (valid-ish)

But wait - r5 (the memAddr) is set at line 10486-10487, not r19!

Let me re-check the flow...
""")

print("\n" + "=" * 70)
print("TRACING r5 AGAIN")
print("=" * 70)

print("""
r5 is set at line 10486-10487:
  ctx.r5.u64 = ctx.r11.u64 + ctx.r21.u64;

At this point:
  r11 = result of rlwinm (r26 * 10)
  r21 = (r10 * 14) + r20 + 4

r11 should be r26 * 10 where r26 is a small count from buffer.
r21 should be a pointer into the buffer.

For r5 = 0xFFFF020E:
  Either r11 has 0xFFFF in upper bits, or r21 does.

Most likely: r21 has garbage because it involves SIGNED addi operations!

Line 10476-10477:
  ctx.r21.s64 = ctx.r11.s64 + 4;  // SIGNED!

If r11.s64 is large (like 0x00000000B9538556), it's positive.
But if r11 somehow got garbage upper bits (0xFFFFFFFFB9538556),
then r11.s64 would be NEGATIVE!

And r21.s64 = negative + 4 = still negative = 0xFFFFFFFFxxxxxxxx
Then r21.u64 = 0xFFFFFFFFxxxxxxxx (garbage upper bits!)

When added to r11.u64 (clean r26*10), the result inherits the garbage!
""")

# Verify this theory
r11_with_garbage = 0xFFFFFFFF_B9538556  # If r11 got garbage upper bits
r21_s64 = (r11_with_garbage + 4) & 0xFFFFFFFFFFFFFFFF
print(f"\nIf r11.s64 = 0x{r11_with_garbage:016X} (with garbage)")
print(f"r21 = r11 + 4 = 0x{r21_s64:016X}")

r26_times_10 = 0x14A  # Small value (330)
r5 = (r26_times_10 + r21_s64) & 0xFFFFFFFFFFFFFFFF
print(f"r26 * 10 = 0x{r26_times_10:08X}")
print(f"r5 = r11 + r21 = 0x{r5:016X}")
print(f"r5.u32 = 0x{r5 & 0xFFFFFFFF:08X}")
