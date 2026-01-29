cmake_minimum_required(VERSION 3.13)

# Set Pico SDK path (adjust if needed)
# Assumes PICO_SDK_PATH is set as environment variable
if (NOT DEFINED ENV{PICO_SDK_PATH})
    set(ENV{PICO_SDK_PATH} "C:/Pico/pico-sdk")
endif()

include($ENV{PICO_SDK_PATH}/external/pico_sdk_import.cmake)

# Project name
project(pico_force_sensor C CXX ASM)

set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

# Initialize the SDK
pico_sdk_init()

# Add executable
add_executable(force_sensor
    force_sensor.c
)

# Link libraries
target_link_libraries(force_sensor
    pico_stdlib
    hardware_i2c
)

# Enable USB output, disable UART output
pico_enable_stdio_usb(force_sensor 1)
pico_enable_stdio_uart(force_sensor 0)

# Create map/bin/hex/uf2 files
pico_add_extra_outputs(force_sensor)
