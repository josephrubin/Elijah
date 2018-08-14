#include <Adafruit_NeoPixel.h>
#include "pattern.h"
#include "color.h"

/**
 * Small library of LED strip functions.
 * @author Joseph Rubin
 */

void fill(Adafruit_NeoPixel *strip, unsigned int count, color_t color)
{
    strip->clear();
    strip->show();

    // If the count was COUNT_ALL, use all of the LEDs available to the LED strip.
    if (count == COUNT_ALL)
    {
        count = strip->numPixels();
    }

    // Set every pixel...
    for (unsigned int i = 0; i < count; i++)
    {
        strip->setPixelColor(i, color);
    }

    // ...and only after do we call show, so that it is all shown at once.
    strip->show();
}

void fill(Adafruit_NeoPixel *strip, unsigned int count, ColorPicker colorPicker)
{
    strip->clear();
    strip->show();
    
    if (count == COUNT_ALL)
    {
        count = strip->numPixels();
    }
    
    for (unsigned int i = 0; i < count; i++)
    {
        // Rather than set the LEDs to a specified color, we use the output of the provided ColorPicker.
        strip->setPixelColor(i, colorPicker(i));
    }
    
    strip->show();
}

void wave(Adafruit_NeoPixel *strip, unsigned int count, long delayMs, color_t color)
{
    strip->clear();
    strip->show();
    
    if (count == COUNT_ALL)
        count = strip->numPixels();
    
    for (unsigned int i = 0; i < count; i++)
    {
        // We call show in between each LED, before the delay, so that we get the 'wave' effect.
        strip->setPixelColor(i, color);
        strip->show();
        delay(delayMs);
    }
}

void wave(Adafruit_NeoPixel *strip, unsigned int count, long delayMs, ColorPicker colorPicker)
{
    strip->clear();
    strip->show();
    
    if (count == COUNT_ALL)
        count = strip->numPixels();
    
    for (unsigned int i = 0; i < count; i++)
    {
        strip->setPixelColor(i, colorPicker(i));
        strip->show();
        delay(delayMs);
    }
}
