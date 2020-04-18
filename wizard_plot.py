import eqn_parser

import wx
import wx.lib.mixins.listctrl

import functools
import operator
import itertools
import string

import matplotlib.tri as mtri
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar
from matplotlib.ticker import LinearLocator, FormatStrFormatter, FuncFormatter
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 unused import

import numpy as np


def increment_column_index():
    n = 1
    while True:
        yield from (''.join(group) for group in itertools.product(string.ascii_uppercase, repeat=n))
        n += 1


class PlotFrame(wx.Frame):
    """
    Class used for creating frames other than the main one

    Matplotlib
    Object-Oriented API vs Pyplot
        Matplotlib has two interfaces.
            [1] The first is an object-oriented (OO) interface. In this case, we utilize an nstance of axes.Axes in
                order to render visualizations on an instance of figure.Figure.

            [2] The second is based on MATLAB and uses a state-based interface. This is encapsulated in the pyplot
                module.
    """

    def __init__(self, title='Matplotlib Output', id=-1, dpi=100, parent=None, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER
        wx.Frame.__init__(self, parent=parent, title=title, **kwds)

        self.SetSize((843, 554))
        self.panel_2 = wx.Panel(self, wx.ID_ANY)

        # self.figure = mpl.figure.Figure(dpi=dpi, figsize=(2, 2))  # look into Figure((5, 4), 75)
        self.figure = plt.figure(figsize=(2, 2))  # look into Figure((5, 4), 75)
        self.canvas = FigureCanvas(self.panel_2, -1, self.figure)
        self.toolbar = NavigationToolbar(self.canvas)
        self.toolbar.Realize()

        self.choices = []
        self.button_9 = wx.Button(self.panel_2, wx.ID_ANY, "Edit Data")
        self.radio_box_1 = wx.RadioBox(self.panel_2, wx.ID_ANY, "",
                                       choices=["2D", "3D"],
                                       majorDimension=1,
                                       style=wx.RA_SPECIFY_ROWS)

        self.choice_dropdown = [wx.Choice(), CheckListCtrl, wx.Choice()]
        self.choice_dropdown[0] = wx.Choice(self.panel_2, wx.ID_ANY, choices=self.choices)
        self.choice_dropdown[1] = CheckListCtrl(self.panel_2, prefHeight=None, readOnly=True)  # style=wx.TE_READONLY
        self.choice_dropdown[2] = wx.Choice(self.panel_2, wx.ID_ANY, choices=self.choices)

        self.text_ctrl_17 = wx.TextCtrl(self.panel_2, wx.ID_ANY, "", style=wx.TE_PROCESS_ENTER)
        self.text_ctrl_axis_labels = [wx.TextCtrl()] * 4
        for idx in range(4):
            self.text_ctrl_axis_labels[idx] = wx.TextCtrl(self.panel_2, wx.ID_ANY, "", style=wx.TE_PROCESS_ENTER)

        # # Menu Bare
        # self.frame_1_menubar = wx.MenuBar()
        # self.SetMenuBar(self.frame_1_menubar)
        # # Menu Bar end

        self.x = np.array(0.)
        self.y = np.array(0.)
        self.z = np.array(0.)
        self.ax = None

        # Event Triggers -----------------------------------------------------------------------------------------------
        onPlotMode_event = lambda event: self.onPlotMode(event)
        self.Bind(wx.EVT_RADIOBOX, onPlotMode_event, self.radio_box_1)

        update_xAxisData_event = lambda event: self.update_xAxisData(event)
        self.Bind(wx.EVT_CHOICE, update_xAxisData_event, self.choice_dropdown[0])

        update_yAxisData_event = lambda event: self.update_yAxisData(event)
        self.Bind(wx.EVT_CHECKBOX, update_yAxisData_event, self.choice_dropdown[1])

        update_zAxisData_event = lambda event: self.update_zAxisData(event)
        self.Bind(wx.EVT_CHOICE, update_zAxisData_event, self.choice_dropdown[2])

        # Update plot title
        onUpdateTitle_event = lambda event: self.onUpdateTitle(event)
        self.Bind(wx.EVT_TEXT_ENTER, onUpdateTitle_event, self.text_ctrl_axis_labels[0])

        # Update plot title
        onUpdateXLabel_event = lambda event: self.onUpdateXLabel(event)
        self.Bind(wx.EVT_TEXT_ENTER, onUpdateXLabel_event, self.text_ctrl_axis_labels[1])

        # Update plot title
        onUpdateYLabel_event = lambda event: self.onUpdateYLabel(event)
        self.Bind(wx.EVT_TEXT_ENTER, onUpdateYLabel_event, self.text_ctrl_axis_labels[2])

        # Update plot title
        onUpdateZLabel_event = lambda event: self.onUpdateZLabel(event)
        self.Bind(wx.EVT_TEXT_ENTER, onUpdateZLabel_event, self.text_ctrl_axis_labels[3])

        # Update plot title
        onParseYexpression_event = lambda event: self.onParseY_expression(event)
        self.Bind(wx.EVT_TEXT_ENTER, onParseYexpression_event, self.text_ctrl_17)

        self.__set_properties()
        self.__do_layout()
        self.Show()
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: MyFrame1.__set_properties
        self.SetTitle("Plot Data")
        self.SetFocus()

        for idx in range(3):
            self.choice_dropdown[idx].SetMinSize((80, 23))

        for idx in range(4):
            self.text_ctrl_axis_labels[idx].SetMinSize((200, 23))

        self.radio_box_1.SetSelection(0)
        self.choice_dropdown[0].SetSelection(0)
        self.choice_dropdown[1].ClearSelections()
        self.choice_dropdown[2].SetSelection(0)

        self.choice_dropdown[2].Enable(False)
        self.text_ctrl_axis_labels[3].Enable(False)
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: MyFrame1.__do_layout
        sizer_3 = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_2 = wx.GridBagSizer(0, 0)

        grid_sizer_2.Add(self.canvas, (2, 6), (13, 1), wx.ALL | wx.EXPAND, 10)
        grid_sizer_2.Add(self.toolbar, (15, 6), (1, 1), wx.ALL | wx.EXPAND, 10)
        # update the axes menu on the toolbar
        # self.toolbar.update()

        label_16 = wx.StaticText(self.panel_2, wx.ID_ANY, "Configure Plot")
        label_16.SetFont(wx.Font(20, wx.FONTFAMILY_DECORATIVE, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_BOLD, 0, ""))
        grid_sizer_2.Add(label_16, (0, 0), (1, 4), wx.ALIGN_CENTER_VERTICAL | wx.ALL, 10)
        bitmap_1 = wx.StaticBitmap(self.panel_2, wx.ID_ANY, wx.Bitmap("images/Fluke Logo.png", wx.BITMAP_TYPE_ANY))
        grid_sizer_2.Add(bitmap_1, (0, 6), (1, 1), wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.ALL, 10)
        static_line_2 = wx.StaticLine(self.panel_2, wx.ID_ANY)
        static_line_2.SetMinSize((800, 2))
        grid_sizer_2.Add(static_line_2, (1, 0), (1, 7), wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 10)
        label_17 = wx.StaticText(self.panel_2, wx.ID_ANY, "Data")
        label_17.SetFont(wx.Font(12, wx.FONTFAMILY_DECORATIVE, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_BOLD, 0, ""))
        grid_sizer_2.Add(label_17, (2, 0), (1, 2), wx.LEFT | wx.RIGHT, 10)
        grid_sizer_2.Add(self.button_9, (3, 1), (1, 2), wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_2.Add(self.radio_box_1, (3, 3), (1, 1), wx.ALL, 10)
        label_19 = wx.StaticText(self.panel_2, wx.ID_ANY, "X:")
        grid_sizer_2.Add(label_19, (4, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL | wx.ALL, 10)
        grid_sizer_2.Add(self.choice_dropdown[0], (4, 1), (1, 2), wx.ALIGN_CENTER_VERTICAL, 0)
        label_20 = wx.StaticText(self.panel_2, wx.ID_ANY, "Y:")
        grid_sizer_2.Add(label_20, (5, 0), (1, 1), wx.ALL, 10)
        grid_sizer_2.Add(self.choice_dropdown[1], (5, 1), (1, 2), wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_2.Add(self.text_ctrl_17, (5, 3), (1, 2), wx.ALIGN_CENTER_VERTICAL, 0)
        label_21 = wx.StaticText(self.panel_2, wx.ID_ANY, "Z:")
        grid_sizer_2.Add(label_21, (6, 0), (1, 1), wx.ALL, 10)
        grid_sizer_2.Add(self.choice_dropdown[2], (6, 1), (1, 2), wx.ALIGN_CENTER_VERTICAL, 0)
        static_line_3 = wx.StaticLine(self.panel_2, wx.ID_ANY)
        static_line_3.SetMinSize((250, 2))
        grid_sizer_2.Add(static_line_3, (7, 0), (1, 6), wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT | wx.TOP, 10)
        label_18 = wx.StaticText(self.panel_2, wx.ID_ANY, "Properties")
        label_18.SetFont(wx.Font(12, wx.FONTFAMILY_DECORATIVE, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_BOLD, 0, ""))
        grid_sizer_2.Add(label_18, (8, 0), (1, 3), wx.LEFT | wx.RIGHT, 10)
        label_22 = wx.StaticText(self.panel_2, wx.ID_ANY, "Title:")
        grid_sizer_2.Add(label_22, (9, 0), (1, 2), wx.ALIGN_CENTER_VERTICAL | wx.ALL, 10)
        grid_sizer_2.Add(self.text_ctrl_axis_labels[0], (9, 2), (1, 3), wx.ALIGN_CENTER_VERTICAL, 0)
        label_23 = wx.StaticText(self.panel_2, wx.ID_ANY, "X Label:")
        grid_sizer_2.Add(label_23, (10, 0), (1, 2), wx.ALIGN_CENTER_VERTICAL | wx.ALL, 10)
        grid_sizer_2.Add(self.text_ctrl_axis_labels[1], (10, 2), (1, 3), wx.ALIGN_CENTER_VERTICAL, 0)
        label_24 = wx.StaticText(self.panel_2, wx.ID_ANY, "Y Label:")
        grid_sizer_2.Add(label_24, (11, 0), (1, 2), wx.ALIGN_CENTER_VERTICAL | wx.ALL, 10)
        grid_sizer_2.Add(self.text_ctrl_axis_labels[2], (11, 2), (1, 3), wx.ALIGN_CENTER_VERTICAL, 0)
        label_25 = wx.StaticText(self.panel_2, wx.ID_ANY, "Z Label:")
        grid_sizer_2.Add(label_25, (12, 0), (1, 2), wx.ALIGN_CENTER_VERTICAL | wx.ALL, 10)
        grid_sizer_2.Add(self.text_ctrl_axis_labels[3], (12, 2), (1, 3), wx.ALIGN_CENTER_VERTICAL, 0)
        self.panel_2.SetSizer(grid_sizer_2)
        sizer_3.Add(self.panel_2, 1, wx.EXPAND, 0)

        self.SetSizer(sizer_3)
        self.Layout()
        self.Centre()
        # end wxGlade

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

    def Draw_3DPlot(self):
        """
        Use surf to plot modelised data, and you use trisurf to plot experimental data. (because your
        experimental data are not necessarily distributed on a nice regular grids). In general you use surf to plot
        modelised data, and you use trisurfto plot experimental data. (because your experimental data are not
        necessarily distributed on a nice regular grids)

        surf takes as input rectilinear grids and plots surfaces as rectilinear facets, while trisurf takes as input
        triangular representations and plots surfaces as triangular facets.

        first line determines if axes object is a 3D projection and if so, skip re-declaration:
            >   if not hasattr(self.ax, 'get_zlim'): do_something()
        https://stackoverflow.com/a/39334099

        Useful info on animated (or updating) 3D surfaces: https://stackoverflow.com/a/45713451
        There is a lot going on under the surface when calling plot_surface. You would need to replicate all of it when
        trying to set new data to the Poly3DCollection
        """
        self.ax = self.figure.add_subplot(111, projection='3d')

        triang = mtri.Triangulation(self.x, self.y[0])
        self.plot = self.ax.plot_trisurf(triang, self.z, cmap=cm.CMRmap)  # cmap=cm.viridis
        self.ax.zaxis.set_major_locator(LinearLocator(10))
        self.ax.zaxis.set_major_formatter(FormatStrFormatter('%.2f'))
        self.ax.set_zlim(round(min(self.z), 2), round(max(self.z), 2))
        self.ax.view_init(elev=15, azim=220)
        self.ax.view_init(elev=15, azim=220)

        # self.figure.colorbar(self.plot, orientation='horizontal', pad=-0.05, shrink=0.5, aspect=20)  # TODO

        self.UpdateAxisLabels()
        self.figure.tight_layout()
        self.toolbar.update()  # Not sure why this is needed - ADS

    def update_xAxisData(self, event):
        """
        There are two options for updating a plot in matplotlib:
            [1] Call self.ax.clear() and graph2.clear() before replotting the data. This is the slowest, but most
                simplest and most robust option.
                    >   The sequence for each new frame should be clear, plot, draw

            [2] Instead of replotting every new update, update the data of the plot objects, which is a much faster
                approach. However, two things must be noted:
                    >   The shape of the data cannot change
                    >   If the range of the data is changing, x and y axis limits must manually be reset. Use:
                            self.ax.relim()
                            self.ax.autoscale_view()
        In addition, ensure self.canvas.draw() is called after plotting each update to the frame
        Source: https://stackoverflow.com/a/4098938

        :param event: event waits for change in choice dropdown
        """
        column = self.choice_dropdown[0].GetSelection()
        self.x = self.data[:, column]
        if self.radio_box_1.GetStringSelection() == '2D':
            self.plot[0].set_xdata(self.x)

            self.UpdateAxisLabels()
            self.ax.relim()
            self.ax.autoscale_view()
        else:
            self.figure.delaxes(self.ax)
            self.Draw_3DPlot()

        self.canvas.draw()
        self.canvas.flush_events()

    def update_yAxisData(self, event):
        selections = self.choice_dropdown[1].GetSelection()
        self.y = [0.] * len(selections)
        for i, column in enumerate(selections):
            self.y[i] = self.data[:, column]
        if self.radio_box_1.GetStringSelection() == '2D':
            self.ax.clear()
            for i, y in enumerate(self.y):
                self.plot = self.ax.plot(self.x, y)

            self.UpdateAxisLabels()
            self.ax.relim()
            self.ax.autoscale_view()
        else:
            self.figure.delaxes(self.ax)
            self.Draw_3DPlot()

        self.canvas.draw()
        self.canvas.flush_events()

    def update_zAxisData(self, event):
        """
        Useful info on animated (or updating) 3D surfaces: https://stackoverflow.com/a/45713451
        There is a lot going on under the surface when calling plot_surface. You would need to replicate all of it when
        trying to set new data to the Poly3DCollection.
        """
        column = self.choice_dropdown[2].GetSelection()
        self.z = self.data[:, column]
        if self.radio_box_1.GetStringSelection() == '3D':
            self.figure.delaxes(self.ax)
            self.Draw_3DPlot()
        else:
            self.plot.set_3d_properties(self.z)

        self.canvas.draw()
        self.canvas.flush_events()

    def UpdateAxisLabels(self):
        """
        [Text Hints]:
            There are two approaches to including text hints inside text control objects.
                [1] Use the method SetHint found in the wx.TextEntry class. This class is not derive from wx.Window and
                    so is not a control itself, however, it is used as a base class by other controls,
                    notably wx.TextCtrl and Wx.ComboBox and gathers the methods common to both of them.
                [2] Write "hint" as actual content inside the textCtrl control object (with grey color). When the user
                    clicks into the control (control gets focus), check if the control still contains the placeholder
                    text.
                    If true, you clear the text. If the focus leaves the control, check if it is empty. And if True,
                    put the placeholder text back in.

            Source: https://forums.wxwidgets.org/viewtopic.php?t=39368
        """
        label = [''] * 4
        hint = [''] * 4
        selectedMode = self.radio_box_1.GetStringSelection()

        for idx in range(4):
            label_text = self.text_ctrl_axis_labels[idx].GetValue()
            if idx == 0:
                if label_text == '':
                    self.text_ctrl_axis_labels[idx].SetHint(f'{selectedMode} Plot Title')
                    label[0] = f'{selectedMode} Plot Title'
                else:
                    label[0] = self.text_ctrl_axis_labels[0].GetValue()
            else:
                if label_text == '':
                    label[idx] = self.choice_dropdown[idx - 1].GetStringSelection()
                else:
                    label[idx] = self.text_ctrl_axis_labels[idx].GetValue()
                self.text_ctrl_axis_labels[idx].SetHint(self.choice_dropdown[idx - 1].GetStringSelection())

        if selectedMode == '2D':
            self.ax.set_title(label[0], fontsize=15, fontweight="bold")
            self.ax.set_xlabel(label[1], fontsize=8)
            self.ax.set_ylabel(label[2], fontsize=8)

        elif selectedMode == '3D':
            self.ax.set_title(label[0], fontsize=15, fontweight="bold")
            self.ax.set_xlabel(label[1], fontsize=8)
            self.ax.set_ylabel(label[2], fontsize=8)
            self.ax.set_zlabel(label[3], fontsize=8)

    def onUpdateTitle(self, event):
        """
        TODO - This is a terrible fix for something that should be so simple. Updating title otherwise incrementally
               changes title position offset
               > Requires removal of the previous plot and then to be redrawn. Silly!
        """

        selectedMode = self.radio_box_1.GetStringSelection()
        if selectedMode == '2D':
            self.ax.set_title(self.text_ctrl_axis_labels[0].GetValue(), fontsize=15, fontweight="bold")
        elif selectedMode == '3D':
            self.figure.delaxes(self.ax)
            self.Draw_3DPlot()

        # make the canvas draw its contents again with the new data
        self.canvas.draw()

    def onUpdateXLabel(self, event):
        self.ax.set_xlabel(self.text_ctrl_axis_labels[1].GetValue())
        # make the canvas draw its contents again with the new data
        self.canvas.draw()

    def onUpdateYLabel(self, event):
        self.ax.set_ylabel(self.text_ctrl_axis_labels[2].GetValue())
        # make the canvas draw its contents again with the new data
        self.canvas.draw()

    def onUpdateZLabel(self, event):
        self.ax.set_zlabel(self.text_ctrl_axis_labels[3].GetValue())
        # make the canvas draw its contents again with the new data
        self.canvas.draw()

    def onPlotMode(self, event):
        selectedMode = self.radio_box_1.GetStringSelection()
        if selectedMode == '3D':
            if self.number_of_columns >= 3:
                self.choice_dropdown[1].Spotlight_on()  # forces only one box be checked. All others are red
                self.choice_dropdown[1].ClearSelections()
                self.choice_dropdown[1].SetSelection(1)
                self.choice_dropdown[2].Enable(True)
                self.text_ctrl_axis_labels[3].Enable(True)

                self.z = self.data[:, 2]
                self.choice_dropdown[2].SetSelection(2)
                self.figure.delaxes(self.ax)
                self.Draw_3DPlot()
                self.canvas.draw()
            else:
                print('Insufficient columns of data for 3D plot!\nReverting mode back to 2D')
                self.radio_box_1.SetSelection(0)
        else:
            self.choice_dropdown[1].Spotlight_off()
            self.choice_dropdown[1].ClearSelections()
            self.choice_dropdown[1].SetSelection(1)
            self.choice_dropdown[2].Enable(False)
            self.text_ctrl_axis_labels[3].Enable(False)

            self.figure.delaxes(self.ax)
            self.Draw_2DPlot()
            self.canvas.draw()

    def onParseY_expression(self, event):
        """
        Equation parsing in Python ---> https://stackoverflow.com/a/5936822
            It will still happily execute all code, not just formulas. Including bad things like os.system calls.
            eval(parser.expr("os.system('echo evil syscall')").compile()) evil syscall

        temporary variables (x, y, newY) are necessary to avoid the reference explosion: self.y[idx] = self.x

        With new_list = my_list, you don't actually have two lists. The assignment just copies the reference to the
        list, not the actual list, so both new_list and my_list refer to the same list after the assignment.

        How to clone or copy a list? ---> https://stackoverflow.com/a/2612815

        :param event:
        :return:
        """
        input_string = self.text_ctrl_17.GetValue()

        nsp = eqn_parser.NumericStringParser()
        nsp.expr(input_string)
        newY = [0.] * len(self.y)
        for idx in range(len(self.y)):
            newY[idx] = nsp.eval(variables={'x': self.x, 'y': self.y[idx]})

        # code = parser.expr(input_string).compile()
        # newY = [0.] * len(self.y)
        # for idx in range(len(self.y)):
        # x = self.x
        # y = self.y[idx]
        # newY[idx] = eval(code)

        if self.radio_box_1.GetStringSelection() == '2D':
            self.ax.clear()
            for i, y in enumerate(newY):
                self.plot = self.ax.plot(self.x, y)
            self.UpdateAxisLabels()  # TODO - silly this has to be broken up. See note in method onUpdateTitle
        else:
            # self.update_3dAxisData()
            self.figure.delaxes(self.ax)
            self.ax = self.figure.add_subplot(111, projection='3d')

            triang = mtri.Triangulation(self.x, newY[0])
            self.plot = self.ax.plot_trisurf(triang, self.z, cmap=cm.CMRmap)  # cmap=cm.viridis
            self.ax.zaxis.set_major_locator(LinearLocator(10))
            self.ax.zaxis.set_major_formatter(FormatStrFormatter('%.2f'))
            self.ax.set_zlim(round(min(self.z), 2), round(max(self.z), 2))
            self.ax.view_init(elev=15, azim=220)
            self.ax.view_init(elev=15, azim=220)

            # self.figure.colorbar(self.plot, orientation='horizontal', pad=-0.05, shrink=0.5, aspect=20)  # TODO

            self.UpdateAxisLabels()
            self.figure.tight_layout()
            self.toolbar.update()  # Not sure why this is needed - ADS

        # self.UpdateAxisLabels()
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas.draw()
        self.canvas.flush_events()


class CheckListCtrl(wx.ComboCtrl):
    """
    A wxListCtrl-like widget where each item in the drop-down list has a check box.
        Modified code from:
        >   https://stackoverflow.com/a/53873874
        >   https://github.com/JoshMayberry/Utilities/blob/master/MyUtilities/wxPython.py (Thanks JoshuaMayberry!)
        >   https://github.com/wxWidgets/Phoenix/blob/master/demo/ComboCtrl.py
    """

    def __init__(self, parent, myId=None, initial=None, position=None, size=None, readOnly=False, **kwargs):
        """
        parent (wxWindow) – Parent window (must not be None)
        initial (str) – Initial selection string
        readOnly (bool) - Determiens if the user can modify values in this widget

        Example Input: CheckListCtrl(self)
        """

        self.parent = parent

        # Configure settings
        style = []

        if readOnly:
            style.append(wx.CB_READONLY)

        # Create object
        super().__init__(parent,
                         id=myId or wx.ID_ANY,
                         value=initial or "",
                         pos=position or wx.DefaultPosition,
                         size=size or wx.DefaultSize,
                         style=functools.reduce(operator.ior, style or (0,)))

        self.popup = self.MyPopup(self, **kwargs)
        self.Bind(wx.EVT_COMBOBOX_CLOSEUP, self._GetStringSelection)

    def SetSelection(self, *args, **kwargs):
        self.popup.SetSelection(*args, **kwargs)
        self.GetStringSelection()

    def GetSelection(self):
        return self.popup.GetSelection()

    def _GetStringSelection(self, event):
        # override method
        self.GetStringSelection()

    def GetStringSelection(self):
        text = ', '.join(self.popup.checkList.GetStringSelection())
        self.SetText(text)
        self.SetToolTip(wx.ToolTip(text))  # https://stackoverflow.com/a/48779658
        return text

    def ClearSelections(self, *args, **kwargs):
        self.popup.ClearSelections(*args, **kwargs)

    def Append(self, *args, **kwargs):
        self.popup.Append(*args, **kwargs)

    def SetItems(self, *args, **kwargs):
        self.popup.SetItems(*args, **kwargs)

    def Spotlight_on(self):
        print('Spotlight select: ON')
        self.popup.checkList.spotlightSelect = True

    def Spotlight_off(self):
        print('Spotlight select: OFF')
        self.popup.checkList.spotlightSelect = False

        count = self.popup.checkList.GetItemCount()
        # This function only works in report view.
        for idx in range(count):
            # This function only works in report view.
            self.popup.checkList.SetItemTextColour(idx, wx.BLACK)

    class MyPopup(wx.ComboPopup):
        """The popup control used by CheckListCtrl."""

        def __init__(self, parent, *, popupId=None,
                     multiple=True, prefHeight=None, image_check=None, image_uncheck=None, lazyLoad=False):
            """
            multiple (bool) - Determines if the user can check multiple boxes or not
            lazyLoad (bool) - Determines if when Create() is called
                - If True: Waits for the first time the popup is called
                - If False: Calls it during the build process

            prefHeight (int) - What height you would prefer the popup box use
                - If None: Will calculate what hight to use based on it's contents
                - If -1: Will use the default height
            """

            self.parent = parent
            self.prefHeight = prefHeight

            self._buildVar_myId = popupId
            self._buildVar_multiple = multiple
            self._buildVar_lazyLoad = lazyLoad
            self._buildVar_image_check = image_check
            self._buildVar_image_uncheck = image_uncheck

            super().__init__()

            parent.SetPopupControl(self)

        def Create(self, parent):
            self.checkList = self.MyListCtrl(self, parent,
                                             myId=self._buildVar_myId,
                                             multiple=self._buildVar_multiple,
                                             image_check=self._buildVar_image_check,
                                             image_uncheck=self._buildVar_image_uncheck)

            return True

        def SetSelection(self, *args, **kwargs):
            self.checkList.SetSelection(*args, **kwargs)

        def GetSelection(self):
            return self.checkList.GetSelection()

        def ClearSelections(self, *args, **kwargs):
            self.checkList.ClearSelections()

        def Append(self, *args, **kwargs):
            self.checkList.Append(*args, **kwargs)

        def SetItems(self, *args, **kwargs):
            self.checkList.SetItems(*args, **kwargs)

        def GetControl(self):
            return self.checkList

        def GetAdjustedSize(self, minWidth, prefHeight, maxHeight):
            if self.prefHeight == -1:
                return super().GetAdjustedSize(minWidth, prefHeight, maxHeight)

            elif self.prefHeight is not None:
                return (minWidth, min(self.prefHeight, maxHeight))

            return self.checkList.GetBestSize(minWidth, prefHeight, maxHeight)

        def LazyCreate(self):
            return self._buildVar_lazyLoad

        class MyListCtrl(wx.ListCtrl, wx.lib.mixins.listctrl.CheckListCtrlMixin):
            """Modified code from: https://github.com/wxWidgets/wxPython/blob/master/demo/CheckListCtrlMixin.py"""

            def __init__(self, parent, root, *, myId=None, multiple=False, image_check=None, image_uncheck=None):
                """
                multiple (bool) - Determines if the user can check multiple boxes or not
                """

                self.parent = parent
                self.suppressTriggerEvent = False
                self.spotlightSelect = False

                """
                wx.LC_LIST: Multicolumn list view, with optional small icons. Columns are computed automatically, 
                i.e. you don’t set columns as in LC_REPORT. In other words, the list wraps, unlike a wx.ListBox.
                """
                # Configure settings
                # style = [wx.LC_LIST, wx.SIMPLE_BORDER]
                style = [wx.LC_REPORT, wx.LC_NO_HEADER, wx.SIMPLE_BORDER]

                if not multiple:
                    style.append(wx.LC_SINGLE_SEL)

                # Create object
                wx.ListCtrl.__init__(self,
                                     root, id=myId or wx.ID_ANY,
                                     style=functools.reduce(operator.ior, style or (0,)))

                self.InsertColumn(0, '')

                """
                The checkboxes are really just ImageList pictures, and the underlying code decides when to change the
                image from an empty box to one with a checkmark in it... and does not support the idea of disabling
                certain ones (so that they cannot be checked or unchecked).

                https://www.experts-exchange.com/questions/21851123/How-to-disable-checkboxes-in-CListCtrl.html
                https://groups.google.com/d/embed/msg/microsoft.public.vc.mfc/e9cbkSsiImA/1w5mi7w-Fp8J
                """
                wx.lib.mixins.listctrl.CheckListCtrlMixin.__init__(self,
                                                                   check_image=image_check,
                                                                   uncheck_image=image_uncheck)

            def ClearSelections(self):
                count = self.GetItemCount()
                for n in range(count):
                    self.suppressTriggerEvent = True
                    self.CheckItem(n, False)

            def SpotlightClear(self, n):
                print(f'\nclear! spotlight: {n}\n')
                count = self.GetItemCount()
                for idx in range(count):
                    if idx != n:
                        self.suppressTriggerEvent = True
                        self.CheckItem(idx, False)
                        # This function only works in report view.
                        self.SetItemTextColour(idx, wx.RED)
                    else:
                        self.SetItemTextColour(n, wx.BLACK)

            def GetSelection(self):
                count = self.GetItemCount()
                checkedItems = [n for n in range(count) if self.IsChecked(n)]
                return checkedItems

            def GetStringSelection(self):
                count = self.GetItemCount()
                checkedStringItems = [self.GetItem(n).GetText() for i, n in enumerate(self.GetSelection())]
                return checkedStringItems

            def SetSelection(self, n):
                self.suppressTriggerEvent = True
                self.CheckItem(n)
                if self.spotlightSelect:
                    self.SpotlightClear(n)
                self.suppressTriggerEvent = False

            def Append(self, value, default=False):
                """Appends the given item to the list.

                value (str) - What the item will say
                default (bool) - What state the check box will start out at

                Example Input: Append("lorem")
                Example Input: Append("lorem", default = True)
                """

                n = self.GetItemCount()
                self.InsertItem(n, value)

                if (default):
                    self.suppressTriggerEvent = True
                    self.CheckItem(n)

            def SetItems(self, data_list):
                if isinstance(data_list, (list, np.ndarray)):
                    n = self.GetItemCount()
                    for i, item in enumerate(data_list, n):
                        self.InsertItem(i, item)
                else:
                    pass

            def GetBestSize(self, minWidth, prefHeight, maxHeight):
                return (minWidth, min(prefHeight, maxHeight,
                                      sum(self.GetItemRect(i)[3] for i in range(self.GetItemCount())) +
                                      self.GetItemRect(0)[3]))

            # this is called by the base class when an item is checked/unchecked
            def OnCheckItem(self, index, state):
                # TODO:
                """
                At time of development (3/2020), wxPython (Phoenix) 4.0.7.post2 was current release.
                However, EVT_LIST_ITEM_CHECKED and EVT_LIST_ITEM_UNCHECKED had not been exposed in ListCtrl (#1520)
                https://github.com/wxWidgets/Phoenix/pull/1520/commits/d92bf5c23347c21d0615fa8869360f5d16822ad8

                Subsequently, the simplest implementation of a trigger event after the user checks or unchecks a list item from
                the dropdown cannot be used. Instead EVT_CHECKBOX is triggered once OnCheckItem is called by the base class.

                If you want to post a EVT_CHECKBOX event. Making it a PyCommandEvent means that it will propagate
                upwards; other event types don't propagate by default
                https://stackoverflow.com/a/841045
                """
                # suppresses trigger event if event was not created by user. Waits for 'False'
                if not self.suppressTriggerEvent:
                    # one hot selection only
                    if self.spotlightSelect:
                        self.SpotlightClear(n=index)
                    else:
                        pass
                    event = wx.PyCommandEvent(eventType=wx.EVT_CHECKBOX.typeId, id=self.parent.parent.GetId())
                    wx.PostEvent(self.GetEventHandler(), event)

                self.suppressTriggerEvent = False

                print(index, state)  # Not needed. Just displaying contents of toggled checkbox item event


class MyApp(wx.App):
    def OnInit(self):
        plot_frame = PlotFrame(title='Plot Wizard', parent=None)
        data = [[1, 0.909297427, 0.82682181, 159.3543639],
                [2, -0.756802495, 0.572750017, 173.4090272],
                [3, -0.279415498, 0.078073021, 283.7879812],
                [4, 0.989358247, 0.97882974, 153.6788816],
                [5, -0.544021111, 0.295958969, 203.6311333],
                [6, -0.536572918, 0.287910496, 205.0236537],
                [7, 0.990607356, 0.981302933, 153.5983163]]
        plot_frame.get_data(data)
        plot_frame.Show()

        return True


if __name__ == '__main__':
    app = MyApp(0)
    app.MainLoop()
