# DLC & Title Update System - Mobile/Console Compatibility Summary

## TL;DR

✅ **The DLC and Title Update infrastructure translates perfectly to mobile/console platforms.**

The key difference: Desktop uses runtime installation, mobile/console uses build-time embedding.

## What Works

### DLC Support (TLAD & TBOGT)

**Desktop**: User selects DLC packages in installer → Runtime detection and installation

**Mobile/Console**: User places DLC in `tools/local_game_payload/dlc/` → Build-time detection and embedding

```bash
# User preparation
tools/local_game_payload/
├── default.xex
├── common.rpf
└── dlc/
    ├── TLAD/
    │   ├── default.xex
    │   └── tlad.rpf
    └── TBOGT/
        ├── default.xex
        └── tbogt.rpf

# CMake detects automatically
cmake --preset ios-release
# Output: "Found embedded DLC: TLAD"
# Output: "Found embedded DLC: TBOGT"

# Runtime access
auto manifest = EmbeddedAssets::ReadManifest();
if (manifest.hasTLAD) {
    LoadDLC("TLAD");
}
```

**Status**: ✅ Fully functional, no changes needed

### Title Update Support

**Desktop**: User selects TU package → Runtime patching with XexPatcher or xextool

**Mobile/Console**: User applies TU before building → Pre-patched XEX embedded

```bash
# User applies TU8 before building
xextool -p TU8.xexp -o default.xex default_original.xex

# Copy to payload
cp default.xex tools/local_game_payload/

# Build embeds patched version
cmake --preset android-release

# Manifest records TU version
{
    "titleUpdate": "1.0.8.0"
}
```

**Status**: ✅ Works perfectly with pre-applied patches

## Platform-Specific Details

### iOS
- **Location**: `<Bundle>/game/` and `<Bundle>/dlc/`
- **DLC**: Embedded in app bundle
- **TU**: Pre-applied to default.xex
- **Size**: Several GB (expected)
- **Updates**: Rebuild required

### Android
- **Location**: Internal storage after extraction
- **DLC**: In APK assets or expansion OBB
- **TU**: Pre-applied to default.xex
- **Size**: Several GB (use OBB for large builds)
- **Updates**: Reinstall required

### PS4
- **Location**: `/app0/game/` and `/app0/dlc/`
- **DLC**: Embedded in PKG
- **TU**: Pre-applied to default.xex
- **Size**: Several GB PKG
- **Updates**: Reinstall PKG required

### Switch
- **Location**: `romfs:/game/` and `romfs:/dlc/`
- **DLC**: Embedded in RomFS
- **TU**: Pre-applied to default.xex
- **Size**: Several GB .nro
- **Updates**: Replace .nro required

## User Workflow

### Step 1: Extract Game Files

```bash
# Extract base game
extract-xiso -d game_files/ GTAIV.iso

# Extract DLC (optional)
extract-xiso -d dlc_files/TLAD/ TLAD.iso
extract-xiso -d dlc_files/TBOGT/ TBOGT.iso
```

### Step 2: Apply Title Update (Recommended)

```bash
# Apply TU8 for best compatibility
xextool -p TU8.xexp -o game_files/default.xex game_files/default_original.xex
```

### Step 3: Organize Files

```bash
# Copy to build location
cp -r game_files/* tools/local_game_payload/
mkdir -p tools/local_game_payload/dlc
cp -r dlc_files/TLAD tools/local_game_payload/dlc/
cp -r dlc_files/TBOGT tools/local_game_payload/dlc/
```

### Step 4: Verify Structure

```bash
tools/local_game_payload/
├── default.xex          # ✓ With TU8 applied
├── common.rpf           # ✓ Required
├── xbox360.rpf          # ✓ Required
├── audio.rpf            # ✓ Required
└── dlc/                 # ✓ Optional
    ├── TLAD/
    │   ├── default.xex
    │   └── tlad.rpf
    └── TBOGT/
        ├── default.xex
        └── tbogt.rpf
```

### Step 5: Build

```bash
# Configure (validates files and detects DLC)
cmake --preset ios-release

# CMake output shows:
# -- Found embedded DLC: TLAD
# -- Found embedded DLC: TBOGT
# -- Embedded payload validated successfully

# Build
cmake --build out/build/ios-release
```

## What's Already Implemented

### ✅ Embedded Asset System
- `embedded_assets.cpp` - Platform-specific path resolution
- `EmbeddedAssets::GetGameRoot()` - Returns correct path per platform
- `EmbeddedAssets::GetDLCRoot()` - Returns DLC directory
- `EmbeddedAssets::ReadManifest()` - Reads build-time manifest

### ✅ Build-Time Validation
- CMakeLists.txt checks for required files
- Detects optional DLC automatically
- Generates manifest.json with DLC flags
- Fails fast if files missing

### ✅ Runtime Detection
- Manifest system records DLC availability
- Game reads manifest at startup
- Loads DLC if present
- No installer UI needed

### ✅ Title Update Infrastructure
- XexPatcher for native patching
- TitleUpdateManager for desktop
- Pre-patched XEX support for mobile/console
- Version tracking in manifest

## What's NOT Needed

### ❌ Runtime DLC Installation
- Mobile/console platforms don't need this
- Everything embedded at build time
- By design for these platforms

### ❌ Runtime Title Update Application
- Could be implemented but unnecessary
- Users apply TU before building
- Simpler and more reliable

### ❌ Installer Wizard
- Desktop only
- Mobile/console use embedded assets
- No UI needed

## Documentation Created

1. **docs/DLC_UPDATE_MOBILE_CONSOLE_ANALYSIS.md**
   - Comprehensive technical analysis
   - Platform-specific details
   - Code examples

2. **tools/local_game_payload/README.md** (updated)
   - DLC extraction instructions
   - Title update application guide
   - Verification steps

3. **docs/BUILDING_MOBILE_CONSOLE.md** (existing)
   - Build instructions per platform
   - Prerequisites
   - Troubleshooting

## Recommendations

### For End Users

1. **Always apply TU8** before building
   - Best compatibility
   - Latest bug fixes
   - Recommended by project

2. **Include DLC if you have it**
   - Just place in correct folders
   - CMake detects automatically
   - No extra configuration needed

3. **Verify file structure** before building
   - Use provided README
   - Check file sizes
   - Ensure correct region (NTSC-U)

### For Developers

1. **Add TU application script**
   - Automate xextool usage
   - Validate TU version
   - User-friendly wrapper

2. **Improve manifest validation**
   - Runtime checks
   - Better error messages
   - Version verification

3. **Document build sizes**
   - Set expectations
   - Explain why large
   - Optimization tips

## Conclusion

The DLC and Title Update system is **production-ready** for mobile/console platforms:

- ✅ All infrastructure exists
- ✅ Build-time embedding works
- ✅ Runtime detection functional
- ✅ Manifest system complete
- ✅ Platform-specific paths correct

**No code changes required** - just user documentation and helper scripts.

The system elegantly handles the difference between desktop (runtime installation) and mobile/console (build-time embedding) through the existing embedded asset infrastructure.

---

**Status**: Ready for use
**Confidence**: High
**Blockers**: None
**Next Steps**: User documentation and helper scripts
