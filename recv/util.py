"""General utilities used by many of the scripts."""

__author__ = 'Joseph Rubin'

from serial.tools.list_ports import comports
from math import sqrt
import os

# The highest value we can store in a 16 bit value.
SIXTEEN_BIT_MAX_VALUE = 32767


def get_arduino_port():
    """Return the first serial port connected to an Arduino Uno."""
    return get_port_of('Arduino Uno')


def get_port_of(device_name: str):
    """Return the first serial port that is connected to a device, given its name."""
    for port in comports():
        if device_name in port.description:
            return port.device
    return None


def format_csv(items):
    """Return a comma-delimited string from the given items."""
    return ','.join(str(item) for item in items)


def get_capture_subdirectory(capture_number: int):
    """Given a capture number, return its proper subdirectory name.

    For example, raw and processed data associated with a capture are stored under a subdirectory with its proper name.
    Capture three would have a subdirectory name of 'capture00003/'
    """
    return 'capture{}/'.format(str(capture_number).zfill(5))


def raw_capture_exists(capture_number):
    """Return whether the capture indicated by capture_number exists."""
    return os.path.isdir('raw/' + get_capture_subdirectory(capture_number))


def calculate_dps(gyro_reading, max_dps):
    """Return degrees per second from a gyroscope reading."""
    return gyro_reading * (max_dps / SIXTEEN_BIT_MAX_VALUE)


def calculate_gs(accl_reading, max_gs):
    """Return gs (number of gravitational accelerations) from an accelerometer reading."""
    return accl_reading * (max_gs / SIXTEEN_BIT_MAX_VALUE)


def magnitude(a, b, c):
    """Returns the 3d vector magnitude."""
    return sqrt((a * a) + (b * b) + (c * c))
