"""A Configuration class to make it easier to deal with config values."""

__author__ = 'Joseph Rubin'


class Config(object):
    # The gyro_scale represents the gyroscope max dps.
    # The accl_scale represents the accelerometer max g's.
    __slots__ = ['capture_rate', 'gyro_scale', 'accl_scale']

    def __init__(self, *, capture_rate, gyro_scale, accl_scale):
        self.capture_rate = capture_rate
        self.gyro_scale = gyro_scale
        self.accl_scale = accl_scale
