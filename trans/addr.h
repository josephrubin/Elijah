#ifndef ADDR_H
#define ADDR_H

/**
 * Address constants for our MEMS chips.
 * @author Joseph Rubin
 */

// ________________
// SLAVE ADDRESSES.

// Note: as you can see, no addresses use the first bit. This is because the first bit is reserved for the signal (READ:1 or WRITE:0).
// Our read/write functions set that bit automatically, so no need to set them by ourselves.

#define ADDR_NOTHING 0x00

// This register always reads 0x6A on our MEMS devices.
// We can use it to make sure we are connected to the correct slave, and reading properly.
#define ADDR_WHO_I_AM 0x0F

// Gyroscope/Accelerometer registers.
// Each sensor axis is a two byte word:
// X low  byte.
// X high byte.
// Y low  byte.
// Y high byte.
// Z low  byte.
// Z high byte.
// We only really need the address of the gyro; then we simply read all the way through.
#define ADDR_GYRO 0x22
#define ADDR_ACCL 0x28

// The status register tells us when new readings are available.
// From right to left:
// Bit 0 is for accelerometer.
// Bit 1 is for gyroscope.
// Bit 2 is for temperature (irrelevant).
#define ADDR_STATUS 0x1E
#define ACCL_STATUS_INDEX 0
#define GYRO_STATUS_INDEX 1

#endif /* ADDR_H */
