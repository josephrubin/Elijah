#ifndef PATTERN_H
#define PATTERN_H

#include "color.h"

/**
 * Small library of LED strip functions.
 * @author Joseph Rubin
 */

// This value, when passed as count, means to use as many pixels as the device has when performing patterns.
#define COUNT_ALL 0U

// Versions that take a ColorPicker instead of a color_t allow you to provide a function that returns a distinct color for each light (see ./color.h).

/**
 * Sets every LED of the strip to the specified color.
 * @param strip the strip to modify.
 * @param color the color to apply.
 */
void fill(Adafruit_NeoPixel *strip, unsigned int count, color_t color);

/**
 * Sets every LED of the strip according to the colorPicker function.
 * @param strip the strip to modify.
 * @param colorPicker a function of the current LED which says what color_t to apply to it.
 */
void fill(Adafruit_NeoPixel *strip, unsigned int count, ColorPicker colorPicker);

/**
 * Causes the LEDs to light up in succession.
 * @param strip the strip to modify.
 * @param delayMs the amount of ms to wait after each LED.
 * @param colorPicker a function of the current LED which says what color_t to apply to it.
 */
void wave(Adafruit_NeoPixel *strip, unsigned int count, long delayMs, color_t color);

/**
 * Causes the LEDs to light up in succession.
 * @param strip the strip to modify.
 * @param delayMs the amount of ms to wait after each LED.
 * @param color what color_t to make each LED.
 */
void wave(Adafruit_NeoPixel *strip, unsigned int count, long delayMs, ColorPicker colorPicker);

#endif /* PATTERN_H */

