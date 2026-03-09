# PS4 / OpenOrbis Toolchain
# Requirements:
#   - OpenOrbis PS4 Toolchain cloned into tools/OpenOrbis-PS4-Toolchain
#     (already present — see tools/OpenOrbis-PS4-Toolchain)
#   - LLVM/lld installed: brew install llvm  (macOS/Linux)
#   - Environment variable OO_PS4_TOOLCHAIN pointing at the toolchain root
#
# Setup:
#   export OO_PS4_TOOLCHAIN="$(pwd)/tools/OpenOrbis-PS4-Toolchain"
#   cmake -DCMAKE_TOOLCHAIN_FILE=toolchains/ps4-openorbis.cmake \
#         -DLIBERTY_RECOMP_TARGET_PLATFORM=ps4 \
#         -DLIBERTY_RECOMP_EMBEDDED_GAME_PATH=tools/local_game_payload \
#         ..

# Resolve toolchain root
if(NOT DEFINED OO_PS4_TOOLCHAIN)
    if(DEFINED ENV{OO_PS4_TOOLCHAIN})
        set(OO_PS4_TOOLCHAIN "$ENV{OO_PS4_TOOLCHAIN}")
    else()
        # Default: repo-local clone
        set(OO_PS4_TOOLCHAIN "${CMAKE_SOURCE_DIR}/tools/OpenOrbis-PS4-Toolchain")
    endif()
endif()

if(NOT EXISTS "${OO_PS4_TOOLCHAIN}")
    message(FATAL_ERROR
        "OpenOrbis toolchain not found at: ${OO_PS4_TOOLCHAIN}\n"
        "Run: git clone https://github.com/OpenOrbis/OpenOrbis-PS4-Toolchain.git tools/OpenOrbis-PS4-Toolchain\n"
        "Or set OO_PS4_TOOLCHAIN to the correct path.")
endif()

message(STATUS "Using OpenOrbis PS4 Toolchain: ${OO_PS4_TOOLCHAIN}")

set(CMAKE_SYSTEM_NAME PS4)
set(CMAKE_SYSTEM_PROCESSOR x86_64)

# OpenOrbis uses LLVM/clang targeting orbis
find_program(CLANG_PATH "clang" REQUIRED)
find_program(CLANGPP_PATH "clang++" REQUIRED)
find_program(LLD_PATH "lld" REQUIRED)

set(CMAKE_C_COMPILER   "${CLANG_PATH}")
set(CMAKE_CXX_COMPILER "${CLANGPP_PATH}")
set(CMAKE_LINKER        "${LLD_PATH}")

set(CMAKE_C_COMPILER_TARGET   "x86_64-scei-ps4")
set(CMAKE_CXX_COMPILER_TARGET "x86_64-scei-ps4")

# OpenOrbis sysroot
set(CMAKE_SYSROOT "${OO_PS4_TOOLCHAIN}/include")

# Add OpenOrbis include/lib paths
include_directories(SYSTEM "${OO_PS4_TOOLCHAIN}/include")
link_directories("${OO_PS4_TOOLCHAIN}/lib")

# PS4 uses a custom Vulkan-like GNM API via OpenOrbis's SDL-PS4 or GNM headers.
# For now we target SDL-PS4 with software-emulated Vulkan layer.
set(LIBERTY_RECOMP_VULKAN ON CACHE BOOL "Use Vulkan renderer (via PS4 layer)" FORCE)
set(LIBERTY_RECOMP_D3D12 OFF CACHE BOOL "" FORCE)
set(LIBERTY_RECOMP_METAL OFF CACHE BOOL "" FORCE)

# No installer wizard on PS4
set(LIBERTY_RECOMP_EMBEDDED_ASSETS ON CACHE BOOL "Package assets at build time (no installer UI)" FORCE)

# PKG output target name
set(LIBERTY_PS4_TITLE_ID "LBTY00001" CACHE STRING "PS4 title ID for PKG packaging")
set(LIBERTY_PS4_APP_VERSION "01.00" CACHE STRING "PS4 application version")
