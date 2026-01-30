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

- ✅ MLX90393 3-axis magnetometer (Z-axis magnetic field measurement)
- ✅ **Raw Z-axis output only** (no force calculation on Pico)
- ✅ Smoothing filter for stable readings
- ✅ LED activity indicator (GPIO25)
- ✅ Serial output at 10Hz (115200 baud)
- ✅ Python calibration scripts for desktop/ROS2
- ✅ Real-time force visualization with `visualizer.py`

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

### Step 2: View Serial Output

Verify the sensor is working and outputting Z-axis values:

```powershell
# Find COM port
Get-WMIObject Win32_SerialPort | Select-Object Name, DeviceID

# Connect to serial (replace COM3 with your port)
python -m serial.tools.miniterm COM3 115200
```

You should see **raw Z-axis readings in millitesla (mT)**:
```
Z-axis(M1): 12.989 mT
Z-axis(M1): 12.997 mT
Z-axis(M1): 13.005 mT
```

### Step 3: Calibration (Desktop/ROS2)

**Force calculation is done on the desktop**, not on the Pico. Use the Python calibration scripts:

```powershell
cd calibration

# Install dependencies (first time only)
pip install pyserial numpy matplotlib
```

**Calibrate with known weights:**

1. Edit `calibration_pico.py` and set your COM port:
   ```python
   SERIAL_PORT = 'COM3'  # Change to your port
   ```

2. Run calibration:
   ```powershell
   python calibration_pico.py
   ```

3. Follow the prompts:
   - Place 0.1 kg weight → Press Enter
   - Place 0.5 kg weight → Press Enter
   - Place 1.0 kg weight → Press Enter
   - Type `done` to finish

4. This generates `calibration_data.json` with **slope and intercept** values:
   ```json
   {
     "slope": 51.94029384743018,
     "intercept": -692.9925307532482
   }
   ```

### Step 4: Real-Time Force Visualization

The `visualizer.py` script reads raw Z-axis values from the Pico and converts them to force in real-time:

```powershell
cd calibration

# Edit visualiser.py and set your COM port
# SERIAL_PORT = 'COM3'

python visualiser.py
```

**What it does:**
- Reads Z-axis (mT) from Pico serial output
- Applies calibration: `Force (N) = slope × Z-axis (mT) + intercept`
- Displays real-time force graph
- Shows force in Newtons (N) and kilograms (kg)

## 📊 Output Format

**Pico Serial Output (Raw Z-axis only):**
```
===========================================
  RASPBERRY PI PICO - FORCE SENSOR
===========================================
Sensor: MLX90393 Magnetometer
I2C: SDA=GPIO4, SCL=GPIO5
Mode: RAW Z-AXIS OUTPUT
===========================================

MLX90393 initialized successfully!

Starting measurements...
Format: Z-axis(M1): X.XXX mT

Z-axis(M1): 12.989 mT
Z-axis(M1): 12.997 mT
Z-axis(M1): 13.005 mT
Z-axis(M1): 18.543 mT
Z-axis(M1): 22.134 mT
```

**Python Visualizer Output (Force calculated on desktop):**
```
Reading from COM3...
Using calibration: slope=51.940, intercept=-692.993

Z-axis: 12.989 mT → Force: 0.000 N (0.000 kg)
Z-axis: 18.543 mT → Force: 0.032 N (0.003 kg)
Z-axis: 22.134 mT → Force: 0.912 N (0.093 kg)
```

## 🔧 Configuration

**Pico Firmware (`force_sensor.c`):**

```c
#define LED_PIN 25                // LED pin
#define GPIO3_VCC 3               // Optional VCC from GPIO3
#define I2C_SDA_PIN 4             // I2C SDA pin
#define I2C_SCL_PIN 5             // I2C SCL pin
#define I2C_FREQ 400000           // I2C frequency (400kHz)
#define Z_OFFSET_MT 20.0f         // Z-axis offset (keeps values positive)
#define FILTER_VAL 0.4f           // Smoothing filter (0.0-1.0)
```

**Python Scripts:**
- `calibration_pico.py` - Set `SERIAL_PORT` to your COM port
- `visualiser.py` - Set `SERIAL_PORT` and reads `calibration_data.json`

## 🛠️ Troubleshooting

### Runtime Issues

| Issue | Solution |
|-------|----------|
| "MLX90393 initialization failed" | Check I2C wiring (SDA/SCL), sensor power, I2C address |
| No Z-axis output | Verify sensor connection, check serial port (115200 baud) |
| Noisy readings | Increase `FILTER_VAL` (0.0-1.0, higher = smoother) |
| Negative Z-axis values | Normal - adjust `Z_OFFSET_MT` if needed |
| No serial output | Check USB cable, COM port, baud rate (115200) |

### Python Script Issues

| Issue | Solution |
|-------|----------|
| Can't connect to COM port | Check port in Device Manager, ensure Pico is connected |
| "calibration_data.json not found" | Run `calibration_pico.py` first to generate calibration |
| Force values incorrect | Recalibrate with accurate known weights |
| Visualizer not showing data | Verify COM port and ensure Pico is sending Z-axis data |

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

The `calibration/` folder contains Python scripts for desktop/ROS2:

| File | Description |
|------|-------------|
| `calibration_pico.py` | Calibrate sensor with known weights, generates slope/intercept |
| `visualiser.py` | Real-time force visualization, converts Z-axis to Force |
| `calibration_data.json` | Stores calibration constants (slope, intercept) |
| `README.md` | Detailed calibration instructions |

## 📐 How It Works

**System Architecture:**

```
[Force Applied] → [Magnet Moves] → [MLX90393 Sensor]
       ↓
   [Pico Firmware]
       ↓
  [Z-axis (mT)] → Serial USB → [Desktop/ROS2]
                                      ↓
                              [Python Visualizer]
                                      ↓
                            [Force (N) Calculated]
```

**Process:**

1. **Magnetic Field Detection:**
   - MLX90393 magnetometer measures magnetic field strength
   - When force is applied, magnet moves closer/farther
   - Z-axis reading (mT) changes proportionally to displacement

2. **Pico Processing:**
   - Reads sensor via I2C
   - Applies smoothing filter (`FILTER_VAL`)
   - Outputs **raw Z-axis values only** (no force calculation)
   - Sends data via USB serial at 10Hz

3. **Desktop/ROS2 Processing:**
   - Python reads Z-axis values from serial
   - Applies linear calibration formula:
     ```
     Force (N) = slope × Z-axis (mT) + intercept
     ```
   - Displays force in Newtons (N) and kilograms (kg)

**Why separate processing?**
- Pico handles fast sensor reading
- Desktop handles complex calculations and visualization
- Easier to update calibration without reflashing firmware
- Better for ROS2 integration

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
