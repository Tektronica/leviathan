#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import wx
import wx.lib.mixins.listctrl as listmix
import csv
import sys
import itertools
import string
import numpy as np
import re
import pyunivisa
"""
ObjectListView2 is a fork of http://objectlistview.sourceforge.net/python/index.html , as Phillip Piper is no longer
maintaining the Python version.
If pip installed, look in C:\\users\\'username'\\appdata\local\programs\python\python38-32\lib\site-packages
"""
from ObjectListView2 import ObjectListView, ColumnDefn  # TODO - covered under GPL license! commercial distribute issues


def rowFormatter(listItem, Variable):
    """
    Toggles the rows in a ListCtrl or ObjectListView widget
    conditional formatting can be used here too.
    See https://objectlistview-python-edition.readthedocs.io/en/latest/recipes.html#how-can-i-change-the-colours-of-a-row
    """
    if hasattr(Variable, 'variable'):
        if Variable.variable == '*':
            listItem.SetBackgroundColour(wx.WHITE)
        elif Variable.variable == '':
            Variable.variable = '*'
            listItem.SetBackgroundColour(wx.WHITE)
        else:
            listItem.SetBackgroundColour((196, 226, 105))


def increment_column_index():
    n = 1
    while True:
        yield from (''.join(group) for group in itertools.product(string.ascii_uppercase, repeat=n))
        n += 1


def indent(level):
    return ' ' * 4 * level


def FindSubstringIndices(substring='', fullstring=''):
    """
    Returns positions of the word using the re library.
        >   https://stackoverflow.com/a/46317361/3382269
        >   https://docs.python.org/3/library/re.html

    The re module provides regular expression matching operations similar to those found in Perl. Both patterns and
    strings to be searched can be Unicode strings (str) as well as 8-bit strings (bytes).

    :param substring: word/character to locate in the full string
    :param fullstring: The string of interest
    :return: returns a list of indices (x.start()) from the start of the substring matched by group.
    """
    return [x.start() for x in re.finditer(substring, fullstring)]


class EditableListCtrl(wx.ListCtrl, listmix.TextEditMixin, listmix.ColumnSorterMixin):
    """
    TextEditMixin allows any column to be edited.
    https://wxpython.org/Phoenix/docs/html/wx.lib.mixins.listctrl.TextEditMixin.html#wx.lib.mixins.listctrl.TextEditMixin

    There are a few requirements needed in order for this to work generically:
        1. The combined class must have a GetListCtrl method that returns the wx.ListCtrl to be sorted, and the list
           control must exist at the time the wx.ColumnSorterMixin.__init__ method is called because it uses
           GetListCtrl.

        2. Items in the list control must have a unique data value set with list.SetItemData.
                > Items appended to list_ctrl must set using SetItemData

        3. The combined class must have an attribute named itemDataMap that is a dictionary mapping the data values
           to a sequence of objects representing the values in each column. These values are compared in the column
           sorter to determine sort order.
                > In other words, .itemDataMap has to be a dictionary, where the key of each entry are the data of a
                  row. The value is a list:
                > Note: .itemDataMap must be updated whenever label text (contents of cell) is edited

        EXAMPLE --------------------------------------------------------------------------------------------------------
            data = [['col1', 'col2', 'col3', ... , 'coln'],
                    ['col1', 'col2', 'col3', ... , 'coln'],
                    ['col1', 'col2', 'col3', ... , 'coln']]
            self.list_ctrl = EditableListCtrl('parent', wx.ID_ANY, style=wx.LC_HRULES | wx.LC_REPORT | wx.LC_VRULES)
            for row_num, row_data in enumerate(data):
                self.list_ctrl.Append(row_data)
                self.list_ctrl.itemDataMap[row_num] = row_data
                self.list_ctrl.SetItemData(row_num, row_data)
        END EXAMPLE ----------------------------------------------------------------------------------------------------
        https://www.blog.pythonlibrary.org/2011/01/04/wxpython-wx-listctrl-tips-and-tricks/
        https://stackoverflow.com/a/56689103/3382269

        windings - http://www.alanwood.net/demos/wingdings-3.html
    """

    def __init__(self, parent, ID=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize, style=0):
        """Constructor"""
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        listmix.TextEditMixin.__init__(self)
        self.itemDataMap = {}
        listmix.ColumnSorterMixin.__init__(self, 3)
        print('done')

    # Used by the ColumnSorterMixin, see wx/lib/mixins/listctrl.py
    def GetListCtrl(self):
        return self


class CommandParser(object):
    def __init__(self):
        self.variables = {}
        self.keys = []

    def buildStack(self, cmd):
        """
        https://stackoverflow.com/a/4998688/3382269
        https://stackoverflow.com/a/2136580/3382269
        """
        s = re.split(f'({"|".join(self.keys)})', cmd)
        # s = re.split(f'({"|".join(self.variables.keys())})',cmd)
        opStack = []
        stack = []
        for item in s:
            if item in self.keys:
                opStack.append(item)
            else:
                stack.append(item)
        return stack + opStack[::-1]  # merges opStack in reverse order with stack

    def evaluateStack(self, s):
        # note: operands are pushed onto the stack in reverse order. See .pop()
        op, num_args = s.pop(), 0
        if isinstance(op, tuple):
            op, num_args = op
        if op in self.variables:
            op2 = self.evaluateStack(s)
            op1 = self.evaluateStack(s)
            return f'{op1}{self.variables[op]}{op2}'
        else:
            return op


class Variable(object):
    def __init__(self, variable, header, data):
        self.variable = variable
        self.header = header
        self.data = data


class WizardFrame(wx.Frame):
    def __init__(self, title='Script Wizard', parent=None, **kwds):
        # begin wxGlade: WizardFrame.__init__
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER
        wx.Frame.__init__(self, parent=parent, title=title, **kwds)

        self.SetSize((585, 918))
        self.panel_1 = wx.Panel(self, wx.ID_ANY)
        self.panel_2 = wx.Panel(self.panel_1, wx.ID_ANY)
        self.panel_3 = wx.ScrolledWindow(self.panel_2, wx.ID_ANY, style=wx.BORDER_NONE)
        self.panel_4 = wx.ScrolledWindow(self.panel_3, wx.ID_ANY, style=wx.BORDER_NONE)

        # Class scope variables ----------------------------------------------------------------------------------------
        self.config = {}
        self.itemDataMap = {}
        self.choiceStringList = ['']
        self.variables = []
        self.instruments = {}
        self.savedResult = {}

        self.filepath_ctrl = wx.TextCtrl(self.panel_2, wx.ID_ANY, "", style=wx.TE_PROCESS_ENTER)
        self.import_btn = wx.Button(self.panel_2, wx.ID_ANY, "Import Variables")

        # SECTION: Assigning Variables ---------------------------------------------------------------------------------
        self.panel_5 = wx.Panel(self.panel_2, wx.ID_ANY)
        self.panel_6 = wx.Panel(self.panel_5, wx.ID_ANY)
        # self.list_ctrl_1 = EditableListCtrl(self.panel_5, wx.ID_ANY, style=wx.LC_HRULES | wx.LC_REPORT | wx.LC_VRULES)
        self.list_ctrl = ObjectListView(self.panel_5, wx.ID_ANY,
                                        sortable=False,
                                        useAlternateBackColors=False,
                                        cellEditMode=ObjectListView.CELLEDIT_DOUBLECLICK,
                                        style=wx.LC_REPORT | wx.SUNKEN_BORDER)
        self.btn_up = wx.Button(self.panel_5, wx.ID_ANY, u"▲")
        self.btn_down = wx.Button(self.panel_5, wx.ID_ANY, u"▼")
        self.btn_addRow = wx.Button(self.panel_5, wx.ID_ANY, u"🞦")
        self.radio_box_2 = wx.RadioBox(self.panel_5, wx.ID_ANY, "",
                                       choices=["Iterate sequentially", "Iterate over permutations"],
                                       majorDimension=0, style=wx.RA_SPECIFY_ROWS)
        self.label_32 = wx.StaticText(self.panel_6, wx.ID_ANY, "")
        self.label_33 = wx.StaticText(self.panel_6, wx.ID_ANY, "")
        self.text_ctrl_12 = wx.TextCtrl(self.panel_6, wx.ID_ANY, "")

        # SECTION: Construct Script ------------------------------------------------------------------------------------
        self.lineNum = [wx.StaticText()] * 5
        self.choice = [wx.Choice()] * 5
        self.variable_ctrl = [wx.TextCtrl()] * 5
        self.equal_label = [wx.StaticText()] * 5
        self.code_ctrl = [wx.TextCtrl()] * 5

        for idx in range(5):
            row = idx + 1
            self.lineNum[idx] = wx.StaticText(self.panel_4, wx.ID_ANY, f"[{row}]")
            self.choice[idx] = wx.Choice(self.panel_4, wx.ID_ANY, choices=self.choiceStringList)
            self.equal_label[idx] = wx.StaticText(self.panel_4, wx.ID_ANY, "=")
            self.equal_label[idx].SetFont(wx.Font(15, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, 0, ""))
            self.code_ctrl[idx] = wx.TextCtrl(self.panel_4, wx.ID_ANY, "", style=wx.TE_RICH2)
            self.variable_ctrl[idx] = wx.TextCtrl(self.panel_4, wx.ID_ANY, "")

        self.bitmap_button_1 = wx.BitmapButton(self.panel_4, wx.ID_ANY,
                                               wx.Bitmap("btn_add_depressed.png", wx.BITMAP_TYPE_ANY))
        self.bitmap_button_1.SetBitmapPressed(wx.Bitmap("btn_add_pressed.png", wx.BITMAP_TYPE_ANY))
        self.btn_execute = wx.Button(self.panel_2, wx.ID_ANY, "Execute")
        self.spin_ctrl_double_1 = wx.SpinCtrlDouble(self.panel_2, wx.ID_ANY, "1.0", min=0.0, max=100.0)
        self.btn_clear = wx.Button(self.panel_2, wx.ID_ANY, "Clear")
        self.btn_generate = wx.Button(self.panel_2, wx.ID_ANY, "Generate Code")
        self.btn_save = wx.Button(self.panel_2, wx.ID_ANY, "Save")

        # Menu Bar
        self.Frame_menubar = wx.MenuBar()
        self.SetMenuBar(self.Frame_menubar)
        # Menu Bar end

        self.__set_properties()
        self.__do_layout()
        # end wxGlade

        # Import Variables
        onBrowse_Event = lambda event: self.OnBrowse(event)
        self.Bind(wx.EVT_BUTTON, onBrowse_Event, self.import_btn)

        _LoadVariablesFromCSV_Event = lambda event: self._LoadVariablesFromCSV(event)
        self.Bind(wx.EVT_TEXT_ENTER, _LoadVariablesFromCSV_Event, self.filepath_ctrl)

        # Sort by column
        self.Bind(wx.EVT_LIST_COL_CLICK, self.OnColClick, self.list_ctrl)

        # Move selected row up
        RowUp_Event = lambda event: self.RowUp(event)
        self.Bind(wx.EVT_BUTTON, RowUp_Event, self.btn_up)

        # Move selected row down
        RowDown_Event = lambda event: self.RowDown(event)
        self.Bind(wx.EVT_BUTTON, RowDown_Event, self.btn_down)

        # Add new row
        AddRow_Event = lambda event: self._AddRow(event)
        self.Bind(wx.EVT_BUTTON, AddRow_Event, self.btn_addRow)

        # Change how variables are iterated over
        OnChangeTraversal_Event = lambda event: self._ChangeTraversal(event)
        self.Bind(wx.EVT_RADIOBOX, OnChangeTraversal_Event, self.radio_box_2)

        # Add new row of controls
        OnAddRow_Event = lambda event: self.OnAddRow(event)
        self.Bind(wx.EVT_BUTTON, OnAddRow_Event, self.bitmap_button_1)

        # Report assigned variables
        OnReportAssignedVariables_Event = lambda event: self._UpdateStyle(event)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, OnReportAssignedVariables_Event, self.list_ctrl)

        # Change style of text ctrl variables
        for code_ctrl in self.code_ctrl:
            OnSetStyle_Event = lambda event, text_ctrl=code_ctrl: self._SetStyle(event, text_ctrl)
            self.Bind(wx.EVT_TEXT, OnSetStyle_Event, code_ctrl)

        # Execute program
        OnRun_Event = lambda event: self.OnRun(event)
        self.Bind(wx.EVT_BUTTON, OnRun_Event, self.btn_execute)

        # Execute program
        OnGenerateCode_Event = lambda event: self.OnGenerateCode(event)
        self.Bind(wx.EVT_BUTTON, OnGenerateCode_Event, self.btn_generate)

        OnClear_Event = lambda event: self.OnClear(event)
        self.Bind(wx.EVT_BUTTON, OnClear_Event, self.btn_clear)

    def __set_properties(self):
        # begin wxGlade: WizardFrame.__set_properties
        self.SetTitle("Script Wizard")
        self.filepath_ctrl.SetMinSize((400, 23))

        # SECTION: Import Variables ____________________________________________________________________________________
        self.list_ctrl.SetMinSize((480, 154))
        self.btn_up.SetMinSize((40, 26))
        self.btn_down.SetMinSize((40, 26))
        self.btn_addRow.SetMinSize((40, 26))
        self.btn_up.SetToolTip("Move row up")
        self.btn_down.SetToolTip("Move row down")
        self.btn_addRow.SetToolTip("Add new row")
        self.list_ctrl.rowFormatter = rowFormatter
        self.list_ctrl.OwnerDraw = True
        self.list_ctrl.SetEmptyListMsg("No Variables Loaded")
        self.list_ctrl.SetColumns([ColumnDefn(title="",         align="left", valueGetter="", maximumWidth=0),
                                   ColumnDefn(title="Variable", align="left", width=100, valueGetter="variable"),
                                   ColumnDefn(title="Header",   align="left", width=100, valueGetter="header"),
                                   ColumnDefn(title="Data",     align="left", width=326, valueGetter="data")])
        self.AddRow()
        self.radio_box_2.SetSelection(0)
        self.label_32.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL, 0, ""))
        self.label_33.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL, 0, ""))
        self.text_ctrl_12.SetMinSize((300, 23))
        self.ChangeTraversal()

        # SECTION: Assign Variables ____________________________________________________________________________________
        for idx in range(5):
            self.choice[idx].SetSelection(0)
            self.choice[idx].SetMinSize((72, 23))
            self.code_ctrl[idx].SetMinSize((270, 23))
            self.variable_ctrl[idx].SetMinSize((40, 23))
            self.variable_ctrl[idx].SetToolTip("Assign result to variable")
            self.variable_ctrl[idx].SetFont(
                wx.Font(9, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, ""))
            self.code_ctrl[idx].SetFont(
                wx.Font(9, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, ""))

        # Example use expressed as hint
        self.code_ctrl[0].SetHint('out curA; out freqHz')
        self.code_ctrl[1].SetHint('oper')
        self.code_ctrl[2].SetHint('SYST:REM')
        self.code_ctrl[3].SetHint('CONF:VOLT:AC')
        self.code_ctrl[4].SetHint('READ?')
        self.variable_ctrl[4].SetHint('rslt')

        self.bitmap_button_1.SetMinSize((23, 23))
        self.panel_4.SetMinSize((530, 170))
        self.panel_4.SetScrollRate(10, 10)
        self.spin_ctrl_double_1.SetMinSize((50, 23))

    def __do_layout(self):
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_3 = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_1 = wx.GridBagSizer(0, 0)
        grid_sizer_2 = wx.GridBagSizer(0, 0)
        self.grid_sizer_3 = wx.GridBagSizer(0, 0)
        grid_sizer_4 = wx.GridBagSizer(0, 0)
        sizer_5 = wx.BoxSizer(wx.VERTICAL)

        label_1 = wx.StaticText(self.panel_2, wx.ID_ANY, "Script Wizard")
        label_1.SetFont(wx.Font(20, wx.FONTFAMILY_DECORATIVE, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_BOLD, 0, ""))
        bitmap_1 = wx.StaticBitmap(self.panel_2, wx.ID_ANY, wx.Bitmap("Fluke Logo.png", wx.BITMAP_TYPE_ANY))
        static_line_1 = wx.StaticLine(self.panel_2, wx.ID_ANY)
        static_line_1.SetMinSize((550, 2))
        grid_sizer_1.Add(label_1, (0, 0), (1, 6), wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_1.Add(bitmap_1, (0, 6), (1, 2), wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.RIGHT, 5)
        grid_sizer_1.Add(static_line_1, (1, 0), (1, 8), wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM | wx.TOP, 4)

        section_headers = [wx.StaticText()] * 4
        section_descriptions = [wx.StaticText()] * 4

        # SECTION: Import Variables ____________________________________________________________________________________
        section_headers[0] = wx.StaticText(self.panel_2, wx.ID_ANY, "Import Variables")
        section_descriptions[0] = wx.StaticText(self.panel_2, wx.ID_ANY, "Import variables into script to allow for easy iteration over values")
        section_headers[0].SetFont(wx.Font(12, wx.FONTFAMILY_DECORATIVE, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_BOLD, 0, ""))

        grid_sizer_1.Add(section_headers[0],      (2, 0), (1, 8), wx.LEFT | wx.RIGHT | wx.TOP, 10)
        grid_sizer_1.Add(section_descriptions[0], (3, 0), (1, 8), wx.BOTTOM | wx.LEFT, 10)
        grid_sizer_1.Add(self.filepath_ctrl,      (4, 0), (1, 7), wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 10)
        grid_sizer_1.Add(self.import_btn,         (4, 7), (1, 1), wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.LEFT | wx.RIGHT, 10)
        ################################################################################################################

        # SECTION: Assign Variables ____________________________________________________________________________________
        section_headers[1] = wx.StaticText(self.panel_5, wx.ID_ANY, "Assign Variables:")
        section_descriptions[1] = wx.StaticText(self.panel_5, wx.ID_ANY, "In the variable column, assign a unique variable name to an associated row of data")
        section_headers[1].SetFont(wx.Font(12, wx.FONTFAMILY_DECORATIVE, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_BOLD, 0, ""))

        grid_sizer_4.Add(section_headers[1],        (0, 0), (1, 7), wx.LEFT | wx.RIGHT | wx.TOP, 10)
        grid_sizer_4.Add(section_descriptions[1],   (1, 0), (1, 7), wx.LEFT, 10)
        grid_sizer_4.Add(self.list_ctrl,            (2, 0), (3, 7), wx.EXPAND | wx.LEFT, 10)
        grid_sizer_4.Add(self.btn_up,               (2, 7), (1, 1), wx.BOTTOM | wx.LEFT | wx.RIGHT, 5)
        grid_sizer_4.Add(self.btn_down,             (3, 7), (1, 1), wx.ALL, 5)
        grid_sizer_4.Add(self.btn_addRow,           (4, 7), (1, 1), wx.ALL, 5)
        grid_sizer_4.Add(self.radio_box_2,          (5, 0), (1, 3), wx.ALIGN_CENTER_VERTICAL | wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        grid_sizer_4.Add(self.panel_6,              (5, 3), (1, 5), wx.EXPAND | wx.TOP, 10)

        sizer_5.Add(self.label_32, 0, 0, 0)
        sizer_5.Add(self.label_33, 0, 0, 0)
        sizer_5.Add(self.text_ctrl_12, 0, wx.TOP, 5)
        self.panel_6.SetSizer(sizer_5)
        self.panel_5.SetSizer(grid_sizer_4)
        grid_sizer_1.Add(self.panel_5, (5, 0), (1, 8), wx.EXPAND | wx.TOP, 10)
        ################################################################################################################

        static_line_3 = wx.StaticLine(self.panel_2, wx.ID_ANY)
        static_line_3.SetMinSize((550, 2))
        grid_sizer_1.Add(static_line_3, (6, 0), (1, 8), wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM | wx.TOP, 10)

        # SECTION: Construct Script ------------------------------------------------------------------------------------
        section_headers[2] = wx.StaticText(self.panel_3, wx.ID_ANY, "Construct Script:")
        section_descriptions[2] = wx.StaticText(self.panel_3, wx.ID_ANY, "For each line, a command can be sent to the selected instrument ID (INSTR ID)")
        section_headers[2].SetFont(wx.Font(12, wx.FONTFAMILY_DECORATIVE, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_BOLD, 0, ""))
        label_10 = wx.StaticText(self.panel_3, wx.ID_ANY, "Line #")
        label_11 = wx.StaticText(self.panel_3, wx.ID_ANY, "INSTR ID")
        label_13 = wx.StaticText(self.panel_3, wx.ID_ANY, "Result")
        label_15 = wx.StaticText(self.panel_3, wx.ID_ANY, "=")
        label_12 = wx.StaticText(self.panel_3, wx.ID_ANY, "Code")
        label_10.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, 0, ""))
        label_11.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, 0, ""))
        label_13.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, 0, ""))
        label_15.SetFont(wx.Font(15, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, 0, ""))
        label_12.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, 0, ""))
        label_10.SetMinSize((34, 16))
        label_11.SetMinSize((72, 16))
        label_13.SetMinSize((40, 16))
        grid_sizer_2.Add(section_headers[2],        (0, 0), (1, 6), wx.LEFT | wx.TOP, 10)
        grid_sizer_2.Add(section_descriptions[2],   (1, 0), (1, 6), wx.BOTTOM | wx.LEFT, 10)
        grid_sizer_2.Add(label_10, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 15)
        grid_sizer_2.Add(label_11, (2, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        grid_sizer_2.Add(label_13, (2, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        grid_sizer_2.Add(label_15, (2, 3), (1, 1), wx.ALIGN_CENTER, 0)
        grid_sizer_2.Add(label_12, (2, 4), (1, 2), wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 5)
        # START OF SCROLLING PANEL -------------------------------------------------------------------------------------
        for row in range(5):
            self.grid_sizer_3.Add(self.lineNum[row], (row, 0), (1, 1), wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, 17)
            self.grid_sizer_3.Add(self.choice[row], (row, 1), (1, 1), wx.ALL, 5)
            self.grid_sizer_3.Add(self.variable_ctrl[row], (row, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
            self.grid_sizer_3.Add(self.equal_label[row], (row, 3), (1, 1), wx.ALIGN_CENTER, 0)
            self.grid_sizer_3.Add(self.code_ctrl[row], (row, 4), (1, 1), wx.ALL, 5)
        self.grid_sizer_3.Add(self.bitmap_button_1, (4, 5), (1, 1), wx.ALL, 5)

        self.panel_4.SetSizer(self.grid_sizer_3)
        grid_sizer_2.Add(self.panel_4, (3, 0), (1, 6), wx.BOTTOM | wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        self.panel_3.SetSizer(grid_sizer_2)
        grid_sizer_1.Add(self.panel_3, (7, 0), (1, 8), wx.EXPAND, 0)
        ################################################################################################################

        # SECTION: Execute Script --------------------------------------------------------------------------------------
        section_headers[3] = wx.StaticText(self.panel_2, wx.ID_ANY, "Execute Script:")
        section_descriptions[3] = wx.StaticText(self.panel_2, wx.ID_ANY, "Executes the current program.")
        section_headers[3].SetFont(wx.Font(12, wx.FONTFAMILY_DECORATIVE, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_BOLD, 0, ""))
        grid_sizer_1.Add(section_headers[3], (8, 0), (1, 3), wx.LEFT | wx.RIGHT | wx.TOP, 10)
        grid_sizer_1.Add(section_descriptions[3], (9, 0), (1, 3), wx.BOTTOM | wx.LEFT, 10)
        label_7 = wx.StaticText(self.panel_2, wx.ID_ANY, "FOR")
        label_8 = wx.StaticText(self.panel_2, wx.ID_ANY, "LOOP(S)")

        grid_sizer_1.Add(self.btn_execute,          (10, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 10)
        grid_sizer_1.Add(label_7,                   (10, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        grid_sizer_1.Add(self.spin_ctrl_double_1,   (10, 2), (1, 1), wx.ALL, 5)
        grid_sizer_1.Add(label_8,                   (10, 3), (1, 1), wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)

        ################################################################################################################

        static_line_2 = wx.StaticLine(self.panel_2, wx.ID_ANY)
        static_line_2.SetMinSize((550, 2))
        grid_sizer_1.Add(static_line_2, (11, 0), (1, 8), wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM | wx.TOP, 10)

        # SECTION: Buttons ---------------------------------------------------------------------------------------------
        grid_sizer_1.Add(self.btn_clear, (12, 0), (1, 1), wx.LEFT, 10)
        grid_sizer_1.Add(self.btn_generate, (12, 6), (1, 1), wx.LEFT, 10)
        grid_sizer_1.Add(self.btn_save, (12, 7), (1, 1), wx.ALIGN_RIGHT | wx.LEFT, 10)
        self.panel_2.SetSizer(grid_sizer_1)
        sizer_3.Add(self.panel_2, 1, wx.ALL | wx.EXPAND, 10)
        self.panel_1.SetSizer(sizer_3)
        sizer_2.Add(self.panel_1, 1, wx.EXPAND, 0)
        self.SetSizer(sizer_2)
        ################################################################################################################

        self.Layout()
        self.Centre()

    def OnBrowse(self, e):
        """
        A file dialog is dispalyed and files are filtered to show only files with the wildcard '.csv' file extension.
        The file path to the selected file is retrieved and displayed in the text ctrl object

        :param e: event e waits for button press from 'Browse...'
        """
        with wx.FileDialog(self, "Open CSV file", wildcard="CSV files (*.csv)|*.csv",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return  # the user changed their mind

            # Proceed loading the file chosen by the user
            path = fileDialog.GetPath()
        self.filepath_ctrl.SetValue(path)
        self.LoadVariablesFromCSV()

    def _LoadVariablesFromCSV(self, e):
        self.LoadVariablesFromCSV()

    def LoadVariablesFromCSV(self):
        """
        https://stackoverflow.com/a/41585079/3382269
        Ignore blank cells: https://stackoverflow.com/a/19128600/3382269

        Check if header exists: https://stackoverflow.com/a/40193471/3382269
            Grab the top (zeroth) row. Iterate through the cells and check if they contain any pure digit strings.
            If so, it's not a header. Negate that with a not in front of the whole expression.

        If converting a 2D list to a 2D numpy array, the sub-arrays must have the same length. Otherwise, a numpy array
        of lists is created (i.e. the inner lists won't be converted to numpy arrays). You cannot have a 2D array
        (matrix) with variable 2nd dimension.

        Consider list of numpy arrays instead. However, transposing may need to be done manually. zip_longest from
        itertools module may be suit this situation. zip_longest pads the results with None due to unmatching lengths,
        so the list comprehension and filter(None, ...) is used to remove the None values

            >   https://stackoverflow.com/a/38466687/3382269

        TODO -  (Resolved) Column sorting
            + https://stackoverflow.com/a/56689103/3382269
            + https://www.blog.pythonlibrary.org/2011/01/04/wxpython-wx-listctrl-tips-and-tricks/

        :return:
        """

        path = self.filepath_ctrl.GetValue()
        has_header = True
        # Read CSV file
        kwargs = {'newline': ''}
        mode = 'r'
        if sys.version_info < (3, 0):
            kwargs.pop('newline', None)
            mode = 'rb'
        with open(path, mode, **kwargs) as csvfile:
            reader = csv.reader(csvfile, delimiter=',', quotechar='"')
            fullstring_list = [[item for item in row if item != ''] for row in reader]  # ignore blank cells
            has_header = not any(cell.isdigit() for cell in fullstring_list[0])
        columnOriented = True

        if columnOriented:
            if has_header:
                self.varHeaders = fullstring_list[0]
                fullstring_list = fullstring_list[1:]  # Remove Header Row
            else:
                self.varHeaders = list(itertools.islice(increment_column_index(), len(fullstring_list)))

            self.varValues = [list(filter(None, row)) for row in itertools.zip_longest(*fullstring_list)]
        self.variables = [Variable(variable='*',
                                   header=self.varHeaders[row],
                                   data=', '.join(item)) for row, item in enumerate(self.varValues)]
        self.UpdateOLV()

    def UpdateOLV(self):
        """
        Remove the gap (usually intended for an icon or checkbox) in the first column of each row of an
        ObjectListView object by creating a 0 width first column.
            > https://stackoverflow.com/a/25080026/3382269
        :return:
        """
        self.list_ctrl.SetObjects(self.variables)

    def RowUp(self, e):
        """
        Move an item up the list
        """
        current_selection = self.list_ctrl.GetSelectedObject()
        variables = self.list_ctrl.GetObjects()
        if current_selection:
            index = variables.index(current_selection)
            if index > 0:
                new_index = index - 1
            else:
                new_index = len(variables) - 1
            variables.insert(new_index, variables.pop(index))
            self.variables = variables
            self.UpdateOLV()
            self.list_ctrl.Select(new_index)
            self.UpdateTraversalText()

    def RowDown(self, e):
        """
        Move an item down the list
        """
        current_selection = self.list_ctrl.GetSelectedObject()
        variables = self.list_ctrl.GetObjects()
        if current_selection:
            index = variables.index(current_selection)
            if index < len(variables) - 1:
                new_index = index + 1
            else:
                new_index = 0
            variables.insert(new_index, variables.pop(index))
            self.variables = variables
            self.UpdateOLV()
            self.list_ctrl.Select(new_index)
            self.UpdateTraversalText()

    def _AddRow(self, e):
        self.AddRow()

    def AddRow(self):
        newRow = [Variable(variable='*', header='NewRow', data='*')]
        self.variables = self.variables + newRow
        self.UpdateOLV()

    def OnColClick(self, e):
        print('column clicked')
        e.Skip()

    def SetChoices(self, config):
        """
        https://stackoverflow.com/a/23177452/3382269
        bool(dct) returns False if dct is an empty dictionary

        :param config: dictionary containing instrument info created in the wizard_instrument.py Frame
        :return:
        """
        if isinstance(config, dict) and config:
            self.config = config
            self.choiceStringList = ['']
            for instrID in self.config:
                instrName = self.config[instrID]['instr']
                self.choiceStringList.append(instrName)
            for choice in self.choice:
                choice.Clear()
                for item in self.choiceStringList:
                    choice.Append(item)
        else:
            pass

    def _ChangeTraversal(self, e):
        self.ChangeTraversal()

    def ChangeTraversal(self):
        selection = self.radio_box_2.GetSelection()
        if selection == 0:
            self.label_32.SetLabel("Sequentially iterates over each variable's data series.")
            self.label_33.SetLabel("Max traversal length = length of shortest series of data")
            self.text_ctrl_12.Enable(False)
        else:
            self.label_32.SetLabel("Iterates over all permutations as a Gray code sequence")
            self.label_33.SetLabel("The permutation order is indicated below:")
            self.text_ctrl_12.Enable(True)
            # self.text_ctrl_12.SetHint('Example: "X, Y, Z"                 X changes value slowest.')
            self.UpdateTraversalText()

    def GetTraversalOrder(self):
        return [var for _Variable in self.variables if (var := _Variable.variable) != ('' or '*')]

    def UpdateTraversalText(self):
        traversalString = u' ▶ '.join(self.GetTraversalOrder())

        self.text_ctrl_12.SetLabelText(traversalString)

    def GetCommands(self):
        return [{'choice': self.choice[row].GetStringSelection(),
                 'code': code.GetValue(),
                 'variable': self.variable_ctrl[row].GetValue()}
                for row, code in enumerate(self.code_ctrl)
                if code.GetValue() != '']

    def _GetCommandVariables(self):
        """
        Typically an internal method called by GetInputVariables and GetOutputVariables

        ==UNSORTED==
        Retrieves variables used in commands.
        NOTE: This method returns a set and thus order is not retaiend.
        :return: set(Example) --> {'input': set(inVar0, inVar1), 'output': set(outVar0, outVar1)}
        """
        cmdVars = {'input': set(), 'output': set()}
        for cmd in self.GetCommands():
            for inVar in self.variables:
                if inVar.variable in cmd['code']:
                    cmdVars['input'].add(inVar.variable)

            if cmd['variable'] != '' and cmd['code'] != '':
                cmdVars['output'].add(cmd['variable'])

        return cmdVars

    def GetInputVariables(self):
        """
        ==SORT ORDER PRESERVED==
        :return: {sample} ---> {'inVar0': 'data0', 'inVar1': 'data1', 'inVar2': 'data2'}
        """
        return {inVar: var.data
                for var in self.variables
                if (inVar := var.variable) in self._GetCommandVariables()['input']}

    def GetOutputVariables(self):
        """
        ==SORT ORDER PRESERVED==
        https://stackoverflow.com/a/34534134/3382269

        :return: {sample} ---> {'outVar0': rowNum0, 'outVar1': rowNum1, 'outVar2': rowNum2}
        """
        return {outVar: row
                for row, cmd in enumerate(self.GetCommands())
                if (outVar := cmd['variable']) in self._GetCommandVariables()['output']}

    def ReportUsedInstr(self):
        """https://stackoverflow.com/a/34534134/3382269"""
        return list(dict.fromkeys(choice.GetStringSelection() for choice in self.choice))

    def ReportInstrList(self):
        instrUsed = self.ReportUsedInstr()
        return [cfg for row, instr in enumerate(instrUsed) for cfg in self.config.values() if instr == cfg['instr']]

    def OnAddRow(self, e):
        """
        https://stackoverflow.com/a/22914694/3382269

        REMOVING A CONTROL FROM A SIZER --------------------------------------------------------------------------------
        For historical reasons calling this method with a wx.Window parameter is depreacted, as it will not be able to
        destroy the window since it is owned by its parent. You should use Detach instead.
            >   https://stackoverflow.com/a/13815383/3382269

        ScrolledPanel NOT UPDATING SCROLL BAR AFTER UPDATE -------------------------------------------------------------
        "Notify" the panel that the size of its child controls has changed. While sizes of all controls are recalculated
        automatically on resizing the window itself, to get the panel to update programmatically, add:
            >   self.test_panel.FitInside()
            >   https://stackoverflow.com/a/5914064/3382269

        SCROLL TO END OF PANEL -----------------------------------------------------------------------------------------
            >   self.Scroll(-1, self.GetClientSize()[1])
            >   clientSize is a tuple (x, y) of the widget's size and -1 specifies to not make any changes across the
                X direction.
            >   https://stackoverflow.com/a/3600699/3382269

        http://www.blog.pythonlibrary.org/2017/06/28/wxpython-getting-data-from-all-columns-in-a-listctrl/

        :param e: event e waits for button press from bitmap button
        """
        row = len(self.lineNum)

        # Append new controls to new row
        self.lineNum.append(wx.StaticText(self.panel_4, wx.ID_ANY, f"[{row + 1}]"))
        self.choice.append(wx.Choice(self.panel_4, wx.ID_ANY, choices=self.choiceStringList))
        self.variable_ctrl.append(wx.TextCtrl(self.panel_4, wx.ID_ANY, ""))
        self.equal_label.append(wx.StaticText(self.panel_4, wx.ID_ANY, "="))
        self.equal_label[-1].SetFont(wx.Font(15, wx.FONTFAMILY_DEFAULT,
                                             wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, 0, ""))
        self.code_ctrl.append(wx.TextCtrl(self.panel_4, wx.ID_ANY, "", style=wx.TE_RICH2))

        # Events
        OnSetStyle_Event = lambda event, text_ctrl=self.code_ctrl[-1]: self._SetStyle(event, text_ctrl)
        self.Bind(wx.EVT_TEXT, OnSetStyle_Event, self.code_ctrl[-1])

        # Set Properties
        self.choice[-1].SetSelection(0)
        self.choice[-1].SetMinSize((72, 23))
        self.code_ctrl[-1].SetMinSize((270, 23))
        self.variable_ctrl[-1].SetMinSize((40, 23))
        self.variable_ctrl[-1].SetFont(wx.Font(9, wx.FONTFAMILY_MODERN,
                                               wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, ""))
        self.code_ctrl[-1].SetFont(wx.Font(9, wx.FONTFAMILY_MODERN,
                                           wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, ""))
        # Set Layout
        self.grid_sizer_3.Add(self.lineNum[-1], (row, 0), (1, 1), wx.ALIGN_CENTER | wx.ALL, 5)
        self.grid_sizer_3.Add(self.choice[-1], (row, 1), (1, 1), wx.ALL, 5)
        self.grid_sizer_3.Add(self.variable_ctrl[-1], (row, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        self.grid_sizer_3.Add(self.equal_label[-1], (row, 3), (1, 1), wx.ALIGN_CENTER, 0)
        self.grid_sizer_3.Add(self.code_ctrl[-1], (row, 4), (1, 1), wx.ALL, 5)

        # Move button to the new row
        self.grid_sizer_3.Detach(self.bitmap_button_1)
        self.grid_sizer_3.Add(self.bitmap_button_1, (row, 5), (1, 1), wx.ALL, 5)

        self.grid_sizer_3.Layout()
        self.panel_4.FitInside()
        self.panel_4.Scroll(-1, self.panel_4.GetClientSize()[1])

    def _SetStyle(self, evt, text_ctrl, color=wx.RED):
        self.SetStyle(text_ctrl, color)

    def SetStyle(self, text_ctrl, color=wx.RED):
        """
        change the color of specific words in wxPython TextCtrl
            >   https://stackoverflow.com/a/46317361/3382269
        """
        fullstring = text_ctrl.GetValue()
        variable_dict = self.GetInputVariables()
        usedVar_dict = self.GetOutputVariables()

        for variable in variable_dict.keys():
            substring_occurrences = FindSubstringIndices(substring=variable, fullstring=fullstring)

            for idx in substring_occurrences:
                print(f'Instance of {variable} at ({idx}, {idx + len(variable)})')
                # SetStyle(start pos, end pos, style)
                text_ctrl.SetStyle(idx, idx + len(variable), wx.TextAttr(wx.RED))
                text_ctrl.SetStyle(idx + len(variable), -1, wx.TextAttr(wx.BLACK))

        for usedVar in usedVar_dict.keys():
            substring_occurrences = FindSubstringIndices(substring=usedVar, fullstring=fullstring)
            for idx in substring_occurrences:
                print(f'Instance of {usedVar} at ({idx}, {idx + len(usedVar)})')
                # SetStyle(start pos, end pos, style)
                text_ctrl.SetStyle(idx, idx + len(usedVar), wx.TextAttr(wx.Colour(148, 0, 211)))  # PURPLE
                text_ctrl.SetStyle(idx + len(usedVar), -1, wx.TextAttr(wx.BLACK))

    def _UpdateStyle(self, e):
        for code_line in self.code_ctrl:
            self.SetStyle(code_line)
        self.UpdateTraversalText()

    def OnRun(self, e):
        """
        https://stackoverflow.com/a/18648679/3382269

        STRUCTURES USED:
        commands = [['instr name', 'user's string command', 'optional user assigned variable to result'],
                    ['instr name', 'user's string command', 'optional user assigned variable to result']]
        :param e:
        :return:
        """
        inputVariable_dict = self.GetInputVariables()
        outputVariable_list = self.GetOutputVariables().keys()
        commands = self.GetCommands()

        # Convert string value to numpy array --------------------------------------------------------------------------
        inVars = {var: np.fromstring(inputVariable_dict[var], dtype=float, sep=', ')
                  for var in inputVariable_dict.keys()}

        # Create dictionary of results assigned to a variable. Repeated variables ignored ------------------------------
        self.savedResult = {var: [] for var in outputVariable_list if var not in self.savedResult.keys()}

        # Initialize instruments ---------------------------------------------------------------------------------------
        self.instruments = {instr['instr']: pyunivisa.CreateInstance(instr) for instr in self.ReportInstrList()}

        # Traversal method ---------------------------------------------------------------------------------------------
        dataPts = []
        if self.radio_box_2.GetSelection() == 0:    # Traverse simultaneously
            dataPts = [dict(zip(inVars, i)) for i in zip(*inVars.values())]
        elif self.radio_box_2.GetSelection() == 1:  # Traverse all permutations
            dataPts = [dict(zip(inVars, i)) for i in itertools.product(*inVars.values())]

        # Create command stack using parser ----------------------------------------------------------------------------
        parse = CommandParser()
        parse.keys = inVars
        stack = [parse.buildStack(cmd['code']) for cmd in commands]  # shunting-yard algorithm

        # Do command ---------------------------------------------------------------------------------------------------
        for parse.variables in dataPts:
            for idx, cmd in enumerate(stack):
                cmdCopy = cmd[:]
                choice = commands[idx]['choice']
                if choice != '':  # True if instrument sends command
                    outVar = commands[idx]['variable']
                    if outVar != '':  # True if result assigned a variable
                        print(f"{choice}.read({parse.evaluateStack(cmdCopy)})")
                        # self.savedResult[outVar].append(self.instruments[choice].read(parse.evaluateStack(cmdCopy))
                    else:
                        print(f"{choice}.write({parse.evaluateStack(cmdCopy)})")
                        # self.instruments[choice].write(parse.evaluateStack(cmdCopy))
                else:
                    print(f"# {choice}")
            print()

    def OnGenerateCode(self, e):
        """
        https://stackoverflow.com/a/18648679/3382269
        :param e:
        :return:
        """
        inputVariable_dict = self.GetInputVariables()
        outputVariable_dict = self.GetOutputVariables()
        commands = self.GetCommands()

        for level, line in enumerate(commands):
            cmd = line['code']
            for var in inputVariable_dict.keys():
                if var in cmd:
                    cmd = cmd.replace(var, 'f{' + var + '}')
            for var_saved_result in outputVariable_dict.keys():
                cmd = cmd.replace(var_saved_result, 'f{' + var_saved_result + '}')
            commands[level]['code'] = cmd

        print("\n# ============================================")
        for key in inputVariable_dict.keys():
            print('_' + key + ' = ' + str(inputVariable_dict[key]))
        print()
        level = 0
        if self.radio_box_2.GetSelection() == 0:
            unpackVars = []
            for key in inputVariable_dict.keys():
                unpackVars.append(f'{key}')
            # Note that if x and y are not the same length, zip will truncate to the shortest list.
            print(f"for {', '.join(unpackVars)} in zip(_{', _'.join(unpackVars)}):")
            level += 1

        elif self.radio_box_2.GetSelection() == 1:
            for key in inputVariable_dict.keys():
                print(indent(level) + f'for {key} in _{key}')
                level += 1

        # TODO make tracking indents a class
        for cmd in commands:
            if cmd['choice'] != '':
                if cmd['variable'] != '':
                    print(indent(level) + cmd['variable'] + ' = ' + f"{cmd['choice']}.read({cmd['code']})")
                else:
                    print(indent(level) + f"{cmd['choice']}.write({cmd['code']})")
            else:
                print(indent(level) + f"# {cmd['code']}")
        print("# ============================================")

    def OnClear(self, e):
        print('clear')
        self.list_ctrl.ClearAll()
        for choice in self.choice:
            choice.SetSelection(0)


class MyApp(wx.App):
    def OnInit(self):
        config = {'INSTR0': {'instr': 'f5560A', 'ip_address': '129.196.136.130', 'port': '3490', 'gpib_address': '',
                             'mode': 'SOCKET'},
                  'INSTR1': {'instr': 'k34461A', 'ip_address': '10.205.92.67', 'port': '3490', 'gpib_address': '',
                             'mode': 'SOCKET'},
                  'INSTR2': {'instr': 'f8846A', 'ip_address': '10.205.92.248', 'port': '3490', 'gpib_address': '',
                             'mode': 'SOCKET'},
                  'INSTR3': {'instr': 'f5520A', 'ip_address': '', 'port': '', 'gpib_address': '6', 'mode': 'GPIB'}}
        self.Scrip = WizardFrame(title='Script Wizard', parent=None)
        self.SetTopWindow(self.Scrip)
        self.Scrip.SetChoices(config)
        self.Scrip.Show()
        return True


# end of class MyApp

if __name__ == "__main__":
    app = MyApp(0)
    app.MainLoop()
