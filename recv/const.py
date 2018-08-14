"""Constants for Elijah.

Recommended use:
from const import *
"""

__author__ = 'Joseph Rubin'

# Used to differentiate between the sensors.
# These values match the flag value that identifies a sensor.
TONGUE_SENSOR_ID = 0
THROAT_SENSOR_ID = 1

TRANSMITTER_BAUD_RATE = 1000000
MS_PER_SECOND = 1000

# Signals. See spec/ for more information on what they mean.

# Transmitter is ready for requests.
SIG_READY = b'\x24\x25\x26'

# Request a capture.
SIG_REQUEST = b'\x3C'
# We are done with a capture.
SIG_ENOUGH = b'\x3E'

# Capture has begun.
SIG_HEAD = b'\x22'
# Capture request was denied.
SIG_DENIED = b'\x21'


class RequestDeniedException(Exception):
    """Raised when a SIG_REQUEST was replied to with a SIG_DENIED."""
    pass
