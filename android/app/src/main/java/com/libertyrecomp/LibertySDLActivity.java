package com.libertyrecomp;

import android.content.Context;
import android.os.Bundle;
import android.os.Environment;

import org.libsdl.app.SDLActivity;

import java.io.File;

/**
 * LibertySDLActivity — extends SDL's SDLActivity.
 *
 * Responsibilities:
 *  1. Load the LibertyRecomp native library.
 *  2. Call nativeSetPaths() with internal storage and OBB paths
 *     BEFORE SDL calls SDL_main (and therefore before any C++ code runs).
 *  3. Optionally trigger OBB extraction on first boot.
 */
public class LibertySDLActivity extends SDLActivity {

    static {
        // Load our native library. CMake outputs "libLibertyRecomp.so".
        System.loadLibrary("LibertyRecomp");
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        // Set paths before SDL initializes (SDLActivity.onCreate calls nativeInit indirectly)
        setPaths();
        super.onCreate(savedInstanceState);
    }

    /**
     * Pass the paths the native layer needs to the JNI glue.
     * This must be called before any SDL/native initialization.
     */
    private void setPaths() {
        Context ctx = getApplicationContext();

        // Internal files directory: /data/data/com.libertyrecomp/files
        String internalPath = ctx.getFilesDir().getAbsolutePath();

        // OBB path: /sdcard/Android/obb/com.libertyrecomp/<main.*.apk>
        // Falls back to internal storage if external is unavailable.
        File obbDir = ctx.getObbDir();
        String obbPath = (obbDir != null && obbDir.exists())
                ? obbDir.getAbsolutePath()
                : internalPath;

        nativeSetPaths(internalPath, obbPath);
    }

    /**
     * JNI declaration — implemented in os/android/jni_glue.cpp.
     */
    public static native void nativeSetPaths(String internalPath, String obbPath);

    // ── SDL library name override ─────────────────────────────────────────────

    @Override
    protected String[] getLibraries() {
        return new String[] {
            // SDL2 is statically linked into LibertyRecomp — list only our lib.
            "LibertyRecomp"
        };
    }
}
