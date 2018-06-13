"""
+------------------------------------------------------------------------------+
|                       Copyright 2017 Rockwell Collins                        |
|                             All Rights Reserved                              |
|                           Proprietary Information                            |
+------------------------------------------------------------------------------+

Constant values used throughout the common widgets
"""
import tkFont
import Tkinter as tk


__version__ = '$Rev: 235241 $'

TK_ROOT = tk.Tk()

# fonts
FONT_NORMAL = tkFont.Font(family='Helvetica', size=8)
FONT_CELL = tkFont.Font(family='MS Sans Serif', size=8)
FONT_BOLD = tkFont.Font(family='Helvetica', size=8, weight=tkFont.BOLD)
FONT_BIG = tkFont.Font(family='Helvetica', size=10, weight=tkFont.BOLD)

# colors
COLOR_CHECKLIST_HEADER_BG = 'gainsboro'
COLOR_CHECKLIST_ITEM_BG = 'white'
