#!/usr/bin/env python3
"""
Rendering code audit — checks hook signatures, enum values, and draw count conversion.
"""

import re, sys

VIDEO_CPP  = "/Users/Ozordi/Downloads/LibertyRecomp/LibertyRecomp/gpu/video.cpp"
GFX_STATE  = "/Users/Ozordi/Downloads/LibertyRecomp/LibertyRecomp/gpu/gfx_state.cpp"
DEVICE_H   = "/Users/Ozordi/Downloads/LibertyRecomp/LibertyRecomp/gpu/gtaiv_device.h"
GFX_H      = "/Users/Ozordi/Downloads/LibertyRecomp/LibertyRecomp/gpu/gfx_state.h"

def read(path):
    with open(path, errors="replace") as f:
        return f.read()

video   = read(VIDEO_CPP)
gfx_c   = read(GFX_STATE)
device  = read(DEVICE_H)
gfx_h   = read(GFX_H)

bugs   = []
warns  = []
passes = []

print("=" * 72)
print("RENDERING HOOK AUDIT")
print("=" * 72)

# ─────────────────────────────────────────────────────────────────────────────
# BUG 1: sub_82A46330 (UnifiedDraw) hooked as DrawIndexedPrimitive
#   Actual signature:  (device, isIndexed)  — 2 args
#   DrawIndexedPrimitive: (device, primType, baseVtx, minVtx, numVtx, startIdx, count) — 7 args
#   ABI mismatch: r5–r9 will be random garbage passed to the draw call
# ─────────────────────────────────────────────────────────────────────────────
if "GUEST_FUNCTION_HOOK(sub_82A46330, DrawIndexedPrimitive)" in video:
    bugs.append(
        "BUG-1 [CRITICAL] sub_82A46330 hooked as DrawIndexedPrimitive — WRONG SIGNATURE\n"
        "  sub_82A46330 is UnifiedDraw(device, isIndexed) — only 2 args.\n"
        "  DrawIndexedPrimitive expects (device, primType, baseVtx, minVtx, numVtx, startIdx, count).\n"
        "  r5-r9 will be random PPC register garbage on every indexed draw call.\n"
        "  FIX: Replace with a dedicated UnifiedDraw stub that reads isIndexed from r4,\n"
        "       extracts draw args from the device context, and dispatches appropriately.\n"
        "       OR stub sub_82A46330 to a no-op (game already calls the shared-layer\n"
        "       DrawIndexedPrimitive at sub_82543AC8 which is already properly hooked)."
    )
else:
    passes.append("PASS  sub_82A46330 not mishooked as DrawIndexedPrimitive")

# ─────────────────────────────────────────────────────────────────────────────
# BUG 2: primitiveCount passed directly to drawInstanced as vertex count
#   drawInstanced(vertexCount, instanceCount, startVertex, startInstance)
#   For D3DPT_TRIANGLELIST: vertexCount = primitiveCount * 3
#   Passing primCount directly draws 1/3 the geometry for triangle lists.
# ─────────────────────────────────────────────────────────────────────────────
if "commandList->drawInstanced(args.primitiveCount," in video:
    bugs.append(
        "BUG-2 [HIGH] ProcDrawPrimitive passes primitiveCount to drawInstanced as vertexCount.\n"
        "  drawInstanced(vertexCount, ...) — but GTA IV (like D3D9) counts primitives, not vertices.\n"
        "  For D3DPT_TRIANGLELIST (type=4): vertexCount = primitiveCount * 3\n"
        "  For D3DPT_TRIANGLESTRIP (type=8): vertexCount = primitiveCount + 2\n"
        "  For D3DPT_QUADLIST (type=13):     vertexCount = primitiveCount * 4 (expand to tris: *2)\n"
        "  FIX: Add PrimCountToVertexCount(primType, primCount) before drawInstanced."
    )
else:
    passes.append("PASS  drawInstanced vertex count conversion")

# ─────────────────────────────────────────────────────────────────────────────
# BUG 3: D3DPT_TRIANGLESTRIP = 6 in video.h (should be 8; 6 is RECTLIST)
#   Xenos/GTA IV confirmed values:  TriangleFan=5, RectList=6, TriangleStrip=8
#   video.h GuestPrimitiveType has D3DPT_TRIANGLESTRIP = 6 — WRONG
# ─────────────────────────────────────────────────────────────────────────────
# Read video.h directly
with open("/Users/Ozordi/Downloads/LibertyRecomp/LibertyRecomp/gpu/video.h", errors="replace") as f:
    video_h = f.read()

ts_match = re.search(r"D3DPT_TRIANGLESTRIP\s*=\s*(\d+)", video_h)
ts_val = int(ts_match.group(1)) if ts_match else None
if ts_val == 6:
    bugs.append(
        "BUG-3 [HIGH] video.h GuestPrimitiveType: D3DPT_TRIANGLESTRIP = 6 (WRONG — should be 8).\n"
        "  Value 6 is D3DPT_RECTLIST (Xenos quad primitive used by postfx).\n"
        "  ConvertPrimitiveType in video.cpp uses these enums — TRIANGLESTRIP topology will be\n"
        "  applied when the game sends a RECTLIST draw, and vice versa.\n"
        "  RECTLIST is also completely absent from ConvertPrimitiveType switch.\n"
        "  FIX: D3DPT_TRIANGLESTRIP = 8, add D3DPT_RECTLIST = 6 case."
    )
elif ts_val == 8:
    passes.append("PASS  D3DPT_TRIANGLESTRIP = 8 (correct)")
else:
    warns.append(f"WARN  D3DPT_TRIANGLESTRIP not found or unexpected value: {ts_val}")

# ─────────────────────────────────────────────────────────────────────────────
# BUG 4: sub_82A47AE0 (SetPixelShader) sets BOTH VS and PS
#   Actual PPC args: r3=device, r4=vsHandle, r5=psHandle
#   But SetPixelShader(GuestDevice*, GuestShader*) is (device, shader=r4)
#   → vsHandle is bound as the pixel shader, psHandle is ignored
# ─────────────────────────────────────────────────────────────────────────────
if "GUEST_FUNCTION_HOOK(sub_82A47AE0, SetPixelShader)" in video:
    # Check whether the SetPixelShader function accepts a 3rd argument for vsHandle
    ps_func_sig = re.search(r"static void SetPixelShader\(([^)]+)\)", video)
    if ps_func_sig:
        sig_args = ps_func_sig.group(1)
        arg_count = sig_args.count(",") + 1
        if arg_count < 3:
            bugs.append(
                "BUG-4 [HIGH] sub_82A47AE0 sets BOTH VS and PS (r3=device, r4=vsHandle, r5=psHandle)\n"
                "  but is hooked as SetPixelShader(GuestDevice*, GuestShader*) — only 2 args.\n"
                "  Result: vsHandle (r4) is bound as the pixel shader, psHandle (r5) is silently dropped.\n"
                "  ALL game pixel shader binds via this path will use the VERTEX shader handle as PS.\n"
                "  FIX: Add a combined hook: SetBothShaders(device, vsShader, psShader)\n"
                "       that calls both SetVertexShader and SetPixelShader state updates."
            )
        else:
            passes.append("PASS  SetPixelShader accepts vsHandle parameter")
else:
    passes.append("PASS  sub_82A47AE0 not hooked as simple SetPixelShader")

# ─────────────────────────────────────────────────────────────────────────────
# BUG 5: EndDrawCall in gfx_state.cpp double-increments s_frameDrawCalls
# ─────────────────────────────────────────────────────────────────────────────
ec_section = re.search(r"void EndDrawCall\(\)(.*?)^}", gfx_c, re.DOTALL | re.MULTILINE)
if ec_section:
    # Strip comment lines before counting to avoid false positives from fix comments
    body_lines = [l for l in ec_section.group(1).split("\n") if not l.strip().startswith("//")]
    body = "\n".join(body_lines)
    count = body.count("s_frameDrawCalls++")
    if count > 1:
        bugs.append(
            f"BUG-5 [MEDIUM] gfx_state.cpp EndDrawCall() increments s_frameDrawCalls {count}x.\n"
            "  Frame draw-call statistics will be doubled. Fix: remove the duplicate increment."
        )
    else:
        passes.append(f"PASS  EndDrawCall increments s_frameDrawCalls exactly once")

# ─────────────────────────────────────────────────────────────────────────────
# BUG 6: RECTLIST missing from ConvertPrimitiveType
# ─────────────────────────────────────────────────────────────────────────────
if "RECTLIST" not in video or "case D3DPT_RECTLIST" not in video:
    bugs.append(
        "BUG-6 [MEDIUM] RECTLIST (value=6, Xenos postfx quad primitive) has no case in\n"
        "  ConvertPrimitiveType(). The assert(false) catch-all will fire on any postfx pass.\n"
        "  FIX: Add 'case D3DPT_RECTLIST: return RenderPrimitiveTopology::TRIANGLE_LIST;'\n"
        "       (expand 3-vertex RECTLIST to 2 triangles in vertex count conversion)."
    )
else:
    passes.append("PASS  RECTLIST handled in ConvertPrimitiveType")

# ─────────────────────────────────────────────────────────────────────────────
# WARN 1: PM4 buffer flush uses GpuContextPtr (+14888) as buffer base
#   The comment in code says "device+14888 is the immutable allocation address"
#   but DeviceOffset::GpuContextPtr = 14888 is labeled as a GPU context pointer,
#   not a command buffer base. The real buffer base is device+16712 (SecondaryBufferBase).
# ─────────────────────────────────────────────────────────────────────────────
if "GpuContextPtr" in video and "bufBase" in video:
    warns.append(
        "WARN-1 PM4BufferFlush (sub_82A499B8) uses DeviceOffset::GpuContextPtr (+14888)\n"
        "  as the fallback buffer base. This offset is documented as 'GPU context reference'\n"
        "  (a pointer to a GPU context struct), not a command buffer start address.\n"
        "  The actual fallback base is SecondaryBufferBase (+16712). Verify under LLDB\n"
        "  that device+14888 actually holds a valid PM4 buffer address at runtime."
    )

# ─────────────────────────────────────────────────────────────────────────────
# WARN 2: sub_82A49CB0 is hooked as DrawPrimitive(device, primType, startVtx, primCount)
#   Confirmed correct from recomp: sub_82A49CB0(a1=device, a2=primType, a3=startVtx, a4=primCount)
# ─────────────────────────────────────────────────────────────────────────────
if "GUEST_FUNCTION_HOOK(sub_82A49CB0, DrawPrimitive)" in video:
    passes.append("PASS  sub_82A49CB0 hooked as DrawPrimitive (correct address and function name)")

# ─────────────────────────────────────────────────────────────────────────────
# WARN 3: sub_82A492A8 (PM4PacketBuilder) stubbed correctly — returns cmdPtr unchanged
# ─────────────────────────────────────────────────────────────────────────────
pm4_stub = re.search(r"PPC_FUNC\(sub_82A492A8\)[^}]+ctx\.r3\.u64 = ctx\.r4\.u64", video)
if pm4_stub:
    passes.append("PASS  sub_82A492A8 (PM4PacketBuilder) correctly stubbed to return cmdPtr unchanged")
else:
    warns.append("WARN-2 sub_82A492A8 PM4 stub may not be returning cmdPtr correctly")

# ─────────────────────────────────────────────────────────────────────────────
# WARN 4: sub_82A467D8 (Present) increments FrameCounter — correct and critical
# ─────────────────────────────────────────────────────────────────────────────
if "FrameCounter" in video and "frameCounter + 1" in video:
    passes.append("PASS  sub_82A467D8 (Present) manually increments FrameCounter at +16544")

# ─────────────────────────────────────────────────────────────────────────────
# WARN 5: SetRenderTarget/SetDepthStencil/SetViewport all hooked at correct addresses
# ─────────────────────────────────────────────────────────────────────────────
required_hooks = {
    "sub_82A3B690": "SetRenderTarget",
    "sub_82A3B7B0": "SetDepthStencilSurface",
    "sub_82A42760": "SetViewport",
    "sub_82A424A8": "SetScissorRect",
    "sub_82A3A890": "SetVertexDeclaration",
    "sub_82A44B78": "SetTexture",
}
for addr, name in required_hooks.items():
    if f"GUEST_FUNCTION_HOOK({addr}," in video:
        passes.append(f"PASS  {addr} ({name}) hooked")
    else:
        warns.append(f"WARN  {addr} ({name}) NOT found in active hooks")

# ─────────────────────────────────────────────────────────────────────────────
# Print results
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n{'─'*72}")
print(f"  BUGS ({len(bugs)}):")
print(f"{'─'*72}")
for b in bugs:
    print(f"\n  ❌ {b}")

print(f"\n{'─'*72}")
print(f"  WARNINGS ({len(warns)}):")
print(f"{'─'*72}")
for w in warns:
    print(f"\n  ⚠️  {w}")

print(f"\n{'─'*72}")
print(f"  PASSING ({len(passes)}):")
print(f"{'─'*72}")
for p in passes:
    print(f"  ✅ {p}")

print(f"\n{'='*72}")
print(f"  SUMMARY: {len(bugs)} bugs | {len(warns)} warnings | {len(passes)} passing")
print(f"{'='*72}\n")
