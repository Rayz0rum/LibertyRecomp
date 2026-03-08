# Game Payload Directory

This directory is used for **embedded builds** (iOS, Android, PS4, Switch) where the game files must be bundled at compile time.

## Required Files

Place your GTA IV Xbox 360 game files in this directory with the following structure:

```
tools/local_game_payload/
├── default.xex          # Main executable (required)
├── common.rpf           # Common game data (required)
├── xbox360.rpf          # Xbox 360 specific data (required)
├── audio.rpf            # Audio data (required)
└── dlc/                 # DLC content (optional)
    ├── TLAD/            # The Lost and Damned
    │   └── ...
    └── TBOGT/           # The Ballad of Gay Tony
        └── ...
```

## How to Obtain These Files

You need a **legally obtained copy** of GTA IV for Xbox 360. You can extract these files from:

1. **Physical Xbox 360 disc** - Use tools like extract-xiso
2. **Xbox 360 ISO file** - Mount and copy files
3. **Installed Xbox 360 game** - Copy from console storage

## Extraction Tools

### Using extract-xiso (Recommended)

```bash
# Install extract-xiso (already in tools/extract-xiso)
cd tools/extract-xiso
make

# Extract your GTA IV disc/ISO
./extract-xiso -d /path/to/output /path/to/GTAIV.iso

# Copy required files to payload directory
cp /path/to/output/default.xex tools/local_game_payload/
cp /path/to/output/*.rpf tools/local_game_payload/
```

### Manual Extraction

If you have access to an Xbox 360 with the game installed:

1. Use FTP or USB to copy files from the console
2. Navigate to the game installation directory
3. Copy all `.xex` and `.rpf` files

## DLC Setup (Optional)

If you have The Lost and Damned (TLAD) or The Ballad of Gay Tony (TBOGT):

```bash
# Create DLC directories
mkdir -p tools/local_game_payload/dlc/TLAD
mkdir -p tools/local_game_payload/dlc/TBOGT

# Copy DLC files
cp -r /path/to/TLAD/* tools/local_game_payload/dlc/TLAD/
cp -r /path/to/TBOGT/* tools/local_game_payload/dlc/TBOGT/
```

## Verification

After copying files, verify the structure:

```bash
ls -lh tools/local_game_payload/
# Should show:
# - default.xex (several MB)
# - common.rpf (hundreds of MB)
# - xbox360.rpf (hundreds of MB)
# - audio.rpf (large file, GB+)
```

## Build Configuration

Once files are in place, configure your build:

```bash
# iOS
cmake --preset ios-release

# Android
cmake --preset android-release

# PS4
cmake --preset ps4-release

# Switch
cmake --preset switch-release
```

## Custom Path

If you want to use a different location for game files:

```bash
cmake --preset ios-release \
  -DLIBERTY_RECOMP_EMBEDDED_GAME_PATH=/path/to/your/game/files
```

## Security Note

**Never commit game files to version control!** This directory is already in `.gitignore`.

## Legal Notice

You must own a legitimate copy of GTA IV for Xbox 360 to use these files. This project does not distribute any copyrighted game content.

## Title Updates

GTA IV received several title updates on Xbox 360. **Title Update 8 (TU8)** is recommended for best compatibility.

### Applying Title Updates

Title updates must be applied to `default.xex` **before** building for mobile/console platforms.

#### Method 1: Using xextool (Windows)

```bash
# Download xextool.exe
# Extract .xexp from Title Update STFS package
# Apply patch
xextool.exe -p TU8.xexp -o default.xex default_original.xex
```

#### Method 2: Using Native Patcher (All Platforms)

```bash
# The project includes XexPatcher for native patching
# TODO: Add standalone patcher tool script
```

#### Method 3: Pre-Patched XEX

If you already have a patched `default.xex` from a title-updated Xbox 360 installation, you can use it directly.

### Verifying Title Update

Check the XEX version:
```bash
# The version should be 1.0.8.0 for TU8
# TODO: Add verification script
```

## DLC Setup Details

### The Lost and Damned (TLAD)

Required files in `dlc/TLAD/`:
- `default.xex` - DLC executable
- `tlad.rpf` - Main DLC archive
- Other supporting files

### The Ballad of Gay Tony (TBOGT)

Required files in `dlc/TBOGT/`:
- `default.xex` - DLC executable
- `tbogt.rpf` - Main DLC archive
- Other supporting files

### DLC Extraction

```bash
# Extract TLAD
extract-xiso -d dlc/TLAD/ TLAD.iso

# Extract TBOGT
extract-xiso -d dlc/TBOGT/ TBOGT.iso

# Or from STFS packages
# Use Xbox 360 content extraction tools
```

## Build Validation

Before building, verify your setup:

```bash
# Check required files
ls -lh tools/local_game_payload/
# Should show:
# - default.xex (with TU applied, ~10-20MB)
# - common.rpf (hundreds of MB)
# - xbox360.rpf (hundreds of MB)
# - audio.rpf (several GB)

# Check DLC (optional)
ls -lh tools/local_game_payload/dlc/TLAD/
ls -lh tools/local_game_payload/dlc/TBOGT/
```

## Manifest Generation

CMake automatically generates `manifest.json` during configuration:

```json
{
    "gameVersion": "1.0.0",
    "titleUpdate": "1.0.8.0",
    "hasTLAD": true,
    "hasTBOGT": true,
    "buildTimestamp": 1234567890
}
```

This manifest is embedded in your build and read at runtime to determine available content.

## Troubleshooting

### "Title Update not applied"

Make sure you applied the title update to `default.xex` before copying to `tools/local_game_payload/`.

### "DLC not detected"

Ensure DLC files are in the correct subdirectories:
- `tools/local_game_payload/dlc/TLAD/`
- `tools/local_game_payload/dlc/TBOGT/`

### "File hash mismatch"

This usually means:
1. Wrong region (need NTSC-U/USA version)
2. Corrupted extraction
3. Modified files

Re-extract from original disc/ISO.

### "Build size too large"

This is expected. With base game + both DLCs + audio, the build will be several GB. This is normal for embedded asset builds.
