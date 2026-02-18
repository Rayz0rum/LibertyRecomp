# iOS CMake Toolchain
# Requirements:
#   - macOS host with Xcode (xcode-select --install)
#   - iOS SDK >= 9.0 (bundled with Xcode)
#   - SDL2 iOS project files (in thirdparty/SDL2)
#
# Usage:
#   cmake -DCMAKE_TOOLCHAIN_FILE=toolchains/ios.cmake \
#         -DLIBERTY_RECOMP_TARGET_PLATFORM=ios \
#         -DLIBERTY_RECOMP_EMBEDDED_GAME_PATH=tools/local_game_payload \
#         -G Xcode ..

set(CMAKE_SYSTEM_NAME iOS)
set(CMAKE_SYSTEM_PROCESSOR arm64)

# Minimum deployment target
set(CMAKE_OSX_DEPLOYMENT_TARGET "16.0" CACHE STRING "Minimum iOS version")
set(CMAKE_OSX_ARCHITECTURES "arm64" CACHE STRING "Target architecture")

# Use Xcode's embedded iOS SDK
set(CMAKE_OSX_SYSROOT iphoneos CACHE STRING "iOS SDK sysroot")

# Require Xcode generator for proper signing / xcframework support
if(NOT CMAKE_GENERATOR STREQUAL "Xcode")
    message(WARNING "iOS builds are best built with -G Xcode. "
                    "Other generators may not handle code signing correctly.")
endif()

# We use Metal on iOS (same path as macOS)
set(LIBERTY_RECOMP_METAL ON CACHE BOOL "Use Metal renderer" FORCE)
set(LIBERTY_RECOMP_D3D12 OFF CACHE BOOL "" FORCE)
set(LIBERTY_RECOMP_VULKAN OFF CACHE BOOL "" FORCE)

# Point SDL2 at its iOS CMake integration
set(SDL2_IOS ON CACHE BOOL "Build SDL2 for iOS" FORCE)

# No installer wizard on iOS
set(LIBERTY_RECOMP_EMBEDDED_ASSETS ON CACHE BOOL "Package assets at build time (no installer UI)" FORCE)
