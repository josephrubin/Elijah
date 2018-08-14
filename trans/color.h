#ifndef COLOR_H
#define COLOR_H

/**
 * @author Joseph Rubin
 */

// When setting an LED of a strip using NEO_GRB + NEO_KHZ800 (e.g. Adafruit_NeoPixel(LED_COUNT, STRIP_INPUT_PIN, NEO_GRB + NEO_KHZ800))
// we can rely on our color_t being no larger than a uint32_t.
typedef uint32_t color_t;

// A function that takes an LED index and returns a color_t.
// The purpose is to pass these functions to wave or fill of ./pattern.h
// to specify a color for each LED of the strip.
// See ./picker.h for the ones that we use for the metric LED strips.
typedef color_t (*ColorPicker)(int index);

#endif /* COLOR_H */

