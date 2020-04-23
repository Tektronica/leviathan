import pyunivisa

import wx
import wx.lib.masked as masked
import os
import yaml  # used for writing yaml config file (save configuration settings)
import pyvisa


def ReadConfig():
    """
    TODO - if the yaml config file is not found, write template to running directory
    Reads in configuration file (yaml) as the  settings for the current instance of 'Configuration Settings' dialog.

    :return: function yaml.safe_load converts a YAML document to a Python list of dictionaries.
    """
    if os.path.exists("instrument_config.yaml"):
        with open("instrument_config.yaml", 'r') as stream:
            try:
                return yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)
    else:
        pass


class MyDialog(wx.Dialog):
    def __init__(self, *args, **kwds):
        """
        TODO: use masked.IpAddrCtrl(parent) ? Requires 'import wx.lib.masked as masked'
        https://github.com/wxWidgets/Phoenix/issues/639
        Requies this snippet be added to the top of the code to work on other platforms.

        _oldinit = masked.IpAddrCtrl.__init__
        def patched_init(self, *args, **kwargs):
            _oldinit(self, *args, **kwargs)
            self.Unbind(wx.EVT_CHAR)
            self.Bind(wx.EVT_CHAR_HOOK, self._OnChar)
        masked.IpAddrCtrl.__init__ = patched_init
        """
        # begin wxGlade: MyDialog.__init__
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_DIALOG_STYLE
        wx.Dialog.__init__(self, *args, **kwds)
        self.SetSize((636, 378))
        self.panel_1 = wx.Panel(self, wx.ID_ANY)
        self.panel_2 = wx.ScrolledWindow(self.panel_1, wx.ID_ANY, style=wx.TAB_TRAVERSAL)

        self.config = {}
        self.choices = ["SOCKET", "GPIB", "INSTR", "SERIAL", "USB", "NIGHTHAWK"]
        # Scrolling Panel ----------------------------------------------------------------------------------------------
        self.instrID_text = [wx.TextCtrl()] * 4
        self.ipAddress_text = [wx.TextCtrl()] * 4
        self.port_text = [wx.TextCtrl()] * 4
        self.static_line = [wx.StaticLine()] * 4
        self.gpib_text = [wx.TextCtrl()] * 4
        self.mode_choice = [wx.Choice()] * 4
        for row in range(4):
            self.instrID_text[row] = wx.TextCtrl(self.panel_2, wx.ID_ANY, "")
            self.ipAddress_text[row] = wx.TextCtrl(self.panel_2, -1, style=wx.TE_PROCESS_TAB)
            self.port_text[row] = wx.TextCtrl(self.panel_2, wx.ID_ANY, "")
            self.static_line[row] = wx.StaticLine(self.panel_2, wx.ID_ANY)
            self.gpib_text[row] = wx.TextCtrl(self.panel_2, wx.ID_ANY, "")
            self.mode_choice[row] = wx.Choice(self.panel_2, wx.ID_ANY, choices=self.choices)
        self.bitmap_button_1 = wx.BitmapButton(self.panel_2, wx.ID_ANY, wx.Bitmap("images/btn_add_depressed.png", wx.BITMAP_TYPE_ANY))
        self.bitmap_button_1.SetBitmapPressed(wx.Bitmap("images/btn_add_pressed.png", wx.BITMAP_TYPE_ANY))
        # Buttons ------------------------------------------------------------------------------------------------------
        self.button_10 = wx.Button(self.panel_1, wx.ID_ANY, "Clear")
        self.button_12 = wx.Button(self.panel_1, wx.ID_ANY, "Test")
        self.button_11 = wx.Button(self.panel_1, wx.ID_ANY, "Save")

        self.__set_properties()
        self.__do_layout()
        self.LoadConfig()

        # Configure Instruments ----------------------------------------------------------------------------------------
        # To initialize a list of empty lambda's, lambda only allows an expression. However, that function can be 'None'
        toggle_event = [lambda: None] * 4
        ipchange_event = [lambda: None] * 4
        for row in range(4):
            toggle_event[row] = lambda event, _row=row: self._toggle_text_ctrl(event, _row)
            self.Bind(wx.EVT_CHOICE, toggle_event[row], self.mode_choice[row])

            # ipchange_event[row] = lambda event, _row=row: self.OnIpAddrChange(event, _row)
            # self.Bind(wx.EVT_TEXT, ipchange_event[row], self.mode_choice[row])

        # Event Triggers -----------------------------------------------------------------------------------------------
        # Add new row of controls
        OnAddRow_Event = lambda event: self._AddRow(event)
        self.Bind(wx.EVT_BUTTON, OnAddRow_Event, self.bitmap_button_1)

        # Clear the dialog entries
        self.Bind(wx.EVT_BUTTON, self.OnClear, self.button_10)

        # Test communication
        self.Bind(wx.EVT_BUTTON, self.OnTest, self.button_12)

        # Save configuration and close dialog
        self.Bind(wx.EVT_BUTTON, self.OnSave, self.button_11)

    def __set_properties(self):
        """
        Sets the properties by first checking for any available settings otherwise loads defaults.

        For each of the 4 rows, there are 3 text ctrl objects and 1 drop-down choice object.
        A for-loop of m rows and n columns iterates through each position of the dialog while reducing code clutter
        """
        # begin wxGlade: MyDialog.__set_properties
        self.SetTitle("Configure Instruments")
        self.SetSize((636, 378))
        for row in range(4):
            self.instrID_text[row].SetMinSize((100, 23))
            self.ipAddress_text[row].SetMinSize((111, 23))
            self.port_text[row].SetMinSize((60, 23))
            self.static_line[row].SetMinSize((2, 23))
            self.gpib_text[row].SetMinSize((60, 23))
            self.instrID_text[row].SetFont(
                wx.Font(9, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, ""))
            self.ipAddress_text[row].SetFont(
                wx.Font(9, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, ""))
            self.port_text[row].SetFont(
                wx.Font(9, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, ""))
            self.gpib_text[row].SetFont(
                wx.Font(9, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, ""))
            self.mode_choice[row].SetSelection(0)

            self.toggle_text_ctrl(row)

        self.bitmap_button_1.SetMinSize((23, 23))


        # Loads configuration file into settings
        self.panel_2.SetMinSize((580, 160))
        self.panel_2.SetScrollRate(10, 10)

    def __do_layout(self):
        """
        Sets layout of the wxDialog window
        """
        sizer_4 = wx.BoxSizer(wx.VERTICAL)
        self.grid_sizer_3 = wx.GridBagSizer(0, 0)
        self.grid_sizer_4 = wx.GridBagSizer(0, 0)

        label_6 = wx.StaticText(self.panel_1, wx.ID_ANY, "Configure Instruments")
        label_6.SetFont(wx.Font(20, wx.FONTFAMILY_DECORATIVE, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_BOLD, 0, ""))
        self.grid_sizer_3.Add(label_6, (0, 0), (1, 3), wx.ALIGN_CENTER_VERTICAL, 0)
        bitmap_1 = wx.StaticBitmap(self.panel_1, wx.ID_ANY, wx.Bitmap("images/Fluke Logo.png", wx.BITMAP_TYPE_ANY))
        self.grid_sizer_3.Add(bitmap_1, (0, 3), (1, 4), wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT, 10)
        static_line_4 = wx.StaticLine(self.panel_1, wx.ID_ANY)
        static_line_4.SetMinSize((600, 2))
        self.grid_sizer_3.Add(static_line_4, (1, 0), (1, 7), wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM | wx.TOP, 10)

        # START OF HEADER ----------------------------------------------------------------------------------------------
        label_7 = wx.StaticText(self.panel_1, wx.ID_ANY, "INSTR")
        label_8 = wx.StaticText(self.panel_1, wx.ID_ANY, "IP Address")
        label_9 = wx.StaticText(self.panel_1, wx.ID_ANY, "Port")
        static_line_header = wx.StaticLine(self.panel_1, wx.ID_ANY)
        label_10 = wx.StaticText(self.panel_1, wx.ID_ANY, "GPIB")
        label_11 = wx.StaticText(self.panel_1, wx.ID_ANY, "Mode")

        label_7.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, 0, ""))
        label_8.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, 0, ""))
        label_9.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, 0, ""))
        label_10.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, 0, ""))
        label_11.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, 0, ""))

        label_7.SetMinSize((100, 16))
        label_8.SetMinSize((111, 16))
        label_9.SetMinSize((60, 16))
        static_line_header.SetMinSize((2, 23))
        label_10.SetMinSize((60, 16))
        label_11.SetMinSize((60, 16))

        self.grid_sizer_3.Add(label_7, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 10)
        self.grid_sizer_3.Add(label_8, (2, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.grid_sizer_3.Add(label_9, (2, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.grid_sizer_3.Add(static_line_header, (2, 3), (1, 1), wx.ALIGN_CENTER | wx.BOTTOM | wx.RIGHT, 10)
        self.grid_sizer_3.Add(label_10, (2, 4), (1, 1), wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.grid_sizer_3.Add(label_11, (2, 5), (1, 1), wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)

        # END OF HEADER ------------------------------------------------------------------------------------------------
        # START OF SCROLLING PANEL -------------------------------------------------------------------------------------
        row = 0
        for row in range(4):
            self.grid_sizer_4.Add(self.instrID_text[row], (row, 0), (1, 1),
                                  wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM | wx.RIGHT, 10)
            self.grid_sizer_4.Add(self.ipAddress_text[row], (row, 1), (1, 1),
                                  wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM | wx.RIGHT, 10)
            self.grid_sizer_4.Add(self.port_text[row], (row, 2), (1, 1),
                                  wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM | wx.RIGHT, 10)
            self.grid_sizer_4.Add(self.static_line[row], (row, 3), (1, 1),
                                  wx.ALIGN_CENTER | wx.BOTTOM | wx.RIGHT, 10)
            self.grid_sizer_4.Add(self.gpib_text[row], (row, 4), (1, 1),
                                  wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM | wx.RIGHT, 10)
            self.grid_sizer_4.Add(self.mode_choice[row], (row, 5), (1, 1),
                                  wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM | wx.RIGHT, 10)
        self.grid_sizer_4.Add(self.bitmap_button_1, (row, 6), (1, 1), wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM, 10)
        self.panel_2.SetSizer(self.grid_sizer_4)

        self.grid_sizer_3.Add(self.panel_2, (3, 0), (1, 7), wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        # END OF SCROLLING PANEL ---------------------------------------------------------------------------------------

        static_line_9 = wx.StaticLine(self.panel_1, wx.ID_ANY)
        static_line_9.SetMinSize((600, 2))

        self.grid_sizer_3.Add(static_line_9, (4, 0), (1, 7), wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM | wx.TOP, 10)
        self.grid_sizer_3.Add(self.button_10, (5, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL, 0)
        self.grid_sizer_3.Add(self.button_12, (5, 5), (1, 1), wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.RIGHT, 10)
        self.grid_sizer_3.Add(self.button_11, (5, 6), (1, 1), wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT, 0)

        self.panel_1.SetSizer(self.grid_sizer_3)
        sizer_4.Add(self.panel_1, 1, wx.ALL | wx.EXPAND, 10)
        self.SetSizer(sizer_4)

        self.Layout()
        self.Centre()
        # end wxGlade

    def _toggle_text_ctrl(self, e, row):
        self.toggle_text_ctrl(row)

    def toggle_text_ctrl(self, row):
        """
        Toggles control of text ctrl boxes after combo box choice event. Choice determines which text entries are
        available to user.

        :param row:
        """
        if self.mode_choice[row].GetStringSelection() == 'SOCKET':
            self.instrID_text[row].Enable(True)
            self.ipAddress_text[row].Enable(True)
            self.port_text[row].Enable(True)
            self.gpib_text[row].Enable(False)
        elif self.mode_choice[row].GetStringSelection() == 'GPIB':
            self.instrID_text[row].Enable(True)
            self.ipAddress_text[row].Enable(False)
            self.port_text[row].Enable(False)
            self.gpib_text[row].Enable(True)
        elif self.mode_choice[row].GetStringSelection() == 'INSTR' or 'SERIAL' or 'USB':
            self.instrID_text[row].Enable(True)
            self.ipAddress_text[row].Enable(True)
            self.port_text[row].Enable(False)
            self.gpib_text[row].Enable(False)
        elif self.mode_choice[row].GetStringSelection() == 'NIGHTHAWK':
            self.instrID_text[row].Enable(True)
            self.ipAddress_text[row].Enable(True)
            self.port_text[row].Enable(True)
            self.gpib_text[row].Enable(False)

    def _AddRow(self, e):
        self.AddRow()

    def AddRow(self):
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
        row = self.grid_sizer_4.GetRows()

        # Append new controls to new row
        self.instrID_text.append(wx.TextCtrl(self.panel_2, wx.ID_ANY, ""))
        self.ipAddress_text.append(wx.TextCtrl(self.panel_2, wx.ID_ANY, ""))
        self.port_text.append(wx.TextCtrl(self.panel_2, wx.ID_ANY, ""))
        self.static_line.append(wx.StaticLine(self.panel_2, wx.ID_ANY))
        self.gpib_text.append(wx.TextCtrl(self.panel_2, wx.ID_ANY, ""))
        self.mode_choice.append(wx.Choice(self.panel_2, wx.ID_ANY, choices=self.choices))

        self.instrID_text[-1].SetMinSize((100, 23))
        self.ipAddress_text[-1].SetMinSize((111, 23))
        self.port_text[-1].SetMinSize((60, 23))
        self.static_line[-1].SetMinSize((2, 23))
        self.gpib_text[-1].SetMinSize((60, 23))

        self.instrID_text[-1].SetFont(
            wx.Font(9, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, ""))
        self.ipAddress_text[-1].SetFont(
            wx.Font(9, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, ""))
        self.port_text[-1].SetFont(wx.Font(9, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, ""))
        self.gpib_text[-1].SetFont(wx.Font(9, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, ""))
        self.mode_choice[-1].SetSelection(0)

        self.grid_sizer_4.Add(self.instrID_text[-1], (row, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM | wx.RIGHT,
                              10)
        self.grid_sizer_4.Add(self.ipAddress_text[-1], (row, 1), (1, 1),
                              wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM | wx.RIGHT, 10)
        self.grid_sizer_4.Add(self.port_text[-1], (row, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM | wx.RIGHT, 10)
        self.grid_sizer_4.Add(self.static_line[-1], (row, 3), (1, 1), wx.ALIGN_CENTER | wx.BOTTOM | wx.RIGHT, 10)
        self.grid_sizer_4.Add(self.gpib_text[-1], (row, 4), (1, 1), wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM | wx.RIGHT, 10)
        self.grid_sizer_4.Add(self.mode_choice[-1], (row, 5), (1, 1), wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM | wx.RIGHT,
                              10)

        toggle = lambda event, _row=row-1: self._toggle_text_ctrl(event, _row)
        self.Bind(wx.EVT_CHOICE, toggle, self.mode_choice[-1])

        # Move button to the new row
        self.grid_sizer_4.Detach(self.bitmap_button_1)
        self.grid_sizer_4.Add(self.bitmap_button_1, (row, 6), (1, 1), wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM, 10)

        self.grid_sizer_3.Layout()
        self.panel_2.FitInside()
        self.panel_2.Scroll(-1, self.panel_2.GetClientSize()[1])
        self.toggle_text_ctrl(row-1)

    def OnTest(self, e):
        """
        Collects the current text entries from text ctrl boxes and maps each row into a dictionary and is sent to the
        'Visa' class of the 'Instruments' module to be tested using '*IDN?'.
        Each instrument (row) is tested individually and waits for response.

        :param e: event e waits for button press from 'Test'
        """
        self.OnListResources()
        for row in range(len(self.instrID_text)):
            pyunivisa.Client(self.config[f'INSTR{row}']).info()

    def LoadConfig(self):
        config_dict = ReadConfig()
        # load config file into settings if available
        if isinstance(config_dict, dict):
            self.config = config_dict

            rows = len(self.config)
            if rows > len(self.instrID_text):
                for row in range(rows - len(self.instrID_text)):
                    self.AddRow()

            for row, instr in enumerate(self.config.keys()):
                self.instrID_text[row].SetValue(instr)
                self.ipAddress_text[row].SetValue(self.config[instr]['ip_address'])
                self.port_text[row].SetValue(self.config[instr]['port'])
                self.gpib_text[row].SetValue(self.config[instr]['gpib_address'])
                self.mode_choice[row].SetStringSelection(self.config[instr]['mode'])
                self.toggle_text_ctrl(row)
        else:
            print('no config')

    def OnListResources(self):
        rm = pyvisa.ResourceManager()
        resources = rm.list_resources()
        print(f'items: {len(resources)}')
        print(resources)

    def OnSave(self, e):
        """
        When 'Configuration Settings' dialog is closed using the 'Save' button, all text entries are retrieved and
        written (dumped) to a yaml config file in the running directory.

        yaml.dump has a sort_keys kwarg that is set to True by default. Set to False to no longer reorder.
            > https://stackoverflow.com/a/55858112/3382269

        :param e: event e waits for button press from 'Save'
        :return:
        """
        self.config = {}
        for row in range(len(self.instrID_text)):
            # self.config[f'INSTR{row}'] = {'instr': self.instrID_text[row].GetValue(),
            #                               'ip_address': self.ipAddress_text[row].GetValue(),
            #                               'port': self.port_text[row].GetValue(),
            #                               'gpib_address': self.gpib_text[row].GetValue(),
            #                               'mode': self.mode_choice[row].GetStringSelection()}
            self.config[self.instrID_text[row].GetValue()] = {'ip_address': self.ipAddress_text[row].GetValue(),
                                                              'port': self.port_text[row].GetValue(),
                                                              'gpib_address': self.gpib_text[row].GetValue(),
                                                              'mode': self.mode_choice[row].GetStringSelection()}
            print(self.config)

        with open('instrument_config.yaml', 'w') as f:
            yaml.dump(self.config, f, sort_keys=False)
        self.Destroy()

    def GetConfig(self):
        return self.config

    def OnClear(self, e):
        """
        Clears all text ctrl entries and resets both text ctrl enable/disables and 'choice' drop-down's to defaults

        :param e: event e waits for button press from 'Clear'
        """
        for row in range(len(self.instrID_text)):
            self.instrID_text[row].Enable(True)  # Reset to default enabled 'True'
            self.ipAddress_text[row].Enable(True)  # Reset to default enabled 'True'
            self.port_text[row].Enable(True)  # Reset to default enabled 'True'
            self.gpib_text[row].Enable(False)  # Reset to default enabled 'True'
            self.instrID_text[row].Clear()  # Clear textbox
            self.ipAddress_text[row].Clear()  # Clear textbox
            self.port_text[row].Clear()  # Clear textbox
            self.gpib_text[row].Clear()  # Clear textbox
            self.mode_choice[row].SetSelection(0)
            self.toggle_text_ctrl(row)


class MyApp(wx.App):
    def OnInit(self):
        dialog = MyDialog(None, wx.ID_ANY, "")
        dialog.ShowModal()
        return True


if __name__ == '__main__':
    app = MyApp(0)
    app.MainLoop()
