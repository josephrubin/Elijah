/**
 * Items relating to reading and writing the MEMS slaves.
 * @author Joseph Rubin
 */

#include "mems.h"
#include "pins.h"

void setSlave(int id, int state)
{
    if (id == TONGUE_SLAVE)
    {
        digitalWrite(SS_TONGUE_OUTPUT_PIN, state);
    }
    else if (id == THROAT_SLAVE)
    {
        digitalWrite(SS_THROAT_OUTPUT_PIN, state);
    }
}

void writeAddress(int id, byte address, byte data)
{
    // Write
    //  [0]     0b0        MOSI (send)
    //  [1-7]   <address>  MOSI (send)
    //  [8-15]  <data>     MOSI (send)

    // The write command.
    byte firstPayload = WRITE & address;
    // The data to write.
    byte secondPayload = data;
    
    slaveOn(id);
    SPI.transfer(firstPayload);
    SPI.transfer(secondPayload);
    slaveOff(id);
}

byte readAddress(int id, byte address)
{
    // Read
    //  [0]     0b1        MOSI (send)
    //  [1-7]   <address>  MOSI (send)
    //  [8-15]  <data>     MISO (receive)

    // The read command.
    byte firstPayload = READ | address;
    // After the read command, we expect the data. We have nothing interesting to say to the slave, so it doesn't matter what we send here at that time.
    // We will just send zero (0x00), and read in the data.
    byte secondPayload = ADDR_NOTHING;
    
    slaveOn(id);
    SPI.transfer(firstPayload);
    byte data = SPI.transfer(secondPayload);
    slaveOff(id);
    
    return data;
}

void readMany(int id, byte *outputBuffer, int byteCount, byte startingAddress)
{
    if (byteCount < 1)
    {
        if (DEBUG_MODE)
        {
            Serial.println("byteCount cannot be < 1. Quiting.");
            delay(100);
        }
        exit(1);
    }

    // The read command.
    byte readPayload = READ | startingAddress;
    slaveOn(id);
    SPI.transfer(readPayload);

    // Now read in the data.
    SPI.transfer(outputBuffer, byteCount);
    slaveOff(id);
}
