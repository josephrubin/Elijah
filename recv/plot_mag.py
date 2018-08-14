#!/usr/bin/env python3
"""Processes and then plots a given capture.

The capture number can be specified with the first command line argument
or by modifying the default value of the variable capture_number below.
"""

__author__ = 'Joseph Rubin'

import sys
import pandas as pd
from matplotlib import pyplot as plt
from itertools import chain
from util import *
import process


# Modify this value to plot different captures!
# Alternatively, provide a command line argument.
CAPTURE_NUMBER = 0
INPUT_DIRECTORY_ROOT = 'processed/'

# Choose what to plot.
PLOT_TONGUE = False
PLOT_THROAT = True
PLOT_BUTTON = False


def main():
    capture_number = CAPTURE_NUMBER
    # If we are provided a cmdline arg then use it instead as the capture number to plot.
    if len(sys.argv) > 1:
        capture_number = int(sys.argv[1])

    if not raw_capture_exists(capture_number):
        raise ValueError('That capture does not exist!')

    capture_directory = INPUT_DIRECTORY_ROOT + get_capture_subdirectory(capture_number)

    # If we have not processed the capture before, or if we think we have
    # but the processed data doesn't exist, we process the capture now.
    if not process.capture_was_processed(capture_number)\
            or not os.path.isfile(capture_directory + 'tongue.csv')\
            or not os.path.isfile(capture_directory + 'throat.csv'):
        # debug
        print('$ Processing...')
        process.process_capture(capture_number)
    # debug
    print('$ Plotting...')
    plot(capture_directory)


def plot(input_path):
    """Plot a capture given the path to its subdirectory."""
    input_filename_tongue = input_path + 'tongue.csv'
    input_filename_throat = input_path + 'throat.csv'
    input_filename_button = input_path + 'button.csv'

    # Plot sensor files, depending on the status of the debugging constants.
    # We save the minimum and maximum data values for later.
    min_a, max_a = plot_sensor_file(input_filename_tongue, 'Tongue') if PLOT_TONGUE else (0, 0)
    min_b, max_b = plot_sensor_file(input_filename_throat, 'Throat') if PLOT_THROAT else (0, 0)

    plt.xlabel('Milliseconds')
    plt.ylabel('Degrees per second')

    # We can plot the button presses as vertical lines if we want to.
    # Here is where the min and max data values come in.
    # We plot the lines as low as the min, and as high as the max,
    # so we are certain that the line extends the entire reach of the plot
    # without going over or under.
    if PLOT_BUTTON:
        plot_button_presses(input_filename_button, min(min_a, min_b), max(max_a, max_b))

    # The two plots were labeled, so let's generate the legend.
    plt.legend()

    plt.show()


def plot_sensor_file(input_filename, plot_label):
    """Plot a sensor capture data given the path to its file."""
    input_reader = pd.read_csv(input_filename, delimiter=',')
    # If we are just plotting the throat, having it blue would be confusing
    # (since it is usually orange). Resolve this ambiguity by making it orange as usual.
    if PLOT_THROAT and not PLOT_TONGUE:
        color = '#FF8000'
    else:
        color = ''
    plt.plot(input_reader.time, input_reader.gyro_m, color, lw=0.8, label=plot_label)
    return min(input_reader.gyro_m), max(input_reader.gyro_m)


def plot_button_presses(input_filename, low_y_coord, high_y_coord):
    """Make vertical lines in the plot for the button presses."""
    assert high_y_coord >= low_y_coord
    input_reader = pd.read_csv(input_filename, delimiter=',')
    # Plot a line for each button press.
    for time in input_reader.time:
        plt.plot([time, time], [low_y_coord, high_y_coord], 'k:', lw=1.6, solid_capstyle='round')


if __name__ == '__main__':
    main()
