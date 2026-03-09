# Nintendo Switch / libnx (devkitPro) Toolchain
# Requirements:
#   - devkitPro with devkitA64 and libnx installed
#     Install: https://devkitpro.org/wiki/Getting_Started
#     Then:    dkp-pacman -S switch-dev
#   - Environment: DEVKITPRO and DEVKITA64 set by devkitPro's env.sh
#
# Setup:
#   source $DEVKITPRO/devkita64/environment-setup-aarch64-none-elf
#   cmake -DCMAKE_TOOLCHAIN_FILE=toolchains/switch-libnx.cmake \
#         -DLIBERTY_RECOMP_TARGET_PLATFORM=switch \
#         -DLIBERTY_RECOMP_EMBEDDED_GAME_PATH=tools/local_game_payload \
#         ..
#
# Verify installed packages:
#   dkp-pacman -Q switch-dev

# Resolve devkitPro paths
if(NOT DEFINED DEVKITPRO)
    if(DEFINED ENV{DEVKITPRO})
        set(DEVKITPRO "$ENV{DEVKITPRO}")
    else()
        set(DEVKITPRO "/opt/devkitpro")  # common default
    endif()
endif()

if(NOT DEFINED DEVKITA64)
    if(DEFINED ENV{DEVKITA64})
        set(DEVKITA64 "$ENV{DEVKITA64}")
    else()
        set(DEVKITA64 "${DEVKITPRO}/devkitA64")
    endif()
endif()

if(NOT EXISTS "${DEVKITA64}")
    message(FATAL_ERROR
        "devkitA64 not found at: ${DEVKITA64}\n"
        "Install devkitPro: https://devkitpro.org/wiki/Getting_Started\n"
        "Then run: dkp-pacman -S switch-dev\n"
        "Then source devkitPro's environment script and re-run cmake.\n"
        "Verify: dkp-pacman -Q switch-dev")
endif()

message(STATUS "Using devkitA64: ${DEVKITA64}")
message(STATUS "Using devkitPro: ${DEVKITPRO}")

set(CMAKE_SYSTEM_NAME Switch)
set(CMAKE_SYSTEM_PROCESSOR aarch64)

set(CMAKE_C_COMPILER   "${DEVKITA64}/bin/aarch64-none-elf-gcc")
set(CMAKE_CXX_COMPILER "${DEVKITA64}/bin/aarch64-none-elf-g++")
set(CMAKE_AR           "${DEVKITA64}/bin/aarch64-none-elf-ar")
set(CMAKE_RANLIB       "${DEVKITA64}/bin/aarch64-none-elf-ranlib")
set(CMAKE_LINKER       "${DEVKITA64}/bin/aarch64-none-elf-ld")

set(CMAKE_SYSROOT "${DEVKITA64}/aarch64-none-elf")

# libnx headers and libs
include_directories(SYSTEM
    "${DEVKITPRO}/libnx/include"
    "${DEVKITA64}/aarch64-none-elf/include"
)
link_directories(
    "${DEVKITPRO}/libnx/lib"
    "${DEVKITA64}/aarch64-none-elf/lib"
)

# Compile flags for Switch homebrew
set(SWITCH_C_FLAGS   "-march=armv8-a+crc+crypto -mtune=cortex-a57 -mtp=soft -fPIE")
set(SWITCH_CXX_FLAGS "${SWITCH_C_FLAGS} -fno-rtti -fno-exceptions")

set(CMAKE_C_FLAGS_INIT   "${SWITCH_C_FLAGS}")
set(CMAKE_CXX_FLAGS_INIT "${SWITCH_CXX_FLAGS}")

# Switch uses Vulkan via deko3d or SDL2's libnx backend
set(LIBERTY_RECOMP_VULKAN ON CACHE BOOL "Use Vulkan/deko3d renderer" FORCE)
set(LIBERTY_RECOMP_D3D12 OFF CACHE BOOL "" FORCE)
set(LIBERTY_RECOMP_METAL OFF CACHE BOOL "" FORCE)

# No installer wizard on Switch
set(LIBERTY_RECOMP_EMBEDDED_ASSETS ON CACHE BOOL "Package assets at build time (no installer UI)" FORCE)

# NRO (homebrew) output settings
set(LIBERTY_SWITCH_APP_TITLE "Liberty Recomp" CACHE STRING "Switch homebrew title")
set(LIBERTY_SWITCH_APP_AUTHOR "LibertyRecomp Team" CACHE STRING "Switch homebrew author")
set(LIBERTY_SWITCH_APP_VERSION "1.0.0" CACHE STRING "Switch homebrew version")
