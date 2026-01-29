# Build Pico Force Sensor with Docker

Write-Host "Building Pico Force Sensor with Docker..." -ForegroundColor Cyan

$currentPath = (Get-Location).Path.Replace('\', '/')

if (Test-Path "build") {
    Write-Host "Cleaning build directory..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force build
}

Write-Host "Creating build directory..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path build | Out-Null

Write-Host "Starting Docker build..." -ForegroundColor Yellow
docker run -it --rm -v "${currentPath}:/home/dev" lukstep/raspberry-pi-pico-sdk bash -c "cd /home/dev && cd build && cmake .. && make"

if (Test-Path "build\force_sensor.uf2") {
    Write-Host ""
    Write-Host "=============================================" -ForegroundColor Green
    Write-Host "Build complete!" -ForegroundColor Green
    Write-Host "File: build\force_sensor.uf2" -ForegroundColor Cyan
    Write-Host "=============================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "To upload to Pico:" -ForegroundColor Yellow
    Write-Host "1. Hold BOOTSEL button on Pico"
    Write-Host "2. Connect USB cable"
    Write-Host "3. Release BOOTSEL"
    Write-Host "4. Copy file to Pico drive"
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "Build failed! Check errors above." -ForegroundColor Red
    Write-Host ""
}
