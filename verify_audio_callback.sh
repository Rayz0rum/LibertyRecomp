#!/bin/bash
# verify_audio_callback.sh

export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

echo "Building LibertyRecomp..."
cmake --build ./out/build/macos-release --target LibertyRecomp

echo "Running LibertyRecomp with audio diagnostics (15s timeout)..."
# Run in background and capture output
"./out/build/macos-release/LibertyRecomp/Liberty Recompiled.app/Contents/MacOS/Liberty Recompiled" > audio_verify.log 2>&1 &
PID=$!
echo "Game running with PID $PID"

sleep 15
echo "Timeout reached, stopping game..."
kill $PID || true

echo "==================================================="
echo "AUDIO CALLBACK VERIFICATION REPORT"
echo "==================================================="

echo "1. Audio Thread Start:"
if grep -q "Starting audio thread" audio_verify.log; then
    echo "✅ Audio thread started"
else
    echo "❌ Audio thread NOT started"
    echo "Debug - Search for XAudioRegisterClient in log:"
    grep "XAudioRegisterClient" audio_verify.log
fi

echo "2. Callback Invocations:"
CALLBACK_COUNT=$(grep -c "Invoking guest callback" audio_verify.log)
if [ "$CALLBACK_COUNT" -gt 0 ]; then
    echo "✅ Audio callback invoked $CALLBACK_COUNT times"
    grep "Invoking guest callback" audio_verify.log | head -n 3
else
    echo "❌ Audio callback NEVER invoked"
fi

echo "3. Loading Gate State Changes:"
grep "sub_821238D0" audio_verify.log | head -n 5

echo "4. Loading Gate Bypass Status:"
if grep -q "BYPASS" audio_verify.log; then
    echo "⚠️ BYPASS TRIGGERED - Audio callback didn't clear gate in time"
    grep "BYPASS" audio_verify.log
else
    # Check if BC9 became 0
    if grep -q "BC9=0" audio_verify.log; then
        echo "✅ SUCCESS: Gate cleared naturally (BC9=0 observed)"
    else
        echo "❓ UNKNOWN: No bypass log, but also no BC9=0 log (possibly crashed/timed out early)"
    fi
fi
