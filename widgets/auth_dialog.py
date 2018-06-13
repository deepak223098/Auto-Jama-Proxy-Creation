"""
+------------------------------------------------------------------------------+
|                       Copyright 2017 Rockwell Collins                        |
|                             All Rights Reserved                              |
|                           Proprietary Information                            |
+------------------------------------------------------------------------------+

Simple dialog used to get authentication credentials from the user
"""
try:
    # Python2
    import Tkinter as tk
    import tkMessageBox
    import tkSimpleDialog

except ImportError:
    # Python3
    import tkinter as tk
    from tkinter import messagebox as tkMessageBox
    from tkinter import simpledialog as tkSimpleDialog
import unamepass


__version__ = '$Rev: 235184 $'


class _QueryAuthDialog(tkSimpleDialog.Dialog):
    """Auth query dialog (replicates tkSimpleDialog._QueryDialog)"""
    def __init__(self, title, prompt, initialvalue=None, parent=None):
        """
        Constructor called in instantiation.  Creates an auth query dialog 
        window.

        :param title: the dialog title
        :type  title: basestring
        :param prompt: the label text
        :type  prompt: basestring
        :param initialvalue: initial username value
        :type  initialvalue: basestring
        :param parent: a parent window (the application window)
        :type  parent: tk.Tk
        """
        if not parent:
            parent = tk.Tk()
            parent.withdraw()

        self.prompt = prompt
        self.initialvalue = initialvalue

        self.username_entry = None
        self.pass_entry = None

        tkSimpleDialog.Dialog.__init__(self, parent, title)

    def destroy(self):
        """
        Destroys the auth query dialog window and its widgets.
        """
        self.username_entry = None
        self.pass_entry = None
        tkSimpleDialog.Dialog.destroy(self)

    def body(self, master):
        """
        Constructs the auth query dialog widgets.

        :param master: master widget for the widgets embedded in the dialog
        :type  master: tk.Widget
        :return: the username widgets (so it gets initial focus)
        :rtype: tk.Entry
        """
        w = tk.Label(master, text=self.prompt, justify=tk.LEFT)
        w.grid(row=0, column=1, columnspan=2, padx=5, sticky=tk.W)

        username_label = tk.Label(master, text='Username', justify=tk.LEFT)
        username_label.grid(row=1, column=1, padx=(5, 0), sticky=tk.W)

        self.username_entry = tk.Entry(master, name='username_entry')
        self.username_entry.grid(row=1, column=2, padx=5, sticky=tk.W+tk.E)
        if self.initialvalue:
            self.username_entry.insert(0, self.initialvalue)
            self.username_entry.select_range(0, tk.END)

        pass_label = tk.Label(master, text='Password', justify=tk.LEFT)
        pass_label.grid(row=2, column=1, padx=(5, 0), sticky=tk.W)

        self.pass_entry = tk.Entry(master, name='pass_entry', show='*')
        self.pass_entry.grid(row=2, column=2, padx=5, sticky=tk.W+tk.E)

        return self.username_entry

    def validate(self):
        """
        Validates the contents of the results and stores them in the results 
        attribute.

        :return: code to indicate validation success (0 is fail, 1 is success)
        :rtype: int
        """
        try:
            result = self.getresult()

        except ValueError:
            tkMessageBox.showwarning(
                'Illegal value',
                'Invalid auth.\nPlease try again',
                parent=self)

            return 0

        self.result = result
        return 1

    def getresult(self):
        """
        Gets the auth values from the widgets.

        :return: auth values
        :rtype: tuple(basestring, basestring)
        """
        unamepass.username=self.username_entry.get()
        unamepass.password=self.pass_entry.get()
        return self.username_entry.get(), self.pass_entry.get()


def askauth(title, prompt, **kw):
    """
    Gets a username and password from the user.

    :param title: the dialog title
    :type  title: basestring
    :param prompt: the label text
    :type  prompt: basestring
    :return: username and password
    :rtype: tuple(basestring, basestring)
    """
    d = _QueryAuthDialog(title, prompt, **kw)
    return d.result
