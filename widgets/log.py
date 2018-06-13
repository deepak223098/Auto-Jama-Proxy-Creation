"""
+------------------------------------------------------------------------------+
|                       Copyright 2017 Rockwell Collins                        |
|                             All Rights Reserved                              |
|                           Proprietary Information                            |
+------------------------------------------------------------------------------+

Text frame that periodically updates its contents to reflect a file
"""
import Tkinter as tk
import os

from constants import FONT_NORMAL
from ..utils import files


__version__ = '$Rev: 235221 $'

LONG_WAIT = 2500
SHORT_WAIT = 500


class Log(tk.Frame):
    """Frame that displays the contents of a file"""
    def __init__(self, root, logfile, *args, **kwargs):
        """
        Constructor called in instantiation. Prepares a frame that actively
        displays the contents of a log file.
        """
        tk.Frame.__init__(self, *args, **kwargs)
        self.root = root
        self.logfile = files.real(logfile)
        self._stop = False
        self._previous_length = 0
        self._same_length_count = 0

        # create the textbox to hold the contents
        self.text = tk.Text(self, height=10, font=FONT_NORMAL)
        self.text.configure(state=tk.DISABLED)
        self.text.tag_config('error', foreground='firebrick')
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # create a scrollbar to allow the user to scroll through the textbox
        scroll = tk.Scrollbar(self, command=self.text.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.text['yscrollcommand'] = scroll.set

        # start updating
        self.update()

    def highlight(self):
        """
        Highlights error text as red.
        """
        pos = '1.0'
        while True:
            count = tk.IntVar()
            idx = self.text.search(
                r'ERROR:[^\n]*\n', pos, tk.END, count=count, regexp=True)

            if idx == '' or count.get() == 0:
                break

            pos = '{}+{}c'.format(idx, count.get())
            self.text.tag_add('error', idx, pos)

    def update(self):
        """
        Updates the contents of the frame.
        """
        if self._stop:
            # quit updating
            return

        # wait for the log file to exist
        if not os.path.exists(self.logfile):
            self.root.after(LONG_WAIT, self.update)
            return

        # read the log file
        with open(self.logfile, 'r') as f:
            contents = f.read()

        # don't update if the log file hasn't changed
        length = len(contents)
        if length == self._previous_length:
            # slow down updates if the log file hasn't changed recently
            if self._same_length_count >= 10:
                self.root.after(LONG_WAIT, self.update)

            else:
                self._same_length_count += 1
                self.root.after(SHORT_WAIT, self.update)

            return

        # update the frame with the new log file contents
        self.text.configure(state=tk.NORMAL)
        self.text.delete('1.0', tk.END)
        self.text.insert(tk.END, contents)
        self.text.configure(state=tk.DISABLED)
        self.text.see(tk.END)
        self.highlight()

        # reset the update timer
        self._previous_length = length
        self._same_length_count = 0

        # do it all over again
        self.root.after(SHORT_WAIT, self.update)

    def stop(self):
        """
        Prevents the frame from continuing to update.
        """
        self._stop = True
