# =============================================================================
# RexGlue SDK Integration for LibertyRecomp
# =============================================================================
# Selectively builds only the RexGlue subsystems needed by LibertyRecomp:
#   - rexcore       (threading, memory utils, exception handling, logging)
#   - rexfilesystem (VFS, STFS/disc image devices)
#   - rexruntime    (processor, MMIO handler, XEX module loading)
#   - rexkernel     (kernel objects, threading, kernel state)
#
# LibertyRecomp provides its own: GPU, audio, input, UI, file I/O, patches.
# =============================================================================

include(GNUInstallDirs)

set(REXGLUE_SDK_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/rexglue-sdk-main")

# --- Configuration -----------------------------------------------------------

# Enable headless mode: LibertyRecomp provides its own GPU/audio/input
# subsystems, so RexGlue's graphics/input/SDL dependencies are not needed.
# REX_HEADLESS affects: kernel_state (no input drivers), xobject (wait caps),
# runtime (no GPU/APU init), xam_ui (headless dialog dispatch).
# LibertyRecomp's rendering, audio, and input code handle these instead.
set(REXGLUE_HEADLESS ON)

# Compiler flags needed by RexGlue code (normally set by its root CMakeLists)
add_compile_options(-fno-char8_t)

# Disable RexGlue tests when building as part of LibertyRecomp
set(REXGLUE_BUILD_TESTS OFF CACHE BOOL "" FORCE)

# --- vcpkg dependencies needed by rexcore/runtime/kernel --------------------
# These are declared in the root vcpkg.json; just find them here.

find_package(spdlog CONFIG REQUIRED)
find_package(fmt CONFIG REQUIRED)
find_package(date CONFIG REQUIRED)
find_package(utf8cpp CONFIG REQUIRED)

# --- RexGlue vendored thirdparty (selective) ---------------------------------
# Only build the targets needed by rexcore/rexruntime/rexkernel.
# Skips xxHash, disasm (conflict with XenonRecomp), glslang, FFmpeg (unused).

set(REX_3P "${REXGLUE_SDK_ROOT}/thirdparty")

# Header-only libraries
add_library(disruptorplus INTERFACE)
target_include_directories(disruptorplus INTERFACE
    $<BUILD_INTERFACE:${REX_3P}/disruptorplus/include>
    $<INSTALL_INTERFACE:include/disruptorplus>)

add_library(tomlplusplus INTERFACE)
target_include_directories(tomlplusplus INTERFACE
    $<BUILD_INTERFACE:${REX_3P}/tomlplusplus/include>
    $<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}>)

add_library(simde INTERFACE)
target_include_directories(simde INTERFACE
    $<BUILD_INTERFACE:${REX_3P}/simde>
    $<BUILD_INTERFACE:${REX_3P}/simde/simde>
    $<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}>)

# aes_128 - AES-128 encryption/decryption (used by rexkernel crypt routines)
add_library(aes128 STATIC "${REX_3P}/aes_128/aes.c")
target_include_directories(aes128 PUBLIC
    $<BUILD_INTERFACE:${REX_3P}>
    $<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}>)
target_compile_options(aes128 PRIVATE -w)

# libmspack - LZX decompression (used by rexruntime XEX loader)
set(MSPACK_DIR "${REX_3P}/libmspack/cabextract/mspack")
add_library(mspack STATIC "${MSPACK_DIR}/lzxd.c")
target_include_directories(mspack PUBLIC
    $<BUILD_INTERFACE:${MSPACK_DIR}>
    $<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}>)
target_compile_options(mspack PRIVATE -w)

# abseil-cpp - use vcpkg's abseil to avoid duplicate symbols with
# protobuf/GameNetworkingSockets which also link vcpkg abseil.
find_package(absl CONFIG REQUIRED)

# --- Fix: vcpkg fmt/spdlog compatibility -------------------------------------
# XenonRecomp vendors fmt 11.0.2 with `basic_format_string` alias removed.
# vcpkg's spdlog was compiled against vcpkg's fmt which retains the alias.
# Create a wrapper target that uses vcpkg fmt headers + XenonRecomp's fmt lib.
set(_VCPKG_INC "${CMAKE_BINARY_DIR}/vcpkg_installed/${VCPKG_TARGET_TRIPLET}/include")
if(EXISTS "${_VCPKG_INC}/fmt")
    message(STATUS "RexGlue: Creating rexglue_fmt wrapper (vcpkg headers + vendored lib)")
    # Copy vcpkg fmt headers outside vcpkg_installed/ so the vcpkg toolchain
    # won't auto-convert the include path to -isystem (which loses to -I).
    set(_REXFMT_INC "${CMAKE_CURRENT_BINARY_DIR}/rexglue_fmt_inc")
    file(MAKE_DIRECTORY "${_REXFMT_INC}")
    file(COPY "${_VCPKG_INC}/fmt" DESTINATION "${_REXFMT_INC}")
    # Wrapper target: vcpkg fmt headers (as -I) + XenonRecomp fmt library only
    add_library(rexglue_fmt INTERFACE)
    target_include_directories(rexglue_fmt INTERFACE "${_REXFMT_INC}")
    target_link_libraries(rexglue_fmt INTERFACE $<LINK_ONLY:fmt>)
    set(REXGLUE_FMT_TARGET rexglue_fmt)
else()
    message(STATUS "RexGlue: Using default fmt::fmt target")
endif()

# --- RexGlue core subsystems ------------------------------------------------

add_subdirectory(
    "${REXGLUE_SDK_ROOT}/src/core"
    "${CMAKE_CURRENT_BINARY_DIR}/rexglue-core"
)

add_subdirectory(
    "${REXGLUE_SDK_ROOT}/src/filesystem"
    "${CMAKE_CURRENT_BINARY_DIR}/rexglue-filesystem"
)

add_subdirectory(
    "${REXGLUE_SDK_ROOT}/src/system"
    "${CMAKE_CURRENT_BINARY_DIR}/rexglue-runtime"
)

add_subdirectory(
    "${REXGLUE_SDK_ROOT}/src/kernel"
    "${CMAKE_CURRENT_BINARY_DIR}/rexglue-kernel"
)
