cmake_minimum_required(VERSION 3.20)

project(SCEWIN_GUI LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

add_executable(scewin-cli
  src/cli/main.cpp
  src/core/nvram_parser.cpp
)

target_include_directories(scewin-cli PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/src
)
