#!/usr/bin/env bash
# lldb_attach_session.sh
# Launches LibertyRecomp, waits for it to reach VBlank steady state,
# then attaches lldb, captures full bt+memory dump, kills app.

APP="/Users/Ozordi/Downloads/LibertyRecomp/out/build/macos-release/LibertyRecomp/Liberty Recompiled.app/Contents/MacOS/Liberty Recompiled"
LOGDIR="/Users/Ozordi/Downloads/LibertyRecomp/out/build/macos-release/LibertyRecomp/run_logs"
TS=$(date +%Y%m%d_%H%M%S)
APPLOG="$LOGDIR/app_${TS}.txt"
LLDBLOG="$LOGDIR/lldb_${TS}.txt"

mkdir -p "$LOGDIR"

echo "[LAUNCHER] Starting LibertyRecomp in background..."
"$APP" >"$APPLOG" 2>&1 &
APPPID=$!
echo "[LAUNCHER] PID=$APPPID, waiting 8 s for steady state..."
sleep 8

echo "[LAUNCHER] Checking if still alive..."
if ! kill -0 "$APPPID" 2>/dev/null; then
    echo "[LAUNCHER] App already exited. App log:"
    tail -30 "$APPLOG"
    exit 1
fi
echo "[LAUNCHER] App alive. Attaching lldb..."

# LLDB commands to run after attach
LLDB_CMDS=$(cat <<'LLDBEOF'
thread list
thread backtrace all
expr -- (uint32_t)*(volatile uint32_t*)(0x8000000000ULL + 0x106B1080ULL + 10900ULL)
expr -- (uint32_t)*(volatile uint32_t*)(0x8000000000ULL + 0x106B1080ULL + 48ULL)
expr -- (uint32_t)*(volatile uint32_t*)(0x8000000000ULL + 0x106B1080ULL + 56ULL)
expr -- (uint32_t)*(volatile uint32_t*)(0x8000000000ULL + 0x106B1080ULL + 16544ULL)
expr -- (uint32_t)*(volatile uint32_t*)(0x8000000000ULL + 0x83192F8CUL)
expr -- (uint32_t)*(volatile uint32_t*)(0x8000000000ULL + 0x83192FF4UL)
image lookup --name VdSetGraphicsInterruptCallback
image lookup --name sub_82A49CB0
image lookup --name sub_82A46330
image lookup --name sub_82A467D8
image lookup --name sub_82A492A8
image lookup --name sub_82A499B8
detach
LLDBEOF
)

lldb --batch \
    --one-line "attach --pid $APPPID" \
    --one-line "thread list" \
    --one-line "thread backtrace all" \
    --one-line "expr -- (uint32_t)*(volatile uint32_t*)(0x8000000000ULL + 0x106B1080ULL + 10900ULL)" \
    --one-line "expr -- (uint32_t)*(volatile uint32_t*)(0x8000000000ULL + 0x106B1080ULL + 48ULL)" \
    --one-line "expr -- (uint32_t)*(volatile uint32_t*)(0x8000000000ULL + 0x106B1080ULL + 56ULL)" \
    --one-line "expr -- (uint32_t)*(volatile uint32_t*)(0x8000000000ULL + 0x106B1080ULL + 16544ULL)" \
    --one-line "expr -- (uint32_t)*(volatile uint32_t*)(0x8000000000ULL + 0x83192F8CUL)" \
    --one-line "expr -- (uint32_t)*(volatile uint32_t*)(0x8000000000ULL + 0x83192FF4UL)" \
    --one-line "image lookup --name VdSetGraphicsInterruptCallback" \
    --one-line "image lookup --name sub_82A49CB0" \
    --one-line "image lookup --name sub_82A467D8" \
    --one-line "detach" \
    2>&1 | tee "$LLDBLOG"

echo "[LAUNCHER] Killing app PID=$APPPID"
kill "$APPPID" 2>/dev/null
wait "$APPPID" 2>/dev/null

echo ""
echo "=== App stdout log ==="
cat "$APPLOG"
echo ""
echo "=== LLDB log saved: $LLDBLOG ==="
