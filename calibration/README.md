# Raspberry Pi Pico Z-Axis Calibration System

Python-based calibration system for converting MLX90393 Z-axis magnetometer readings to force measurements.

## Quick Setup

```bash
pip install pyserial numpy matplotlib
```

Update `SERIAL_PORT` in both scripts:
```python
SERIAL_PORT = 'COM3'  # Change to your Pico's port
```

## Usage

### Step 1: Calibration (5-10 minutes)

```bash
python calibration_pico.py
```

**Process:**
1. Place 0.1 kg weight → Press Enter → Collects 10 Z-axis samples
2. Place 0.5 kg weight → Press Enter → Collects 10 Z-axis samples  
3. Place 1.0 kg weight → Press Enter → Collects 10 Z-axis samples
4. Type `done` → Generates `calibration_data.json`

**Output:** Calibration constants with slope, intercept, and R² value

### Step 2: Visualize (Real-time)

```bash
python visualiser.py
```

Displays two live bar charts:
- **Left:** Z-axis reading (mT)
- **Right:** Force (Newtons and kilograms)

Press Ctrl+C or close window to stop.

## File Structure

```
calibration/
├── calibration_pico.py      # Calibration script
├── visualiser.py            # Real-time visualization
├── calibration_data.json    # Auto-generated after calibration
└── README.md                # This file
```

## Expected Serial Format

Your Pico should output:
```
Z-axis(M1): 12.693 mT
Z-axis(M2): 12.704 mT
Z-axis(M1): 12.706 mT
```

Supported variations:
- `Z-axis(M1): 12.693` ✅
- `Z-axis: 12.693` ✅
- `Z(M1): 12.693` ❌ (change `Z_AXIS_KEYWORD = "Z"`)

## Calibration Data Structure

Generated `calibration_data.json`:
```json
{
  "generated": "2026-01-26 10:45:00",
  "num_calibration_points": 3,
  "z_axis_sensor": {
    "slope": 125.847,
    "intercept": -1205.123,
    "r_squared": 0.9876,
    "formula": "Force (N) = slope * Z-axis (mT) + intercept",
    "sensor_label": "M1"
  },
  "sensor_config": {
    "z_axis_keyword": "Z-axis"
  }
}
```

## Configuration

### Change Sensor Label (M1 → M2)

Edit both scripts:
```python
Z_AXIS_KEYWORD = "Z-axis"  # Works with any label (M1, M2, etc.)
```

## Calibration Formulas

```
Force (N) = slope × Z-axis (mT) + intercept
Force (kg) = Force (N) ÷ 9.81
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Could not open serial port" | Check COM port in Device Manager |
| "No sensor data" | Verify Z_AXIS_KEYWORD matches Pico output |
| "Need at least 2 calibration points" | Enter 2+ different weights |
| Negative force values | Recalibrate with wider weight range |

## Features

✅ Flexible sensor mapping - easily change keywords  
✅ Automatic data extraction with regex parsing  
✅ Linear calibration with R² goodness-of-fit  
✅ JSON format for easy integration  
✅ Real-time auto-scaling visualization  
✅ Force clamped to ≥0 (no negative values)  

## Units

- **Z-axis:** Millitesla (mT)
- **Force:** Newtons (N) and kilograms-force (kg)
- **Conversion:** 1 kg = 9.80665 N

## Workflow

```
1. Run calibration with known weights
   └─> calibration_pico.py
       └─> calibration_data.json

2. Visualize real-time force
   └─> visualiser.py
       └─> Live plots

3. Integrate into firmware
   └─> Load slope/intercept from JSON
```

## Tips

- Use 4-5 different weights for best accuracy
- Minimum 2 calibration points required
- R² > 0.95 indicates good fit
- Re-calibrate if output format changes
- Store `calibration_data.json` in version control
