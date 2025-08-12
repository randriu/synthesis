cmake_minimum_required(VERSION 3.15)

project(paynt)

set(CMAKE_CXX_STANDARD 20)

# Configuration options
set(STORM_DIR_HINT "" CACHE STRING "A hint where the Storm library can be found.")

find_package(Python 3.10 REQUIRED COMPONENTS Interpreter Development)

add_subdirectory(payntbind_src)

add_subdirectory(paynt)
