/**
 * Main sketch file for the transmitter (Arduino) device.
 * Purpose: transmit data from our sensors to the receiver.
 * Created by Sixdof Space.
 * @author Joseph Rubin
 */

// Libraries for LED strip and SPI communication with the MEMS devices.
#include <Adafruit_NeoPixel.h>
#include <SPI.h>

#include "metric.h"
#include "demo.h"
#include "config.h"
#include "addr.h"
#include "pins.h"
#include "mems.h"
#include "calculate.h"
#include "color.h"
#include "pattern.h"
#include "picker.h"
#include "signal.h"

// When pressed, the current can flow to GND and we read a LOW.
#define buttonIsPressed() (digitalRead(BUTTON_INPUT_PIN) == LOW)

// Number of data points we would like to receive.
// X, Y, Z for both gyro and accl.
static const int NUM_READINGS = 3 * 2;
// Each reading has a low byte and a high byte.
static const int NUM_BYTES = NUM_READINGS * 2;

// Bring in our configuration settings from ./config.
extern const CAPTURE_RATE_t CAPTURE_RATE;
extern const GYRO_SCALE_t GYRO_SCALE;
extern const ACCL_SCALE_t ACCL_SCALE;

// __________
// LED STRIP.

// Total number of LEDs on each strip, indexed from [0, LED_COUNT - 1].
#define LED_COUNT 20
// The brightness (out of 255) that we use for the LEDs.
#define BRIGHTNESS 10

// We have three strips, and each one has its own data pin (see pins.h).
static Adafruit_NeoPixel magnitudeStrip;
static Adafruit_NeoPixel frequencyStrip;
static Adafruit_NeoPixel blindspotStrip;

// ________
// CONTROL.

// Set to false after the first round of capturing.
static bool isFirstCaptureRound = true;

// The millis() reading at the start of the first round of capturing.
static unsigned long firstCaptureRoundMs = 0;

// Whether or not we should be capturing.
static bool doCapture = false;

// Buffer to store readings in.
static byte *dataBuffer;
// One frame to capture data in; we clear it before reading each frame.
static FRAME *captureFrame;

// Button press state last capture round.
static bool buttonWasPressed = false;

// ________
// METRICS.

// Code that that deals with the LED strips is marked with 'DEMO MODE' or 'metrics'.
// I have tried to make it easy to remove this code (since I do not think that it will not be in the final product).

// =Magnitude metric=
// How many total samples we collected.
static int tongueSampleCount;
static int throatSampleCount;

// The magnitude of the gyro in the previous capture round.
static double lastTongueMagnitude;
static double lastThroatMagnitude;

// The sum total of all of the gyro magnitudes (which were above MAGNITUDE_THRESHOLD)
static double tongueTotalMagnitude;
static double throatTotalMagnitude;

// =Peak metric=
// How many total peaks there were.
static int tonguePeakCount;
static int throatPeakCount;

// The total distance between peaks.
static unsigned long long tonguePeakDistanceTotalMs;
static unsigned long long throatPeakDistanceTotalMs;

// The time the last peak occurred.
static unsigned long lastTonguePeakMs;
static unsigned long lastThroatPeakMs;

// =Blindspot metric=
// We can only have a blindspot after the first reading that is above MAGNITUDE_THRESHOLD.
static bool tongueCanHaveBlindspot;
static bool throatCanHaveBlindspot;

// Whether we are curently in a blindspot.
static bool tongueOnBlindspot;
static bool throatOnBlindspot;

// The sum total of the width of every blindspot.
static unsigned long long tongueBlindspotWidthTotal;
static unsigned long long throatBlindspotWidthTotal;

// The time the current blindspot started.
static unsigned long tongueBlindspotStartMs;
static unsigned long throatBlindspotStartMs;

// The total number of blindspots.
static unsigned int tongueBlindspotCount;
static unsigned int throatBlindspotCount;

/**
 * This function is run once - when the Arduino boots up.
 * It is not necessarily run every time a serial connection is formed.
 * This is the difference between a resetting and a non resetting
 * connection. By default, an Arduino resets when it is connected
 * to over serial, but some care in the python code allows us to
 * circumvent that behavior. This means that the only code
 * that should go in setup is code that is run once per
 * bootup, but code that must be run once per capture
 * should be placed in beginCapture.
 */
void setup()
{
    // Allow serial output for transmitting and debugging.
    if (DEBUG_MODE || TRANSMIT_MODE)
    {
        Serial.begin(BAUD_RATE);
    }

    // Set up our MEMS pins.
    // We don't need to set up MISO, MOSI, or SCK because the SPI library does this for us (read the source code to see this for yourself).
    //pinMode(MOSI_OUTPUT_PIN, OUTPUT);//pinMode(MISO_INPUT_PIN, INPUT);//pinMode(SCK_OUTPUT_PIN, OUTPUT);
    pinMode(SS_TONGUE_OUTPUT_PIN, OUTPUT);
    pinMode(SS_THROAT_OUTPUT_PIN, OUTPUT);

    // LED strip setup.
    if (DEMO_MODE)
    {
        // Configure their pins...
        pinMode(LED_MAGNITUDE_OUTPUT_PIN, OUTPUT);
        pinMode(LED_FREQUENCY_OUTPUT_PIN, OUTPUT);
        pinMode(LED_BLINDSPOT_OUTPUT_PIN, OUTPUT);

        // ...build them...
        magnitudeStrip = Adafruit_NeoPixel(LED_COUNT, LED_MAGNITUDE_OUTPUT_PIN, NEO_RGB + NEO_KHZ800);
        frequencyStrip = Adafruit_NeoPixel(LED_COUNT, LED_FREQUENCY_OUTPUT_PIN, NEO_RGB + NEO_KHZ800);
        blindspotStrip = Adafruit_NeoPixel(LED_COUNT, LED_BLINDSPOT_OUTPUT_PIN, NEO_RGB + NEO_KHZ800);

        // ...and start them.
        Adafruit_NeoPixel *strips[] = {&magnitudeStrip, &frequencyStrip, &blindspotStrip};
        for (unsigned short i = 0; i < 3; i++)
        {
            // We do not wish to distract the patients, so choose a very low brightness.
            strips[i]->setBrightness(BRIGHTNESS);
            strips[i]->begin();
        }

        // Reset the strips (all LEDs off) before we start.
        clearStrips();
    }

    // Debug pins.
    pinMode(BUTTON_INPUT_PIN, INPUT);

    // Now that we have set up our pins, it is necessary to disable the slaves before we can start SPI (or it won't work correctly).
    slaveOff(TONGUE_SLAVE);
    slaveOff(THROAT_SLAVE);

    // Our device is compatible with modes 0 and 3.
    // We will choose mode 0.
    // MSBFIRST is referring to the most significant BIT, and has nothing to do with byte endianness.
    SPI.begin();
    SPI.beginTransaction(SPISettings(SPI_SPEED, MSBFIRST, SPI_MODE0));
    delay(20);

    // We can check if
    // 1) Our connection is good, and
    // 2) We are connected to the right device
    // by making sure that the whoiam reading (device id) is as we expect.
    if (readAddress(THROAT_SLAVE, ADDR_WHO_I_AM) != EXPECTED_WHO_I_AM)
    {
        Serial.println("Received unexpected whoiam. We have not correctly connected to our slaves through SPI. Quitting.");
        delay(100);
        exit(1);
    }
    else if (DEBUG_MODE)
    {
        Serial.println("Whoiam correctly received! We should have a good SPI connection.");
    }

    // Set configuration bytes.
    // Make sure that our SPI is good by giving it a moment.
    delay(50);
    writeConfiguration();
    delay(70);

    // We don't begin the capture here. We wait for a button press or a SIG_REQUEST.
    // Clear the incoming serial buffer because we do not process any requests before we send SIG_READY.
    if (TRANSMIT_MODE)
    {
        while (Serial.available() > 0)
        {
            if (Serial.read() == SIG_REQUEST)
            {
                Serial.write(SIG_DENIED);
            }
        }
    }
    
    // Now we are ready for capture requests, so let the receiver know by sending SIG_READY.
    Serial.write(SIG_READY);
}

/**
 * Run once per capture, before the capture begins.
 * Reset all metric variables, send our cnofiguration (see spec/),
 * and tell the loop function to capture data.
 */
void beginCapture()
{
    if (DEBUG_MODE)
    {
        Serial.println("Begin Capture!");
    }

    if (DEMO_MODE)
    {
        clearStrips();
    }

    if (DEMO_MODE)
    {
        // Reset metric variables.
        // The board itself is not necessarily reset each time that we make a new capture, so we need to reset the state ourselves.
        isFirstCaptureRound = true;
        firstCaptureRoundMs = 0;
        buttonWasPressed = false;
        tongueSampleCount = 0;
        throatSampleCount = 0;
        lastTongueMagnitude = 0;
        lastThroatMagnitude = 0;
        tongueTotalMagnitude = 0;
        throatTotalMagnitude = 0;
        tonguePeakCount = 0;
        throatPeakCount = 0;
        tonguePeakDistanceTotalMs = 0;
        throatPeakDistanceTotalMs = 0;
        tongueCanHaveBlindspot = false;
        throatCanHaveBlindspot = false;
        tongueOnBlindspot = false;
        throatOnBlindspot = false;
        tongueBlindspotWidthTotal = 0;
        throatBlindspotWidthTotal = 0;
        tongueBlindspotStartMs = 0;
        throatBlindspotStartMs = 0;
        tongueBlindspotCount = 0;
        throatBlindspotCount = 0;
    }

    // Reserve memory for a buffer to read sensor data.
    dataBuffer = (byte *) malloc(sizeof (byte) * NUM_BYTES);
    // Reserve memory for our capture frame (we only need one object).
    captureFrame = (FRAME *) malloc(sizeof * captureFrame);
    if (!dataBuffer || !captureFrame)
    {
        // Malloc failure.
        if (DEBUG_MODE)
        {
            Serial.println("Malloc Fail");
            delay(50);
        }
        exit(1);
    }

    // Start capturing.
    doCapture = true;

    if (TRANSMIT_MODE)
    {
        // Send our start pattern to sync with the receiver.
        Serial.write(SIG_HEAD);

        // Send our configuration, little endian.
        Serial.write(lowByte(CAPTURE_RATE)); Serial.write(highByte(CAPTURE_RATE));
        Serial.write(lowByte(GYRO_SCALE)); Serial.write(highByte(GYRO_SCALE));
        Serial.write(ACCL_SCALE);
    }
}

/**
 * Run once per capture, after the capture ends.
 * If in demo mode, calculate the metrics and send them in the 'Trailer' (see spec/).
 */
void endCapture()
{
    // Stop capturing.
    doCapture = false;

    free(dataBuffer);
    free(captureFrame);

    if (DEBUG_MODE)
    {
        Serial.println("End Capture!");
    }

    if (DEMO_MODE)
    {
        // Calculate the average magnitude of all of the readings that we captured.
        double tongueAverageMagnitude = tongueTotalMagnitude / tongueSampleCount;
        double throatAverageMagnitude = throatTotalMagnitude / throatSampleCount;
        double averageMagnitude = (tongueAverageMagnitude + throatAverageMagnitude) / 2;

        double averagePeakDistanceMs = ((tonguePeakDistanceTotalMs / tonguePeakCount) + (throatPeakDistanceTotalMs / throatPeakCount)) / 2;
    
        double averageBlindspotWidthMs = ((tongueBlindspotWidthTotal / tongueBlindspotCount) + (throatBlindspotWidthTotal / throatBlindspotCount)) / 2;

        // We have our metric now, so map it into a range which tells us how many lights to show. Never show less than 1, or more than LED_COUNT.
        // For the max values, we pick a somewhat arbitrary number that empirically maps our result onto the lights nicely.
        
        // Magnitude - average strength.
        long maxMagnitude = magnitude(GYRO_SCALE, GYRO_SCALE, GYRO_SCALE) / 20;
        int magnitudeLightCount = map(averageMagnitude, 0, maxMagnitude, 1, LED_COUNT);
        magnitudeLightCount = constrain(magnitudeLightCount, 1, LED_COUNT);
    
        // Frequency - distance between peaks.
        long maxFrequency = 8;
        int frequencyLightCount = LED_COUNT - map(averagePeakDistanceMs, 0, maxFrequency, 0, LED_COUNT - 1);
        frequencyLightCount = constrain(frequencyLightCount, 1, LED_COUNT);
    
        // Blindspot - conspicuous deadzones.
        long maxBlindspot = 800;
        int blindspotLightCount = map(averageBlindspotWidthMs, 0, maxBlindspot, 1, LED_COUNT);
        blindspotLightCount = constrain(blindspotLightCount, 1, LED_COUNT);
        
        // Output to the LED strips.
        const int delayBetweenLights = 10;
        wave(&magnitudeStrip, magnitudeLightCount, delayBetweenLights, magnitudeMeter);
        wave(&frequencyStrip, frequencyLightCount, delayBetweenLights, frequencyMeter);
        wave(&blindspotStrip, blindspotLightCount, delayBetweenLights, blindspotMeter);
    
        if (TRANSMIT_MODE)
        {
            // In transmit mode we may write a trailer (see the spec).
            Serial.print("averageMagnitude: ");         Serial.println(averageMagnitude);
            Serial.print("magnitudeLightCount: ");      Serial.println(magnitudeLightCount);
            
            Serial.print("peakCount: ");                Serial.println(tonguePeakCount + throatPeakCount);
            Serial.print("averagePeakDistanceMs: ");    Serial.println(averagePeakDistanceMs);
            Serial.print("frequencyLightCount: ");      Serial.println(frequencyLightCount);

            Serial.print("blindspotCount: ");           Serial.println(tongueBlindspotCount + throatBlindspotCount);
            Serial.print("averageBlindspotWidthMs: ");  Serial.println(averageBlindspotWidthMs);
            Serial.print("blindspotLightCount: ");      Serial.println(blindspotLightCount);
        }
    }

    if (TRANSMIT_MODE)
    {
        // We must terminate the 'Trailer' section (see the spec).
        // Even if we have nothing to say, we must send the dot and nweline.
        // Since the dot must be on a line of its own, send a newline before it just in case.
        Serial.println("");
        Serial.println('.');
    }

    /*
    if (DEBUG_MODE || TRANSMIT_MODE)
    {
        Serial.end();
    }
    */
    
    // End the SPI connection.
    //SPI.end(); // If we don't start this in beginCapture, don't end it here.
}

void loop()
{
    // Save the state of the button at the beginning of each round.
    // We used to use this information to tell us when to begin a capture,
    // but now that we used signals that functionality has been disabled.
    //bool buttonIsPressed = buttonIsPressed();
    if (doCapture)
    {
        // Ms at start of this round. Only used for metrics.
        // We get the current ms for the timestamp of a capture frame
        // individually for each sensor.
        unsigned long currentMs = millis();
        
        if (isFirstCaptureRound)
        {
            // No longer the first capture round.
            isFirstCaptureRound = false;

            // We will time each frame seperately, but we can use the first round start time as a basepoint.
            firstCaptureRoundMs = currentMs;

            lastTonguePeakMs = firstCaptureRoundMs;
            lastThroatPeakMs = firstCaptureRoundMs;
        }

        // _____________
        // DATA CAPTURE.

        // ==TONGUE== //

        // Remove old data from the capture frame.
        clearCaptureFrame(captureFrame);

        // Once the slave has new gyro and accl data...
        waitUntilReady(TONGUE_SLAVE);
        // ...read that data into the capture frame.
        captureFrameFromSlave(TONGUE_SLAVE, captureFrame);

        // In transmit mode we send the captures to the receiver.
        if (TRANSMIT_MODE)
        {
            serialWriteFrame(captureFrame);
        }

        // In demo mode we deal with the LED strip metrics.
        if (DEMO_MODE)
        {
            // Do a calibration and scale the data into real units on the transmitter side.
            // Remember that we transmitted the data before calibrating since the receiver should get the raw data,
            // but since we are doing an analysis of the data here, we need to calibrate and scale.
            calibrateCaptureFrame(captureFrame, TONGUE_SLAVE);
            scaleCaptureFrame(captureFrame);

            double mag = magnitude(captureFrame->reading[0],
                                   captureFrame->reading[1],
                                   captureFrame->reading[2]);
                                   
            if (mag > MAGNITUDE_THRESHOLD)
            {
                // For the purposes of the magnitude metric, we only consider values above the threshold.
                tongueSampleCount++;
                tongueTotalMagnitude += mag;

                // If we currently can't have a blindspot, that either means we are in one now,
                // or we had not yet reached the first point above MAGNITUDE_THRESHOLD.
                // Now that we are reading that high, we are no longer in a blindspot, and we are eligable for one
                // when we start reading low again.
                if (!tongueCanHaveBlindspot)
                {
                    tongueCanHaveBlindspot = true;
                    // If we were in a blindspot...
                    if (tongueOnBlindspot)
                    {
                        // ...add it to our metric data.
                        tongueOnBlindspot = false;
                        unsigned long blindspotDuration = (currentMs - tongueBlindspotStartMs);
                        if (blindspotDuration >= BLINDSPOT_DURATION_MIN)
                        {
                            tongueBlindspotWidthTotal += (currentMs - tongueBlindspotStartMs);
                            tongueBlindspotCount++;
                        }
                    }
                }

                // Peak metric - if we are above the peak threshold...
                if (mag > PEAK_MAGNITUDE_THRESHOLD)
                {
                    // ...and we have just dropped steeply...
                    if (lastTongueMagnitude - mag > PEAK_MAGNITUDE_CHANGE_THRESHOLD)
                    {
                        // ...then we should count this as a peak.
                        unsigned long sinceLastPeak = currentMs - lastTonguePeakMs;
    
                        if (sinceLastPeak < PEAK_DISTANCE_MAX)
                        {
                            tonguePeakDistanceTotalMs += sinceLastPeak;
                            tonguePeakCount++;
                        }
                        
                        lastTonguePeakMs = currentMs;
                    }
                }
            }
            else
            {
                // Since we are reading low, if we are eligable for a new blindspot, start one.
                if (tongueCanHaveBlindspot)
                {
                    tongueBlindspotStartMs = currentMs;
                    tongueCanHaveBlindspot = false;
                    tongueOnBlindspot = true;
                }
            }

            lastTongueMagnitude = mag;
        }

        // ==THROAT== //

        clearCaptureFrame(captureFrame);
        
        waitUntilReady(THROAT_SLAVE);
        captureFrameFromSlave(THROAT_SLAVE, captureFrame);

        if (TRANSMIT_MODE)
        {
            serialWriteFrame(captureFrame);
        }

        if (DEMO_MODE)
        {
            calibrateCaptureFrame(captureFrame, THROAT_SLAVE);
            scaleCaptureFrame(captureFrame);

            double mag = magnitude(captureFrame->reading[0],
                                   captureFrame->reading[1],
                                   captureFrame->reading[2]);

            if (mag > MAGNITUDE_THRESHOLD)
            {
                throatSampleCount++;
                throatTotalMagnitude += mag;

                if (!throatCanHaveBlindspot)
                {
                    throatCanHaveBlindspot = true;
                    if (throatOnBlindspot)
                    {
                        throatOnBlindspot = false;
                        unsigned long blindspotDuration = (currentMs - throatBlindspotStartMs);
                        if (blindspotDuration >= BLINDSPOT_DURATION_MIN)
                        {
                            throatBlindspotWidthTotal += (currentMs - throatBlindspotStartMs);
                            throatBlindspotCount++;
                        }
                    }
                }
                
                if (mag > PEAK_MAGNITUDE_THRESHOLD)
                {
                    if (lastThroatMagnitude - mag > PEAK_MAGNITUDE_CHANGE_THRESHOLD)
                    {
                        unsigned long sinceLastPeak = currentMs - lastThroatPeakMs;
    
                        if (sinceLastPeak < PEAK_DISTANCE_MAX)
                        {
                            throatPeakDistanceTotalMs += sinceLastPeak;
                            throatPeakCount++;
                        }
                        
                        lastThroatPeakMs = currentMs;
                    }
                }
            }
            else
            {
                if (throatCanHaveBlindspot)
                {
                    throatBlindspotStartMs = currentMs;
                    throatCanHaveBlindspot = false;
                    throatOnBlindspot = true;
                }
            }
            
            lastThroatMagnitude = mag;
        }

        // When we receive a SIG_ENOUGH, end the capture and transmission.
        if (/*(buttonIsPressed && !buttonWasPressed) || */(Serial.available() > 0 && Serial.read() == SIG_ENOUGH))
        {
            if (TRANSMIT_MODE)
            {
                // Send a frame with the end marker.
                clearCaptureFrame(captureFrame);
                captureFrame->flag = 0b00000001;
                // Even though we are not sending any data, we need to use a valid checksum so that the receiver
                // doesn't just throw out this frame.
                captureFrame->checksum = 0b00000001;
                serialWriteFrame(captureFrame);
            }
            endCapture();
        }
    }
    else
    {
        // When we receive a SIG_REQUEST, begin a new capture.
        if (/*(buttonIsPressed && !buttonWasPressed) || */(Serial.available() > 0 && Serial.read() == SIG_REQUEST))
        {
            beginCapture();
        }
        else
        {
            delay(5);
        }
    }
    
    //buttonWasPressed = buttonIsPressed;
}

/**
 * Given a FRAME *, write the data it points to over serial.
 */
void serialWriteFrame(FRAME *frame)
{
    // We can't write a struct directly because the method doesn't accept one,
    // but the clever solution is to treat it as a byte pointer.
    Serial.write((byte *) frame, sizeof *frame);
}

/**
 * Populate the FRAME indicated by the given FRAME * with
 * capture data that we will read from the indicated MEMS.
 */
void captureFrameFromSlave(int id, FRAME *frame)
{
    // Timestamp is calculated here with a call to millis,
    // right after data became available and right before we go to read it.
    frame->timestamp = millis() - firstCaptureRoundMs;

    // Reading.
    // Clear the buffer, then
    // start at the gyro address and read right through until the end of the accl readings into a buffer.
    memset(dataBuffer, 0, NUM_BYTES);
    readMany(id, dataBuffer, NUM_BYTES, ADDR_GYRO);
    // With the data buffer, fill the capture frame.
    fillFrameReading(frame, dataBuffer, NUM_BYTES);

    // Flags.
    // See MEMS.h for details on the flags int8.
    // The end flag is not set here because we have no indication of
    // whether or not this is the last capture.
    // The end flag will be set in the loop function on a specifically
    // crafted frame which indicates the end of transmission.
    int8_t flag = 0UL;
    // Sensor id flag.
    switch (id)
    {
        case THROAT_SLAVE:
            flag = setBit(flag, 1);
            break;
    }
    // Pushbutton flag.
    if (buttonIsPressed())
    {
        flag = setBit(flag, 7);
    }
    frame->flag = flag;

    // XOR checksum of every byte in the struct (with the exception of the checksum itself).
    int8_t checksum = 0;
    // Simply iterate over the bytes in the struct.
    byte *ptr = (byte *) frame;
    for (unsigned int i = 0; i < sizeof * frame; i++)
    {
        checksum ^= *(ptr + i);
    }
    frame->checksum = checksum;
}

/**
 * Set every byte of the FRAME to 0.
 */
void clearCaptureFrame(FRAME *frame)
{
    memset(frame, 0, sizeof * frame);
}

/**
 * From a raw capture buffer, fill a FRAME.
 */
void fillFrameReading(FRAME *frame, byte *buf, unsigned int bufLen)
{
    for (unsigned int i = 0; i < bufLen; i += 2)
    {
        // Each reading is a combination of two bytes. Remember that the low byte was read first, so it's first in the buf.
        frame->reading[i / 2] = makeSignedWord(buf[i + 1], buf[i]);
    }
}

/**
 * Return only once dataReady returns true for the given id.
 */
void waitUntilReady(int id)
{
    do
    {
        // todo: see what delay is best
        delayMicroseconds(5);
    }
    while (!dataReady(id));
}

/**
 * Returns whether or not the indicated sensor's gyro and accl both have new data.
 */
bool dataReady(int id)
{
    int8_t statusBits = readAddress(id, ADDR_STATUS);
    return bitRead(statusBits, GYRO_STATUS_INDEX) && bitRead(statusBits, ACCL_STATUS_INDEX);
}

/**
 * Like the library macro bitSet, but it returns the new value rather than modifying a variable.
 * The old value will be returned but with the bit at the specified index guaranteed to be a 1.
 */
int8_t setBit(int8_t int8, int8_t index)
{
    return int8 | (1UL << index);
}

/**
 * Given an address of the low byte, assuming the next address is the high byte, read as a 16 bit two's compliment word.
 * @param lowAddress the address of the low byte.
 * @return a 16 bit two's compliment word (int16_t).
 * (this method is never used because we read all of the sensor data at the same time)
 */
int16_t readSensor(int id, byte lowAddress)
{
    static byte bytes[2];
    readMany(id, bytes, 2, lowAddress);

    // Remember that the lsb (low byte) is read first.
    return makeSignedWord(bytes[1], bytes[0]);
}

/**
 * Create a 16 bit signed value from two bytes, assuming each byte is 8 bits.
 * @param msb the most significant (high) byte.
 * @param lsb the least significant (low) byte.
 * @return a 16 bit signed word respecting msb and lsb.
 */
int16_t makeSignedWord(byte msb, byte lsb)
{
    int16_t wd = (int16_t) msb;
    wd <<= 8;
    wd |= (int16_t) lsb;
    return wd;
}

/**
 * Turn off the pixels from each of the three demo LED strips.
 * @precondition DEMO_MODE == 1.
 */
void clearStrips(void)
{
    magnitudeStrip.clear();
    frequencyStrip.clear();
    blindspotStrip.clear();

    magnitudeStrip.show();
    frequencyStrip.show();
    blindspotStrip.show();
}

