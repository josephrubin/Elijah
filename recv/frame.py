"""These classes make it easier to work with our frames.

By using __slots__, we essentially make a dictionary that we can access using '.' rather than '[]'.
It also allows our editor to complete our typing,
and the compiler will give us an error if we try to access an illegal field (rather than have a runtime error).
"""

__author__ = 'Joseph Rubin'


class Reading(object):
    __slots__ = ['gyro_x', 'gyro_y', 'gyro_z', 'accl_x', 'accl_y', 'accl_z']

    def __init__(self, gyro_x, gyro_y, gyro_z, accl_x, accl_y, accl_z):
        self.gyro_x = gyro_x
        self.gyro_y = gyro_y
        self.gyro_z = gyro_z

        self.accl_x = accl_x
        self.accl_y = accl_y
        self.accl_z = accl_z


class Flag(object):
    __slots__ = ['end', 'sensor', 'button']

    def __init__(self, *, end: bool, sensor: int, button: bool):
        self.end = end
        self.sensor = sensor
        self.button = button


class Frame(object):
    __slots__ = ['flag', 'time', 'reading']

    def __init__(self, time: int, flag: Flag, reading: Reading):
        self.time = time
        self.flag = flag
        self.reading = reading
