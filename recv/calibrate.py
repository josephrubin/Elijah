#!/usr/bin/env python3

"""Calibrate the MEMS devices by assuming their gyroscope readings when at rest should be 0 and their accelerometers should read gravity.

Accelerometer calibration assumes that the device is at rest with the black box facing up.
That is, it should read 1 g in the z axis, and 0 g on the x and y axes.
Place the device in this way so that it doesn't move, then run this module.

We simply apply a constant bias to all readings based on their average rest readings.
This form of calibration is only valid for linear error.

You can check the validity of your calibration by running gyro_test (should get 0, 0, 0)
and accl_test (should get 0, 0, 1) while the device is still in the correct position.

NOTE THAT READINGS FROM THE SENSORS CHANGE DEPENDING ON TEMPERATURE, SO THEY SHOULD BE CALIBRATED IN THE OPERATING ENVIRONMENT,
UNLESS TEMPERATURE DATA IS USED ON-THE-FLY FROM THE TEMPERATURE SENSOR (WHICH IS NOT CURRENTLY THE CASE).
"""

__author__ = 'Joseph Rubin'

from serial import SerialException
import capture
from const import *
from util import *

OUTPUT_DIRECTORY_PYTHON_ROOT = './'
OUTPUT_DIRECTORY_HEADER_ROOT = '../trans/'

# The higher this value, the more samples we gather, but the longer it will take.
# Please understand that raising this to more than a few seconds won't make our calibration much more accurate.
DURATION_SECONDS = 8


def main():
    # Make a serial connection and open it.
    con = capture.make_con()
    try:
        con.open()
    except SerialException:
        raise Exception('Please make sure the device is plugged in\n           and no program is using it!')

    # Wait until the transmitter is ready.
    capture.wait_for_sig_ready(con)

    # Start automatically by sending a SIG_REQUEST.
    con.write(SIG_REQUEST)
    con.flush()

    capture.capture_frames(con, *calibrate_wrapper(OUTPUT_DIRECTORY_PYTHON_ROOT, OUTPUT_DIRECTORY_HEADER_ROOT))
    con.close()


def calibrate_wrapper(output_path_python, output_path_header):
    # This wrapper function allows us to return a custom version of our custom handler. (we are defining a closure)
    # That is, the following code will run just once.

    # Prepare our output files.
    # We will write a python file (for the receiver) and a header file (for demo mode on the transmitter).
    output_filename_python = output_path_python + 'calibration_generated.py'
    output_filename_header = output_path_header + 'calibgen.h'

    # debug
    #print('$ Writing:', output_filename_python)
    #print('$ Writing:', output_filename_header)

    output_python = open(output_filename_python, 'w')
    try:
        writing_header_file = True
        output_cpp = open(output_filename_header, 'w')
    except FileNotFoundError:
        # If there was a problem creating the C++ header file, don't let it stop us from writing the python file.
        writing_header_file = False
        # debug
        print('$ Error writing C++ header file. Maybe the file is open somewhere else? Skipping.')

    # Save capture values so we can average them at the end.
    tongue_values = []
    throat_values = []

    def sample(frame, frame_count, config):
        if frame.flag.sensor == TONGUE_SENSOR_ID:
            tongue_values.append((frame.reading.gyro_x, frame.reading.gyro_y, frame.reading.gyro_z,
                                  frame.reading.accl_x, frame.reading.accl_y, frame.reading.accl_z))
        elif frame.flag.sensor == THROAT_SENSOR_ID:
            throat_values.append((frame.reading.gyro_x, frame.reading.gyro_y, frame.reading.gyro_z,
                                  frame.reading.accl_x, frame.reading.accl_y, frame.reading.accl_z))

        # We divide by two because we are capturing from two sensors.
        return frame_count / config.capture_rate / 2 < DURATION_SECONDS

    def generate(frame_count, bad_checksum_count, config):
        # debug
        print('$ Captured', frame_count, 'frames.')
        print('$ Found', bad_checksum_count, 'bad checksums.')

        def _slice(lst, col):
            """Return as a list the col'th values from every tuple in lst."""
            return [row[col] for row in lst]

        # Our calibration will be the average of our at-rest readings.
        # The exception is accl_z which should be calibrated to read 1g.
        tongue_gyro_x = avg(_slice(tongue_values, 0))
        tongue_gyro_y = avg(_slice(tongue_values, 1))
        tongue_gyro_z = avg(_slice(tongue_values, 2))

        tongue_accl_x = avg(_slice(tongue_values, 3))
        tongue_accl_y = avg(_slice(tongue_values, 4))
        tongue_accl_z = avg(_slice(tongue_values, 5)) - (SIXTEEN_BIT_MAX_VALUE / config.accl_scale)

        throat_gyro_x = avg(_slice(throat_values, 0))
        throat_gyro_y = avg(_slice(throat_values, 1))
        throat_gyro_z = avg(_slice(throat_values, 2))

        throat_accl_x = avg(_slice(throat_values, 3))
        throat_accl_y = avg(_slice(throat_values, 4))
        throat_accl_z = avg(_slice(throat_values, 5)) - (SIXTEEN_BIT_MAX_VALUE / config.accl_scale)

        # Values in the order they will be written.
        order = [tongue_gyro_x, tongue_gyro_y, tongue_gyro_z,
                 tongue_accl_x, tongue_accl_y, tongue_accl_z,
                 throat_gyro_x, throat_gyro_y, throat_gyro_z,
                 throat_accl_x, throat_accl_y, throat_accl_z]

        output_python.write(CALIB_PY_TEMPLATE.format(*order))
        output_python.close()

        if writing_header_file:
            output_cpp.write(CALIB_H_TEMPLATE.format(*order))
            output_cpp.close()

    return sample, None, generate


def avg(lst):
    s = 0
    for item in lst:
        s += item
    return s / len(lst)


def format_csv(tup):
    return ','.join([str(tup[i]) for i in range(len(tup))])


# Below are the output templates for our generated calibration files.

CALIB_PY_TEMPLATE = """\
\"\"\"THIS IS AN AUTO-GENERATED FILE
Do not edit this file manually.
If you want to recalibrate the sensors, follow the instructions in calibrate.py.

If you are looking to use the calibration data, you should include:
from calibration_generated import *
We use * rather than calib so that we do not get an error if this file was not generated properly and we are trying to regenerate it.
\"\"\"


class _Type(object):
    __slots__ = ['x', 'y', 'z']

    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        
        
class _Sensor(object):
    __slots__ = ['gyro', 'accl']

    def __init__(self, gyro: _Type, accl: _Type):
        self.gyro = gyro
        self.accl = accl

        
class _Calib(object):
    __slots__ = ['tongue', 'throat']

    def __init__(self, tongue: _Sensor, throat: _Sensor):
        self.tongue = tongue
        self.throat = throat


_tongue_gyro_x = {}
_tongue_gyro_y = {}
_tongue_gyro_z = {}

_tongue_accl_x = {}
_tongue_accl_y = {}
_tongue_accl_z = {}

_throat_gyro_x = {}
_throat_gyro_y = {}
_throat_gyro_z = {}

_throat_accl_x = {}
_throat_accl_y = {}
_throat_accl_z = {}

_tongue_gyro = _Type(_tongue_gyro_x, _tongue_gyro_y, _tongue_gyro_z)
_tongue_accl = _Type(_tongue_accl_x, _tongue_accl_y, _tongue_accl_z)
_throat_gyro = _Type(_throat_gyro_x, _throat_gyro_y, _throat_gyro_z)
_throat_accl = _Type(_throat_accl_x, _throat_accl_y, _throat_accl_z)

_tongue = _Sensor(_tongue_gyro, _tongue_accl)
_throat = _Sensor(_throat_gyro, _throat_accl)

calib = _Calib(_tongue, _throat)
"""

CALIB_H_TEMPLATE = """\
#ifndef CALIB_GENERATED_H
#define CALIB_GENERATED_H

/*
 * THIS IS AN AUTO-GENERATED FILE
 * Do not edit this file manually.
 * If you want to re-calibrate the sensors, follow the instructions in the spec for ../recv/calibrate.py.
 */

#define TONGUE_GYRO_X {}
#define TONGUE_GYRO_Y {}
#define TONGUE_GYRO_Z {}

#define TONGUE_ACCL_X {}
#define TONGUE_ACCL_Y {}
#define TONGUE_ACCL_Z {}

#define THROAT_GYRO_X {}
#define THROAT_GYRO_Y {}
#define THROAT_GYRO_Z {}

#define THROAT_ACCL_X {}
#define THROAT_ACCL_Y {}
#define THROAT_ACCL_Z {}

#endif /* CALIB_GENERATED_H */
"""


if __name__ == '__main__':
    main()
