"""
+------------------------------------------------------------------------------+
|                       Copyright 2017 Rockwell Collins                        |
|                             All Rights Reserved                              |
|                           Proprietary Information                            |
+------------------------------------------------------------------------------+

Frame with a auto-hiding scrollbar

Implementation from
http://stackoverflow.com/questions/30018148/python-tkinter-scrollable-frame-class
"""
import Tkinter as tk

from scroll_bar import AutoScrollbar


__version__ = '$Rev: 235184 $'


class AutoScrollFrame(tk.Frame):
    """Frame with a auto-hiding scrollbar"""
    def __init__(self, master, *args, **kwargs):
        """
        Constructor called in instantiation.  Creates a frame with an
        auto-hiding scrollbar.

        :param master: parent widget
        :type  master: tk.Widget
        """
        self.maxheight = kwargs.pop('maxheight', None)
        tk.Frame.__init__(self, master, *args, **kwargs)

        self._scroll = AutoScrollbar(self, orient=tk.VERTICAL)
        self._scroll.grid(row=0, column=1, sticky=tk.NS)

        self._canvas = tk.Canvas(
            self, yscrollcommand=self._scroll.set, bd=0, highlightthickness=0)

        self._canvas.grid(row=0, column=0, sticky=tk.NSEW)

        self.grid_columnconfigure(0, weight=1)

        self._scroll.config(command=self._canvas.yview)
        # self.bind_all('<MouseWheel>', self._mouse_scroll, add='+')

        self.frame = tk.Frame(self._canvas, highlightcolor='red')
        self.frame.rowconfigure(1, weight=1)
        self.frame.columnconfigure(1, weight=1)
        self.frame.bind('<Configure>', self._frame_changed)

        self._window = self._canvas.create_window(
            (0, 0), window=self.frame, anchor=tk.NW)

        self._canvas.bind('<Configure>', self._canvas_changed)
        self._frame_changed()

    # def _mouse_scroll(self, event):
    #     print '{} {}'.format(self.name, event.delta)
    #     self._canvas.yview_scroll((event.delta / -120), 'units')

    def _frame_changed(self, event=None):
        """
        Resizes the canvas.  Called when the frame configuration event is
        signaled.
        """
        height = self.frame.winfo_height()
        if self.maxheight is not None:
            height = min(height, self.maxheight)

        self._canvas.configure(height=height)
        self._canvas.configure(scrollregion=self._canvas.bbox('all'))

    def _canvas_changed(self, event):
        """
        Resizes the canvas window.  Called when the canvas configuration event
        is signaled.
        """
        self._canvas.itemconfig(self._window, width=event.width)
