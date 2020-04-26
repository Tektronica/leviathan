from pathlib import Path
import numpy as np
import sys
import time
import csv
import pyvisa
import wx
import wx.grid
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar
import threading

# FILE PATH TO SAVE CSV ------------------------------------------------------------------------------------------------
csv_path = 'output\\csv\\'
fig_path = 'output\\figures\\'

# FOLDER SETUP ---------------------------------------------------------------------------------------------------------
Path('results').mkdir(parents=True, exist_ok=True)
filename = 'test'
path_to_file = f'results\\{filename}_{time.strftime("%Y%m%d_%H%M")}'


# FUNCTION DEFINITIONS -------------------------------------------------------------------------------------------------
def CreateInstance(item):
    if item['mode'] == 'Ethernet':
        instr = {'name': item['name'], 'mode': item['mode'], 'ip_address': item['ip_address'], 'port': item['port']}
    elif item['mode'] == 'GPIB':
        instr = {'name': item['name'], 'mode': item['mode'], 'gpib_address': item['gpib_address']}
    else:
        instr = {'name': item['name'], 'mode': item['mode'], 'ip_address': item['ip_address'], 'port': item['port']}
    return Visa(instr)


def average_reading(instrument, cmd, samples=10):
    data = []
    time.sleep(2)
    for idx in range(samples):
        data.append(float(instrument.read(cmd).split(',')[0]))
        time.sleep(0.20)
    array = np.asarray(data)
    mean = array.mean()
    std = np.sqrt(np.mean(abs(array - mean) ** 2))
    return mean, std


class Test:
    def __init__(self, parent):
        self.parent = parent
        # CONFIGURED INSTRUMENTS ---------------------------------------------------------------------------------------
        f8846A_id = {'ip_address': '10.205.92.248', 'port': '3490', 'gpib_address': '', 'mode': 'SOCKET'}
        k34461A_id = {'ip_address': '10.205.92.67', 'port': '3490', 'gpib_address': '', 'mode': 'SOCKET'}
        f5560A_id = {'ip_address': '129.196.136.130', 'port': '3490', 'gpib_address': '', 'mode': 'SOCKET'}

        # ESTABLISH COMMUNICATION WITH INSTRUMENTS ---------------------------------------------------------------------
        self.f8846A = Visa(f8846A_id)
        self.k34461A = Visa(k34461A_id)
        self.f5560A = Visa(f5560A_id)

    # RUN FUNCTION -----------------------------------------------------------------------------------------------------
    def run(self):
        _cur = [0, 1.20E-03, 4.00E-03, 6.00E-03, 9.00E-03, 1.19E-02, 1.2, 11.9, 12, 119, 120, 1000]
        _freq = [0, 50, 70, 100, 200, 500]
                
        for cur in _cur:
            for freq in _freq:
                self.f8846A.write(f'out {cur}A; out {freq}Hz')
                self.k34461A.write(f'oper')
                self.f5560A.write(f'SYST:REM')
                self.f5560A.write(f'CONF:VOLT:AC')
                rslt, *_ = average_reading(self.k34461A, f'READ?')
                new = rslt + 1
                print(new)
                self.parent.write_to_log([cur, freq, rslt, new])
                self.parent.write_to_log([cur, freq, rslt, new])


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        # begin wxGlade: TestFrame.__init__
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.SetSize((1234, 669))
        self.panel_frame = wx.Panel(self, wx.ID_ANY)

        self.thread = threading.Thread(target=self.run, args=())
        self.row = 0
        self.prevLine = ''
        self.line = ''

        self.panel_main = wx.Panel(self.panel_frame, wx.ID_ANY)
        self.notebook = wx.Notebook(self.panel_main, wx.ID_ANY)
        self.notebook_program = wx.Panel(self.notebook, wx.ID_ANY)
        self.panel_3 = wx.Panel(self.notebook_program, wx.ID_ANY)
        self.text_ctrl_log = wx.TextCtrl(self.panel_3, wx.ID_ANY, "", style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.text_ctrl_log_entry = wx.TextCtrl(self.panel_3, wx.ID_ANY, "", style=wx.TE_PROCESS_ENTER)
        self.button_1 = wx.Button(self.panel_3, wx.ID_ANY, "Enter")
        self.panel_plotter = wx.Panel(self.notebook_program, wx.ID_ANY, style=wx.BORDER_RAISED)

        self.figure = plt.figure(figsize=(2, 2))  # look into Figure((5, 4), 75)
        self.canvas = FigureCanvas(self.panel_plotter, -1, self.figure)
        self.toolbar = NavigationToolbar(self.canvas)
        self.toolbar.Realize()

        self.notebook_Spreadsheet = wx.Panel(self.notebook, wx.ID_ANY)
        self.grid_1 = MyGrid(self.notebook_Spreadsheet)
        self.btn_run = wx.Button(self.panel_main, wx.ID_ANY, "Run Test")
        self.btn_pause = wx.Button(self.panel_main, wx.ID_ANY, "Pause")
        self.btn_stop = wx.Button(self.panel_main, wx.ID_ANY, "Stop")
        self.btn_save = wx.Button(self.panel_main, wx.ID_ANY, "Save")

        # Run Measurement (start subprocess)
        on_run_event = lambda event: self.on_run(event)
        self.Bind(wx.EVT_BUTTON, on_run_event, self.btn_run)

        self.__set_properties()
        self.__do_layout()

    def __set_properties(self):
        # begin wxGlade: TestFrame.__set_properties
        self.SetTitle("Test Application")
        self.text_ctrl_log.SetMinSize((580, 410))
        self.text_ctrl_log_entry.SetMinSize((483, 23))
        self.canvas.SetMinSize((500, 381))
        self.grid_1.CreateGrid(31, 16)
        self.notebook.SetMinSize((1200, 500))

    def __do_layout(self):
        # begin wxGlade: TestFrame.__do_layout
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_1 = wx.GridBagSizer(0, 0)
        sizer_4 = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_2 = wx.GridSizer(1, 2, 0, 0)
        sizer_3 = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_4 = wx.GridBagSizer(0, 0)
        grid_sizer_3 = wx.GridBagSizer(0, 0)
        label_1 = wx.StaticText(self.panel_main, wx.ID_ANY, "Test Application")
        label_1.SetFont(wx.Font(20, wx.FONTFAMILY_DECORATIVE, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_BOLD, 0, ""))
        grid_sizer_1.Add(label_1, (0, 0), (1, 3), wx.ALIGN_CENTER_VERTICAL, 0)
        # bitmap_1 = wx.StaticBitmap(self.panel_main, wx.ID_ANY, wx.Bitmap("Fluke Logo.png", wx.BITMAP_TYPE_ANY))
        # grid_sizer_1.Add(bitmap_1, (0, 3), (1, 1), wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.ALL, 0)
        static_line_1 = wx.StaticLine(self.panel_main, wx.ID_ANY)
        static_line_1.SetMinSize((1200, 2))
        grid_sizer_1.Add(static_line_1, (1, 0), (1, 4), wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM | wx.TOP, 5)
        grid_sizer_3.Add(self.text_ctrl_log, (0, 0), (1, 2), wx.LEFT | wx.RIGHT | wx.TOP, 10)
        grid_sizer_3.Add(self.text_ctrl_log_entry, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL | wx.ALL, 10)
        grid_sizer_3.Add(self.button_1, (1, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL, 0)
        self.panel_3.SetSizer(grid_sizer_3)
        grid_sizer_2.Add(self.panel_3, 1, wx.EXPAND, 0)

        grid_sizer_4.Add(self.canvas, (0, 0), (1, 1), wx.ALL | wx.EXPAND, 10)
        grid_sizer_4.Add(self.toolbar, (1, 0), (1, 1), wx.ALL | wx.EXPAND, 10)

        sizer_3.Add(grid_sizer_4, 1, wx.EXPAND, 0)
        self.panel_plotter.SetSizer(sizer_3)
        grid_sizer_2.Add(self.panel_plotter, 1, wx.ALL | wx.EXPAND, 10)
        self.notebook_program.SetSizer(grid_sizer_2)
        sizer_4.Add(self.grid_1, 1, wx.EXPAND, 0)
        self.notebook_Spreadsheet.SetSizer(sizer_4)
        self.notebook.AddPage(self.notebook_program, "Program")
        self.notebook.AddPage(self.notebook_Spreadsheet, "Spreadsheet")
        grid_sizer_1.Add(self.notebook, (2, 0), (1, 4), wx.EXPAND, 0)
        static_line_2 = wx.StaticLine(self.panel_main, wx.ID_ANY)
        static_line_2.SetMinSize((1200, 2))
        grid_sizer_1.Add(static_line_2, (3, 0), (1, 4), wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM | wx.TOP, 5)
        grid_sizer_1.Add(self.btn_run, (4, 0), (1, 1), wx.ALIGN_RIGHT | wx.RIGHT, 20)
        grid_sizer_1.Add(self.btn_pause, (4, 1), (1, 1), wx.ALIGN_RIGHT | wx.RIGHT, 20)
        grid_sizer_1.Add(self.btn_stop, (4, 2), (1, 1), wx.ALIGN_RIGHT | wx.RIGHT, 10)
        grid_sizer_1.Add(self.btn_save, (4, 3), (1, 1), wx.ALIGN_RIGHT, 0)
        self.panel_main.SetSizer(grid_sizer_1)
        sizer_2.Add(self.panel_main, 1, wx.ALL | wx.EXPAND, 5)
        self.panel_frame.SetSizer(sizer_2)
        sizer_1.Add(self.panel_frame, 1, wx.EXPAND, 0)
        self.SetSizer(sizer_1)
        self.Layout()

    def on_run(self, event):
        self.thread.start()

    def run(self):
        print('run!')
        T = Test(self)
        T.run()

    def write_to_log(self, row_data):
        self.grid_1.write_list_to_row(self.row, row_data)
        self.row += 1

    def get_data(self, list_data):
        if isinstance(list_data, (list, np.ndarray)):
            self.data = np.asarray(list_data).astype(np.float)
            self.number_of_columns = self.data.shape[1]
            self.choices = [''] * self.number_of_columns
        else:
            self.data = np.array([[1, 2, 3], [2, 1, 4]])
            self.number_of_columns = self.data.shape[1]
        alphaidx = list(itertools.islice(increment_column_index(), self.number_of_columns))
        for m in range(self.number_of_columns):
            self.choices[m] = f'Col:{alphaidx[m]}'
        for idx in range(3):
            self.choice_dropdown[idx].SetItems(self.choices)

        self.choice_dropdown[0].SetSelection(0)
        self.choice_dropdown[1].SetSelection(1)

        self.x = 0.
        self.y = [0.]
        if self.number_of_columns >= 2:
            self.x = self.data[:, 0]
            self.y[0] = self.data[:, 1]
        else:
            self.x, self.y[0] = [1, 2, 3], [2, 1, 4]
        self.Draw_2DPlot()

    def Draw_2DPlot(self):
        # TODO - https://stackoverflow.com/questions/594266/equation-parsing-in-python
        self.ax = self.figure.add_subplot(111)

        for i, y in enumerate(self.y):
            # plot returns a list of artists of which you want the first element when changing x or y data
            self.plot = self.ax.plot(self.x, y)
        self.ax.set_title('2D Plot Title', fontsize=15, fontweight="bold")
        self.ax.set_ylabel(self.choices[0], fontsize=8)
        self.ax.set_xlabel(self.choices[1], fontsize=8)

        self.UpdateAxisLabels()
        self.figure.tight_layout()
        self.toolbar.update()  # Not sure why this is needed - ADS

    def update_yAxisData(self, event):
        selections = self.choice_dropdown[1].GetSelection()
        self.y = [0.] * len(selections)
        for i, column in enumerate(selections):
            self.y[i] = self.data[:, column]

        self.ax.clear()
        for i, y in enumerate(self.y):
            self.plot = self.ax.plot(self.x, y)

        self.UpdateAxisLabels()
        self.ax.relim()
        self.ax.autoscale_view()

        self.canvas.draw()
        self.canvas.flush_events()


class MyGrid(wx.grid.Grid):
    def __init__(self, parent):
        """Constructor"""
        wx.grid.Grid.__init__(self, parent, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0)
        self.selected_rows = []
        self.selected_cols = []
        self.history = []

        self.frame_number = 1

        # test all the events
        self.Bind(wx.grid.EVT_GRID_CELL_LEFT_CLICK, self.OnCellLeftClick)
        self.Bind(wx.grid.EVT_GRID_CELL_RIGHT_CLICK, self.OnCellRightClick)
        self.Bind(wx.grid.EVT_GRID_CELL_LEFT_DCLICK, self.OnCellLeftDClick)
        self.Bind(wx.grid.EVT_GRID_CELL_RIGHT_DCLICK, self.OnCellRightDClick)
        self.Bind(wx.grid.EVT_GRID_LABEL_LEFT_CLICK, self.OnLabelLeftClick)
        self.Bind(wx.grid.EVT_GRID_LABEL_RIGHT_CLICK, self.OnLabelRightClick)
        self.Bind(wx.grid.EVT_GRID_LABEL_LEFT_DCLICK, self.OnLabelLeftDClick)
        self.Bind(wx.grid.EVT_GRID_LABEL_RIGHT_DCLICK, self.OnLabelRightDClick)
        self.Bind(wx.grid.EVT_GRID_ROW_SIZE, self.OnRowSize)
        self.Bind(wx.grid.EVT_GRID_COL_SIZE, self.OnColSize)
        self.Bind(wx.grid.EVT_GRID_RANGE_SELECT, self.OnRangeSelect)
        self.Bind(wx.grid.EVT_GRID_CELL_CHANGED, self.OnCellChange)
        self.Bind(wx.grid.EVT_GRID_SELECT_CELL, self.OnSelectCell)
        self.Bind(wx.grid.EVT_GRID_EDITOR_SHOWN, self.OnEditorShown)
        self.Bind(wx.grid.EVT_GRID_EDITOR_HIDDEN, self.OnEditorHidden)
        self.Bind(wx.grid.EVT_GRID_EDITOR_CREATED, self.OnEditorCreated)

    def OnCellLeftClick(self, event):
        print("OnCellLeftClick: (%d,%d) %s\n" % (event.GetRow(), event.GetCol(), event.GetPosition()))
        event.Skip()

    def OnCellRightClick(self, event):
        print("OnCellRightClick: (%d,%d) %s\n" % (event.GetRow(), event.GetCol(), event.GetPosition()))
        menu_contents = [(wx.NewId(), "Cut", self.onCut),
                         (wx.NewId(), "Copy", self.onCopy),
                         (wx.NewId(), "Paste", self.onPaste)]
        popup_menu = wx.Menu()
        for menu_item in menu_contents:
            if menu_item is None:
                popup_menu.AppendSeparator()
                continue
            popup_menu.Append(menu_item[0], menu_item[1])
            self.Bind(wx.EVT_MENU, menu_item[2], id=menu_item[0])

        self.PopupMenu(popup_menu, event.GetPosition())
        popup_menu.Destroy()
        return

    def OnCellLeftDClick(self, evt):
        print("OnCellLeftDClick: (%d,%d) %s\n" % (evt.GetRow(), evt.GetCol(), evt.GetPosition()))
        evt.Skip()

    def OnCellRightDClick(self, evt):
        print("OnCellRightDClick: (%d,%d) %s\n" % (evt.GetRow(), evt.GetCol(), evt.GetPosition()))
        evt.Skip()

    def OnLabelLeftClick(self, evt):
        print("OnLabelLeftClick: (%d,%d) %s\n" % (evt.GetRow(), evt.GetCol(), evt.GetPosition()))
        evt.Skip()

    def OnLabelRightClick(self, evt):
        print("OnLabelRightClick: (%d,%d) %s\n" % (evt.GetRow(), evt.GetCol(), evt.GetPosition()))
        evt.Skip()

    def OnLabelLeftDClick(self, evt):
        print("OnLabelLeftDClick: (%d,%d) %s\n" % (evt.GetRow(), evt.GetCol(), evt.GetPosition()))
        evt.Skip()

    def OnLabelRightDClick(self, evt):
        print("OnLabelRightDClick: (%d,%d) %s\n" % (evt.GetRow(), evt.GetCol(), evt.GetPosition()))
        evt.Skip()

    def OnRowSize(self, evt):
        print("OnRowSize: row %d, %s\n" % (evt.GetRowOrCol(), evt.GetPosition()))
        evt.Skip()

    def OnColSize(self, evt):
        print("OnColSize: col %d, %s\n" % (evt.GetRowOrCol(), evt.GetPosition()))
        evt.Skip()

    def OnRangeSelect(self, evt):
        if evt.Selecting():
            msg = 'Selected'
        else:
            msg = 'Deselected'
        print("OnRangeSelect: %s  top-left %s, bottom-right %s\n" % (
            msg, evt.GetTopLeftCoords(), evt.GetBottomRightCoords()))
        evt.Skip()

    def OnCellChange(self, evt):
        print("OnCellChange: (%d,%d) %s\n" % (evt.GetRow(), evt.GetCol(), evt.GetPosition()))
        # Show how to stay in a cell that has bad data.  We can't just
        # call SetGridCursor here since we are nested inside one so it
        # won't have any effect.  Instead, set coordinates to move to in
        # idle time.
        value = self.GetCellValue(evt.GetRow(), evt.GetCol())
        if value == 'no good':
            self.moveTo = evt.GetRow(), evt.GetCol()

    def OnSelectCell(self, evt):
        if evt.Selecting():
            msg = 'Selected'
        else:
            msg = 'Deselected'
        print("OnSelectCell: %s (%d,%d) %s\n" % (msg, evt.GetRow(), evt.GetCol(), evt.GetPosition()))
        # Another way to stay in a cell that has a bad value...
        row = self.GetGridCursorRow()
        col = self.GetGridCursorCol()
        if self.IsCellEditControlEnabled():
            self.HideCellEditControl()
            self.DisableCellEditControl()
        value = self.GetCellValue(row, col)
        if value == 'no good 2':
            return  # cancels the cell selection
        evt.Skip()

    def OnEditorShown(self, evt):
        if evt.GetRow() == 6 and evt.GetCol() == 3 and \
                wx.MessageBox("Are you sure you wish to edit this cell?",
                              "Checking", wx.YES_NO) == wx.NO:
            evt.Veto()
            return
        print("OnEditorShown: (%d,%d) %s\n" % (evt.GetRow(), evt.GetCol(), evt.GetPosition()))
        evt.Skip()

    def OnEditorHidden(self, evt):
        if evt.GetRow() == 6 and evt.GetCol() == 3 and \
                wx.MessageBox("Are you sure you wish to finish editing this cell?",
                              "Checking", wx.YES_NO) == wx.NO:
            evt.Veto()
            return
        print("OnEditorHidden: (%d,%d) %s\n" % (evt.GetRow(), evt.GetCol(), evt.GetPosition()))
        evt.Skip()

    def OnEditorCreated(self, evt):
        print("OnEditorCreated: (%d, %d) %s\n" % (evt.GetRow(), evt.GetCol(), evt.GetControl()))

    def add_history(self, change):
        self.history.append(change)

    def get_selection(self):
        """
        Returns selected range's start_row, start_col, end_row, end_col
        If there is no selection, returns selected cell's start_row=end_row, start_col=end_col
        """
        if not len(self.GetSelectionBlockTopLeft()):
            selected_columns = self.GetSelectedCols()
            selected_rows = self.GetSelectedRows()
            if selected_columns:
                start_col = selected_columns[0]
                end_col = selected_columns[-1]
                start_row = 0
                end_row = self.GetNumberRows() - 1
            elif selected_rows:
                start_row = selected_rows[0]
                end_row = selected_rows[-1]
                start_col = 0
                end_col = self.GetNumberCols() - 1
            else:
                start_row = end_row = self.GetGridCursorRow()
                start_col = end_col = self.GetGridCursorCol()
        elif len(self.GetSelectionBlockTopLeft()) > 1:
            wx.MessageBox("Multiple selections are not supported", "Warning")
            return []
        else:
            start_row, start_col = self.GetSelectionBlockTopLeft()[0]
            end_row, end_col = self.GetSelectionBlockBottomRight()[0]

        return [start_row, start_col, end_row, end_col]

    def get_selected_cells(self):
        # returns a list of selected cells
        selection = self.get_selection()
        if not selection:
            return

        start_row, start_col, end_row, end_col = selection
        for row in range(start_row, end_row + 1):
            for col in range(start_col, end_col + 1):
                yield [row, col]

    def onCopy(self, event):
        """
        Copies range of selected cells to clipboard.
        """

        selection = self.get_selection()
        if not selection:
            return []
        start_row, start_col, end_row, end_col = selection

        data = u''

        rows = range(start_row, end_row + 1)
        for row in rows:
            columns = range(start_col, end_col + 1)
            for idx, column in enumerate(columns, 1):
                if idx == len(columns):
                    # if we are at the last cell of the row, add new line instead
                    data += self.GetCellValue(row, column) + "\n"
                else:
                    data += self.GetCellValue(row, column) + "\t"

        text_data_object = wx.TextDataObject()
        text_data_object.SetText(data)

        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(text_data_object)
            wx.TheClipboard.Close()
        else:
            wx.MessageBox("Can't open the clipboard", "Warning")

    def onPaste(self, event):
        if not wx.TheClipboard.Open():
            wx.MessageBox("Can't open the clipboard", "Warning")
            return False

        clipboard = wx.TextDataObject()
        wx.TheClipboard.GetData(clipboard)
        wx.TheClipboard.Close()
        data = clipboard.GetText()
        if data[-1] == "\n":
            data = data[:-1]

        try:
            cells = self.get_selected_cells()
            cell = next(cells)
        except StopIteration:
            return False

        start_row = end_row = cell[0]
        start_col = end_col = cell[1]
        max_row = self.GetNumberRows()
        max_col = self.GetNumberCols()

        history = []
        out_of_range = False

        for row, line in enumerate(data.split("\n")):
            target_row = start_row + row
            if not (0 <= target_row < max_row):
                out_of_range = True
                break

            if target_row > end_row:
                end_row = target_row

            for col, value in enumerate(line.split("\t")):
                target_col = start_col + col
                if not (0 <= target_col < max_col):
                    out_of_range = True
                    break

                if target_col > end_col:
                    end_col = target_col

                # save previous value of the cell for undo
                history.append([target_row, target_col, {"value": self.GetCellValue(target_row, target_col)}])

                self.SetCellValue(target_row, target_col, value)

        self.SelectBlock(start_row, start_col, end_row, end_col)  # select pasted range
        if out_of_range:
            wx.MessageBox("Pasted data is out of Grid range", "Warning")

        self.add_history({"type": "change", "cells": history})

    def onDelete(self, e):
        cells = []
        for row, col in self.get_selected_cells():
            attributes = {
                "value": self.GetCellValue(row, col),
                "alignment": self.GetCellAlignment(row, col)
            }
            cells.append((row, col, attributes))
            self.SetCellValue(row, col, "")

        self.add_history({"type": "delete", "cells": cells})

    def onCut(self, e):
        self.onCopy(e)
        self.onDelete(e)

    def retrieveList(self):
        """
        Copies range of selected cells to clipboard.
        """

        selection = self.get_selection()
        if not selection:
            return []
        start_row, start_col, end_row, end_col = selection

        data = u''
        list_row = []
        list_data = []
        rows = range(start_row, end_row + 1)
        for row in rows:
            columns = range(start_col, end_col + 1)
            for idx, column in enumerate(columns, 1):
                if idx == len(columns):
                    # if we are at the last cell of the row, add new line instead
                    list_row.append(self.GetCellValue(row, column))
                    list_data.append(list_row)
                    list_row = []
                else:
                    list_row.append(self.GetCellValue(row, column))

        return list_data

    def write_list_to_row(self, row=0, data=None):
        if data is not None:
            if row >= 0:
                if row >= self.GetNumberRows() - 1:
                    self.AppendRows(5)
                for col, item in enumerate(data):
                    self.SetCellValue(row, col, str(item))
            else:
                print('row must be in range greater than 0')
        else:
            print('No data to write to grid!')
            pass


class Visa:
    def __init__(self, _instr_info):
        self.instr_info = _instr_info
        self.mode = self.instr_info['mode']

        self.INSTR = None
        self.address = None
        self.port = None

        self.rm = pyvisa.ResourceManager()
        self.timeout = 3000  # 1 (60e3) minute timeout

        # TODO - verify this works as intended... Otherwise leave INSTR lines commented
        # if mode is SOCKET:
        if self.mode == 'SOCKET':
            self.address = self.instr_info['ip_address']
            self.port = self.instr_info['port']
            # self.INSTR = self.rm.open_resource(f'TCPIP::{self.address}::{self.port}::SOCKET')
            # self.INSTR.read_termination = '\n'

        # if mode is GPIB:
        elif self.mode == 'GPIB':
            self.address = self.instr_info['gpib_address']
            # self.INSTR = self.rm.open_resource(f'GPIB0::{self.address}::INSTR')

        # if mode is INSTR:
        elif self.mode == 'INSTR':
            self.address = self.instr_info['ip_address']
            # self.INSTR = self.rm.open_resource(f'TCPIP::{self.address}::INSTR')
            # self.INSTR.read_termination = '\n'

        # if mode is SERIAL:
        elif self.mode == 'SERIAL':
            self.address = self.instr_info['ip_address']
            # self.INSTR = self.rm.open_resource(f'{self.address}')
            # self.INSTR.read_termination = '\n'

        # TODO - http://lampx.tugraz.at/~hadley/num/ch9/python/9.2.php
        # if mode is SERIAL:
        elif self.mode == 'USB':
            self.address = self.instr_info['ip_address']
            # self.INSTR = self.rm.open_resource(f'{self.address}')
            # self.INSTR.read_termination = '\n'

        # if mode is NIGHTHAWK:
        elif self.mode == 'NIGHTHAWK':
            self.address = self.instr_info['ip_address']
            self.port = self.instr_info['port']
            # self.INSTR = self.rm.open_resource(f'TCPIP::{self.address}::{self.port}::SOCKET')
            # self.INSTR.read_termination = '>'
            # self.INSTR.read()
        else:
            print('Failed to connect.')

        # TODO - Leave commented until after verifying visa communication works
        # self.INSTR.timeout = self.timeout

    def info(self):
        print(self.instr_info)

    def identify(self):
        print()
        try:
            identity = self.query('*IDN?')
            print(identity + '\n')
        # TODO - do not use bare except. how to find visa?
        # except visa.VisaIOError:
        except:
            print('Failed to connect to address: ' + self.address)

    def write(self, cmd):
        self.INSTR.write(f'{cmd}')

    def read(self):
        response = None
        if self.mode == 'NIGHTHAWK':
            response = (self.INSTR.read().split("\r")[0].lstrip())
        else:
            response = self.INSTR.read()
        return response

    def query(self, cmd):
        response = None
        if self.mode == 'NIGHTHAWK':
            response = (self.INSTR.query(f'{cmd}')).split("\r")[0].lstrip()
        else:
            response = (self.INSTR.query(f'{cmd}'))
        return response

    def close(self):
        self.INSTR.close()


class MyApp(wx.App):
    def OnInit(self):
        self.frame = TestFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(self.frame)
        self.frame.Show()
        return True

    def get_test_frame(self):
        return self.frame


def main():
    app = MyApp(0)
    app.MainLoop()


if __name__ == "__main__":
    main()
