cmake_minimum_required(VERSION 3.15)

project(paynt)

set(CMAKE_CXX_STANDARD 20)

find_package(Python 3.10 REQUIRED COMPONENTS Interpreter Development)

add_subdirectory(payntbind)

add_subdirectory(paynt)
