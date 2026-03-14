#!/usr/bin/env bash
set -e

APP="/Users/Ozordi/Downloads/LibertyRecomp/out/build/macos-release/LibertyRecomp/Liberty Recompiled.app/Contents/MacOS/Liberty Recompiled"
LOGDIR="/Users/Ozordi/Downloads/LibertyRecomp/out/build/macos-release/LibertyRecomp/run_logs"
TS=$(date +%Y%m%d_%H%M%S)
APPLOG="$LOGDIR/app_${TS}.log"
LLDBLOG="$LOGDIR/lldb_${TS}.log"
LLDBCMDS="/tmp/lldb_cmds_${TS}.txt"

mkdir -p "$LOGDIR"

# Write lldb commands file
cat > "$LLDBCMDS" <<'EOF'
thread list
thread backtrace all
thread select 20
bt
register read
thread select 19
bt
register read
thread select 1
bt
register read
detach
quit
EOF

echo "[LAUNCHER] Starting app..."
"$APP" >"$APPLOG" 2>&1 &
APPPID=$!
echo "[LAUNCHER] PID=$APPPID"
echo "[LAUNCHER] Waiting 8s..."
sleep 8

if ! kill -0 "$APPPID" 2>/dev/null; then
    echo "[LAUNCHER] App exited early. Log:"
    tail -30 "$APPLOG"
    echo "APPLOG=$APPLOG"
    exit 1
fi

echo "[LAUNCHER] App alive. Attaching lldb..."
lldb --batch -s "$LLDBCMDS" -p "$APPPID" > "$LLDBLOG" 2>&1 || true

echo "[LAUNCHER] Killing app..."
kill "$APPPID" 2>/dev/null || true
wait "$APPPID" 2>/dev/null || true

echo "[LAUNCHER] Done."
echo "APPLOG=$APPLOG"
echo "LLDBLOG=$LLDBLOG"
wc -l "$LLDBLOG"
