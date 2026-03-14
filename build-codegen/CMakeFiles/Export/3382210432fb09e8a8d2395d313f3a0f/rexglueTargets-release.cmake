#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "rex::core" for configuration "Release"
set_property(TARGET rex::core APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(rex::core PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "CXX"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/librexcore.a"
  )

list(APPEND _cmake_import_check_targets rex::core )
list(APPEND _cmake_import_check_files_for_rex::core "${_IMPORT_PREFIX}/lib/librexcore.a" )

# Import target "rex::filesystem" for configuration "Release"
set_property(TARGET rex::filesystem APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(rex::filesystem PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "CXX"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/librexfilesystem.a"
  )

list(APPEND _cmake_import_check_targets rex::filesystem )
list(APPEND _cmake_import_check_files_for_rex::filesystem "${_IMPORT_PREFIX}/lib/librexfilesystem.a" )

# Import target "rex::ui" for configuration "Release"
set_property(TARGET rex::ui APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(rex::ui PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "CXX"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/librexui.a"
  )

list(APPEND _cmake_import_check_targets rex::ui )
list(APPEND _cmake_import_check_files_for_rex::ui "${_IMPORT_PREFIX}/lib/librexui.a" )

# Import target "rex::input" for configuration "Release"
set_property(TARGET rex::input APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(rex::input PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "CXX"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/librexinput.a"
  )

list(APPEND _cmake_import_check_targets rex::input )
list(APPEND _cmake_import_check_files_for_rex::input "${_IMPORT_PREFIX}/lib/librexinput.a" )

# Import target "rex::audio" for configuration "Release"
set_property(TARGET rex::audio APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(rex::audio PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "CXX"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/librexaudio.a"
  )

list(APPEND _cmake_import_check_targets rex::audio )
list(APPEND _cmake_import_check_files_for_rex::audio "${_IMPORT_PREFIX}/lib/librexaudio.a" )

# Import target "rex::graphics" for configuration "Release"
set_property(TARGET rex::graphics APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(rex::graphics PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "CXX"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/librexgraphics.a"
  )

list(APPEND _cmake_import_check_targets rex::graphics )
list(APPEND _cmake_import_check_files_for_rex::graphics "${_IMPORT_PREFIX}/lib/librexgraphics.a" )

# Import target "rex::system" for configuration "Release"
set_property(TARGET rex::system APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(rex::system PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "CXX"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/librexsystem.a"
  )

list(APPEND _cmake_import_check_targets rex::system )
list(APPEND _cmake_import_check_files_for_rex::system "${_IMPORT_PREFIX}/lib/librexsystem.a" )

# Import target "rex::kernel" for configuration "Release"
set_property(TARGET rex::kernel APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(rex::kernel PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "CXX"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/librexkernel.a"
  )

list(APPEND _cmake_import_check_targets rex::kernel )
list(APPEND _cmake_import_check_files_for_rex::kernel "${_IMPORT_PREFIX}/lib/librexkernel.a" )

# Import target "rex::codegen" for configuration "Release"
set_property(TARGET rex::codegen APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(rex::codegen PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "CXX"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/librexcodegen.a"
  )

list(APPEND _cmake_import_check_targets rex::codegen )
list(APPEND _cmake_import_check_files_for_rex::codegen "${_IMPORT_PREFIX}/lib/librexcodegen.a" )

# Import target "rex::aes128" for configuration "Release"
set_property(TARGET rex::aes128 APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(rex::aes128 PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "C"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libaes128.a"
  )

list(APPEND _cmake_import_check_targets rex::aes128 )
list(APPEND _cmake_import_check_files_for_rex::aes128 "${_IMPORT_PREFIX}/lib/libaes128.a" )

# Import target "rex::mspack" for configuration "Release"
set_property(TARGET rex::mspack APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(rex::mspack PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "C"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libmspack.a"
  )

list(APPEND _cmake_import_check_targets rex::mspack )
list(APPEND _cmake_import_check_files_for_rex::mspack "${_IMPORT_PREFIX}/lib/libmspack.a" )

# Import target "rex::disasm" for configuration "Release"
set_property(TARGET rex::disasm APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(rex::disasm PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "C"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libdisasm.a"
  )

list(APPEND _cmake_import_check_targets rex::disasm )
list(APPEND _cmake_import_check_files_for_rex::disasm "${_IMPORT_PREFIX}/lib/libdisasm.a" )

# Import target "rex::xxhash" for configuration "Release"
set_property(TARGET rex::xxhash APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(rex::xxhash PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "C"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libxxhash.a"
  )

list(APPEND _cmake_import_check_targets rex::xxhash )
list(APPEND _cmake_import_check_files_for_rex::xxhash "${_IMPORT_PREFIX}/lib/libxxhash.a" )

# Import target "rex::imgui" for configuration "Release"
set_property(TARGET rex::imgui APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(rex::imgui PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "CXX"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libimgui.a"
  )

list(APPEND _cmake_import_check_targets rex::imgui )
list(APPEND _cmake_import_check_files_for_rex::imgui "${_IMPORT_PREFIX}/lib/libimgui.a" )

# Import target "rex::rexglue" for configuration "Release"
set_property(TARGET rex::rexglue APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(rex::rexglue PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/bin/rexglue"
  )

list(APPEND _cmake_import_check_targets rex::rexglue )
list(APPEND _cmake_import_check_files_for_rex::rexglue "${_IMPORT_PREFIX}/bin/rexglue" )

# Import target "rex::SPIRV" for configuration "Release"
set_property(TARGET rex::SPIRV APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(rex::SPIRV PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "CXX"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libSPIRV.a"
  )

list(APPEND _cmake_import_check_targets rex::SPIRV )
list(APPEND _cmake_import_check_files_for_rex::SPIRV "${_IMPORT_PREFIX}/lib/libSPIRV.a" )

# Import target "rex::glslang" for configuration "Release"
set_property(TARGET rex::glslang APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(rex::glslang PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "CXX"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libglslang.a"
  )

list(APPEND _cmake_import_check_targets rex::glslang )
list(APPEND _cmake_import_check_files_for_rex::glslang "${_IMPORT_PREFIX}/lib/libglslang.a" )

# Import target "rex::MachineIndependent" for configuration "Release"
set_property(TARGET rex::MachineIndependent APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(rex::MachineIndependent PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "CXX"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libMachineIndependent.a"
  )

list(APPEND _cmake_import_check_targets rex::MachineIndependent )
list(APPEND _cmake_import_check_files_for_rex::MachineIndependent "${_IMPORT_PREFIX}/lib/libMachineIndependent.a" )

# Import target "rex::GenericCodeGen" for configuration "Release"
set_property(TARGET rex::GenericCodeGen APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(rex::GenericCodeGen PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "CXX"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libGenericCodeGen.a"
  )

list(APPEND _cmake_import_check_targets rex::GenericCodeGen )
list(APPEND _cmake_import_check_files_for_rex::GenericCodeGen "${_IMPORT_PREFIX}/lib/libGenericCodeGen.a" )

# Import target "rex::OSDependent" for configuration "Release"
set_property(TARGET rex::OSDependent APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(rex::OSDependent PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "CXX"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libOSDependent.a"
  )

list(APPEND _cmake_import_check_targets rex::OSDependent )
list(APPEND _cmake_import_check_files_for_rex::OSDependent "${_IMPORT_PREFIX}/lib/libOSDependent.a" )

# Import target "rex::OGLCompiler" for configuration "Release"
set_property(TARGET rex::OGLCompiler APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(rex::OGLCompiler PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "CXX"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libOGLCompiler.a"
  )

list(APPEND _cmake_import_check_targets rex::OGLCompiler )
list(APPEND _cmake_import_check_files_for_rex::OGLCompiler "${_IMPORT_PREFIX}/lib/libOGLCompiler.a" )

# Import target "rex::SPIRV-Tools-static" for configuration "Release"
set_property(TARGET rex::SPIRV-Tools-static APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(rex::SPIRV-Tools-static PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "CXX"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libSPIRV-Tools.a"
  )

list(APPEND _cmake_import_check_targets rex::SPIRV-Tools-static )
list(APPEND _cmake_import_check_files_for_rex::SPIRV-Tools-static "${_IMPORT_PREFIX}/lib/libSPIRV-Tools.a" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
