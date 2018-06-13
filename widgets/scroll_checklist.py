"""
+------------------------------------------------------------------------------+
|                       Copyright 2017 Rockwell Collins                        |
|                             All Rights Reserved                              |
|                           Proprietary Information                            |
+------------------------------------------------------------------------------+

Scrollable table with selectable rows
"""
import Tkinter as tk
from collections import namedtuple

from constants import (
    COLOR_CHECKLIST_HEADER_BG, COLOR_CHECKLIST_ITEM_BG, FONT_BOLD, FONT_CELL)
from scroll_frame import AutoScrollFrame


__version__ = '$Rev: 235184 $'

# container for checklist item widgets
ChecklistRow = namedtuple('ChecklistRow', [
    'item', 'cells', 'state', 'checkbox'])

# container for checklist item data
ChecklistItem = namedtuple('ChecklistItem', [
    'values', 'item', 'checked'])


class AutoScrollChecklist(AutoScrollFrame):
    """Scrollable table with selectable rows"""
    def __init__(self, master, headers, sortby, items, *args, **kwargs):
        """
        Constructor called in instantiation.  Creates a scrollable checklist
        table.

        :param master: parent widget
        :type  master: tk.Widget
        :param headers: table column headers
        :type  headers: list[basestring]
        :param sortby: header of the column to sort by
        :type  sortby: basestring
        :param items: initial checklist items
        :type  items: list[ChecklistItem]
        """
        AutoScrollFrame.__init__(self, master, *args, **kwargs)
        self.headers = headers
        self.sortby = sortby
        self.ncol = len(self.headers) + 1

        self.checklist = tk.Frame(
            self.frame, background=COLOR_CHECKLIST_ITEM_BG)

        self.checklist.pack(fill=tk.BOTH, expand=True)

        # create header row
        header_bg = tk.Frame(
            self.checklist, background=COLOR_CHECKLIST_HEADER_BG)

        header_bg.grid(row=0, column=0, columnspan=self.ncol, sticky=tk.NSEW)

        for col, header in enumerate(self.headers):
            self.checklist.columnconfigure(col, weight=0)
            label = tk.Label(
                self.checklist,
                text=header,
                font=FONT_BOLD,
                background=COLOR_CHECKLIST_HEADER_BG,
                justify=tk.LEFT)

            label.grid(row=0, column=(col + 1), padx=5, sticky=tk.W)

        self.checklist.columnconfigure(0, minsize=30)
        self.checklist.columnconfigure(len(self.headers), weight=1)

        # create item rows
        self.items = []
        self.empty_label = None
        self.update_items(items)

    def update_items(self, items):
        """
        Updates the checklist rows.

        :param items: new checklist row items
        :type  items: list[ChecklistItem]
        """
        if self.empty_label is not None:
            self.empty_label.grid_remove()

        # remove old rows
        for item in self.items:
            item.checkbox.grid_remove()
            for cell in item.cells:
                cell.grid_remove()

        # display "(empty)" if no items
        if len(items) == 0:
            self.empty_label = tk.Label(
                self.checklist,
                text='(empty)',
                background=COLOR_CHECKLIST_ITEM_BG,
                justify=tk.LEFT)

            self.empty_label.grid(
                row=1, column=0, columnspan=self.ncol, sticky=tk.W)

        # get the column widths
        colwidth = {h: 1 for h in self.headers}
        for item in items:
            for header in self.headers:
                text = str(item.values.get(header, ''))
                colwidth[header] = max(
                    colwidth[header], int(len(text) + 5))

        # sort items
        items.sort(key=lambda i: str(i.values.get(self.sortby, '')))

        # create row for each item
        self.items = []
        for row, item in enumerate(items):
            # create checkbox
            state = tk.BooleanVar()
            check = tk.Checkbutton(
                self.checklist,
                variable=state,
                background=COLOR_CHECKLIST_ITEM_BG,
                activebackground=COLOR_CHECKLIST_ITEM_BG)

            if item.checked is True:
                state.set(1)

            elif item.checked is None:
                check.configure(state=tk.DISABLED)

            check.grid(row=(row + 1), column=0, sticky=tk.NE)

            # create cell for each item value
            cells = []
            for col, header in enumerate(self.headers):
                cell = tk.Text(
                    self.checklist,
                    height=1,
                    width=colwidth[header],
                    borderwidth=0,
                    font=FONT_CELL)

                cell.insert(1.0, str(item.values.get(header, '')))
                cell.configure(state=tk.DISABLED)
                cell.grid(row=(row + 1), column=(col + 1), padx=5, sticky=tk.W)
                cells.append(cell)

            self.items.append(ChecklistRow(
                item=item.item,
                cells=cells,
                state=state,
                checkbox=check))

    def selected_items(self):
        """
        Gets the selected checklist items.

        :return: selected checklist items
        :rtype: list
        """
        return [item.item for item in self.items if item.state.get()]
