"""
lldb_session.py — automated lldb execution + backtrace capture for LibertyRecomp
Run with:  lldb --batch -s /Users/Ozordi/Downloads/LibertyRecomp/lldb_session.py \
                "/Users/Ozordi/Downloads/LibertyRecomp/out/build/macos-release/LibertyRecomp/Liberty Recompiled.app/Contents/MacOS/Liberty Recompiled"
"""

import lldb
import time
import sys
import os
import datetime

LOG_PATH = "/Users/Ozordi/Downloads/LibertyRecomp/out/build/macos-release/LibertyRecomp/run_logs/"
os.makedirs(LOG_PATH, exist_ok=True)
ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
OUT = LOG_PATH + f"lldb_run_{ts}.txt"

def write(f, s):
    f.write(s + "\n")
    print(s)

def run_cmd(debugger, cmd):
    res = lldb.SBCommandReturnObject()
    debugger.GetCommandInterpreter().HandleCommand(cmd, res)
    return res.GetOutput() + res.GetError()

def __lldb_init_module(debugger, internal_dict):
    with open(OUT, "w") as f:
        write(f, f"=== LibertyRecomp LLDB Session {ts} ===")
        write(f, f"Target: Liberty Recompiled")
        write(f, "")

        # ── 1. target already set by --batch target argument ──────────────────
        target = debugger.GetSelectedTarget()
        if not target.IsValid():
            write(f, "[ERROR] No target. Pass the binary as argument.")
            return

        # ── 2. async off so commands block ────────────────────────────────────
        debugger.SetAsync(False)

        # ── 3. breakpoint on the 20th VBlank printf (reliable steady-state) ──
        #  We break on printf with a condition — fragile; use a raw bp on
        #  VdSetGraphicsInterruptCallback instead, which fires once at startup,
        #  then continue for 4 s to reach steady-state.
        write(f, "[LLDB] Setting startup breakpoint at VdSetGraphicsInterruptCallback")
        out = run_cmd(debugger, "breakpoint set --name VdSetGraphicsInterruptCallback")
        write(f, out.strip())

        # ── 4. launch ──────────────────────────────────────────────────────────
        write(f, "[LLDB] Launching process...")
        error = lldb.SBError()
        process = target.LaunchSimple(None, None, os.path.expanduser("~"))
        if not process or not process.IsValid():
            write(f, "[ERROR] Launch failed")
            return
        write(f, f"[LLDB] Process PID={process.GetProcessID()} state={process.GetState()}")

        # ── 5. wait for first stop (our breakpoint) ───────────────────────────
        write(f, "[LLDB] Waiting for VdSetGraphicsInterruptCallback bp hit...")
        time.sleep(2)
        state = process.GetState()
        write(f, f"[LLDB] State after bp wait: {state} (5=stopped)")

        # ── 6. delete bp, continue, let the game run for 5 seconds ───────────
        run_cmd(debugger, "breakpoint delete 1")
        write(f, "[LLDB] Continuing for 5 s to reach VBlank steady-state...")
        process.Continue()
        time.sleep(5)

        # ── 7. interrupt ───────────────────────────────────────────────────────
        write(f, "[LLDB] Interrupting process...")
        process.SendAsyncInterrupt()
        time.sleep(1)
        write(f, f"[LLDB] State after interrupt: {process.GetState()}")

        # ── 8. full backtrace all threads ─────────────────────────────────────
        write(f, "")
        write(f, "=" * 72)
        write(f, "BACKTRACE ALL THREADS")
        write(f, "=" * 72)
        bt_out = run_cmd(debugger, "thread backtrace all")
        write(f, bt_out)

        # ── 9. per-thread summary ─────────────────────────────────────────────
        write(f, "")
        write(f, "=" * 72)
        write(f, "THREAD LIST")
        write(f, "=" * 72)
        write(f, run_cmd(debugger, "thread list"))

        # ── 10. inspect device[+10900] value (frame_done vtable) ──────────────
        #  device base = 0x106B1080 (from previous log)
        write(f, "")
        write(f, "=" * 72)
        write(f, "MEMORY READS — device context critical fields")
        write(f, "=" * 72)

        device = 0x106B1080
        # We need to read via guest memory base (g_memory.base is ~0x400000000)
        # Use expression to dereference
        for label, guest_addr in [
                ("device[+10900] (indexBufferBase/vtable)", device + 10900),
                ("device[+48]   (cmdBufferCurrent)",        device + 48),
                ("device[+56]   (cmdBufferLimit)",          device + 56),
                ("device[+16544] (frameCounter)",            device + 16544),
                ("dword_83192F8C (streaming_active)",        0x83192F8C),
                ("dword_83192FF4 (single_threaded_flag)",    0x83192FF4),
        ]:
            expr = f"(uint32_t)*(uint32_t*)(0x400000000ULL + 0x{guest_addr:08X}ULL)"
            out = run_cmd(debugger, f"expression -- {expr}")
            write(f, f"  {label}:")
            write(f, f"    {out.strip()}")

        # ── 11. VBlank callback pointer ───────────────────────────────────────
        write(f, "")
        write(f, "=" * 72)
        write(f, "VBlank interrupt callback resolution")
        write(f, "=" * 72)
        for label, expr in [
                ("g_gpuRingBuffer.interruptCallback",
                 "(uint32_t)g_gpuRingBuffer.interruptCallback"),
                ("g_gpuRingBuffer.interruptUserData",
                 "(uint32_t)g_gpuRingBuffer.interruptUserData"),
        ]:
            out = run_cmd(debugger, f"expression -- {expr}")
            write(f, f"  {label}: {out.strip()}")

        # ── 12. registers of the main game thread (Thread #17 equivalent) ─────
        write(f, "")
        write(f, "=" * 72)
        write(f, "REGISTERS — main XThread (first non-system thread)")
        write(f, "=" * 72)
        # Find the thread named "Main XThread"
        for t in process:
            name = t.GetName() or ""
            if "Main" in name or "XThread" in name:
                idx = t.GetIndexID()
                write(f, f"  Thread #{idx}  '{name}'")
                out = run_cmd(debugger, f"thread select {idx}")
                write(f, run_cmd(debugger, "register read"))
                break

        # ── 13. symbol lookup for key rendering functions ─────────────────────
        write(f, "")
        write(f, "=" * 72)
        write(f, "SYMBOL RESOLUTION — key rendering hooks")
        write(f, "=" * 72)
        for sym in ["sub_82A49CB0", "sub_82A46330", "sub_82A467D8",
                    "sub_82A492A8", "sub_82A499B8", "VdSwap",
                    "__imp__sub_82A467D8", "__imp__sub_82A49CB0"]:
            out = run_cmd(debugger, f"image lookup --name {sym}")
            write(f, f"  {sym}: {out.strip()[:120]}")

        # ── 14. kill and finish ───────────────────────────────────────────────
        write(f, "")
        write(f, "[LLDB] Killing process...")
        process.Kill()
        write(f, f"=== Session complete. Log: {OUT} ===")
