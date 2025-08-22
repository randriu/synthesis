cmake_minimum_required(VERSION 3.15)

project(payntbind)

include(${CMAKE_CURRENT_SOURCE_DIR}/cmake/macros.cmake)

set(CMAKE_CXX_STANDARD 20)

option(STORMPY_DISABLE_SIGNATURE_DOC "Disable the signature in the documentation" OFF)
MARK_AS_ADVANCED(STORMPY_DISABLE_SIGNATURE_DOC)
set(PYBIND_VERSION "" CACHE STRING "Pybind11 version to use")
MARK_AS_ADVANCED(PYBIND_VERSION)
set(STORM_DIR_HINT "" CACHE STRING "A hint where the Storm library can be found.")
option(ALLOW_STORM_SYSTEM "Allow finding a storm version on the system" ON)
option(ALLOW_STORM_FETCH "Allow fetching storm" ON)
set(STORM_GIT_REPO "" CACHE STRING  "Git repo used for fetching storm")
set(STORM_GIT_TAG "" CACHE STRING "Git repo tag used for fetching storm")
option(COMPILE_WITH_CCACHE "Compile using CCache (if found)" ON)
mark_as_advanced(COMPILE_WITH_CCACHE)

# Check whether inputs are sane.
if (NOT ALLOW_STORM_SYSTEM AND NOT ALLOW_STORM_FETCH)
    message(FATAL_ERROR "PAYNT - Storm must be either fetched or used from system, yet ALLOW_STORM_SYSTEM=OFF and ALLOW_STORM_FETCH=OFF was set.")
endif()

if (DEFINED DISABLE_SMG)
    add_definitions(-DDISABLE_SMG)
endif()

find_package(Python COMPONENTS Interpreter Development REQUIRED)
set(PYBIND11_FINDPYTHON ON)
find_package(pybind11 CONFIG REQUIRED)
message(STATUS "PAYNT - Using pybind11 version ${pybind11_VERSION}")


function(check_hint NAME DIR_FOUND HINT_DIR FOUND_VERSION)
    # Get absolute path
    get_filename_component(PATH_FOUND ${DIR_FOUND} ABSOLUTE)
    # Print path
    if (NOT "${FOUND_VERSION}" STREQUAL "")
        message(STATUS "PAYNT - Using ${NAME} version ${FOUND_VERSION} from ${PATH_FOUND}")
    else()
        message(STATUS "PAYNT - Using ${NAME} from ${PATH_FOUND}")
    endif()

    # Check that hint was used
    if (NOT "${HINT_DIR}" STREQUAL "")
        get_filename_component(PATH_HINT ${HINT_DIR} ABSOLUTE)
        if (NOT "${PATH_FOUND}" STREQUAL "${PATH_HINT}")
            MESSAGE(SEND_ERROR "PAYNT - Using different ${NAME} directory ${PATH_FOUND} instead of given ${PATH_HINT}!")
        endif()
    endif()
endfunction(check_hint)

if(ALLOW_STORM_SYSTEM)
    set(STORM_MIN_VERSION "1.10.0")
    if (ALLOW_STORM_FETCH)
        find_package(storm HINTS ${STORM_DIR_HINT}) # NOT REQUIRED, can be fetched.
    else()
        find_package(storm REQUIRED HINTS ${STORM_DIR_HINT}) # REQUIRED, cannot be fetched.
    endif()
    check_hint("Storm" ${storm_DIR} "${STORM_DIR_HINT}" ${storm_VERSION})
    # Check Storm version
    if (${storm_VERSION} VERSION_LESS ${STORM_MIN_VERSION})
        MESSAGE(FATAL_ERROR "PAYNT - Storm version ${storm_VERSION} from ${storm_DIR} is not supported anymore!\nPAYNT requires at least Storm version >= ${STORM_MIN_VERSION}.")
    endif()

    message(WARNING "PAYNT - When using system version of Storm, it's up to the user to ensure StormPy was built against the same version!")

    # Set dependency variables
    set_dependency_var(SPOT)
    set_dependency_var(XERCES)
    # Check for optional Storm libraries
    storm_with_lib(DFT)
    storm_with_lib(GSPN)
    storm_with_lib(PARS)
    storm_with_lib(POMDP)
endif ()
if (NOT storm_FOUND AND ALLOW_STORM_FETCH)
    include(FetchContent)
    SET(FETCHCONTENT_QUIET OFF)
    SET(STORM_BUILD_EXECUTABLES OFF)
    FetchContent_Declare(
            storm
            GIT_REPOSITORY ${STORM_GIT_REPO}
            GIT_TAG        ${STORM_GIT_TAG}
    )
    FETCHCONTENT_MAKEAVAILABLE(storm)
    include(${storm_BINARY_DIR}/stormOptions.cmake)
    set(HAVE_STORM_DFT TRUE)
    set(HAVE_STORM_GSPN TRUE)
    set(HAVE_STORM_PARS TRUE)
    set(HAVE_STORM_POMDP TRUE)
    # Set dependency variables
    set_dependency_var(SPOT)
    set_dependency_var(XERCES)
endif()

set(CMAKE_LIBRARY_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/lib/payntbind")

# This sets interprocedural optimization off as this leads to some problems on some systems
set(CMAKE_INTERPROCEDURAL_OPTIMIZATION OFF)
# This sets the default visibility from hidden to default,
# which is recommended *not* to do, but leads to errors otherwise.
set(CMAKE_CXX_VISIBILITY_PRESET "default")

find_package(Boost 1.83 REQUIRED) #+

# RPATH settings (https://gitlab.kitware.com/cmake/community/-/wikis/doc/cmake/RPATH-handling#always-full-rpath)
# don't skip the full RPATH for the build tree
SET(CMAKE_SKIP_BUILD_RPATH  FALSE)
# when building, don't use the install RPATH already (but only when installing)
SET(CMAKE_BUILD_WITH_INSTALL_RPATH FALSE)
# the RPATH to be used when installing
if(APPLE)
    set(RELPOS_STRING "@loader_path")
else()
    set(RELPOS_STRING "$ORIGIN")
endif()
SET(CMAKE_INSTALL_RPATH "${RELPOS_STRING}/../../../lib/storm;${RELPOS_STRING}/../../../lib/storm/resources;${RELPOS_STRING}/../../lib/storm;${RELPOS_STRING}/../../lib/storm/resources;${RELPOS_STRING}/../lib/storm;${RELPOS_STRING}/../lib/storm/resources;${RELPOS_STRING}/lib/storm;${RELPOS_STRING}/lib/storm/resources;${RELPOS_STRING};${RELPOS_STRING}/resources;${storm_DIR}/lib")
# add the automatically determined parts of the RPATH
# which point to directories outside the build tree to the install RPATH
SET(CMAKE_INSTALL_RPATH_USE_LINK_PATH TRUE)
SET(CMAKE_BUILD_RPATH_USE_ORIGIN TRUE)

# CCache
if(COMPILE_WITH_CCACHE)
    find_program(CCACHE_FOUND ccache)
    mark_as_advanced(CCACHE_FOUND)
    if(CCACHE_FOUND)
        message(STATUS "PAYNT - Using ccache")
        set_property(GLOBAL PROPERTY RULE_LAUNCH_COMPILE ccache)
        set_property(GLOBAL PROPERTY RULE_LAUNCH_LINK ccache)
    else()
        message(STATUS "PAYNT - Could not find ccache.")
    endif()
else()
    message(STATUS "PAYNT - Disabled use of ccache.")
endif()

# Set configurations
set(STORM_VERSION ${storm_VERSION})

# Helper functions
function(build_module MOD_NAME # Module name
                      OUT_DIR OUT_NAME # Output directory and name for library
                      MOD_FILE SOURCE_PATH # Module source file and regex for all module source files
                      ADDITIONAL_INCLUDES ADDITIONAL_LIBS) # Additional include directories and libraries
    file(GLOB_RECURSE "${MOD_NAME}_SOURCES" "${CMAKE_CURRENT_SOURCE_DIR}/src/${SOURCE_PATH}")
    
    pybind11_add_module(${MOD_NAME} "${CMAKE_CURRENT_SOURCE_DIR}/src/${MOD_FILE}" ${${MOD_NAME}_SOURCES})
    target_include_directories(${MOD_NAME} PUBLIC ${CMAKE_CURRENT_SOURCE_DIR} ${CMAKE_CURRENT_BINARY_DIR}/src)
    # Parse the additional includes and libs properly
    if(ADDITIONAL_INCLUDES)
        target_include_directories(${MOD_NAME} PUBLIC ${CMAKE_CURRENT_SOURCE_DIR} ${ADDITIONAL_INCLUDES} ${CMAKE_CURRENT_BINARY_DIR}/src)
    endif()
    if(ADDITIONAL_LIBS)
        target_link_libraries(${MOD_NAME} PRIVATE ${ADDITIONAL_LIBS})
    endif()
    set_target_properties(${MOD_NAME} PROPERTIES 
        LIBRARY_OUTPUT_DIRECTORY "${CMAKE_LIBRARY_OUTPUT_DIRECTORY}/${OUT_DIR}" 
        OUTPUT_NAME "_${OUT_NAME}")
    install(TARGETS ${MOD_NAME} DESTINATION "payntbind/${OUT_DIR}")
endfunction(build_module)

function(payntbind_module MOD_NAME)
    build_module("${MOD_NAME}"
                 "${MOD_NAME}" "${MOD_NAME}"
                 "mod_${MOD_NAME}.cpp" "${MOD_NAME}/*.cpp"
                 "${storm_INCLUDE_DIR};${storm-pomdp_INCLUDE_DIR};${storm-parsers_INCLUDE_DIR};${storm-counterexamples_INCLUDE_DIR};${storm-version-info_INCLUDE_DIR}"
                 "storm;storm-pomdp;storm-parsers;storm-counterexamples;storm-version-info")
endfunction(payntbind_module)

# Generate definitions used during compilation
configure_file(${CMAKE_CURRENT_SOURCE_DIR}/src/config.h.in ${CMAKE_CURRENT_BINARY_DIR}/src/config.h)

payntbind_module(synthesis)
target_include_directories(synthesis
  PRIVATE
  src/synthesis/decpomdp/madp/base/
  src/synthesis/decpomdp/madp/include/
  src/synthesis/decpomdp/madp/parser/
)
