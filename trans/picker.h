#ifndef PICKER_H
#define PICKER_H

#include "color.h"

/**
 * Color pickers for the LED strips.
 * @author Joseph Rubin
 */

/**
 * Returns a color given an LED index for the magnitude LED strip.
 */
color_t magnitudeMeter(int i);

/**
 * Returns a color given an LED index for the frequency LED strip.
 */
color_t frequencyMeter(int i);

/**
 * Returns a color given an LED index for the blindspot LED strip.
 */
color_t blindspotMeter(int i);

#endif /* PICKER_H */
