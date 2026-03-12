# rexaudio - Audio subsystem library
# Audio processing and XMA decoding for Xbox 360 emulation

set(REXAUDIO_SOURCES
    audio_driver.cpp
    audio_system.cpp
    xma_register_file.cpp
    # NOP backend (always available)
    nop/nop_audio_system.cpp
    # SDL backend
    sdl/sdl_audio_system.cpp
    sdl/sdl_audio_driver.cpp
)

if(NOT APPLE)
    # XMA decoding requires FFmpeg (libavcodec/libavutil)
    list(APPEND REXAUDIO_SOURCES xma_context.cpp xma_decoder.cpp)
endif()

add_library(rexaudio STATIC ${REXAUDIO_SOURCES})
add_library(rex::audio ALIAS rexaudio)

target_include_directories(rexaudio PUBLIC
    $<BUILD_INTERFACE:${PROJECT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}>
)

target_link_libraries(rexaudio
    PUBLIC rexcore SDL2::SDL2
)

if(NOT APPLE)
    target_link_libraries(rexaudio PRIVATE libavcodec libavutil)
else()
    target_compile_definitions(rexaudio PRIVATE REX_NO_XMA_DECODER=1)
endif()
