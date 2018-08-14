#!/usr/bin/env python3
"""Allows us to define custom handlers for using frames from the Arduino.
The method capture_frames will take care of retrieving the frames.
Simply create a serial connection, then define a handler and plug it in. It will be called with the frame data, frame_count, and config.
The handler should return a boolean indicating whether or not to continue capturing frames.
If it returns False, then we will tell the transmitter not to send any more frames.
    Note that there may still be some frames to give to the handler before the capture is finished
    if the transmitter does not stop right away.
If it returns True, it is up to capture_frames whether or not to continue.

You may optionally define a start_handler which is run before capturing.
It will be called with config.

You may optionally define an end_handler which is run after capturing is completed.
It will be called with frame_count, bad_checksum_count, and config.

@precondition: TRANSMIT_MODE 1
               DEBUG_MODE 0
(these are #defined in the transmitter/Arduino code, make sure their values are correct)
"""

__author__ = 'Joseph Rubin'

import sys
import serial
from serial import SerialException
from serial.serialutil import Timeout
import struct

from const import *
from frame import *
from util import *
from config import Config
from calibration_generated import *

NAME = 'delete_me'

OUTPUT_DIRECTORY_ROOT = 'raw/'
OUTPUT_SUBDIRECTORY = 'capture{}/'

# Fields that we write to the csv file.
HEADERS = ('time', 'gyroX', 'gyroY', 'gyroZ', 'acclX', 'acclY', 'acclZ', 'button')

# How long to capture for (in seconds). This value is only relevant when invoking this file directly (using _main).
# But if we are, for example, capturing from the GUI, this value will be ignored.
DURATION_SECONDS = 5


def _main():
    con = make_con(resetting=True)
    try:
        con.open()
    except SerialException:
        raise Exception('Please make sure the device is plugged in\n           and no program is using it!')
    wait_for_sig_ready(con)

    # Start automatically by sending a SIG_REQUEST.
    con.write(SIG_REQUEST)
    do_writing_capture(con, duration_seconds=DURATION_SECONDS)
    con.close()


def make_con(*, resetting=True, timeout=None):
    """Returns a closed but configured serial connection to the Arduino.

    If resetting is True, the connection will be a resetting connection,
    meaning that it will reset the Arduino when it is opened.

    After opening it you should check con.is_open for success,
    and retrieve con.name to see what was actually opened.

    Understand that if the con is resetting, the connection may finish opening before the Arduino completely resets,
    so don't send anything right away because the Arduino will not receive it! Wait for SIG_READY instead.
    """
    # We use a timeout because it is essentially the only way to recover
    # when the board is disconnected in the middle of a capture.
    con = serial.Serial(timeout=timeout)
    con.port = get_arduino_port()
    con.baudrate = TRANSMITTER_BAUD_RATE
    con.dtr = resetting
    con.terminated = False
    return con


def wait_for_sig_ready(con, *, sig_max_offset=400):
    """Consume bytes in the connection until SIG_READY is encountered (also consumes the signal itself)."""
    until_ready = con.read_until(SIG_READY, sig_max_offset)
    if not until_ready.endswith(SIG_READY):
        raise SerialException('Arduino never sent SIG_READY. Aborting.')


def wait_for_sig_head(con, *, sig_max_offset=30):
    """Consume bytes in the connection until SIG_HEAD is encountered (also consumes the signal itself)."""
    error_message = 'Transmitter never sent SIG_HEAD. Aborting.'
    read_count = 0
    while True:
        b = con.read(1)
        read_count += 1

        if b:
            if b == SIG_HEAD:
                return True
            elif b == SIG_DENIED:
                # debug
                print('Found SIG_DENIED instead')
                return False
        else:
            raise SerialException(error_message)

        if read_count > sig_max_offset:
            raise SerialException(error_message)


def capture_frames(con, handler, start_handler=None, end_handler=None):
    if not wait_for_sig_head(con):
        raise RequestDeniedException()

    # Now we would like to read the configuration data that was sent. See usage of struct.unpack later for more information on the module.
    capture_rate, gyro_scale, accl_scale = struct.unpack('<HHB', con.read(5))
    config = Config(capture_rate=capture_rate, gyro_scale=gyro_scale, accl_scale=accl_scale)

    if start_handler is not None:
        start_handler(config)

    frame_count = 0
    bad_checksum_count = 0
    do_capture = True
    while do_capture:
        raw_frame, frame = read_frame(con)
        frame_count += 1

        # debug
        if frame_count == 1:
            print('$')

        # Resolve the checksum as XOR of every raw byte.
        checksum_resolution = 0
        for byte in raw_frame:
            checksum_resolution ^= byte
        # Since we XOR'd with the Arduino-calculated checksum,
        # we should get zero if the data was successfully received.
        if checksum_resolution != 0:
            print('$ Bad checksum: ' + str(checksum_resolution) + ' - skip!')
            bad_checksum_count += 1
            continue

        # Check end flag to tell us when to stop.
        if frame.flag.end:
            # debug
            print('$ Encountered stop flag.')
            do_capture = False
            # The contents of the frame that has the end flag are to be ignored.
            continue

        # The handler itself can tell us when it's no longer interested in more frames.
        # We don't simply end the capture, we just send a SIG_ENOUGH and let the transmitter
        # send the end frame by itself. This means that until the transmitter decides to stop
        # there may be more frames to give to the handler.
        if not handler(frame, frame_count, config):
            con.write(SIG_ENOUGH)
            con.flush()

    # The optional end_handler is called at the end of capturing.
    if end_handler is not None:
        end_handler(frame_count, bad_checksum_count, config)

    # Notice how we don't close the connection here.
    # It's up to the user to handle the connection,
    # and it's possible to capture more than once before closing it.


def read_frame(con):
    # We read 16 bytes at a time, because that's the size of the struct that the arduino is sending.
    # 2 bytes  (unsigned) time
    # 12 bytes   (signed) reading
    # 1 byte   (unsigned) flags
    # 1 byte   (unsigned) checksum (XOR)
    frame_size = 16
    raw_frame = con.read(frame_size)
    if len(raw_frame) < frame_size:
        raise SerialException('Timeout occurred. Perhaps the board was disconnected.')

    # Struct (module) lets us restore data from structures automatically using a format string to tell it the struct members.
    # The result is put into a tuple.
    # Arduino is little endian, so we use '<'.
    # B = uint8 | H = uint16 | h = int16.
    unpacked_frame = struct.unpack('<HhhhhhhBB', raw_frame)

    flag_byte = unpacked_frame[7]
    flag_dict = {
        # If transmission is over.
        'end': get_bit(flag_byte, 0),
        # What sensor this frame is from. We combine two bits (two's place and unit's place).
        'sensor': (2 * get_bit(flag_byte, 2)) + get_bit(flag_byte, 1),
        # If the button was pressed during this frame.
        'button': get_bit(flag_byte, 7)
    }

    flag = Flag(**flag_dict)
    reading = Reading(*[unpacked_frame[i] for i in range(1, 7)])
    frame = Frame(time=unpacked_frame[0], reading=reading, flag=flag)

    return raw_frame, frame


# Below is a handler configuration that is used to capture data and save to a file.


def do_writing_capture(con: serial.Serial, enable_trailer: bool=True, duration_seconds=None):
    """Capture data from the transmitter and save it to a file. (This does not send a SIG_REQUEST itself.)"""
    # With a duration of None, we will never terminate on our own (we continue until the transmitter sends a frame with the end flag set).

    # Check to make sure that our serial con is good.
    if not con.is_open:
        raise SerialException('Serial did not open.')

    # Since that was successful, we should find a free output path,
    # but don't create it yet in case something goes wrong before we start capturing data.
    output_path = None
    capture_number = -1
    while output_path is None or os.path.isdir(output_path):
        capture_number += 1
        output_path = OUTPUT_DIRECTORY_ROOT + OUTPUT_SUBDIRECTORY.format(str(capture_number).zfill(5))

    # We need to pass the output_path to our handler so we use a wrapper function.
    capture_frames(con, *writing_capture_handler_wrapper(output_path, duration_seconds))

    # Trailer (see the spec under communications protocol for details).
    if enable_trailer:
        while True:
            # noinspection PyArgumentList
            line = con.readline().decode('ascii', errors='ignore')
            if line == '.\r\n' or line == '.\n':
                break
            sys.stdout.write(line)

    # debug
    print('$ End of capture.')

    return output_path


def writing_capture_handler_wrapper(output_path, duration_seconds=None):
    # With a duration of None, we will never terminate on our own (we continue until the transmitter sends a frame with the end flag set).

    # This wrapper function allows us. to return a custom version of our custom handler. (we are defining a closure)
    # That is, the following code will run just once.

    # Prepare our output files.
    # Even though we are capturing 'raw' data, we are still scaling and calibrating it.
    output_filename_tongue = output_path + 'tongue.csv'
    output_filename_throat = output_path + 'throat.csv'
    # But we also keep a copy of the data that is not at all scaled or calibrated (currently we have no use for this).
    output_filename_tongue_no_modification = output_path + 'tongue_unscaled_uncalibrated.csv'
    output_filename_throat_no_modification = output_path + 'throat_unscaled_uncalibrated.csv'

    output_tongue = None
    output_throat = None
    output_tongue_no_modification = None
    output_throat_no_modification = None

    def setup_files(config):
        global output_tongue, output_throat, output_tongue_no_modification, output_throat_no_modification

        os.makedirs(output_path)

        output_tongue = open(output_filename_tongue, 'w')
        output_throat = open(output_filename_throat, 'w')
        output_tongue_no_modification = open(output_filename_tongue_no_modification, 'w')
        output_throat_no_modification = open(output_filename_throat_no_modification, 'w')

        # Write the csv headers.
        output_tongue.write(format_csv(HEADERS) + '\n')
        output_throat.write(format_csv(HEADERS) + '\n')
        output_tongue_no_modification.write(format_csv(HEADERS) + '\n')
        output_throat_no_modification.write(format_csv(HEADERS) + '\n')

        # Save config data as empty files (these are not currently used).
        open(output_path + 'capture_rate_' + str(config.capture_rate), 'w').close()
        open(output_path + 'gyro_scale_' + str(config.gyro_scale), 'w').close()
        open(output_path + 'accl_scale_' + str(config.accl_scale), 'w').close()

        # debug
        #print('$ Writing:', output_filename_tongue)
        #print('$ Writing:', output_filename_throat)

    def write_frames(frame, frame_count, config):
        global output_tongue, output_throat, output_tongue_no_modification, output_throat_no_modification

        flag = frame.flag
        reading = frame.reading

        # Make a raw output string, with no calibration or scaling applied.
        output_string_raw = format_csv((
            frame.time,
            reading.gyro_x, reading.gyro_y, reading.gyro_z,
            reading.accl_x, reading.accl_y, reading.accl_z,
            flag.button
        )) + '\n'

        # Our sensor_id flag tells us which calibration numbers to use.
        if flag.sensor == TONGUE_SENSOR_ID:
            reading.gyro_x -= calib.tongue.gyro.x
            reading.gyro_y -= calib.tongue.gyro.y
            reading.gyro_z -= calib.tongue.gyro.z

            reading.accl_x -= calib.tongue.accl.x
            reading.accl_y -= calib.tongue.accl.y
            reading.accl_z -= calib.tongue.accl.z
        elif flag.sensor == THROAT_SENSOR_ID:
            reading.gyro_x -= calib.throat.gyro.x
            reading.gyro_y -= calib.throat.gyro.y
            reading.gyro_z -= calib.throat.gyro.z

            reading.accl_x -= calib.throat.accl.x
            reading.accl_y -= calib.throat.accl.y
            reading.accl_z -= calib.throat.accl.z

        # Now we can scale the numbers from raw values to dps (for gyro) or gs (for accl).
        reading.gyro_x = calculate_dps(reading.gyro_x, config.gyro_scale)
        reading.gyro_y = calculate_dps(reading.gyro_y, config.gyro_scale)
        reading.gyro_z = calculate_dps(reading.gyro_z, config.gyro_scale)

        reading.accl_x = calculate_gs(reading.accl_x, config.accl_scale)
        reading.accl_y = calculate_gs(reading.accl_y, config.accl_scale)
        reading.accl_z = calculate_gs(reading.accl_z, config.accl_scale)

        # Prepare a line of csv output.
        output_string = format_csv((
            frame.time,
            reading.gyro_x, reading.gyro_y, reading.gyro_z,
            reading.accl_x, reading.accl_y, reading.accl_z,
            flag.button
        )) + '\n'

        # Our sensor_id flag tells us where to output.
        if flag.sensor == TONGUE_SENSOR_ID:
            output_tongue.write(output_string)
            output_tongue_no_modification.write(output_string_raw)
        elif flag.sensor == THROAT_SENSOR_ID:
            output_throat.write(output_string)
            output_throat_no_modification.write(output_string_raw)

        # We divide by two because we are capturing from two sensors.
        return duration_seconds is None or (frame_count / config.capture_rate / 2 < duration_seconds)

    def close_files(frame_count, bad_checksum_count, _config):
        global output_tongue, output_throat, output_tongue_no_modification, output_throat_no_modification

        output_tongue.close()
        output_throat.close()
        output_tongue_no_modification.close()
        output_throat_no_modification.close()

        # Write the name file.
        name_file = open(output_path + 'name.txt', 'w')
        name_file.write(NAME)
        name_file.close()

        # debug
        print('$ Captured', frame_count, 'frames.')
        print('$ Found', bad_checksum_count, 'bad checksums.')

    return write_frames, setup_files, close_files


def get_bit(number, index):
    """Get the index'th bit of a number."""
    return (number >> index) & 1


def format_csv(tup):
    """Join a sequence of values together with commas in between."""
    return ','.join([str(val) for val in tup])


if __name__ == '__main__':
    _main()
