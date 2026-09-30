# SWAT-MODFLOW3 cmake, modeled on swat-model/swatplus (out-of-source builds, Release/Debug,
# gfortran / ifx / ifort). Sources live in src/{swat,modflow,rt3d,smrt}.
###############################################################
if("${CMAKE_SOURCE_DIR}" STREQUAL "${CMAKE_BINARY_DIR}")
   message(FATAL_ERROR "'in-source' builds not permitted, e.g. use 'cmake --preset gfortran_release_linux' instead.")
endif()

cmake_minimum_required(VERSION 3.22)

cmake_host_system_information(RESULT os_id   QUERY DISTRIB_ID)
cmake_host_system_information(RESULT os_like QUERY DISTRIB_ID_LIKE)

project(swatmf3 VERSION 3.0 LANGUAGES Fortran)

include(CTest)

if(NOT TAG)
    find_package(Git QUIET)
    if(GIT_FOUND)
        execute_process(
          COMMAND ${GIT_EXECUTABLE} describe --tags --always
          WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
          OUTPUT_VARIABLE TAG
          OUTPUT_STRIP_TRAILING_WHITESPACE
          ERROR_QUIET
        )
    endif()
    if(NOT TAG)
        set(TAG "unknown")
    endif()
endif()

# The code base is fixed-form (.f) plus some free-form (.f90). CMake picks the form from the
# extension, so no -ffixed/-ffree flag is needed. Legacy MODFLOW/SWAT code needs -std=legacy.
if(CMAKE_Fortran_COMPILER_ID MATCHES "GNU")
    set(fdialect "-std=legacy -fdec -fallow-argument-mismatch -ffixed-line-length-none -ffree-line-length-none -fbacktrace -finit-local-zero -fno-unsafe-math-optimizations -frounding-math -w")
    set(fdebug   "-g -O0 -fcheck=bounds -ffpe-trap=invalid,zero,overflow")
    set(frelease "-O2")
    set(FFC      "gnu")
    string(TOLOWER "${os_id}" os_id_lc)
    string(TOLOWER "${os_like}" os_like_lc)
    # Arch and Fedora do not ship a static libgfortran, so they get a dynamic executable
    if(NOT APPLE AND NOT ("${os_id_lc}" MATCHES "^(arch|fedora)$" OR "${os_like_lc}" MATCHES "arch"))
        link_libraries("-static")
    endif()
elseif(CMAKE_Fortran_COMPILER_ID STREQUAL "IntelLLVM")
    set(fdialect "-fpp -extend-source -fpe0 -traceback")
    set(fdebug   "-warn all,nointerfaces -O0 -check bounds")
    set(frelease "-O2")
    set(FFC      "ifx")
    if(UNIX AND NOT APPLE)
        # Intel runtime (libimf, ...) is not on user machines: link it statically
        link_libraries("-static-intel")
    endif()
elseif(CMAKE_Fortran_COMPILER_ID STREQUAL "Intel")
    set(fdialect "-fpp -extend-source -fpe0 -traceback -diag-disable=10448")
    set(fdebug   "-warn all,nointerfaces -O0 -check bounds")
    set(frelease "-O2")
    set(FFC      "ifort")
    if(UNIX AND NOT APPLE)
        # Intel runtime (libimf, ...) is not on user machines: link it statically
        link_libraries("-static-intel")
    endif()
endif()

string(TOLOWER ${CMAKE_HOST_SYSTEM_PROCESSOR} ARCH)
if(CMAKE_SYSTEM_NAME STREQUAL "Linux")
    set(AR "lin_${ARCH}")
elseif(CMAKE_SYSTEM_NAME STREQUAL "Windows")
    set(AR "win_${ARCH}")
elseif(CMAKE_SYSTEM_NAME STREQUAL "Darwin")
    set(AR "mac_${ARCH}")
else()
    set(AR "unknown")
endif()

if(CMAKE_BUILD_TYPE STREQUAL "Release")
    set(TY "-Rel")
elseif(CMAKE_BUILD_TYPE STREQUAL "Debug")
    set(TY "-Dbg")
else()
    set(TY "")
endif()

set(SWATMF_EXE "swatmf3-${TAG}-${FFC}-${AR}${TY}")

set(CMAKE_Fortran_FLAGS         "${CMAKE_Fortran_FLAGS} ${fdialect}")
set(CMAKE_Fortran_FLAGS_DEBUG   "${fdebug}")
set(CMAKE_Fortran_FLAGS_RELEASE "${frelease}")

file(GLOB sources CONFIGURE_DEPENDS
    src/swat/*.f   src/swat/*.f90
    src/modflow/*.f src/modflow/*.f90
    src/rt3d/*.f   src/rt3d/*.f90
    src/smrt/*.f   src/smrt/*.f90
)
add_executable(${SWATMF_EXE} ${sources})
# mf_openspec.inc is INCLUDEd by several MODFLOW files
target_include_directories(${SWATMF_EXE} PRIVATE src/modflow)
set_target_properties(${SWATMF_EXE} PROPERTIES
    Fortran_MODULE_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}/${SWATMF_EXE}.dir/mod"
)

install(TARGETS ${SWATMF_EXE} RUNTIME DESTINATION ${PROJECT_SOURCE_DIR}/builds)

# Regression test: runs the dataset and compares with its reference outputs.
# Uses the example model in data/MiddleBosque1000 (in git); pass
# -DSWATMF_DATASET=<dir> to use another model.
find_package(Python3 QUIET COMPONENTS Interpreter)
set(SWATMF_DATASET "${PROJECT_SOURCE_DIR}/data/MiddleBosque1000" CACHE PATH "Model folder for the regression test")
if(Python3_FOUND AND EXISTS "${SWATMF_DATASET}/file.cio")
    add_test(NAME dataset_regression
             COMMAND ${Python3_EXECUTABLE} ${PROJECT_SOURCE_DIR}/scripts/regress.py
                     $<TARGET_FILE:${SWATMF_EXE}> ${SWATMF_DATASET})
endif()

message("-- Build Type   ${CMAKE_BUILD_TYPE}")
message("-- Compiler     ${CMAKE_Fortran_COMPILER} (${CMAKE_Fortran_COMPILER_ID} ${CMAKE_Fortran_COMPILER_VERSION})")
message("-- FFLAGS       ${CMAKE_Fortran_FLAGS}")
message("--  RELEASE     ${CMAKE_Fortran_FLAGS_RELEASE}")
message("--  DEBUG       ${CMAKE_Fortran_FLAGS_DEBUG}")
message("-- Executable   ${SWATMF_EXE}")
