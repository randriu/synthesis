cmake_minimum_required(VERSION 3.15)

project(paynt)

set(CMAKE_CXX_STANDARD 20)

# Configuration options
set(STORM_DIR_HINT "" CACHE STRING "A hint where the Storm library can be found.")
option(ALLOW_STORM_SYSTEM "Allow finding a storm version on the system" ON)
option(ALLOW_STORM_FETCH "Allow fetching storm" ON)
set(STORM_GIT_REPO "" CACHE STRING  "Git repo used for fetching storm")
set(STORM_GIT_TAG "" CACHE STRING "Git repo tag used for fetching storm")

# Query stormpy.info to determine Storm configuration
execute_process(
    COMMAND "${Python_EXECUTABLE}" -c "import stormpy.info; print(stormpy.info.storm_from_system())"
    RESULT_VARIABLE _stormpy_result
    OUTPUT_VARIABLE STORMPY_FROM_SYSTEM
    ERROR_VARIABLE _stormpy_error
    OUTPUT_STRIP_TRAILING_WHITESPACE
)

if(NOT _stormpy_result EQUAL 0)
    message(FATAL_ERROR "PAYNT - Failed to query stormpy.info.storm_from_system(): ${_stormpy_error}")
endif()

# Configure Storm settings based on stormpy configuration
if(STORMPY_FROM_SYSTEM STREQUAL "True")
    execute_process(
        COMMAND "${Python_EXECUTABLE}" -c "import stormpy.info; print(stormpy.info.storm_directory())"
        RESULT_VARIABLE _directory_result
        OUTPUT_VARIABLE STORM_DIRECTORY_INFO
        ERROR_VARIABLE _origin_error
        OUTPUT_STRIP_TRAILING_WHITESPACE
    )

    if(NOT _directory_result EQUAL 0)
        message(FATAL_ERROR "PAYNT - Failed to query stormpy.info.storm_directory(): ${_origin_error}")
    endif()

    message(STATUS "PAYNT - StormPy uses system Storm from: ${STORM_DIRECTORY_INFO} - configuring PAYNT to use the same system Storm")

    set(STORM_DIR_HINT "${STORM_DIRECTORY_INFO}")
    set(ALLOW_STORM_SYSTEM ON)
    set(ALLOW_STORM_FETCH OFF)
else()
    message(STATUS "PAYNT - StormPy uses fetched Storm - querying Storm origin information")

    # Get Storm origin information
    execute_process(
        COMMAND "${Python_EXECUTABLE}" -c "import stormpy.info; repo, tag = stormpy.info.storm_origin_info(); print(f'{repo or \"\"};{tag or \"\"}')"
        RESULT_VARIABLE _origin_result
        OUTPUT_VARIABLE STORM_ORIGIN_INFO
        ERROR_VARIABLE _origin_error
        OUTPUT_STRIP_TRAILING_WHITESPACE
    )
    
    if(NOT _origin_result EQUAL 0)
        message(FATAL_ERROR "PAYNT - Failed to query stormpy.info.storm_origin_info(): ${_origin_error}")
    endif()
    
    # Parse repo and tag
    list(GET STORM_ORIGIN_INFO 0 STORM_ORIGIN_REPO)
    list(GET STORM_ORIGIN_INFO 1 STORM_ORIGIN_TAG)
    
    message(STATUS "PAYNT - Storm origin repo: ${STORM_ORIGIN_REPO}")
    message(STATUS "PAYNT - Storm origin tag: ${STORM_ORIGIN_TAG}")
    
    # Configure to fetch the same Storm version as stormpy
    set(ALLOW_STORM_SYSTEM OFF)
    set(ALLOW_STORM_FETCH ON)
    
    if(NOT STORM_ORIGIN_REPO STREQUAL "")
        set(STORM_GIT_REPO "${STORM_ORIGIN_REPO}")
    else()
        message(FATAL_ERROR "PAYNT - Failed to determine Storm origin repository")
    endif()
    
    if(NOT STORM_ORIGIN_TAG STREQUAL "")
        set(STORM_GIT_TAG "${STORM_ORIGIN_TAG}")
    else()
        message(FATAL_ERROR "PAYNT - Failed to determine Storm origin tag")
    endif()
    
    message(STATUS "PAYNT - Configured to fetch Storm from: ${STORM_GIT_REPO} (tag: ${STORM_GIT_TAG})")
endif()

# TODO REMOVE AFTER EVERYTHING IS TESTED
# Debug output
# message(STATUS "Final Storm configuration:")
# message(STATUS "  STORM_DIR_HINT: ${STORM_DIR_HINT}")
# message(STATUS "  ALLOW_STORM_SYSTEM: ${ALLOW_STORM_SYSTEM}")
# message(STATUS "  ALLOW_STORM_FETCH: ${ALLOW_STORM_FETCH}")
# if(DEFINED STORM_GIT_REPO AND NOT STORM_GIT_REPO STREQUAL "")
#     message(STATUS "  STORM_GIT_REPO: ${STORM_GIT_REPO}")
# endif()
# if(DEFINED STORM_GIT_TAG AND NOT STORM_GIT_TAG STREQUAL "")
#     message(STATUS "  STORM_GIT_TAG: ${STORM_GIT_TAG}")
# endif()

# return()

add_subdirectory(payntbind)
