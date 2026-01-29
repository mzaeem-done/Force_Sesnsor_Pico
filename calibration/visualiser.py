

import serial
import time
import os
import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import re

# ========================================
# SENSOR MAPPING CONFIGURATION
# ========================================
# These should match what you used in calibration_pico.py
Z_AXIS_KEYWORD = "Z-axis"        # Keyword for Z-axis sensor

# Serial configuration
SERIAL_PORT = 'COM4'  # Change to your Pico's COM port
BAUD_RATE = 115200

# Get script directory for calibration file
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CALIBRATION_FILE = os.path.join(SCRIPT_DIR, 'calibration_data.json')

# ========================================
# HELPER FUNCTIONS
# ========================================

def extract_sensor_value(line, keyword):
    """
    Extract sensor value from serial output.
    
    Handles formats like:
    - "Current(M1): 0.013 A"
    - "Z-axis(M1): 12.693 mT"
    
    Returns: value or None
    """
    if keyword not in line:
        return None
    
    try:
        # Pattern: Keyword(optional_label): value unit
        pattern = rf"{keyword}\(?([^)]*)\)?:\s*([-+]?\d+\.?\d*)"
        match = re.search(pattern, line)
        
        if match:
            value = float(match.group(2))
            return value
        
        return None
    except (ValueError, IndexError):
        return None


def load_calibration():
    """
    Load calibration constants from JSON file.
    
    Returns: z_axis_calib or None
    """
    if not os.path.exists(CALIBRATION_FILE):
        print(f"✗ Error: Calibration file '{CALIBRATION_FILE}' not found.")
        print("  Please run calibration_pico.py first.")
        return None
    
    try:
        with open(CALIBRATION_FILE, 'r') as f:
            data = json.load(f)
        
        z_axis_calib = data.get('z_axis_sensor')
        
        return z_axis_calib
    
    except (json.JSONDecodeError, IOError) as e:
        print(f"✗ Error reading calibration file: {e}")
        return None


def read_sensor_values(ser):
    """
    Read Z-axis sensor value from serial.
    
    Returns: z_axis_value or None
    """
    while True:
        try:
            line = ser.readline().decode('utf-8').strip()
            if not line:
                continue
            
            z_axis_val = extract_sensor_value(line, Z_AXIS_KEYWORD)
            
            # Return if we got valid data
            if z_axis_val is not None:
                return z_axis_val
        
        except (ValueError, UnicodeDecodeError, AttributeError):
            continue


def calculate_force(z_value, z_calib):
    """
    Convert Z-axis reading to force in Newtons (clamped to non-negative).
    
    Args:
        z_value: Z-axis sensor reading
        z_calib: Calibration data dict with slope and intercept
    
    Returns: Force in Newtons (>= 0)
    """
    if z_value is None or z_calib is None:
        return None
    
    force = (z_calib['slope'] * z_value) + z_calib['intercept']
    return max(0, force)  # Clamp to zero if negative


def main():
    print("=" * 70)
    print("RASPBERRY PI PICO - REAL-TIME FORCE MEASUREMENT")
    print("=" * 70)
    
    # Load calibration
    print(f"\nLoading calibration from '{CALIBRATION_FILE}'...")
    z_axis_calib = load_calibration()
    
    if z_axis_calib is None:
        print("✗ No valid calibration data found.")
        return
    
    print("✓ Calibration loaded!")
    
    if z_axis_calib:
        print(f"\nZ-Axis Sensor:")
        print(f"  Formula: {z_axis_calib['formula']}")
        print(f"  Slope:     {z_axis_calib['slope']:.6f}")
        print(f"  Intercept: {z_axis_calib['intercept']:.6f}")
        print(f"  R² value:  {z_axis_calib['r_squared']:.6f}")
    
    # Connect to Pico
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
    
    print("Starting real-time visualization...")
    print("Close the plot window to stop.\n")
    
    # Initialize data storage
    force_values = [0]
    z_axis_values = [0]
    max_force = [1.0]  # For auto-scaling
    
    # Set up the plot
    fig = plt.figure(figsize=(12, 5))
    fig.suptitle('Raspberry Pi Pico - Z-Axis Force Measurement', 
                 fontsize=16, fontweight='bold')
    
    # Create subplots for Z-axis and Force
    ax_z = fig.add_subplot(1, 2, 1)
    ax_force = fig.add_subplot(1, 2, 2)
    
    # Configure Z-axis
    bar_z = ax_z.barh(['Z-axis'], [0], color='mediumseagreen', height=0.5)
    ax_z.set_xlabel('Z-axis (mT)', fontsize=11)
    ax_z.set_xlim(0, 50)
    ax_z.grid(True, alpha=0.3, axis='x')
    z_text = ax_z.text(0.5, 0.5, '0.000 mT', 
                      transform=ax_z.transAxes,
                      fontsize=20, ha='center', va='center',
                      fontweight='bold', color='white',
                      bbox=dict(boxstyle='round,pad=0.5', 
                               facecolor='mediumseagreen', alpha=0.8))
    
    # Configure Force
    bar_force = ax_force.barh(['Force'], [0], color='crimson', height=0.5)
    ax_force.set_xlabel('Force (N)', fontsize=11)
    ax_force.set_xlim(0, 1.0)
    ax_force.grid(True, alpha=0.3, axis='x')
    force_text = ax_force.text(0.5, 0.5, '0.000 N\n0.000 kg', 
                               transform=ax_force.transAxes,
                               fontsize=18, ha='center', va='center',
                               fontweight='bold', color='white',
                               bbox=dict(boxstyle='round,pad=0.5', 
                                        facecolor='crimson', alpha=0.8))
    
    plt.tight_layout()
    
    def update_plot(frame):
        """Update plot with new sensor data."""
        try:
            # Read new Z-axis data
            z_axis_val = read_sensor_values(ser)
            
            # Update Z-axis and force
            if z_axis_val is not None:
                z_axis_values[0] = z_axis_val
                force_n = calculate_force(z_axis_val, z_axis_calib)
                if force_n is not None:
                    force_values[0] = force_n
                    
                    # Update max force for auto-scaling
                    if force_n > max_force[0]:
                        max_force[0] = force_n * 1.1
                        ax_force.set_xlim(0, max_force[0])
            
            # Update Z-axis display
            bar_z_list = [bar for bar in ax_z.patches]
            if bar_z_list:
                bar_z_list[0].set_width(z_axis_values[0])
            z_text.set_text(f'{z_axis_values[0]:.3f} mT')
            
            # Update force display
            bar_force_list = [bar for bar in ax_force.patches]
            if bar_force_list:
                bar_force_list[0].set_width(force_values[0])
            force_kg = force_values[0] / 9.81
            force_text.set_text(f'{force_values[0]:.3f} N\n{force_kg:.4f} kg')
            
            return bar_z_list + bar_force_list
        
        except Exception as e:
            print(f"Error updating plot: {e}")
            return []
    
    # Create animation
    anim = FuncAnimation(fig, update_plot, interval=50, blit=False, 
                        cache_frame_data=False)
    
    try:
        plt.show()
    except KeyboardInterrupt:
        pass
    finally:
        ser.close()
        print("\n✓ Serial connection closed.")


if __name__ == "__main__":
    main()
