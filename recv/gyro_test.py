#!/usr/bin/env python3
"""Print gyro readings to the console in order to test it out.

This is NOT production code, but instead a quick way to test the sensors.
This also acts as a demo of sorts for the custom handler feature of capture.py.

Modify the variable CHOSEN_ID to choose the sensor you would like to test.
"""

__author__ = 'Joseph Rubin'

from calibration_generated import *
import capture
from util import *
from const import *
from serial import SerialException
import sys


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

    # Have frames delivered to show_gyro.
    capture.capture_frames(con, show_gyro)


def show_gyro(frame, _frame_count, config):
    # Skip all frames that are not from the sensor that we want.
    if frame.flag.sensor != CHOSEN_ID:
        return True

    # Our gyro gives us outputs which are mappable to deg/sec from the range of a 16bit, signed value.
    # By resolving the mapping, and then integrating these readings w/r/t time, we obtain deg.
    # Without some sort of filter, e.g. the Kalman filter (which combines gyro and accl readings), we will never get accurate
    # absolute measurements. A second issue is that if our full-scale range is set small, we will never be able to capture fast movement.
    # But this isn't a problem - we aren't interested in absolute angles,
    # just their change over time - we are monitoring swallowing, not flying a drone.
    # We won't account for dt in this test - we are simply interested in whether or not our calibration was successful.

    # Scale and calibrate the readings.
    if CHOSEN_ID == TONGUE_SENSOR_ID:
        reading_x = calculate_dps(frame.reading.gyro_x - calib.tongue.gyro.x, config.gyro_scale)
        reading_y = calculate_dps(frame.reading.gyro_y - calib.tongue.gyro.y, config.gyro_scale)
        reading_z = calculate_dps(frame.reading.gyro_z - calib.tongue.gyro.z, config.gyro_scale)
    elif CHOSEN_ID == THROAT_SENSOR_ID:
        reading_x = calculate_dps(frame.reading.gyro_x - calib.throat.gyro.x, config.gyro_scale)
        reading_y = calculate_dps(frame.reading.gyro_y - calib.throat.gyro.y, config.gyro_scale)
        reading_z = calculate_dps(frame.reading.gyro_z - calib.throat.gyro.z, config.gyro_scale)
    else:
        raise Exception('Invalid CHOSEN_ID!')

    sys.stdout.write('\r{: 0.2f}°\t{: 0.2f}°\t{: 0.2f}°\t\t'.format(reading_x, reading_y, reading_z))
    sys.stdout.flush()

    # Remember to return true to signal that we want more frames.
    return True


if __name__ == '__main__':
    main()
