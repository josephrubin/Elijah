/**
 * Items for runing a demo of the prototype's capabilities on the Arduino.
 * @author Joseph Rubin
 */

#include "demo.h"
#include "calibgen.h"

extern const GYRO_SCALE_t GYRO_SCALE;
extern const ACCL_SCALE_t ACCL_SCALE;

void calibrateCaptureFrame(FRAME *frame, int sensor)
{
    // We simply subtract the at-rest readings.
    // We only calibrate the gyro because that is all that we use for demo mode.
    // (The receiver code does its own calibration of both gyro and accl).
    if (sensor == TONGUE_SLAVE)
    {
        frame->reading[0] -= TONGUE_GYRO_X;
        frame->reading[1] -= TONGUE_GYRO_Y;
        frame->reading[2] -= TONGUE_GYRO_Z;
    }
    else if (sensor == THROAT_SLAVE)
    {
        frame->reading[0] -= THROAT_GYRO_X;
        frame->reading[1] -= THROAT_GYRO_Y;
        frame->reading[2] -= THROAT_GYRO_Z;
    }
}

void scaleCaptureFrame(FRAME *frame)
{
    // We only scale the gyro because that is all that we use for demo mode.
    // (The receiver code does its own scaling of both gyro and accl).
    frame->reading[0] = frame->reading[0] * (GYRO_SCALE / SIXTEEN_BIT_MAX_VALUE);
    frame->reading[1] = frame->reading[1] * (GYRO_SCALE / SIXTEEN_BIT_MAX_VALUE);
    frame->reading[2] = frame->reading[2] * (GYRO_SCALE / SIXTEEN_BIT_MAX_VALUE);

    /*
        frame->reading[3] = frame->reading[3] * (ACCL_SCALE / SIXTEEN_BIT_MAX_VALUE);
        frame->reading[4] = frame->reading[4] * (ACCL_SCALE / SIXTEEN_BIT_MAX_VALUE);
        frame->reading[5] = frame->reading[5] * (ACCL_SCALE / SIXTEEN_BIT_MAX_VALUE);
    */
}

