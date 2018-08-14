#ifndef MEMS_H
#define MEMS_H

/**
 * Items relating to reading and writing the MEMS slaves.
 * @author Joseph Rubin
 */

// Each frame represents a full reading of every sensor of one MEMS device (see spec/).
// Flag bits from right to left:
//      [0]     end     a 1 represents the end of data transmition.
//      [1-2]   sensor  the id of the sensor this data frame is from
//                      00  Tongue MEMS
//                      01  Throat MEMS
//                      10  Microphone
//                      11  Unassigned
//      [3-6]   unassigned
//      [7]     button  a 1 means the button was pressed during this frame
typedef struct
{
    // Time this frame was captured in ms since the capturing began.
    uint16_t timestamp;
    // Sensor output values.
    int16_t reading[6];
    // Various data bits (see above).
    uint8_t flag;
    // XOR calculated summary of the data.
    uint8_t checksum;
} FRAME;

// ____________________________
// SERIAL PERIPHERAL INTERFACE.

// The slave ids to be passed to slaveOn() and slaveOff().
#define TONGUE_SLAVE 12
#define THROAT_SLAVE 21

// Remember - to enable a device, we set its Slave Select LOW...
#define slaveOn(id)  setSlave(id, LOW)

// ...and to disable we set its Slave Select HIGH.
#define slaveOff(id) setSlave(id, HIGH)

// NOTE: Multiple reads or writes without disabling and renabling the slave can be interperated as a continuous multi-action.
// This may have consequences if the AUTO_INC bit is enabled (it is). Our readAddress and writeAddress functions handle this for us.

// _____________
// SPI COMMANDS.

// Read is specified by a high first bit.
#define READ  0b10000000

// Write is specified by a low first bit.
#define WRITE 0b01111111

// ______________
// COMMUNICATION.

/**
 * Select or deselect one of the slave devices (for us, either the TONGUE_SLAVE or the THROAT_SLAVE).
 * It is reccommended to use the macros slaveOn and slaveOff which will use this function internally.
 */
void setSlave(int id, int state);

/**
 * Write a single byte to the slave at the specified address.
 * @param address the address to write to.
 */
void writeAddress(int id, byte address, byte data);

/**
 * Read a single byte from the slave from a specified address.
 * Remember that some outputs are meant to be read as signed two's compliment int8_t.
 * @param address the address to read from.
 * @return the read byte.
 */
byte readAddress(int id, byte address);

/**
 * Read many bytes in a row.
 * Remember that some outputs are meant to be read as signed two's compliment int8_t.
 * @param *outputBuffer the buffer to place the read data.
 * @param address the address to start from.
 */
void readMany(int id, byte *outputBuffer, int byteCount, byte startingAddress);

#endif /* MEMS_H */
