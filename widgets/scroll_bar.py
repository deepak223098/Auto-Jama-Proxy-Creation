"""
+------------------------------------------------------------------------------+
|                       Copyright 2017 Rockwell Collins                        |
|                             All Rights Reserved                              |
|                           Proprietary Information                            |
+------------------------------------------------------------------------------+

Scrollbar that hides if not needed

Implementation from
http://stackoverflow.com/questions/30018148/python-tkinter-scrollable-frame-class
"""
import Tkinter as tk


__version__ = '$Rev: 235184 $'


class AutoScrollbar(tk.Scrollbar):
    """A scrollbar that hides itself if it's not needed"""
    def __init__(self, *args, **kwargs):
        """
        Constructor called in instantiation.  Creates an auto-hide scrollbar.
        """
        tk.Scrollbar.__init__(self, *args, **kwargs)

    def set(self, lo, hi):
        """
        Remove self if the position bar takes up the entire scroll area.
        """
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            self.grid_remove()

        else:
            self.grid()

        tk.Scrollbar.set(self, lo, hi)

    def pack(self, *args, **kwargs):
        """
        Disable pack.
        """
        raise tk.TclError('Cannot use pack with this widget.')

    def place(self, *args, **kwargs):
        """
        Disable place.
        """
        raise tk.TclError('Cannot use pack with this widget.')
