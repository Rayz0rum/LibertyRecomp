# Install script for directory: /Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2

# Set the install prefix
if(NOT DEFINED CMAKE_INSTALL_PREFIX)
  set(CMAKE_INSTALL_PREFIX "/usr/local")
endif()
string(REGEX REPLACE "/$" "" CMAKE_INSTALL_PREFIX "${CMAKE_INSTALL_PREFIX}")

# Set the install configuration name.
if(NOT DEFINED CMAKE_INSTALL_CONFIG_NAME)
  if(BUILD_TYPE)
    string(REGEX REPLACE "^[^A-Za-z0-9_]+" ""
           CMAKE_INSTALL_CONFIG_NAME "${BUILD_TYPE}")
  else()
    set(CMAKE_INSTALL_CONFIG_NAME "Release")
  endif()
  message(STATUS "Install configuration: \"${CMAKE_INSTALL_CONFIG_NAME}\"")
endif()

# Set the component getting installed.
if(NOT CMAKE_INSTALL_COMPONENT)
  if(COMPONENT)
    message(STATUS "Install component: \"${COMPONENT}\"")
    set(CMAKE_INSTALL_COMPONENT "${COMPONENT}")
  else()
    set(CMAKE_INSTALL_COMPONENT)
  endif()
endif()

# Is this installation the result of a crosscompile?
if(NOT DEFINED CMAKE_CROSSCOMPILING)
  set(CMAKE_CROSSCOMPILING "FALSE")
endif()

# Set path to fallback-tool for dependency-resolution.
if(NOT DEFINED CMAKE_OBJDUMP)
  set(CMAKE_OBJDUMP "/opt/homebrew/opt/llvm/bin/llvm-objdump")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib" TYPE STATIC_LIBRARY FILES "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/out/macos-arm64/libSDL2main.a")
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libSDL2main.a" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libSDL2main.a")
    execute_process(COMMAND "/opt/homebrew/opt/llvm/bin/llvm-ranlib" "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libSDL2main.a")
  endif()
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib" TYPE STATIC_LIBRARY FILES "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/out/macos-arm64/libSDL2.a")
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libSDL2.a" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libSDL2.a")
    execute_process(COMMAND "/opt/homebrew/opt/llvm/bin/llvm-ranlib" "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libSDL2.a")
  endif()
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/cmake/SDL2/SDL2mainTargets.cmake")
    file(DIFFERENT _cmake_export_file_changed FILES
         "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/cmake/SDL2/SDL2mainTargets.cmake"
         "/Users/Ozordi/Downloads/LibertyRecomp/build-codegen/thirdparty/sdl2/CMakeFiles/Export/f084604df1a27ef5b4fef7c7544737d1/SDL2mainTargets.cmake")
    if(_cmake_export_file_changed)
      file(GLOB _cmake_old_config_files "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/cmake/SDL2/SDL2mainTargets-*.cmake")
      if(_cmake_old_config_files)
        string(REPLACE ";" ", " _cmake_old_config_files_text "${_cmake_old_config_files}")
        message(STATUS "Old export file \"$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/cmake/SDL2/SDL2mainTargets.cmake\" will be replaced.  Removing files [${_cmake_old_config_files_text}].")
        unset(_cmake_old_config_files_text)
        file(REMOVE ${_cmake_old_config_files})
      endif()
      unset(_cmake_old_config_files)
    endif()
    unset(_cmake_export_file_changed)
  endif()
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/cmake/SDL2" TYPE FILE FILES "/Users/Ozordi/Downloads/LibertyRecomp/build-codegen/thirdparty/sdl2/CMakeFiles/Export/f084604df1a27ef5b4fef7c7544737d1/SDL2mainTargets.cmake")
  if(CMAKE_INSTALL_CONFIG_NAME MATCHES "^([Rr][Ee][Ll][Ee][Aa][Ss][Ee])$")
    file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/cmake/SDL2" TYPE FILE FILES "/Users/Ozordi/Downloads/LibertyRecomp/build-codegen/thirdparty/sdl2/CMakeFiles/Export/f084604df1a27ef5b4fef7c7544737d1/SDL2mainTargets-release.cmake")
  endif()
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/cmake/SDL2/SDL2staticTargets.cmake")
    file(DIFFERENT _cmake_export_file_changed FILES
         "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/cmake/SDL2/SDL2staticTargets.cmake"
         "/Users/Ozordi/Downloads/LibertyRecomp/build-codegen/thirdparty/sdl2/CMakeFiles/Export/f084604df1a27ef5b4fef7c7544737d1/SDL2staticTargets.cmake")
    if(_cmake_export_file_changed)
      file(GLOB _cmake_old_config_files "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/cmake/SDL2/SDL2staticTargets-*.cmake")
      if(_cmake_old_config_files)
        string(REPLACE ";" ", " _cmake_old_config_files_text "${_cmake_old_config_files}")
        message(STATUS "Old export file \"$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/cmake/SDL2/SDL2staticTargets.cmake\" will be replaced.  Removing files [${_cmake_old_config_files_text}].")
        unset(_cmake_old_config_files_text)
        file(REMOVE ${_cmake_old_config_files})
      endif()
      unset(_cmake_old_config_files)
    endif()
    unset(_cmake_export_file_changed)
  endif()
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/cmake/SDL2" TYPE FILE FILES "/Users/Ozordi/Downloads/LibertyRecomp/build-codegen/thirdparty/sdl2/CMakeFiles/Export/f084604df1a27ef5b4fef7c7544737d1/SDL2staticTargets.cmake")
  if(CMAKE_INSTALL_CONFIG_NAME MATCHES "^([Rr][Ee][Ll][Ee][Aa][Ss][Ee])$")
    file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/cmake/SDL2" TYPE FILE FILES "/Users/Ozordi/Downloads/LibertyRecomp/build-codegen/thirdparty/sdl2/CMakeFiles/Export/f084604df1a27ef5b4fef7c7544737d1/SDL2staticTargets-release.cmake")
  endif()
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Devel" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/cmake/SDL2" TYPE FILE FILES
    "/Users/Ozordi/Downloads/LibertyRecomp/build-codegen/thirdparty/sdl2/SDL2Config.cmake"
    "/Users/Ozordi/Downloads/LibertyRecomp/build-codegen/thirdparty/sdl2/SDL2ConfigVersion.cmake"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/cmake/sdlfind.cmake"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/SDL2" TYPE FILE FILES
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_assert.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_atomic.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_audio.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_bits.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_blendmode.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_clipboard.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_copying.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_cpuinfo.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_egl.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_endian.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_error.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_events.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_filesystem.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_gamecontroller.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_gesture.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_guid.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_haptic.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_hidapi.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_hints.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_joystick.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_keyboard.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_keycode.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_loadso.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_locale.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_log.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_main.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_messagebox.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_metal.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_misc.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_mouse.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_mutex.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_name.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_opengl.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_opengl_glext.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_opengles.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_opengles2.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_opengles2_gl2.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_opengles2_gl2ext.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_opengles2_gl2platform.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_opengles2_khrplatform.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_pixels.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_platform.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_power.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_quit.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_rect.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_render.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_rwops.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_scancode.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_sensor.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_shape.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_stdinc.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_surface.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_system.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_syswm.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_test.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_test_assert.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_test_common.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_test_compare.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_test_crc32.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_test_font.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_test_fuzzer.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_test_harness.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_test_images.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_test_log.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_test_md5.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_test_memory.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_test_random.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_thread.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_timer.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_touch.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_types.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_version.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_video.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/SDL_vulkan.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/begin_code.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/include/close_code.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/build-codegen/thirdparty/sdl2/include/SDL2/SDL_revision.h"
    "/Users/Ozordi/Downloads/LibertyRecomp/build-codegen/thirdparty/sdl2/include-config-release/SDL2/SDL_config.h"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/licenses/SDL2" TYPE FILE FILES "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/LICENSE.txt")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/pkgconfig" TYPE FILE FILES "/Users/Ozordi/Downloads/LibertyRecomp/build-codegen/thirdparty/sdl2/sdl2.pc")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/bin" TYPE PROGRAM FILES "/Users/Ozordi/Downloads/LibertyRecomp/build-codegen/thirdparty/sdl2/sdl2-config")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/aclocal" TYPE FILE FILES "/Users/Ozordi/Downloads/LibertyRecomp/glue/rexglue-sdk-main/thirdparty/sdl2/sdl2.m4")
endif()

string(REPLACE ";" "\n" CMAKE_INSTALL_MANIFEST_CONTENT
       "${CMAKE_INSTALL_MANIFEST_FILES}")
if(CMAKE_INSTALL_LOCAL_ONLY)
  file(WRITE "/Users/Ozordi/Downloads/LibertyRecomp/build-codegen/thirdparty/sdl2/install_local_manifest.txt"
     "${CMAKE_INSTALL_MANIFEST_CONTENT}")
endif()
