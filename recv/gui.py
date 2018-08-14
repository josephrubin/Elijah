#!/usr/bin/env python3
"""A Graphical User Interface application that makes Elijah very easy to use.

All widgets should be packed only at the end of the function in which they were created,
unless there is a good reason to do otherwise.
Our strings are declared at the start of this file (see below) so they are not hardcoded in.
"""

__author__ = 'Joseph Rubin'

import shutil
import threading

import tkinter as tk
import tkinter.scrolledtext
import tkinter.messagebox as message
import tkinter.simpledialog as dialog
from serial import SerialException, SerialTimeoutException

from gui_custom import CustomLabel, CustomFrame, CustomButton, BG_COLOR
from const import *
from util import *
import plot_mag
import process
import capture

# Strings.
# In an attempt to separate data from code, please place all strings here, and do not hard-code in any of them!
STR_TITLE = 'Elijah'
STR_TITLE_BAR = 'Collection Interface'
STR_START_BUTTON = 'Start'
STR_STOP_BUTTON = 'Stop'
STR_ACTION_HEADER = 'New Capture'
STR_CAPTURES_HEADER = 'Captures'
STR_NAME_CAPTURE = '\nEnter a title for this capture,\nor press Cancel to delete it.\n'
STR_NAME_CAPTURE_TITLE_BAR = 'Please Name Your Capture'
STR_FOOTER = 'Developed by Sixdof Space.'
STR_STATUS_1 = 'Press Start to capture.'
STR_STATUS_2 = 'Waiting to connect.'
STR_STATUS_3 = 'Capturing...'
STR_STATUS_4 = 'Entering title.'
STR_STATUS_5 = 'Capture saved!'
STR_STATUS_6 = 'Capture not saved.'

# Fonts.
FONT_MAIN = ('Helvetica', 12)
FONT_TITLE = ('Georgia', 34)
FONT_SUB_TITLE = ('Helvetica', 12)
FONT_CLICK = ('Helvetica', 12, 'underline')
FONT_FINE = ('Helvetica', 10)

# Virtual events allow the spawned thread to interact with the main thread.
# Used to kill the main thread.
EVENT_DIE = '<<event_die>>'
# We generate this when there was a good connection at the start of the program but the board was subsequently disconnected.
# There is no way to salvage an invalidated connection (short of creating a new one)
# so we respond to this event by showing an error message and terminating the program.
EVENT_BOARD_DISCONNECTED = '<<event_board_disconnected>>'
# Used when a capture is finished to update the state of the main thread and save the capture title.
EVENT_CAPTURE_FINISHED = '<<event_capture_finished>>'
# Used when we receive a SIG_DENIED. Update the state of the main thread.
EVENT_CAPTURE_DENIED = '<<event_capture_denied>>'


def main():
    # Create the 'raw/' and 'processed/' folders if they don't already exist.
    if not os.path.isdir('raw'):
        os.mkdir('raw')
    if not os.path.isdir('processed'):
        os.mkdir('processed')

    # Now build and show the GUI.
    window = GraphicalWindow()
    window.show()


class GraphicalWindow(object):
    """A container for our graphical interface.

    We create a namespace (this class) and receive privileged access to
    member fields and methods. This way, we don't need to use global variables.
    """

    def __init__(self):
        # Instance variables that we won't construct later.
        # It is considered good practice to define all members in the constructor.
        self.FRM_files_panel = None
        self.FRM_action_panel = None
        self.SCT_capture_panel = None
        self.LBL_status = None
        self.BTN_start = None
        self.BTN_stop = None
        self.con = None
        self.capture_thread = None
        # To ensure that we only show the disconnected error once (even though multiple
        # threads may encounter the same error) we remember if it has already been triggered.
        # We also use a threading lock to eliminate race conditions.
        self.board_disconnected_triggered = False
        self.board_disconnected_lock = threading.Lock()

        # Root element of the GUI.
        self.root = tk.Tk()
        self.root.config(bg=BG_COLOR)
        self.root.geometry('614x455')
        self.root.option_add('*Font', FONT_MAIN)
        self.root.title(STR_TITLE_BAR)

        # Main body.
        self.FRM_body = CustomFrame(self.root)
        self.make_files_panel(self.FRM_body)
        self.make_action_panel(self.FRM_body)
        self.FRM_body.pack()

        # Footer text.
        self.LB_footer = CustomLabel(self.root, text=STR_FOOTER, fg='dark gray', font=FONT_FINE)
        self.LB_footer.pack(side=tk.BOTTOM, pady=(0, 18))

        # Bind the virtual events.
        self.root.bind(EVENT_DIE, self.on_die)
        self.root.bind(EVENT_BOARD_DISCONNECTED, self.on_board_disconnected)
        self.root.bind(EVENT_CAPTURE_FINISHED, self.on_capture_finished)
        self.root.bind(EVENT_CAPTURE_DENIED, self.on_capture_denied)

        def serial_initial_setup():
            """This function will be called by a separate thread and its purpose is to establish a serial connection."""
            # Make a connection right away and open it.
            # This ensures that we reserve the serial device for the entire lifespan of this program.
            self.con = capture.make_con(resetting=True, timeout=4)
            try:
                self.con.open()
            except SerialException:
                response = dialog.messagebox.askretrycancel(
                    'Unplugged or shared serial device',
                    'Please make sure the device is plugged in\n'
                    'and no other program is using it.'
                )
                if response:
                    # User clicked 'retry'.
                    serial_initial_setup()
                    return
                else:
                    # User clicked 'cancel'.
                    # We can destroy the application even though we are not
                    # on the main thread by invoking a virtual event.
                    self.root.event_generate(EVENT_DIE)
                    # Now we have to end our own thread.
                    exit(0)

            # Look for SIG_READY.
            try:
                capture.wait_for_sig_ready(self.con)
            # Timeout.
            except SerialException:
                # If we timed out when waiting for SIG_READY that means the board was previously
                # connected but subsequently disconnected.
                self.root.event_generate(EVENT_BOARD_DISCONNECTED)
                # Now close our own thread.
                exit(1)
            # debug
            print('$ Got SIG_READY.')

            # Since the Arduino is now fully booted, set the read timeout to a lower value.
            # We only needed it to be so high in the first place because we needed to wait
            # until the Arduino turned on before it could send the SIG_READY.
            self.con.timeout = 1

            # Now that the serial is set up and ready for a SIG_REQUEST,
            # we allow the start button to be pressed.
            self.BTN_start.config(state=tk.NORMAL)

        # Set up the serial in a new thread so that we aren't waiting for the program to start.
        # The start button will be disabled until this thread finishes.
        threading.Thread(target=serial_initial_setup).start()

    def make_action_panel(self, ctx):
        """The action panel is where you can make a new capture.
        It contains a heading (info) label, the 'Start' and 'Stop' buttons, and a status text label.
        """
        FRM_action = CustomFrame(ctx, padx=15, bd=0, highlightthickness=1, highlightcolor='dark gray', relief=tk.SOLID)

        # Info text.
        LBL_info = CustomLabel(FRM_action, text=STR_ACTION_HEADER, font=FONT_SUB_TITLE)

        # Buttons.
        FRM_buttons = CustomFrame(FRM_action)
        self.BTN_start = CustomButton(FRM_buttons, text=STR_START_BUTTON, command=self.on_click_start_button, state=tk.DISABLED)
        self.BTN_stop = CustomButton(FRM_buttons, text=STR_STOP_BUTTON, command=self.on_click_stop_button, state=tk.DISABLED)

        # Status.
        self.LBL_status = CustomLabel(FRM_action, text=STR_STATUS_1)

        LBL_info.pack(pady=17)
        self.BTN_start.pack(side=tk.LEFT, padx=8)
        self.BTN_stop.pack(side=tk.RIGHT, padx=8)
        FRM_buttons.pack()
        self.LBL_status.pack(side=tk.LEFT, padx=5, pady=21)

        FRM_action.pack(side=tk.RIGHT, padx=(70, 0), pady=(0, 7))

    def on_click_start_button(self):
        """The user has pressed the start button; request a capture from the transmitter."""
        # Set our status and start button state.
        self.LBL_status.config(text=STR_STATUS_3)
        self.BTN_start.config(state=tk.DISABLED)

        # Send a SIG_REQUEST to the transmitter to tell it we want it to start a capture.
        try:
            self.con.write(SIG_REQUEST)
            self.con.flush()
        # Although our connection is not configured to have a write_timeout, attempting to write the SIG_REQUEST after the board has
        # been disconnected will almost immediately trigger one. Therefore, we can catch the exception to let us know that this capture was
        # started after the board was disconnected (and therefore has no possibility of being successful).
        except SerialTimeoutException:
            # Since the device has been disconnected, even if it was subsequently reconnected, the connection that we previously
            # established has been invalidated and is no longer usable.
            self.root.event_generate(EVENT_BOARD_DISCONNECTED)
        else:
            # No exception occurred, spawn a new thread to do the capture itself (we don't want to hog the main/gui thread).
            self.capture_thread = CaptureThread(self.con, self.root)
            self.capture_thread.start()
            # The capture is ongoing now so we can allow the user to press the Stop button.
            self.BTN_stop.config(state=tk.NORMAL)

    def on_click_stop_button(self):
        """When the user wishes to stop the capture, we send a SIG_ENOUGH to the transmitter.

        That's it. We make no promises about what is going to happen, or when the capture will stop.
        Therefore, we don't change the button states here. When the capture actually does finish,
        a virtual event will be called (on_capture_finished) which will handle the state change.
        """
        try:
            self.con.write(SIG_ENOUGH)
            self.con.flush()
        # Although our connection is not configured to have a write_timeout, attempting to write the SIG_ENOUGH after the board has
        # been disconnected will almost immediately trigger one. Therefore, we can catch the exception to let us know that the board
        # was disconnected during the course of this capture.
        except SerialTimeoutException:
            # Since the device has been disconnected, even if it was subsequently reconnected, the connection that we previously
            # established has been invalidated and is no longer usable.
            # We can't kill the capture thread directly, but it will die by itself due to a reading timeout.
            # All we must do is generate the virtual event to kill the GUI.
            self.root.event_generate(EVENT_BOARD_DISCONNECTED)

    def make_files_panel(self, ctx):
        """The files panel is the left side of the screen.

        By contrast, the captures themselves are listed in a sub-panel called the capture panel.
        """
        # The title text is part of this panel as well.
        # This is done for layout reasons, since the title appears
        # in the same 'column' as this panel, just above it.
        LB_title = CustomLabel(ctx, text=STR_TITLE, font=FONT_TITLE, justify=tk.LEFT, pady=25)

        self.FRM_files_panel = CustomFrame(ctx)
        LBL_info = CustomLabel(self.FRM_files_panel, text=STR_CAPTURES_HEADER, justify=tk.LEFT, anchor=tk.W)

        LB_title.pack(anchor=tk.W)
        LBL_info.pack(pady=(0, 6), fill=tk.X)
        self.FRM_files_panel.pack(side=tk.LEFT, fill=tk.Y)

        # The files panel lists all the captures.
        self.update_capture_panel()

    def update_capture_panel(self):
        """Remove the old capture panel if it exists and make a new one.

        This should be called when we list the captures initially,
        and whenever we add or remove a capture.
        """
        if self.SCT_capture_panel is not None:
            self.SCT_capture_panel.pack_forget()
        self.make_capture_panel(self.FRM_files_panel)
        self.SCT_capture_panel.config(state=tk.DISABLED)
        self.SCT_capture_panel.pack(fill=tk.X)
        # Scroll to the end of the box automatically to see the newest captures.
        self.SCT_capture_panel.see('end')

    def make_capture_panel(self, ctx):
        # Use a scrolled text widget for our captures, since we want
        # to be able to view all of them if they overflow the box.
        self.SCT_capture_panel = tk.scrolledtext.ScrolledText(ctx, bd=0, highlightthickness=1,
            width=16, height=10, spacing1=3, spacing3=3, borderwidth=0, cursor='hand2')
        # The captures are each a single subdirectory within 'raw/'.
        captures = os.listdir('raw/')
        capture_names = list()
        capture_numbers = list()
        for capture_directory in captures:
            # Each capture subdirectory should start with 'capture*'. Ignore all other garbage in the directory.
            if not capture_directory.startswith('capture'):
                continue
            # Get the capture number and remove the padding '0's. E.g. capture00001 -> 1.
            number = str(int(capture_directory.replace('capture', '')))
            try:
                with open('raw/' + capture_directory + '/name.txt') as name_file:
                    name = name_file.readline()
                # Instead of checking if the name file was there in the first place,
                # we just catch the error if it was not found. Using try/except for
                # logic is considered 'Pythonic', and we get the bonus of avoiding
                # race conditions if the file was deleted after it was found but
                # before it was read.
            except FileNotFoundError:
                # If there was no name file we just use the capture number
                # as the name. So capture 00013 will be shown as '13' if
                # it has not otherwise been provided a name.
                name = number
            capture_names.append(name)
            capture_numbers.append(number)

        for i, cap in enumerate(zip(capture_numbers, capture_names)):
            capture_number = cap[0]
            capture_name = cap[1]
            # Configure 'tags' which are bits of text that can listen to events (they can be clicked).
            # We make plot tags for each capture (ending with 'P') and delete tags for each capture (ending with 'D').
            self.SCT_capture_panel.tag_config(capture_number + 'P', foreground='blue', font=FONT_CLICK)
            self.SCT_capture_panel.tag_config(capture_number + 'D', foreground='red')

            # Inner closure to save the state of the capture_name variable for the event.
            # Without this, the final state of capture_number would be used for all of the event listeners.
            def do_bind(c):
                # Here, we actually do the binding of the tag to the click event.
                # Note that '<Button-1>' refers to the left mouse button.
                self.SCT_capture_panel.tag_bind(capture_number + 'P', '<Button-1>', lambda e: self.on_click_capture(e, c))
                self.SCT_capture_panel.tag_bind(capture_number + 'D', '<Button-1>', lambda e: self.on_click_remove(e, c))

            # Bind the tags we configured earlier to the click events.
            do_bind(capture_number)
            # When we insert the text, we register it with the tags we configured earlier (this is the third parameter of 'insert').
            # This completes the process of configure tag -> bind tag -> register text with tag.
            self.SCT_capture_panel.insert(tk.INSERT, ' ')
            self.SCT_capture_panel.insert(tk.INSERT, 'X', capture_number + 'D')
            self.SCT_capture_panel.insert(tk.INSERT, '  ')
            # Add a newline after each one except the last.
            self.SCT_capture_panel.insert(tk.INSERT, capture_name + ('' if i == len(capture_names) - 1 else '\n'), capture_number + 'P')

    def on_click_capture(self, _event, capture_number):
        """Called when the user clicks on a capture name. We wish to plot the capture."""
        capture_directory = plot_mag.INPUT_DIRECTORY_ROOT + get_capture_subdirectory(capture_number)
        # If we have not processed the capture before, or if we think we have
        # but the processed data doesn't exist, we process the capture now.
        if not process.capture_was_processed(capture_number) \
                or not os.path.isfile(capture_directory + 'tongue.csv') \
                or not os.path.isfile(capture_directory + 'throat.csv'):
            # debug
            print('Processing...')
            process.process_capture(capture_number)
        plot_mag.plot('processed/' + get_capture_subdirectory(capture_number))

    def on_click_remove(self, _event, capture_number):
        """When the 'X' is clicked next to a capture name, remove the capture (delete the files)."""
        # debug
        print('Removing...')
        # Confirm that the user wishes to delete this capture.
        result = message.askquestion('Delete', 'Delete this capture?', icon='warning')
        if result == 'yes':
            # The call to shutil.rmtree with ignore_errors=True will recursively delete a directory.
            # This is what we need, since we want to remove the capture folder along with the data files inside of it.
            shutil.rmtree('raw/' + get_capture_subdirectory(capture_number), ignore_errors=True)
            shutil.rmtree('processed/' + get_capture_subdirectory(capture_number), ignore_errors=True)
            self.update_capture_panel()

    def on_die(self, _event):
        """Virtual event handler to kill the program."""
        # Since we are responding to an event, this function will run on the main thread.
        # This means we are capable of destroying the GUI.
        # Any stray capture threads must be themselves killed to exit cleanly.
        self.root.destroy()

    def on_board_disconnected(self, _event):
        """The board was disconnected during the course of this program.
        There is no way to salvage an invalidated connection so we must show an error and quit.
        The other possibility would be to create a new connection on the fly,
        but successfully recovering from whatever state we were in before the board was disconnected
        would be very difficult since the circumstances vary wildly.
        For example, if we were in the middle of a capture, it would be impossible to recover
        because any real-time delay jeopardises the serial buffer and we will lose information (it will be overwritten by new data).
        """
        self.board_disconnected_lock.acquire()
        # Ensure that we only call this once.
        if not self.board_disconnected_triggered:
            self.board_disconnected_triggered = True
            # Now that we have set the flag we may release the lock.
            self.board_disconnected_lock.release()
            dialog.messagebox.showerror('Board disconnected.', 'The board was disconnected. Press OK to quit,\nthen plug in the board and'
                                                               ' relaunch this program.')
            self.root.event_generate(EVENT_DIE)

    def on_capture_finished(self, _event):
        """This virtual event is called when the transmitter actually stops transmitting the capture."""
        self.LBL_status.config(text=STR_STATUS_4)
        self.BTN_stop.config(state=tk.DISABLED)

        # Name the capture.
        title = dialog.askstring(STR_NAME_CAPTURE_TITLE_BAR, STR_NAME_CAPTURE, parent=self.root)

        if title is None:
            # User pressed 'Cancel'.
            self.LBL_status.config(text=STR_STATUS_6)
            # Don't save the capture.
            # (It's actually already saved, but we will simply delete it).
            self.capture_thread.delete_capture()
        else:
            self.LBL_status.config(text=STR_STATUS_5)
            # Whatever name was given by capture.py will be overwritten with the user's choice.
            self.capture_thread.write_name(title)

        self.BTN_start.config(state=tk.NORMAL)

        self.update_capture_panel()

    def on_capture_denied(self, _event):
        """This virtual event is called when the transmitter actually stops transmitting the capture."""
        self.LBL_status.config(text=STR_STATUS_1)
        self.BTN_stop.config(state=tk.DISABLED)
        self.BTN_start.config(state=tk.NORMAL)

    def show(self):
        # We already built the GUI in the constructor,
        # so simply start the main loop and listen for events/input!
        self.root.mainloop()


class CaptureThread(threading.Thread):
    """This class inherits from thread, and it's used to record a capture.

    We don't want to hog the main/GUI thread so we spawn these instead.
    A new instance is used for each capture.
    """
    def __init__(self, con, event_hook):
        threading.Thread.__init__(self)
        self.output_path = None
        self.con = con
        # Event hook is the tkinter object we invoke our virtual events on.
        # In practice, it is always the root object.
        self.event_hook = event_hook

    def run(self):
        """Calling our start() method runs this in a new thread."""
        try:
            self.output_path = capture.do_writing_capture(self.con, enable_trailer=True)
        except RequestDeniedException:
            # Our SIG_REQUEST was responded to with a SIG_DENIED.
            # debug
            print('$ Our request was denied. ' +
                  'End the capture and send the virtual event to revert our button state without saving a capture.')
            self.event_hook.event_generate(EVENT_CAPTURE_DENIED)
        except SerialException:
            # There was a timeout while reading the data.
            # Probably the board was disconnected during a capture,
            # we cannot recover mid-capture so we must terminate this thread and show an error.
            self._terminate_self()
        else:
            self.event_hook.event_generate(EVENT_CAPTURE_FINISHED)

    def write_name(self, name):
        """Create a name.txt file for this thread's capture."""
        name_file = open(self.output_path + 'name.txt', 'w')
        name_file.write(name)
        name_file.close()

    def delete_capture(self):
        """Remove this thread's capture."""
        # The call to shutil.rmtree with ignore_errors=True will recursively delete a directory.
        # This is what we need, since we want to remove the capture folder along with the data files inside of it.
        shutil.rmtree(self.output_path, ignore_errors=True)

    def _terminate_self(self):
        # The capture was not totally completed, only partially started.
        # There is no way to recover in the middle of a capture, but we
        # must trigger the disconnected event to let the GUI know before
        # terminating ourself.
        try:
            self.event_hook.event_generate(EVENT_BOARD_DISCONNECTED)
        finally:
            # A RuntimeError is triggered if we have already killed the GUI thread
            # and now we are trying to generate an event (to kill it). We are
            # trying to end it anyway so the error itself does not represent
            # unintended or unexpected behavior.
            exit(1)


if __name__ == '__main__':
    main()
else:
    raise Exception('This is not an importable module!')
