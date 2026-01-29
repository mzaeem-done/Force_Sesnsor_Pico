#include <stdio.h>
#include <math.h>
#include "pico/stdlib.h"
#include "hardware/i2c.h"

// ========================================
// CONFIGURATION
// ========================================
#define LED_PIN 25
#define GPIO3_VCC 3               // Optional: Use GPIO3 as VCC for sensor

// I2C Configuration
#define I2C_PORT i2c0
#define I2C_SDA_PIN 4
#define I2C_SCL_PIN 5
#define I2C_FREQ 400000

// MLX90393 I2C Address and Commands
#define MLX90393_ADDR 0x0C
#define MLX90393_REG_SM 0x30      // Start single measurement
#define MLX90393_REG_RM 0x40      // Read measurement
#define MLX90393_REG_EX 0x80      // Exit mode
#define MLX90393_REG_RT 0xF0      // Reset
#define MLX90393_AXIS_ALL 0x0E

// Calibration Constants (from calibration_data.json)
// UPDATE THESE VALUES AFTER RUNNING CALIBRATION
#define CALIBRATION_SLOPE 51.94029384743018f
#define CALIBRATION_INTERCEPT -692.9925307532482f
#define Z_OFFSET_MT 20.0f         // Offset to keep Z-axis values positive

// Filter settings
#define FILTER_VAL 0.4f

// ========================================
// GAIN AND RESOLUTION SETTINGS
// ========================================
typedef enum {
    MLX90393_GAIN_5X = 0,
    MLX90393_GAIN_4X = 1,
    MLX90393_GAIN_3X = 2,
    MLX90393_GAIN_2_5X = 3,
    MLX90393_GAIN_2X = 4,
    MLX90393_GAIN_1_67X = 5,
    MLX90393_GAIN_1_33X = 6,
    MLX90393_GAIN_1X = 7
} mlx90393_gain_t;

typedef enum {
    MLX90393_RES_16 = 0,
    MLX90393_RES_17 = 1,
    MLX90393_RES_18 = 2,
    MLX90393_RES_19 = 3
} mlx90393_resolution_t;

// LSB lookup table [HALLCONF=0][GAIN][RES][XY/Z]
const float mlx90393_lsb_lookup[2][8][4][2] = {
    /* HALLCONF = 0xC (default) */
    {
        {{0.751f, 1.210f}, {1.502f, 2.420f}, {3.004f, 4.840f}, {6.009f, 9.680f}},  // GAIN 5X
        {{0.601f, 0.968f}, {1.202f, 1.936f}, {2.403f, 3.872f}, {4.840f, 7.744f}},  // GAIN 4X
        {{0.451f, 0.726f}, {0.901f, 1.452f}, {1.803f, 2.904f}, {3.605f, 5.808f}},  // GAIN 3X
        {{0.376f, 0.605f}, {0.751f, 1.210f}, {1.502f, 2.420f}, {3.004f, 4.840f}},  // GAIN 2.5X
        {{0.300f, 0.484f}, {0.601f, 0.968f}, {1.202f, 1.936f}, {2.403f, 3.872f}},  // GAIN 2X
        {{0.250f, 0.403f}, {0.501f, 0.807f}, {1.001f, 1.613f}, {2.003f, 3.227f}},  // GAIN 1.67X
        {{0.200f, 0.323f}, {0.401f, 0.645f}, {0.801f, 1.291f}, {1.602f, 2.581f}},  // GAIN 1.33X
        {{0.150f, 0.242f}, {0.300f, 0.484f}, {0.601f, 0.968f}, {1.202f, 1.936f}},  // GAIN 1X
    },
    /* HALLCONF = 0x0 */
    {
        {{0.787f, 1.267f}, {1.573f, 2.534f}, {3.146f, 5.068f}, {6.292f, 10.137f}},
        {{0.629f, 1.014f}, {1.258f, 2.027f}, {2.517f, 4.055f}, {5.034f, 8.109f}},
        {{0.472f, 0.760f}, {0.944f, 1.521f}, {1.888f, 3.041f}, {3.775f, 6.082f}},
        {{0.393f, 0.634f}, {0.787f, 1.267f}, {1.573f, 2.534f}, {3.146f, 5.068f}},
        {{0.315f, 0.507f}, {0.629f, 1.014f}, {1.258f, 2.027f}, {2.517f, 4.055f}},
        {{0.262f, 0.422f}, {0.524f, 0.845f}, {1.049f, 1.689f}, {2.097f, 3.379f}},
        {{0.210f, 0.338f}, {0.419f, 0.676f}, {0.839f, 1.352f}, {1.678f, 2.703f}},
        {{0.157f, 0.253f}, {0.315f, 0.507f}, {0.629f, 1.014f}, {1.258f, 2.027f}},
    }
};

// Current sensor settings
mlx90393_gain_t mlx_gain = MLX90393_GAIN_1X;
mlx90393_resolution_t mlx_res_z = MLX90393_RES_16;

// ========================================
// GLOBAL VARIABLES
// ========================================
float smoothed_z = 0.0f;
bool first_mag_reading = true;
bool mlx_initialized = false;

// ========================================
// MLX90393 FUNCTIONS
// ========================================

bool mlx_transceive(uint8_t *tx_data, uint8_t tx_len, uint8_t *rx_data, uint8_t rx_len) {
    int ret = i2c_write_blocking(I2C_PORT, MLX90393_ADDR, tx_data, tx_len, false);
    if (ret < 0) return false;
    
    sleep_ms(10);
    
    if (rx_len > 0) {
        ret = i2c_read_blocking(I2C_PORT, MLX90393_ADDR, rx_data, rx_len + 1, false);  // +1 for status
        return ret > 0;
    }
    
    uint8_t status;
    ret = i2c_read_blocking(I2C_PORT, MLX90393_ADDR, &status, 1, false);
    if (ret > 0 && rx_data) {
        rx_data[0] = status;
    }
    return ret > 0;
}

bool mlx_exit_mode() {
    uint8_t cmd = MLX90393_REG_EX;
    uint8_t status;
    if (!mlx_transceive(&cmd, 1, &status, 0)) return false;
    return (status >> 2) == 0x00;
}

bool mlx_reset() {
    uint8_t cmd = MLX90393_REG_RT;
    uint8_t status;
    if (!mlx_transceive(&cmd, 1, &status, 0)) return false;
    sleep_ms(5);
    return (status >> 2) == 0x01;
}

bool mlx_start_measurement() {
    uint8_t cmd = MLX90393_REG_SM | MLX90393_AXIS_ALL;
    uint8_t status;
    if (!mlx_transceive(&cmd, 1, &status, 0)) return false;
    uint8_t stat = status >> 2;
    return (stat == 0x00 || stat == 0x08);
}

bool mlx_read_measurement(float *z) {
    uint8_t cmd = MLX90393_REG_RM | MLX90393_AXIS_ALL;
    uint8_t data[7];  // 1 status + 6 data bytes
    
    if (!mlx_transceive(&cmd, 1, data, 6)) return false;
    
    if ((data[0] >> 2) == 0x00) {
        // Parse Z-axis raw value (big-endian signed 16-bit)
        int16_t zi = (data[5] << 8) | data[6];
        
        // Adjust for 18/19 bit resolution
        if (mlx_res_z == MLX90393_RES_18) zi -= 0x8000;
        if (mlx_res_z == MLX90393_RES_19) zi -= 0x4000;
        
        // Convert to uT using LSB lookup table (HALLCONF=0xC)
        float z_uT = (float)zi * mlx90393_lsb_lookup[0][mlx_gain][mlx_res_z][1];
        
        // Convert to mT (millitesla) and add offset
        float z_mT = (z_uT / 1000.0f) + Z_OFFSET_MT;
        
        // Ensure non-negative
        *z = (z_mT < 0.0f) ? 0.0f : z_mT;
        
        return true;
    }
    return false;
}

bool mlx_read_data(float *z) {
    if (!mlx_start_measurement()) return false;
    sleep_ms(10);
    return mlx_read_measurement(z);
}

bool mlx_init() {
    if (!mlx_exit_mode()) return false;
    if (!mlx_reset()) return false;
    sleep_ms(10);
    mlx_initialized = true;
    return true;
}

float smooth(float data, float filter_val, float smoothed_val) {
    return (data * (1.0f - filter_val)) + (smoothed_val * filter_val);
}

/**
 * Calculate force from Z-axis reading using calibration constants
 * Formula: Force (N) = slope * Z-axis (mT) + intercept
 */
float calculate_force(float z_axis_mT) {
    float force = (CALIBRATION_SLOPE * z_axis_mT) + CALIBRATION_INTERCEPT;
    // Clamp to non-negative values
    return (force < 0.0f) ? 0.0f : force;
}

// ========================================
// MAIN
// ========================================
int main() {
    // Initialize stdio
    stdio_init_all();
    
    // Setup LED
    gpio_init(LED_PIN);
    gpio_set_dir(LED_PIN, GPIO_OUT);
    
    // Setup GPIO3 as VCC (optional - comment out if not needed)
    gpio_init(GPIO3_VCC);
    gpio_set_dir(GPIO3_VCC, GPIO_OUT);
    gpio_put(GPIO3_VCC, 1);
    
    // Initialize I2C for MLX90393
    i2c_init(I2C_PORT, I2C_FREQ);
    gpio_set_function(I2C_SDA_PIN, GPIO_FUNC_I2C);
    gpio_set_function(I2C_SCL_PIN, GPIO_FUNC_I2C);
    gpio_pull_up(I2C_SDA_PIN);
    gpio_pull_up(I2C_SCL_PIN);
    
    printf("\n===========================================\n");
    printf("  RASPBERRY PI PICO - FORCE SENSOR\n");
    printf("===========================================\n");
    printf("Sensor: MLX90393 Magnetometer\n");
    printf("I2C: SDA=GPIO%d, SCL=GPIO%d\n", I2C_SDA_PIN, I2C_SCL_PIN);
    printf("Mode: RAW Z-AXIS OUTPUT\n");
    printf("===========================================\n\n");
    
    sleep_ms(2000);
    
    // Initialize MLX90393
    if (mlx_init()) {
        printf("MLX90393 initialized successfully!\n\n");
    } else {
        printf("ERROR: MLX90393 initialization failed!\n");
        printf("Check I2C wiring and sensor power.\n\n");
    }
    
    printf("Starting measurements...\n");
    printf("Format: Z-axis(M1): X.XXX mT\n\n");
    
    bool led_state = false;
    
    // Main loop
    while (true) {
        // Toggle LED
        gpio_put(LED_PIN, led_state);
        led_state = !led_state;
        
        // Read MLX90393 Z-axis
        if (mlx_initialized) {
            float z;
            if (mlx_read_data(&z)) {
                if (first_mag_reading) {
                    smoothed_z = z;
                    first_mag_reading = false;
                } else {
                    smoothed_z = smooth(z, FILTER_VAL, smoothed_z);
                }
                
                // Output Z-axis value only (force calculation done in Python)
                printf("Z-axis(M1): %.3f mT\n", smoothed_z);
            } else {
                printf("Z-axis(M1): ERROR\n");
            }
        } else {
            printf("Sensor not initialized\n");
        }
        
        sleep_ms(100);  // 10Hz sample rate
    }
    
    return 0;
}
