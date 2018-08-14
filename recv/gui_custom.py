import tkinter as tk


# In order to make our background color consistent we must ensure that every widget uses the same color.
BG_COLOR = 'white'


class CustomLabel(tk.Label):
    """Custom label to make our look and feel consistent."""
    def __init__(self, ctx, *args, **kwargs):
        super(CustomLabel, self).__init__(ctx, *args, **kwargs,
                                          bg=BG_COLOR)


class CustomFrame(tk.Frame):
    """Custom frame to make our look and feel consistent."""
    def __init__(self, ctx, *args, **kwargs):
        super(CustomFrame, self).__init__(ctx, *args, **kwargs,
                                          bg=BG_COLOR)


class CustomButton(tk.Button):
    """Custom button to make our look and feel consistent."""
    def __init__(self, ctx, *args, **kwargs):
        super(CustomButton, self).__init__(ctx, *args, **kwargs,
                                           width=12, height=-20, pady=-20, relief=tk.GROOVE)
