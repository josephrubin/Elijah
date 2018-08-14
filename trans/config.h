#ifndef CONFIG_H
#define CONFIG_H

/*
 * Configuration of the MEMS devices.
 * We are using the LSM6DS3 MEMS devices.
 * It will also work with LSM6DSL if the EXPECTED_WHO_I_AM is correctly set below.
 * @author Joseph Rubin
 */

// Called on bootup to confiure the MEMS sensors' configuration addresses.
void writeConfiguration();

// The capture rate of our MEMS sensors. Both gyro and accl will use the same rate.
typedef enum
{
    VERY_SLOW = 104, // 0100
    SLOW = 208,      // 0101
    MEDIUM = 416,    // 0110
    FAST = 833,      // 0111
    VERY_FAST = 1660 // 1000
} CAPTURE_RATE_t;

// The positive half of the range of our gyroscope (negative half is equivalent in magnitude).
typedef enum
{
    GYRO_VERY_SMALL = 125, // FS_G = xx, FS_125 = 1
    GYRO_SMALL = 250,      // FS_G = 00
    GYRO_MEDIUM = 500,     // FS_G = 01
    GYRO_BIG = 1000,       // FS_G = 10
    GYRO_VERY_BIG = 2000   // FS_G = 11
} GYRO_SCALE_t;

// The positive half of the range of our accelerometer (negative half is equivalent in magnitude).
typedef enum
{
    ACCL_SMALL = 2,        // FS_XL = 00
    ACCL_MEDIUM = 4,       // FS_XL = 10
    ACCL_BIG = 8,          // FS_XL = 11
    ACCL_VERY_BIG = 16,    // FS_XL = 01
} ACCL_SCALE_t;

// __________
// OPERATION.

// TRANSMIT_MODE is for transmitting data to a receiver. If this is 1, the Arduino will write captured data to serial.
// DEMO_MODE is a outputs limited data to LED strips if this is 1.
// DEBUG_MODE will print some extra header and footer info. This will mess with our python scripts.

#define TRANSMIT_MODE 1
#define DEMO_MODE 0
#define DEBUG_MODE 0

// ________
// POLLING.

// Maximum SPI communication speed for this device.
#define SPI_SPEED 10000000
// Serial communication baud rate. This should match the number in the serial monitor, and the python scripts (../recv/const.py).
#define BAUD_RATE 1000000
// The value we expect to read from ADDR_WHO_I_AM (see addr.h). If we change which MEMS we are using, this value must be changed accordingly.
#define EXPECTED_WHO_I_AM 0x69

#endif /* CONFIG_H */
