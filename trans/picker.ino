#include "picker.h"
#include "color.h"

/**
 * Color pickers for the LED strips.
 * @author Joseph Rubin
 */

// Amount of color to change by per LED.
const double STEP_PER_LED = (double) 0xFF / LED_COUNT;

// The color for our strips is RGB.
// That means a single byte for each color component where the MSByte is red and the LSByte is blue.

color_t magnitudeMeter(int i)
{
    // Gradient from red to green.
    color_t redPart = 0xFF - (i * STEP_PER_LED);
    color_t greenPart = 0x00 + (i * STEP_PER_LED);

    return (redPart << 16) + (greenPart << 8);
}

color_t frequencyMeter(int i)
{
    // Gradient from blue to red.
    color_t bluePart = 0xFF - (i * STEP_PER_LED);
    color_t redPart = (i * STEP_PER_LED);

    return (redPart << 16) + bluePart;
}

color_t blindspotMeter(int i)
{
    // Gradient from green to blue.
    color_t greenPart = 0xFF - (i * STEP_PER_LED);
    color_t bluePart = 0x00 + (i * STEP_PER_LED);

    return (greenPart << 8) + bluePart;
}

