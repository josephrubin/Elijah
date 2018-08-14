#!/usr/bin/env python3
"""Print accl readings to the console in order to test it out.

This is NOT production code, but instead a quick way to test the sensors.
This also acts as a demo of sorts for the custom handler feature of capture.py.

Modify the variable CHOSEN_ID to choose the sensor you would like to test.
"""

__author__ = 'Joseph Rubin'

import sys

import capture
from calibration_generated import *
from const import *
from util import *
from serial import SerialException


# Choose the sensor you would like to test.
CHOSEN_ID = TONGUE_SENSOR_ID


def main():
    # Make a serial connection and open it.
    con = capture.make_con()
    try:
        con.open()
    except SerialException:
        raise Exception('Please make sure the device is plugged in\n           and no program is using it!')
    # We must wait until the transmitter gives us a SIG_READY so we know we can make requests.
    capture.wait_for_sig_ready(con)

    # Start automatically by sending a SIG_REQUEST.
    con.write(SIG_REQUEST)
    con.flush()

    # Have frames delivered to show_accl.
    capture.capture_frames(con, show_accl)


def show_accl(frame, frame_count, config):
    # Skip all frames that are not from the sensor that we want.
    if frame.flag.sensor != CHOSEN_ID:
        return True

    # Scale and calibrate the readings.
    if CHOSEN_ID == TONGUE_SENSOR_ID:
        reading_x = calculate_gs(frame.reading.accl_x - calib.tongue.accl.x, config.accl_scale)
        reading_y = calculate_gs(frame.reading.accl_y - calib.tongue.accl.y, config.accl_scale)
        reading_z = calculate_gs(frame.reading.accl_z - calib.tongue.accl.z, config.accl_scale)
    elif CHOSEN_ID == THROAT_SENSOR_ID:
        reading_x = calculate_gs(frame.reading.accl_x - calib.throat.accl.x, config.accl_scale)
        reading_y = calculate_gs(frame.reading.accl_y - calib.throat.accl.y, config.accl_scale)
        reading_z = calculate_gs(frame.reading.accl_z - calib.throat.accl.z, config.accl_scale)
    else:
        raise Exception('Invalid CHOSEN_ID!')

    sys.stdout.write('\r{: 0.2f}g\t{: 0.2f}g\t{: 0.2f}g\t\t'.format(reading_x, reading_y, reading_z))
    sys.stdout.flush()

    # Remember to return true to signal that we want more frames.
    return True


if __name__ == '__main__':
    main()
