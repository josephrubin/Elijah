"""Process the data from 'raw/' into a form that can be better understood or plotted.

Currently, our processing consists of calculating a vector magnitude for the gyro readings
and collecting the button presses into a single file.
Remember that the 'raw' data is actually already scaled and calibrated.
"""

__author__ = 'Joseph Rubin'

import pandas as pd
from util import *

# These values will be generated from the raw data.
#                          magnitude
PROCESS_HEADERS = ('time', 'gyro_m', 'gyro_x', 'gyro_y', 'gyro_z')

# Directory where the raw data comes from.
INPUT_DIRECTORY_ROOT = 'raw/'

# Directory where the processed data should be output.
OUTPUT_DIRECTORY_ROOT = 'processed/'

# Name of the empty file that is placed in a raw capture subdirectory to indicate that we have processed this capture.
PROCESSED_MARKER_FILENAME = 'processed'


def process_capture(capture_number: int):
    """Given a capture number, process the capture."""
    input_path = INPUT_DIRECTORY_ROOT + get_capture_subdirectory(capture_number)
    output_path = OUTPUT_DIRECTORY_ROOT + get_capture_subdirectory(capture_number)

    # Create the output folder if it is not already there.
    if not os.path.isdir(output_path):
        os.makedirs(output_path)

    def process_sensor_file(input_filename: str, output_filename: str):
        """Process a single sensor."""
        with open(output_filename, 'w') as output_file:
            input_reader = pd.read_csv(input_filename, delimiter=',')

            # Write the csv headers.
            output_file.write(format_csv(PROCESS_HEADERS) + '\n')

            previous_time = 0
            time_offset = 0
            for time, gyro_x, gyro_y, gyro_z in \
                    zip(input_reader.time, input_reader.gyroX, input_reader.gyroY, input_reader.gyroZ):

                # We don't apply calibration data or scaling here because it has already been applied
                # to the file we are reading when it was captured.
                gyro_m = magnitude(gyro_x, gyro_y, gyro_z)

                # We must correct for overflow in the time byte.
                # In the future, it might just be better to increase the size of our timestamp.
                if time < previous_time:
                    # Overflow occurred, correct for it!
                    # We increase the offset that we add to every time value.
                    time_offset += (2**16)
                previous_time = time
                time += time_offset

                output_file.write(format_csv([time, gyro_m, gyro_x, gyro_y, gyro_z]) + '\n')

    def process_button(input_filenames: list, output_filename: str):
        """Generate processed button output, given sensor filenames."""
        # Create a list of all the (non-contiguous) times a button press was reported.
        button_pressed_last_frame = False
        button_press_times = list()
        for input_filename in input_filenames:
            input_reader = pd.read_csv(input_filename, delimiter=',')

            previous_time = 0
            time_offset = 0
            for time, button in zip(input_reader.time, input_reader.button):
                if button == 1:
                    # Don't count a new button press if we have not let go of the button since last frame.
                    if not button_pressed_last_frame:
                        button_pressed_last_frame = True

                        # We must correct for overflow in the time byte.
                        # In the future, it might just be better to increase the size of our timestamp.
                        if time < previous_time:
                            # Overflow occurred, correct for it!
                            # We increase the offset that we add to every time value.
                            time_offset += (2 ** 16)
                        previous_time = time
                        time += time_offset

                        # It's possible that two distinct presses are at the same time if packets were collected very quickly,
                        # and also because two sensor frames may both be reporting the button press,
                        # but we rather not add that press twice.
                        if time not in button_press_times:
                            button_press_times.append(time)
                else:
                    button_pressed_last_frame = False
        # Now save those press times to a file.
        with open(output_filename, 'w') as output_file:
            # Write the csv headers.
            output_file.write(format_csv(['time']) + '\n')
            for time in button_press_times:
                output_file.write(str(time) + '\n')

    # Process the sensors.
    tongue_ending = 'tongue.csv'
    throat_ending = 'throat.csv'
    process_sensor_file(input_path + tongue_ending, output_path + tongue_ending)
    process_sensor_file(input_path + throat_ending, output_path + throat_ending)

    # Process the button.
    button_ending = 'button.csv'
    process_button([input_path + tongue_ending,
                    # Only need to use button presses that came with the tongue frames,
                    # since the throat presses will be nearly identical.
                    #input_path + throat_ending
                    ],
                   output_path + button_ending)

    # Mark the raw capture as processed by adding the processed marker (see PROCESSED_MARKER_FILENAME).
    open(input_path + PROCESSED_MARKER_FILENAME, 'w').close()


def capture_was_processed(capture_number: int):
    """Given a capture number, return whether we can find the processed marker (see PROCESSED_MARKER_FILENAME) in its subdirectory."""
    return os.path.isfile(INPUT_DIRECTORY_ROOT + get_capture_subdirectory(capture_number) + PROCESSED_MARKER_FILENAME)


"""
# Process the data we got from Alyn.
if __name__ == '__main__':
    for a in range(12):
        print('Processing', a)
        process_capture(a)
"""
