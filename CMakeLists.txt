cmake_minimum_required (VERSION 3.20)

if(NOT DEFINED ENV{VCPKG_ROOT})
    message(FATAL_ERROR "VCPKG_ROOT is not defined!")
endif()

set(LIBERTY_RECOMP_THIRDPARTY_ROOT ${CMAKE_SOURCE_DIR}/thirdparty)
set(LIBERTY_RECOMP_TOOLS_ROOT ${CMAKE_SOURCE_DIR}/tools)
set(CMAKE_CXX_STANDARD 20)
set(BUILD_SHARED_LIBS OFF)

# Enable Hot Reload for MSVC compilers if supported.
if (POLICY CMP0141)
  cmake_policy(SET CMP0141 NEW)
  set(CMAKE_MSVC_DEBUG_INFORMATION_FORMAT "$<IF:$<AND:$<C_COMPILER_ID:MSVC>,$<CXX_COMPILER_ID:MSVC>>,$<$<CONFIG:Debug,RelWithDebInfo>:EditAndContinue>,$<$<CONFIG:Debug,RelWithDebInfo>:ProgramDatabase>>")
endif()

set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")

project("LibertyRecomp-ALL")

if (APPLE)
    enable_language(OBJC OBJCXX)
endif()

if (CMAKE_OSX_ARCHITECTURES)
    set(LIBERTY_RECOMP_ARCHITECTURE ${CMAKE_OSX_ARCHITECTURES})
elseif(CMAKE_SYSTEM_PROCESSOR)
    set(LIBERTY_RECOMP_ARCHITECTURE ${CMAKE_SYSTEM_PROCESSOR})
else()
    set(LIBERTY_RECOMP_ARCHITECTURE ${CMAKE_HOST_SYSTEM_PROCESSOR})
endif()
string(TOLOWER "${LIBERTY_RECOMP_ARCHITECTURE}" LIBERTY_RECOMP_ARCHITECTURE)
message(STATUS "Detected architecture: ${LIBERTY_RECOMP_ARCHITECTURE}")

if (LIBERTY_RECOMP_ARCHITECTURE STREQUAL "x86_64" OR LIBERTY_RECOMP_ARCHITECTURE STREQUAL "amd64")
    # Target Sandy Bridge for all projects
    add_compile_options(
        -march=sandybridge
    )
endif()

if (CMAKE_BUILD_TYPE STREQUAL "Debug")
    # Normally only defined by Visual Studio, added for consistency
    add_compile_definitions(_DEBUG)
endif()

add_subdirectory(${LIBERTY_RECOMP_THIRDPARTY_ROOT})
add_subdirectory(${LIBERTY_RECOMP_TOOLS_ROOT})


# ---------------------------------------------------------------------------
# ReXGlue SDK — pre-built static libraries
# glue/rexglue-sdk-main/out/macos-arm64/<config>/lib*.a
# These provide all __imp__Ke*, __imp__Nt*, __imp__Xam*, __imp__Vd*, etc.
# symbols that the generated PPC recompiled code references at link time.
# ---------------------------------------------------------------------------
if (APPLE)
    set(REXGLUE_LIB_DIR "${CMAKE_SOURCE_DIR}/glue/rexglue-sdk-main/out/macos-arm64")

    if (CMAKE_BUILD_TYPE STREQUAL "Release")
        set(REXGLUE_CONFIG_DIR "${REXGLUE_LIB_DIR}/Release")
    elseif (CMAKE_BUILD_TYPE STREQUAL "RelWithDebInfo")
        set(REXGLUE_CONFIG_DIR "${REXGLUE_LIB_DIR}/RelWithDebInfo")
    else()
        set(REXGLUE_CONFIG_DIR "${REXGLUE_LIB_DIR}/Debug")
    endif()

    # Fallback to flat dir if config subdir missing
    if (NOT EXISTS "${REXGLUE_CONFIG_DIR}/librexkernel.a")
        set(REXGLUE_CONFIG_DIR "${REXGLUE_LIB_DIR}")
    endif()

    set(REXGLUE_LIBS rexkernel rexsystem rexcore rexgraphics rexinput rexaudio rexfilesystem rexui rexcodegen)
    foreach(_rexlib IN LISTS REXGLUE_LIBS)
        set(_lib "${REXGLUE_CONFIG_DIR}/lib${_rexlib}.a")
        if (EXISTS "${_lib}")
            add_library(${_rexlib}_prebuilt STATIC IMPORTED GLOBAL)
            set_target_properties(${_rexlib}_prebuilt PROPERTIES IMPORTED_LOCATION "${_lib}")
        endif()
    endforeach()
    unset(_rexlib)
    unset(_lib)
endif()

# Include sub-projects.
add_subdirectory("LibertyRecompLib")
add_subdirectory("LibertyRecomp")
