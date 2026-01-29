# Raspberry Pi Pico - Force Sensor Project

Magnetic force sensing system using MLX90393 3-axis magnetometer with calibration support.

## 📋 Hardware Requirements

- **Raspberry Pi Pico** (RP2040)
- **MLX90393** magnetometer module (I2C)
- USB cable for power and serial communication
- Known weights for calibration (e.g., 0.1kg, 0.5kg, 1.0kg)

## 🔌 Wiring

| MLX90393 Pin | Pico Pin | Description |
|--------------|----------|-------------|
| VCC | 3.3V (or GPIO3*) | Power supply |
| GND | GND | Ground |
| SDA | GPIO4 | I2C Data |
| SCL | GPIO5 | I2C Clock |

**Note:** GPIO3 can optionally be used as VCC (configured in code)

## ⚙️ Features

- ✅ MLX90393 3-axis magnetometer (Z-axis used for force)
- ✅ Built-in calibration constants
- ✅ Real-time force calculation (Newtons & kilograms)
- ✅ Smoothing filter for stable readings
- ✅ LED activity indicator (GPIO25)
- ✅ Serial output at 10Hz (115200 baud)
- ✅ Python calibration scripts included

## 🚀 Quick Start

### Build with Docker

**Prerequisites:**
- ✅ Docker Desktop installed and running
- ✅ Docker image: `lukstep/raspberry-pi-pico-sdk`

**Build Steps:**

```powershell
# Navigate to project folder
cd C:\Users\done\OneDrive\Desktop\pico_force_sensor

# Build using Docker
.\docker-build.ps1
```

The script will:
- Clean and create build directory
- Run Docker container with Pico SDK
- Compile and generate `force_sensor.uf2`
- Display upload instructions

### Step 1: Upload Firmware to Pico

After building (either method), you'll have `build\force_sensor.uf2`:

```powershell
# 1. Hold BOOTSEL button on Pico
# 2. Connect USB cable
# 3. Release BOOTSEL (Pico appears as USB drive)

# Find Pico drive
Get-Volume | Where-Object {$_.FileSystemLabel -eq "RPI-RP2"}

# Copy firmware (replace D: with your drive letter)
Copy-Item build\force_sensor.uf2 D:\
```

Pico will automatically reboot and start running the force sensor code!

### Step 2: Initial Test (Without Calibration)

View serial output to verify sensor works:
```bash
python -m serial.tools.miniterm COM3 115200
```

You should see Z-axis readings in millitesla (mT).

### Step 3: Calibration (IMPORTANT!)

The firmware has default calibration values. For accurate force measurements, **you must calibrate**:

```bash
cd calibration

# Install dependencies (first time only)
pip install pyserial numpy matplotlib

# Update COM port in calibration_pico.py
# Change: SERIAL_PORT = 'COM3'

# Run calibration
python calibration_pico.py
```

**Calibration Process:**
1. Place 0.1 kg weight → Press Enter
2. Place 0.5 kg weight → Press Enter
3. Place 1.0 kg weight → Press Enter
4. Type `done`

This generates `calibration_data.json` with slope and intercept values.

### Step 4: Update Firmware with Calibration

1. Open `force_sensor.c`
2. Update these lines (around line 28-29):
```c
#define CALIBRATION_SLOPE 51.94029384743018f      // Replace with your value
#define CALIBRATION_INTERCEPT -692.9925307532482f  // Replace with your value
```
3. Rebuild and upload firmware:

**Using Docker (recommended):**
```powershell
.\docker-build.ps1
# Then upload the new .uf2 file to Pico
```

**Using native build:**
```powershell
cd build
cmake --build .
# Then upload the new .uf2 file to Pico
```

### Step 5: Visualize (Optional)

Real-time force visualization:
```bash
cd calibration
python visualiser.py
```

## 📊 Output Format

**After calibration:**
```
===========================================
  RASPBERRY PI PICO - FORCE SENSOR
===========================================
Sensor: MLX90393 Magnetometer
I2C: SDA=GPIO4, SCL=GPIO5
Calibration: ACTIVE
  Slope: 51.940294
  Intercept: -692.992531
===========================================

MLX90393 initialized successfully!

Starting measurements...
Format: Z-axis(M1): X.XXX mT | Force: X.XXX N (X.XXX kg)

Z-axis(M1): 18.543 mT | Force: 0.032 N (0.003 kg)
Z-axis(M1): 18.548 mT | Force: 0.037 N (0.004 kg)
Z-axis(M1): 22.134 mT | Force: 0.912 N (0.093 kg)
```

## 🔧 Configuration

Edit `force_sensor.c` to customize:

```c
#define LED_PIN 25                // LED pin
#define GPIO3_VCC 3               // Optional VCC from GPIO3
#define I2C_SDA_PIN 4             // I2C SDA pin
#define I2C_SCL_PIN 5             // I2C SCL pin
#define I2C_FREQ 400000           // I2C frequency (400kHz)
#define CALIBRATION_SLOPE ...     // From calibration
#define CALIBRATION_INTERCEPT ... // From calibration
#define Z_OFFSET_MT 20.0f         // Z-axis offset
#define FILTER_VAL 0.4f           // Smoothing filter
```

## 🛠️ Troubleshooting

### Runtime Issues

| Issue | Solution |
|-------|----------|
| "MLX90393 initialization failed" | Check I2C wiring (SDA/SCL), sensor power, I2C address |
| Incorrect force readings | Run calibration with known weights |
| Noisy readings | Increase `FILTER_VAL` (0.0-1.0, higher = smoother) |
| Negative force values | Recalibrate or adjust `Z_OFFSET_MT` |
| No serial output | Check USB cable, COM port, baud rate (115200) |

### Build Issues

| Issue | Solution |
|-------|----------|
| Docker build fails | Ensure Docker Desktop is running: `docker ps` |
| "Cannot find Docker image" | Pull image: `docker pull lukstep/raspberry-pi-pico-sdk` |
| Permission errors (Docker) | Run PowerShell as Administrator |
| Build takes too long | First build downloads SDK, subsequent builds are faster |

### Upload Issues

| Issue | Solution |
|-------|----------|
| Pico not appearing as drive | Hold BOOTSEL before connecting USB, ensure cable supports data |
| "Access denied" when copying | Eject and reconnect Pico in BOOTSEL mode |
| Wrong drive letter | Use `Get-Volume \| Where-Object {$_.FileSystemLabel -eq "RPI-RP2"}` |

## 📝 Calibration Files

The `calibration/` folder contains:

| File | Description |
|------|-------------|
| `calibration_pico.py` | Run calibration with known weights |
| `visualiser.py` | Real-time force visualization |
| `calibration_data.json` | Generated calibration constants |
| `README.md` | Detailed calibration instructions |

## 📐 How It Works

1. **Magnetic sensor** detects magnet displacement when force is applied
2. **Z-axis reading** (mT) changes proportionally to force
3. **Linear calibration** converts mT to Newtons:
   ```
   Force (N) = slope × Z-axis (mT) + intercept
   ```
4. **Smoothing filter** reduces noise for stable readings

## 🔗 Related Projects

- **pico_current_sensor** - ACS712 current monitoring system

## 📚 MLX90393 Information

- **Type:** 3-axis magnetometer
- **Interface:** I2C (address 0x0C)
- **Resolution:** 16-bit (configurable)
- **Measurement Range:** ±50mT (configurable gain)
- **Datasheet:** [Melexis MLX90393](https://www.melexis.com/en/product/MLX90393)

## ⚡ Quick Reference

### Common Commands

```powershell
# Build with Docker
.\docker-build.ps1

# Upload to Pico
Copy-Item build\force_sensor.uf2 D:\    # Replace D: with your Pico drive

# Find Pico drive letter
Get-Volume | Where-Object {$_.FileSystemLabel -eq "RPI-RP2"}

# View serial output (find COM port first)
Get-WMIObject Win32_SerialPort | Select-Object Name, DeviceID
python -m serial.tools.miniterm COM3 115200    # Replace COM3

# Run calibration
cd calibration
python calibration_pico.py

# Visualize real-time data
cd calibration
python visualiser.py

# Check Docker image
docker images | Select-String "raspberry-pi-pico"

# Pull Docker image (if missing)
docker pull lukstep/raspberry-pi-pico-sdk
```

### Project Files

- `force_sensor.c` - Main firmware code
- `CMakeLists.txt` - Build configuration
- `docker-build.ps1` - Docker build script (Windows)
- `docker-build.sh` - Docker build script (Linux/Mac)
- `calibration/` - Calibration scripts and tools
- `build/force_sensor.uf2` - Generated firmware (after build)

## 📄 License

This project is provided as-is for educational and development purposes.
