cmake_minimum_required(VERSION 3.20)
project(sdrmon_native VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Warnings
if(MSVC)
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /W3")
else()
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Wextra -Wpedantic")
endif()

find_package(pybind11 CONFIG REQUIRED)

add_library(sdrmon_core_obj OBJECT
    src/core/manager.cpp
    src/backends/fake_backend.cpp
    src/backends/rtl_sdr/rtl_sdr_loader.cpp
    src/backends/rtl_sdr/rtl_sdr_device.cpp
    src/backends/rtl_sdr/rtl_sdr_backend.cpp
)

target_include_directories(sdrmon_core_obj PUBLIC 
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
)

# Pybind11 module
pybind11_add_module(sdrmon_native bindings/module.cpp)
target_link_libraries(sdrmon_native PRIVATE sdrmon_core_obj)
install(TARGETS sdrmon_native DESTINATION .)

# CTest
option(BUILD_TESTING "Build tests" OFF)
include(CTest)
if(BUILD_TESTING)
    # We can use Catch2 or GoogleTest. FetchContent Catch2 for ease.
    include(FetchContent)
    FetchContent_Declare(
      Catch2
      GIT_REPOSITORY https://github.com/catchorg/Catch2.git
      GIT_TAG        v3.4.0
    )
    FetchContent_MakeAvailable(Catch2)

    add_executable(sdrmon_tests
        tests/test_manager.cpp
        tests/test_stream.cpp
        tests/test_ring_buffer.cpp
        tests/test_fake_backend.cpp
    )
    target_link_libraries(sdrmon_tests PRIVATE sdrmon_core_obj Catch2::Catch2WithMain)
    
    # Catch2 requires linking with threads
    find_package(Threads REQUIRED)
    target_link_libraries(sdrmon_tests PRIVATE Threads::Threads)
    
    add_test(NAME sdrmon_tests COMMAND sdrmon_tests)
endif()
