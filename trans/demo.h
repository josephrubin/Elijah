#ifndef DEMO_H
#define DEMO_H

/**
 * Items for running a demo of the prototype's capabilities on the Arduino.
 * @author Joseph Rubin
 */

#include "mems.h"

// The highest positive value of a sixteen bit, two's complement number.
#define SIXTEEN_BIT_MAX_VALUE 32767.0

/**
 * Apply calibration constants to the readings from a frame.
 * We send raw readings to the receiver (it does the calibration itself),
 * but afterwards, for the purposes of demo mode (the light strips),
 * we must do our own corrections.
 */
void calibrateCaptureFrame(FRAME *frame, int sensor);

/**
 * Scale raw readings to
 * gyroscope: degrees per second, or
 * accelerometer: g's.
 * We send raw readings to the receiver (it does the scaling itself),
 * but afterwards, for the purposes of demo mode (the light strips),
 * we must do our own corrections.
 */
void scaleCaptureFrame(FRAME *frame);

#endif /* DEMO_H */
