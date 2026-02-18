# local_game_payload

This directory is the **build-time game payload staging area** used for platform
targets that cannot present a file-picker installer at runtime (iOS, Android, PS4,
Nintendo Switch).

## Expected Layout

```
local_game_payload/
├── default.xex          ← Required: patched/raw XEX executable
├── common.rpf           ← Required: common game archive
├── xbox360.rpf          ← Required: platform-specific archive
├── audio.rpf            ← Required: audio archive
├── dlc/
│   ├── TLAD/            ← Optional: The Lost and Damned
│   └── TBOGT/           ← Optional: The Ballad of Gay Tony
└── README.md            ← This file
```

## How to Populate

1. Install/extract your legitimately-owned GTA IV Xbox 360 copy.
2. Copy `default.xex`, `common.rpf`, `xbox360.rpf`, and `audio.rpf` into this directory.
3. Optionally copy DLC folders under `dlc/`.

## Configuring the CMake Path

By default, CMake looks here (`tools/local_game_payload/`). To override, set
`LIBERTY_RECOMP_EMBEDDED_GAME_PATH` in your CMake cache:

```bash
cmake -DLIBERTY_RECOMP_EMBEDDED_GAME_PATH=/path/to/your/game_files -DLIBERTY_RECOMP_TARGET_PLATFORM=ios ..
```

## Note

This directory and its game files are **gitignored** — game assets must not be
committed to the repository. Only this README and the directory structure are tracked.
