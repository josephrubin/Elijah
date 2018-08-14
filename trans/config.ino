/*
 * Configuration of the MEMS devices.
 * We are using the LSM6DS3 MEMS devices.
 * It will also work with LSM6DSL if the EXPECTED_WHO_I_AM is correctly set below.
 * @author Joseph Rubin
 */
 
#include "config.h"
#include "mems.h"

// THESE VALUES ARE EDITABLE TO CONFIGURE THE MEMS SENSORS.
// In general, we want a somewhat fast capture rate, and a fairly small (and therefore sensitive) gyro scale range.
const CAPTURE_RATE_t CAPTURE_RATE = FAST;
const GYRO_SCALE_t GYRO_SCALE = GYRO_SMALL;
const ACCL_SCALE_t ACCL_SCALE = ACCL_SMALL;

// ___________________
// CONFIGURATION BITS.

// Here we initialize some configuration data we would like to write to the MEMS sensors.
// See the manual (old mems) for information about what we are writing.

// The first two constants because they are subject to change at run-time depending on the enum choices above.
int8_t config_10_h = 0b00000000;
int8_t config_11_h = 0b00000000;
const int8_t CONFIG_12_H = 0b01000100;
const int8_t CONFIG_13_H = 0b00001100;
const int8_t CONFIG_16_H = 0b00000000;

void writeConfiguration()
{
    // Based on our chosen configuration constants (CAPTURE_RATE,GYRO_SCALE,ACCL_SCALE)
    // we modify the configuration bits that we will write to the MEMS sensors.
    
    switch (CAPTURE_RATE)
    {
        case VERY_SLOW:
            config_10_h |= 0b01000000;
            config_11_h |= 0b01000000;
            break;
        case SLOW:
            config_10_h |= 0b01010000;
            config_11_h |= 0b01010000;
            break;
        case MEDIUM:
            config_10_h |= 0b01100000;
            config_11_h |= 0b01100000;
            break;
        case FAST:
            config_10_h |= 0b01110000;
            config_11_h |= 0b01110000;
            break;
        case VERY_FAST:
            config_10_h |= 0b10000000;
            config_11_h |= 0b10000000;
            break;
        default:
            if (DEBUG_MODE)
            {
                Serial.println("Invalid configuration constant. Quiting.");
                delay(100);
            }
            exit(1);
    }

    switch (GYRO_SCALE)
    {
        case GYRO_VERY_SMALL:
            config_11_h |= 0b00000010;
            break;
        case GYRO_SMALL:
            config_11_h |= 0b00000000;
            break;
        case GYRO_MEDIUM:
            config_11_h |= 0b00000100;
            break;
        case GYRO_BIG:
            config_11_h |= 0b00001000;
            break;
        case GYRO_VERY_BIG:
            config_11_h |= 0b00001100;
            break;
        default:
            if (DEBUG_MODE)
            {
                Serial.println("Invalid configuration constant. Quiting.");
                delay(100);
            }
            exit(1);
    }
    
    switch (ACCL_SCALE)
    {
        case ACCL_SMALL:
            config_10_h |= 0b00000000;
            break;
        case ACCL_MEDIUM:
            config_10_h |= 0b00001000;
            break;
        case ACCL_BIG:
            config_10_h |= 0b00001100;
            break;
        case ACCL_VERY_BIG:
            config_10_h |= 0b00000100;
            break;
        default:
            if (DEBUG_MODE)
            {
                Serial.println("Invalid configuration constant. Quiting.");
                delay(100);
            }
            exit(1);
    }
    
    // It is a waste of time to implement a multi-write,
    // because this small amount of writing to the MEMS at the start is the only writing we ever do.
    
    // Configure the Tongue sensor.
    writeAddress(TONGUE_SLAVE, 0x10, config_10_h);
    writeAddress(TONGUE_SLAVE, 0x11, config_11_h);
    writeAddress(TONGUE_SLAVE, 0x12, CONFIG_12_H);
    writeAddress(TONGUE_SLAVE, 0x13, CONFIG_13_H);
    writeAddress(TONGUE_SLAVE, 0x16, CONFIG_16_H);

    // Configure the Throat sensor.
    writeAddress(THROAT_SLAVE, 0x10, config_10_h);
    writeAddress(THROAT_SLAVE, 0x11, config_11_h);
    writeAddress(THROAT_SLAVE, 0x12, CONFIG_12_H);
    writeAddress(THROAT_SLAVE, 0x13, CONFIG_13_H);
    writeAddress(THROAT_SLAVE, 0x16, CONFIG_16_H);
}
