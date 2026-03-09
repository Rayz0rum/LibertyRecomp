project("LibertyRecompLib")

add_compile_options(
    -fno-strict-aliasing
)

if (WIN32)
    add_compile_options(/fp:strict)
else()
    add_compile_options(-ffp-model=strict)
endif()

# Use pre-generated rexglue PPC recompiled sources
set(REXGLUE_ROOT "${CMAKE_SOURCE_DIR}/glue/rexglue-sdk-main")
set(REXGLUE_GENERATED "${REXGLUE_ROOT}/gta4-recomp/generated")

# Include the auto-generated sources list (sets GENERATED_SOURCES)
include("${REXGLUE_GENERATED}/sources.cmake")

add_library(LibertyRecompLib
    ${GENERATED_SOURCES}
    "shader/shader_cache.h"
    "shader/shader_cache.cpp"
    "crt_stubs.cpp"
)

target_include_directories(LibertyRecompLib PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
target_include_directories(LibertyRecompLib PUBLIC "${REXGLUE_GENERATED}")
target_include_directories(LibertyRecompLib PUBLIC "${REXGLUE_ROOT}/include")
target_include_directories(LibertyRecompLib PRIVATE "${REXGLUE_ROOT}/thirdparty/spdlog/include")
target_include_directories(LibertyRecompLib PRIVATE "${REXGLUE_ROOT}/thirdparty/fmt/include")
target_include_directories(LibertyRecompLib PRIVATE "${REXGLUE_ROOT}/thirdparty/simde")
target_include_directories(LibertyRecompLib PRIVATE "${LIBERTY_RECOMP_TOOLS_ROOT}/XenonRecomp/thirdparty/simde")
target_include_directories(LibertyRecompLib PRIVATE "${CMAKE_SOURCE_DIR}/thirdparty/o1heap/.")

# Link pre-built rexglue libs so the generated PPC code can resolve
# all __imp__* kernel/XAM/Vd symbols at compile time.
if (APPLE)
    set(_rexglue_libs rexkernel rexsystem rexcore rexgraphics rexinput rexaudio rexfilesystem rexui rexcodegen)
    foreach(_lib IN LISTS _rexglue_libs)
        if (TARGET ${_lib}_prebuilt)
            target_link_libraries(LibertyRecompLib PUBLIC ${_lib}_prebuilt)
        endif()
    endforeach()
    unset(_lib)
    unset(_rexglue_libs)
endif()
