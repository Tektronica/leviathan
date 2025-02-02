from pathlib import Path
import numpy as np
import threading
import visa
import time
import sys
import csv
import os
import wx
import wx.grid
import wx.propgrid as wxpg

import matplotlib.pyplot as plt
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar


# FILE PATH TO SAVE CSV ------------------------------------------------------------------------------------------------
csv_path = 'output\\csv\\'
fig_path = 'output\\figures\\'

# FOLDER SETUP ---------------------------------------------------------------------------------------------------------
Path('results').mkdir(parents=True, exist_ok=True)
filename = 'test'
path_to_file = f'results\\{filename}_{time.strftime("%Y%m%d_%H%M")}'


# FUNCTION DEFINITIONS -------------------------------------------------------------------------------------------------
def average_reading(instrument, cmd, samples=10):
    data = []
    time.sleep(5)
    for idx in range(samples):
        data.append(float(instrument.query(cmd).split(',')[0]))
        time.sleep(0.20)
    array = np.asarray(data)
    mean = array.mean()
    std = np.sqrt(np.mean(abs(array - mean) ** 2))
    return mean, std


class Test:
    def __init__(self, parent):
        self.parent = parent
        # CONFIGURED INSTRUMENTS ---------------------------------------------------------------------------------------
        f5560A_id = {'ip_address': '129.196.136.130', 'port': '3490', 'gpib_address': '', 'mode': 'NIGHTHAWK'}
        f5790A_id = {'ip_address': '', 'port': '', 'gpib_address': '6', 'mode': 'GPIB'}
        k34461A_id = {'ip_address': '10.205.92.155', 'port': '3490', 'gpib_address': '', 'mode': 'INSTR'}

        # ESTABLISH COMMUNICATION WITH INSTRUMENTS ---------------------------------------------------------------------
        self.f5560A = VisaClient(f5560A_id)
        self.f5790A = VisaClient(f5790A_id)
        self.k34461A = VisaClient(k34461A_id)

    # SETUP ------------------------------------------------------------------------------------------------------------
    def setup(self):
        self.f5790A.write(f'*RST; INPUT INPUT2; EXTRIG OFF; HIRES ON; EXTGUARD ON')
        self.k34461A.write('*RST;CONF:VOLT:DC')
        self.f5560A.write('*RST')

    # RUN FUNCTION -----------------------------------------------------------------------------------------------------
    def run(self):
        self.setup()
        _freq = [1000]
        _cur = [119e-3]
        _range_label = ["120uA", "1.2mA", "12mA", "120mA"]
        # _cur = [11.9e-3]
        self.parent.write_header(["range", "freq", "cur", "nom", "nom_dist",
                                  "loaded", "loaded_dist", "resistor", "cur_shift", "ppm_shift"])

        for freq in _freq:
            for idx, cur in enumerate(_cur):
                self.f5560A.write(f'out {cur}A;out {freq}Hz ')

                print('===================================================')
                print(f'\nOperating in {_range_label[idx]} range at {cur}A')
                resistor = input('\nSpecify the sense resistor in ohms:')
                input('\nReady to operate?')
                self.f5560A.write(f'OPER')

                self.f5790A.write(f'TRIG')
                nom, *_ = average_reading(self.f5790A, f'*WAI;VAL?')
                nom = nom / float(resistor)
                self.k34461A.write('SYST:REM')
                nom_dist, *_ = average_reading(self.k34461A, f'READ?')
                nom_dist = round(nom_dist / 100e-3, 4)
                self.f5560A.write(f'STBY')

                input('\nConnect 400uH. Ready to operate?')
                self.f5560A.write(f'OPER')
                loaded, *_ = average_reading(self.f5790A, f'*WAI;VAL?')
                loaded = loaded / float(resistor)
                self.k34461A.write('SYST:REM')
                loaded_dist, *_ = average_reading(self.k34461A, f'READ?')
                loaded_dist = round(loaded_dist / 100e-3, 4)
                self.f5560A.write(f'STBY')

                cur_shift = loaded - nom
                ppm_shift = round((cur_shift / nom) * 1e6, 2)

                self.parent.write_to_log([_range_label[idx], freq, cur, nom, nom_dist,
                                          loaded, loaded_dist, resistor, cur_shift, ppm_shift])
                self.parent.plot_data()

        self.close_instruments()

    def close_instruments(self):
        self.f5560A.close()
        self.f5790A.close()
        self.k34461A.close()


class TestFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        # begin wxGlade: TestFrame.__init__
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.SetSize((1234, 669))
        self.panel_frame = wx.Panel(self, wx.ID_ANY)

        self.thread = threading.Thread(target=self.run, args=())
        self.thread.daemon = True
        self.row = 0
        self.prevLine = ''
        self.line = ''
        self.table = {}
        self.overlay = {}
        self.ax = None
        self.x, self.y = [0.], [[0.]]
        self.flag_complete = False

        self.panel_main = wx.Panel(self.panel_frame, wx.ID_ANY)
        self.notebook = wx.Notebook(self.panel_main, wx.ID_ANY)
        self.notebook_program = wx.Panel(self.notebook, wx.ID_ANY)
        self.panel_3 = wx.Panel(self.notebook_program, wx.ID_ANY)
        self.text_ctrl_log = wx.TextCtrl(self.panel_3, wx.ID_ANY, "", style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.text_ctrl_log_entry = wx.TextCtrl(self.panel_3, wx.ID_ANY, "", style=wx.TE_PROCESS_ENTER)
        sys.stdout = self.text_ctrl_log
        self.button_1 = wx.Button(self.panel_3, wx.ID_ANY, "Enter")
        self.notebook_1 = wx.Notebook(self.notebook_program, wx.ID_ANY)
        self.notebook_1_pane_2 = wx.Panel(self.notebook_1, wx.ID_ANY)

        self.figure = plt.figure(figsize=(2, 2))  # look into Figure((5, 4), 75)
        self.canvas = FigureCanvas(self.notebook_1_pane_2, -1, self.figure)
        self.toolbar = NavigationToolbar(self.canvas)
        self.toolbar.Realize()
        self.notebook_1_Settings = wx.Panel(self.notebook_1, wx.ID_ANY)
        # Use PropertyGridManger instead, if pages are desired
        self.property_grid_1 = wx.propgrid.PropertyGrid(self.notebook_1_Settings, wx.ID_ANY)

        self.notebook_Spreadsheet = wx.Panel(self.notebook, wx.ID_ANY)
        self.grid_1 = MyGrid(self.notebook_Spreadsheet)
        self.btn_run = wx.Button(self.panel_main, wx.ID_ANY, "Run Test")
        # TODO - Pause: https://stackoverflow.com/a/34313474/3382269
        self.btn_pause = wx.Button(self.panel_main, wx.ID_ANY, "Pause")
        self.btn_stop = wx.Button(self.panel_main, wx.ID_ANY, "Stop")
        self.btn_save = wx.Button(self.panel_main, wx.ID_ANY, "Save")

        # Run Measurement (start subprocess)
        on_run_event = lambda event: self.on_run(event)
        self.Bind(wx.EVT_BUTTON, on_run_event, self.btn_run)

        self.Bind(wxpg.EVT_PG_CHANGED, self.OnGridChangeEvent)

        self.__set_properties()
        self.__do_layout()

    def __set_properties(self):
        # begin wxGlade: TestFrame.__set_properties
        self.SetTitle("Test Application")
        self.text_ctrl_log.SetMinSize((580, 410))
        self.text_ctrl_log_entry.SetMinSize((483, 23))
        self.canvas.SetMinSize((585, 406))
        self.grid_1.CreateGrid(31, 16)
        self.grid_1.SetDefaultColSize(150)
        self.notebook.SetMinSize((1200, 500))
        self._create_plot_properties()

    def __do_layout(self):
        # begin wxGlade: TestFrame.__do_layout
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_1 = wx.GridBagSizer(0, 0)
        sizer_4 = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_2 = wx.GridSizer(1, 2, 0, 0)
        sizer_5 = wx.BoxSizer(wx.VERTICAL)
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

        grid_sizer_4.Add(self.canvas, (0, 0), (1, 1), wx.ALL | wx.EXPAND)
        grid_sizer_4.Add(self.toolbar, (1, 0), (1, 1), wx.ALL | wx.EXPAND)

        sizer_3.Add(grid_sizer_4, 1, wx.EXPAND, 0)
        self.notebook_1_pane_2.SetSizer(sizer_3)
        sizer_5.Add(self.property_grid_1, 1, wx.EXPAND, 0)
        self.notebook_1_Settings.SetSizer(sizer_5)
        self.notebook_1.AddPage(self.notebook_1_pane_2, "Plot")
        self.notebook_1.AddPage(self.notebook_1_Settings, "Settings")
        grid_sizer_2.Add(self.notebook_1, 1, wx.EXPAND, 0)

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

    def _create_plot_properties(self):
        pg = self.property_grid_1
        # pg.AddPage("Page 1 - Plot Settings")  # if pages are needed, use PropertyGridManger instead
        dir_path = os.path.dirname(os.path.realpath(__file__))
        pg.Append(wxpg.PropertyCategory("1 - Basic Properties"))
        pg.Append(wxpg.StringProperty(label="Title",    value="Title"))
        pg.Append(wxpg.StringProperty(label="X Label",  value="X Label"))
        pg.Append(wxpg.StringProperty(label="Y Label",  value="Y Label"))
        pg.Append(wxpg.BoolProperty(label="Grid",       value=True))
        pg.SetPropertyAttribute(id="Grid", attrName="UseCheckbox", value=True)

        pg.Append(wxpg.PropertyCategory("2 - Data"))
        # https://discuss.wxpython.org/t/wxpython-pheonix-4-0-2-question-regarding-multichoiceproperty-and-setting-the-selection-of-the-choices/30044
        # https://discuss.wxpython.org/t/how-to-set-propertygrid-values/30152/4
        pg.Append(wxpg.EnumProperty(label="Scale", labels=['Linear', 'SemilogX', 'SemilogY', 'LogLog']))
        pg.Append(wxpg.EnumProperty(label="X Data",             name="X Data", labels=['NaN'],   values=[0]))
        pg.Append(wxpg.MultiChoiceProperty(label="Y Data",      name='Y Data', choices=['NaN'],  value=['NaN']))
        pg.Append(wxpg.EnumProperty(label="Data Labels", name="Data Labels",   labels=['NaN'],   values=[0]))

        pg.Append(wxpg.PropertyCategory("3 - Optional Static Plot Overlay"))
        pg.Append(wxpg.FileProperty(label="Overlay Plot", value=rf"{dir_path}"))
        pg.Append(wxpg.EnumProperty(label="X Axis Variable", labels=['']))
        pg.Append(wxpg.EnumProperty(label="Y Axis Variable", labels=['']))

        pg.Append(wxpg.PropertyCategory("4 - Advanced Properties"))
        pg.Append(wxpg.ArrayStringProperty(label="xLim",   value=['0', '100']))
        pg.Append(wxpg.ArrayStringProperty(label="yLim",   value=['0', '100']))
        pg.Append(wxpg.DateProperty(label="Date",          value=wx.DateTime.Now()))
        pg.Append(wxpg.ColourProperty(label="Line Colour", value='#1f77b4'))
        pg.Append(wxpg.FontProperty(label="Font",          value=self.GetFont()))
        pg.Grid.FitColumns()

    def on_run(self, event):
        self.thread.start()

    def run(self):
        print('run!')
        self.flag_complete = False
        T = Test(self)
        T.run()
        self.flag_complete = True

    def OnGridChangeEvent(self, evt):
        pg = self.property_grid_1
        prop = evt.GetProperty()
        if prop.GetName() == 'Overlay Plot':
            self.get_static_overlay_data()
            choices = list(self.overlay.keys())
            pg.GetProperty('X Axis Variable').SetChoices(wxpg.PGChoices(['Select option'] + choices))
            pg.GetProperty('Y Axis Variable').SetChoices(wxpg.PGChoices(['Select option'] + choices))

        elif prop.GetName() == 'X Axis Variable' or 'Y Axis Variable' and self.flag_complete:
            self.update_yAxisData()

    def get_static_overlay_data(self):
        pg = self.property_grid_1
        file = pg.GetPropertyValue('Overlay Plot')
        # Read CSV file
        kwargs = {'newline': '', 'encoding': "utf-8-sig"}  # https://stackoverflow.com/a/49543191/3382269
        mode = 'r'
        if sys.version_info < (3, 0):
            kwargs.pop('newline', None)
            mode = 'rb'
        with open(f'{file}', mode, **kwargs) as csvfile:
            spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
            for row in spamreader:
                if not self.overlay:
                    self.overlay = {key: [] for key in row}
                else:
                    for idx, key in enumerate(self.overlay.keys()):
                        self.overlay[key].append(row[idx])

    def write_header(self, header):
        if not self.table:
            self.table = {key: [] for key in header}
        else:
            self.table = {header[col]: self.table[key] for col, key in enumerate(self.table.keys())}

        self.grid_1.write_list_to_row(self.row, self.table.keys())
        self.row += 1

    def write_to_log(self, row_data):
        self.grid_1.write_list_to_row(self.row, row_data)
        self.row += 1

        if not self.table:
            self.table = {f'col {idx}': item for idx, item in enumerate(row_data)}
        else:
            for idx, key in enumerate(self.table.keys()):
                self.table[key].append(row_data[idx])

    def plot_data(self):
        if not self.ax:
            self.draw_2dplot()
        else:
            pg = self.property_grid_1
            # self.x = self.table[pg.GetProperty('X Data').GetValueAsString()]
            self.x = self.table[pg.GetPropertyValueAsString('X Data')]
            self.y = [self.table[col] for col in pg.GetPropertyValue('Y Data')]
            self.update_yAxisData()

    def _plot_helper(self):
        pg = self.property_grid_1
        self.plot = [self.ax.plot]*len(self.y)
        for idx, y in enumerate(self.y):
            # plot returns a list of artists of which you want the first element when changing x or y data
            scale = pg.GetPropertyValueAsString('Scale')
            if scale == 'Linear':
                self.plot[idx], = self.ax.plot(self.x, y)
                self.draw_overlay(self.ax.plot)
            if scale == 'SemilogX':
                self.plot[idx], = self.ax.semilogx(self.x, y)
                self.draw_overlay(self.ax.semilogx)
            if scale == 'SemilogY':
                self.plot[idx], = self.ax.semilogy(self.x, y)
                self.draw_overlay(self.ax.semilogy)
            if scale == 'LogLog':
                self.plot[idx], = self.ax.loglog(self.x, y)
                self.draw_overlay(self.ax.loglog)

    def draw_overlay(self, plot_type):
        pg = self.property_grid_1
        x_var = pg.GetPropertyValueAsString('X Axis Variable')
        y_var = pg.GetPropertyValueAsString('Y Axis Variable')
        if x_var and y_var != ('' or 'Select option'):
            plot_type(self.overlay[x_var], self.overlay[y_var])

    def draw_2dplot(self):
        pg = self.property_grid_1
        if self.table:
            choices = list(self.table.keys())
            pg.GetProperty('X Data').SetChoices(wxpg.PGChoices(choices))
            pg.GetProperty('Y Data').SetChoices(wxpg.PGChoices(choices))
            pg.GetProperty('Data Labels').SetChoices(wxpg.PGChoices([""]+choices))
            pg.SetPropertyValue('X Data', choices[0])
            pg.SetPropertyValue('Y Data', [choices[1]])

            self.x, self.y = self.table[choices[0]], [self.table[choices[1]]]
        else:
            self.x, self.y = [0.], [[0.]]

        self.ax = self.figure.add_subplot(111)
        self._plot_helper()

        self.update_axis_labels()
        self.figure.tight_layout()
        self.toolbar.update()  # Not sure why this is needed - ADS

    def update_yAxisData(self):
        self.ax.clear()
        self._plot_helper()

        self.update_data_labels()
        self.update_axis_labels()
        self.ax.relim()
        self.ax.autoscale_view()

        self.canvas.draw()
        self.canvas.flush_events()

    def update_data_labels(self):
        pg = self.property_grid_1
        label_var = pg.GetPropertyValueAsString('Data Labels')
        if label_var:
            for idx, text in enumerate(self.table[label_var]):
                plt.annotate(f'{label_var}={round(text, 3)}',
                             (self.x[idx], self.y[0][idx]),
                             xytext=(0, 10),
                             textcoords='offset pixels',
                             horizontalalignment='center')

    def update_axis_labels(self):
        pg = self.property_grid_1
        self.ax.set_title(pg.GetPropertyValue('Title'), fontsize=15, fontweight="bold")
        self.ax.set_xlabel(pg.GetPropertyValue('X Label'), fontsize=8)
        self.ax.set_ylabel(pg.GetPropertyValue('Y Label'), fontsize=8)
        self.ax.grid(pg.GetPropertyValue('Grid'))
        self.plot[0].set_color(tuple(x/255 for x in pg.GetPropertyValue('Line Colour')))


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


class VisaClient:
    def __init__(self, id):
        try:
            self.rm = visa.ResourceManager()
            self.instr_info = id
            self.mode = self.instr_info['mode']
            self.timeout = 60000  # 1 (60e3) minute timeout
        except ValueError:
            from textwrap import dedent
            msg = ("\n[ValueError] - Could not locate a VISA implementation. Install either the NI binary or pyvisa-py."
                   "\n\n    PyVISA includes a backend that wraps the National Instruments' VISA library by default.\n"
                   "    PyVISA-py is another such library and can be used for Serial/USB/GPIB/Ethernet\n"
                   "    See NI-VISA Installation:\n"
                   "        > https://pyvisa.readthedocs.io/en/1.8/getting_nivisa.html#getting-nivisa\n")
            print(msg)
        for attempt in range(5):
            try:
                # TODO - verify this works as intended... Otherwise leave INSTR lines commented
                # if mode is SOCKET:
                if self.mode == 'SOCKET':
                    # SOCKET is a non-protocol raw TCP connection
                    address = self.instr_info['ip_address']
                    port = self.instr_info['port']
                    self.INSTR = self.rm.open_resource(f'TCPIP0::{address}::{port}::SOCKET', read_termination='\n')

                # if mode is GPIB:
                elif self.mode == 'GPIB':
                    address = self.instr_info['gpib_address']
                    self.INSTR = self.rm.open_resource(f'GPIB0::{address}::0::INSTR')

                # if mode is INSTR:
                elif self.mode == 'INSTR':
                    # INSTR is a VXI-11 protocol
                    address = self.instr_info['ip_address']
                    self.INSTR = self.rm.open_resource(f'TCPIP0::{address}::inst0::INSTR', read_termination='\n')

                # if mode is SERIAL:
                elif self.mode == 'SERIAL':
                    address = self.instr_info['ip_address']
                    self.INSTR = self.rm.open_resource(f'{address}')
                    self.INSTR.read_termination = '\n'

                # TODO - http://lampx.tugraz.at/~hadley/num/ch9/python/9.2.php
                # if mode is SERIAL:
                elif self.mode == 'USB':
                    address = self.instr_info['ip_address']
                    self.INSTR = self.rm.open_resource(f'{address}', read_termination='\n')

                # if mode is NIGHTHAWK:
                elif self.mode == 'NIGHTHAWK':
                    address = self.instr_info['ip_address']
                    port = self.instr_info['port']
                    self.INSTR = self.rm.open_resource(f'TCPIP::{address}::{port}::SOCKET', read_termination='>')
                    self.read()
                else:
                    print('Failed to connect.')

                self.INSTR.write('BEEP')
                print(self.INSTR.query('*IDN?'))

                self.INSTR.timeout = self.timeout

            except (visa.VisaIOError, Exception) as e:
                # https://github.com/pyvisa/pyvisa-py/issues/146#issuecomment-453695057
                print(f'[attempt {attempt + 1}/5] - retrying connection to instrument')
            else:
                break
        else:
            print('Invalid session handle. The resource might be closed.')

    def info(self):
        return self.instr_info

    def IDN(self):
        try:
            print(self.INSTR.query('*IDN?'))
        # TODO - does this work now?
        except visa.VisaIOError:
            print('Failed to connect to address.')

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
