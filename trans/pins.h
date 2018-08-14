#ifndef PINS_H
#define PINS_H

/**
 * Pin number constants for our Arduino board.
 * @author Joseph Rubin
 */

// ______________
// MEMS/SPI PINS.

// These next three pins are dictated by the SPI library, and thus cannot be changed.

// Master Out Slave In - Master sends data to slaves.
#define MOSI_OUTPUT_PIN 11

// Master In Slave Out - Slaves send data to master.
#define MISO_INPUT_PIN  12

// Serial clock pin - tells the components when to send and recieve.
#define SCK_OUTPUT_PIN  13

// Slave Select - enables:(low output) or disables:(high output) its slave device.
// These pins can be set to whatever we want, because they are not dictated by the SPI library.

// We have more than one slave, so we have more than one SS pin - and we use them to select which slave we are reading from.
#define SS_TONGUE_OUTPUT_PIN 9
#define SS_THROAT_OUTPUT_PIN 10

// _________
// LED PINS.

// These pins can be set to whatever we want.

// For showing the magnitude of gyro readings.
#define LED_MAGNITUDE_OUTPUT_PIN 3
// For showing the frequency of peaks in gyro readings.
#define LED_FREQUENCY_OUTPUT_PIN 4
// For showing deadzones in gyro readings.
#define LED_BLINDSPOT_OUTPUT_PIN 5

// ___________
// BUTTON PIN.

// These pins can be set to whatever we want.

// This pin is connected to the signal line of the pushbutton.
#define BUTTON_INPUT_PIN 7

#endif /* PINS_H */
