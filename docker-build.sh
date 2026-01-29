#!/bin/bash
# Build script for Pico Force Sensor using Docker

# Remove old build directory
rm -rf build

# Create fresh build directory
mkdir build

# Run Docker container with Pico SDK and build the project
docker run -it --rm -v $(pwd):/home/dev lukstep/raspberry-pi-pico-sdk bash -c "cd /home/dev && cd build && cmake .. && make"

echo ""
echo "Build complete! Look for force_sensor.uf2 in the build/ directory"
echo ""
echo "To upload to Pico:"
echo "1. Hold BOOTSEL button on Pico"
echo "2. Connect USB cable"
echo "3. Release BOOTSEL"
echo "4. Copy build/force_sensor.uf2 to the Pico drive"
