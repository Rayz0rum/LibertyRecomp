# LibertyRecomp — no Java code to obfuscate; all logic is native.
# Keep SDL activity so it survives release builds.
-keep class org.libsdl.app.** { *; }
-keep class com.libertyrecomp.** { *; }
