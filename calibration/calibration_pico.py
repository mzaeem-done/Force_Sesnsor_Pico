import serial
import numpy as np
import time
import os
import json
import re

# ========================================
# SENSOR MAPPING CONFIGURATION
# ========================================
# Update these if sensor labels change (e.g., M1 -> M2, or sensor names change)
Z_AXIS_KEYWORD = "Z-axis"        # Keyword to search for Z-axis data (e.g., "Z-axis(M1)")

# ========================================
# CALIBRATION CONFIGURATION
# ========================================
SERIAL_PORT = 'COM4'  # Change to your Pico's COM port
BAUD_RATE = 115200
SAMPLES_PER_WEIGHT = 10
KG_TO_NEWTONS = 9.80665

# ========================================
# HELPER FUNCTIONS
# ========================================

def extract_sensor_value(line, keyword):
    """
    Extract sensor value from serial output.
    
    Handles formats like:
    - "Current(M1): 0.013 A"
    - "Z-axis(M1): 12.693 mT"
    - "Current: 0.013 A"
    
    Returns: (value, sensor_label) or (None, None) if not found
    """
    if keyword not in line:
        return None, None
    
    try:
        # Pattern: Keyword(optional_label): value unit
        # Matches: "Current(M1): 0.013" or "Z-axis: 12.693"
        pattern = rf"{keyword}\(?([^)]*)\)?:\s*([-+]?\d+\.?\d*)"
        match = re.search(pattern, line)
        
        if match:
            sensor_label = match.group(1) if match.group(1) else keyword
            value = float(match.group(2))
            return value, sensor_label
        
        return None, None
    except (ValueError, IndexError):
        return None, None


def read_sensor_value(ser, keyword, description):
    """
    Read a single sensor value from serial.
    
    Args:
        ser: Serial connection
        keyword: Keyword to search for (e.g., "Current", "Z-axis")
        description: Human-readable description (e.g., "Current", "Z-axis")
    
    Returns: (value, sensor_label) or (None, None)
    """
    if keyword is None:
        return None, None
    
    while True:
        try:
            line = ser.readline().decode('utf-8').strip()
            if not line:
                continue
            
            value, label = extract_sensor_value(line, keyword)
            if value is not None:
                return value, label
        except (ValueError, UnicodeDecodeError, AttributeError):
            continue


def collect_samples(ser, keyword, description, num_samples):
    """
    Collect multiple sensor readings and return the average.
    
    Args:
        ser: Serial connection
        keyword: Sensor keyword to track
        description: Human-readable description
        num_samples: Number of samples to collect
    
    Returns: (average_value, sensor_label) or (None, None) if not available
    """
    if keyword is None:
        return None, None
    
    ser.reset_input_buffer()
    time.sleep(0.2)
    
    print(f"\n  Collecting {num_samples} {description} samples...")
    samples = []
    sensor_label = None
    
    for i in range(num_samples):
        value, label = read_sensor_value(ser, keyword, description)
        if value is not None:
            samples.append(value)
            sensor_label = label
            print(f"    Sample {i+1}: {description} = {value:.3f}")
            time.sleep(0.1)
        else:
            print(f"    Sample {i+1}: {description} = (skipped - no data)")
    
    if not samples:
        print(f"  ✗ No {description} samples collected!")
        return None, None
    
    avg = np.mean(samples)
    std = np.std(samples)
    print(f"\n  Average {description}: {avg:.3f} ± {std:.3f}")
    return avg, sensor_label


# ========================================
# MAIN CALIBRATION LOGIC
# ========================================

def main():
    print("=" * 70)
    print("RASPBERRY PI PICO SENSOR CALIBRATION")
    print("=" * 70)
    
    # Show configuration
    print("\nSensor Configuration:")
    print(f"  Z-axis sensor: ENABLED")
    print(f"    Keyword: {Z_AXIS_KEYWORD}")
    
    print(f"\nConnecting to Pico on {SERIAL_PORT}...")
    
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(2)
        ser.reset_input_buffer()
        print("✓ Connected!\n")
    except serial.SerialException as e:
        print(f"✗ Error: Could not open serial port {SERIAL_PORT}")
        print(f"  {e}")
        return
    
    weights_kg = []
    z_axis_readings = []
    z_axis_labels = []
    
    print("CALIBRATION INSTRUCTIONS:")
    print("=" * 70)
    print("1. Place a known weight on the sensor")
    print("2. Enter the weight in kilograms")
    print("3. Press Enter to collect samples")
    print("4. Type 'done' when finished\n")
    
    calibration_point = 1
    
    while True:
        print(f"\n[Calibration Point {calibration_point}]")
        weight_input = input("Enter weight in kg (or 'done' to finish): ").strip()
        
        if weight_input.lower() == 'done':
            break
        
        try:
            weight_kg = float(weight_input)
            force_newtons = weight_kg * KG_TO_NEWTONS
            
            print(f"  Weight: {weight_kg} kg = {force_newtons:.2f} N")
            
            # Collect Z-axis data
            z_axis_avg, z_axis_label = collect_samples(
                ser, Z_AXIS_KEYWORD, "Z-axis", SAMPLES_PER_WEIGHT
            )
            
            # Store calibration point
            weights_kg.append(weight_kg)
            z_axis_readings.append(z_axis_avg)
            z_axis_labels.append(z_axis_label)
            
            calibration_point += 1
            
        except ValueError:
            print("✗ Invalid input. Please enter a number or 'done'.")
    
    ser.close()
    
    if len(weights_kg) < 2:
        print("\n✗ Error: Need at least 2 calibration points.")
        return
    
    # Convert to numpy arrays
    weights_kg = np.array(weights_kg)
    forces_newtons = weights_kg * KG_TO_NEWTONS
    
    # ========================================
    # Z-AXIS SENSOR CALIBRATION
    # ========================================
    z_axis_calib = None
    if any(x is not None for x in z_axis_readings):
        z_axis_readings_clean = np.array([x for x in z_axis_readings if x is not None])
        
        if len(z_axis_readings_clean) >= 2:
            # Linear fit: Force = slope * Z_axis + intercept
            slope_z, intercept_z = np.polyfit(z_axis_readings_clean,
                                              forces_newtons[:len(z_axis_readings_clean)], 1)
            
            predicted = slope_z * z_axis_readings_clean + intercept_z
            residuals = forces_newtons[:len(z_axis_readings_clean)] - predicted
            ss_res = np.sum(residuals**2)
            ss_tot = np.sum((forces_newtons[:len(z_axis_readings_clean)] - 
                           np.mean(forces_newtons[:len(z_axis_readings_clean)]))**2)
            r_squared_z = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
            
            z_axis_calib = {
                "slope": float(slope_z),
                "intercept": float(intercept_z),
                "r_squared": float(r_squared_z),
                "formula": "Force (N) = slope * Z-axis (mT) + intercept",
                "sensor_label": z_axis_labels[0] if z_axis_labels[0] else Z_AXIS_KEYWORD
            }
            
            print("\n" + "=" * 70)
            print("Z-AXIS SENSOR CALIBRATION RESULTS")
            print("=" * 70)
            print(f"Formula: Force (N) = {slope_z:.6f} * Z-axis (mT) + {intercept_z:.6f}")
            print(f"Slope:     {slope_z:.6f}")
            print(f"Intercept: {intercept_z:.6f}")
            print(f"R² value:  {r_squared_z:.6f}")
    
    # ========================================
    # SAVE CALIBRATION DATA TO JSON
    # ========================================
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_file = os.path.join(script_dir, 'calibration_data.json')
    
    calibration_data = {
        "generated": time.strftime('%Y-%m-%d %H:%M:%S'),
        "num_calibration_points": len(weights_kg),
        "z_axis_sensor": z_axis_calib,
        "sensor_config": {
            "z_axis_keyword": Z_AXIS_KEYWORD
        }
    }
    
    with open(json_file, 'w') as f:
        json.dump(calibration_data, f, indent=2)
    
    print(f"\n✓ Calibration saved to '{json_file}'")
    
    # ========================================
    # PRINT CALIBRATION TABLE
    # ========================================
    print("\n" + "=" * 70)
    print("CALIBRATION DATA TABLE")
    print("=" * 70)
    print(f"{'Weight (kg)':<15} {'Force (N)':<15} {'Z-axis (mT)':<15}")
    print("-" * 70)
    
    for i in range(len(weights_kg)):
        z_val = z_axis_readings[i] if i < len(z_axis_readings) and z_axis_readings[i] is not None else None
        z_str = f"{z_val:.3f}" if z_val is not None else "N/A"
        print(f"{weights_kg[i]:<15.3f} {forces_newtons[i]:<15.3f} {z_str:<15}")
    
    print("=" * 70)


if __name__ == "__main__":
    main()
