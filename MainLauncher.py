#!/usr/bin/env python
# -*-coding=utf-8 -*-

import wizard_instrument
import grid_wrapper
import wizard_script


import wx
import wx.adv

from threading import Thread
from subprocess import Popen, PIPE, STDOUT
import os
import sys
import time
import errno
import yaml  # used for writing yaml config file (save configuration settings)
import json  # used for converting a string representation of list into list

APP_EXIT = 1
"""
Description:
Application aims to improve data acquisition for future measurements. Some of these improvements include simplifying
script development so the user can focus on the measurement rather than any of the backend. 

https://scotch.io/tutorials/how-to-push-an-existing-project-to-github
"""


def OnAbout(e):
    description = """The Test and Validation Suite is a set of automated tests for use in validating Units Under
                     Test (UUT) within the calibration, metrology, and test facilities at FLUKE.
                  """

    info = wx.adv.AboutDialogInfo()
    info.SetName('Test and Validation Suite')
    # info.SetIcon(wx.Icon('Fluke Logo.png', wx.BITMAP_TYPE_PNG))
    info.SetVersion('1.0')
    info.SetDescription(description)
    info.SetCopyright('2020 FLUKE Corporation')
    # info.SetWebSite('https://www.fluke.com')
    wx.adv.AboutBox(info)


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        # begin wxGlade: MyFrame.__init__
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER
        wx.Frame.__init__(self, *args, **kwds)
        self.frame_number = 1
        self.SetSize((1075, 779))

        self.panel_1 = wx.Panel(self, wx.ID_ANY)
        self.panel_2 = wx.Panel(self.panel_1, wx.ID_ANY)

        self.config = {'INSTR01': {'instr': '', 'ip_address': '', 'port': '', 'gpib_address': '', 'mode': ''}}
        # Combo Drop-down  ---------------------------------------------------------------------------------------------
        self.choice = wx.Choice(self.panel_2, wx.ID_ANY, choices=[])
        self.__onRefresh()  # fills choice drop-down with available test scripts
        # Text Ctrl Boxes  ---------------------------------------------------------------------------------------------
        self.text_ctrl_1 = wx.TextCtrl(self.panel_2, wx.ID_ANY, "")
        self.text_ctrl_2 = wx.TextCtrl(self.panel_2, wx.ID_ANY, "")
        self.text_ctrl_3 = wx.TextCtrl(self.panel_2, wx.ID_ANY, "",
                                       style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_DONTWRAP)  # | wx.TE_RICH
        self.text_ctrl_3.SetFont(wx.Font(10, wx.MODERN, wx.NORMAL, wx.NORMAL, False, u'Consolas'))
        self.text_ctrl_4 = wx.TextCtrl(self.panel_2, wx.ID_ANY, "", style=wx.TE_PROCESS_ENTER)
        # Checkboxes  --------------------------------------------------------------------------------------------------
        self.checkbox_1 = wx.CheckBox(self.panel_2, wx.ID_ANY, "Save results to \".../output\"")
        self.checkbox_2 = wx.CheckBox(self.panel_2, wx.ID_ANY, "Save plots")
        self.checkbox_3 = wx.CheckBox(self.panel_2, wx.ID_ANY, "Display results in realtime")
        # Buttons  -----------------------------------------------------------------------------------------------------
        self.button_1 = wx.Button(self.panel_2, wx.ID_ANY, "Refresh")
        self.button_2 = wx.Button(self.panel_2, wx.ID_ANY, "Browse...")
        self.button_6 = wx.Button(self.panel_2, wx.ID_ANY, "Clear")
        self.button_3 = wx.Button(self.panel_2, wx.ID_ANY, "Configure Instruments")
        self.button_4 = wx.Button(self.panel_2, wx.ID_ANY, "Script Wizard")
        self.button_5 = wx.Button(self.panel_2, wx.ID_ANY, "Run Measurement")
        self.button_7 = wx.Button(self.panel_2, wx.ID_ANY, "Enter")

        self.grid_1 = grid_wrapper.MyGrid(self.panel_2)

        # Menu Bar -----------------------------------------------------------------------------------------------------
        self.frame_menubar = wx.MenuBar()
        self.fileMenu = wx.Menu()
        self.helpMenu = wx.Menu()
        self.frame_menubar.Append(self.fileMenu, '&File')  # The "File" menu is accessible via the Alt+F shortcut.
        self.frame_menubar.Append(self.helpMenu, '&Help')  # The "File" menu is accessible via the Alt+F shortcut.

        self.fileMenu.Append(wx.ID_NEW, '&New')  # The menu item "New" is appended into the menu object.
        self.fileMenu.AppendSeparator()  # A menu separator is appended with the AppendSeparator() method

        """        
        Manually create a wx.MenuItem and accelerator key
        The character following the ampersand is underlined specifying Ctrl+Q after the tab escape character ensures
        that if pressed, the application will close. 
        > "Exit" is appended into the menu object.
        """
        self.fileMenu.Append(wx.MenuItem(self.fileMenu, APP_EXIT, 'E&xit\tCtrl+Q'))
        self.helpItem = self.helpMenu.Append(wx.ID_ABOUT, '&About')

        self.Bind(wx.EVT_MENU, self.OnExit, id=APP_EXIT)
        self.Bind(wx.EVT_MENU, OnAbout, self.helpItem)
        self.SetMenuBar(self.frame_menubar)
        # Menu Bar end -------------------------------------------------------------------------------------------------

        self.__set_properties()
        self.__do_layout()

        # Event Triggers -----------------------------------------------------------------------------------------------
        """
        lambda is the simplest to implement since it doesn't require any additional imports like functools.partial does,
        though some people think that functools.partial is easier to understand. In every way, lambda is a function
        except it doesn't have a name. When a lambda command is called, it returns a reference to the created function,
        which means it can be used for the value of the command option to the button.
        For more info: http://stackoverflow.com/a/5771787/2276527
        """
        # Add a new test directory
        onRefresh_Event = lambda event: self.onRefresh(event)
        self.Bind(wx.EVT_BUTTON, onRefresh_Event, self.button_1)

        # Browse files
        onBrowse_Event = lambda event: self.OnBrowse(event)
        self.Bind(wx.EVT_BUTTON, onBrowse_Event, self.button_2)

        # Clear entries
        self.Bind(wx.EVT_BUTTON, self.OnClear, self.button_6)

        # Configure Instruments
        self.Bind(wx.EVT_BUTTON, self.OnConf, self.button_3)

        # Open Script Wizard
        OnOpenScriptWizard_Event = lambda event: self.OnOpenScriptWizard(event)
        self.Bind(wx.EVT_BUTTON, OnOpenScriptWizard_Event, self.button_4)

        # Run Measurement (start subprocess)
        OnRun_Event = lambda event: self.onRun2(event)
        self.Bind(wx.EVT_BUTTON, OnRun_Event, self.button_5)

        # Send command to subprocess
        OnCommand_Event = lambda event: self.send_Command(event)
        self.Bind(wx.EVT_TEXT_ENTER, OnCommand_Event, self.text_ctrl_4)
        self.Bind(wx.EVT_BUTTON, OnCommand_Event, self.button_7)

        # Button events end --------------------------------------------------------------------------------------------
        # end wxGlade

    def __set_properties(self):
        """
        Sets the properties of the control boxes and frame. Such as the frame title, frame behavior, and minimum sizes
        of the control boxes.
        """
        # begin wxGlade: MyFrame.__set_properties
        self.SetTitle("Test and Validation Suite")
        self.SetFocus()
        self.choice.SetMinSize((260, 23))
        self.text_ctrl_1.SetMinSize((260, 23))
        self.text_ctrl_2.SetMinSize((260, 23))
        self.text_ctrl_3.SetMinSize((500, 300))
        self.text_ctrl_4.SetMinSize((402, 23))

        self.grid_1.CreateGrid(16, 13)
        self.grid_1.SetMinSize((950, 334))
        # end wxGlade

    def __do_layout(self):
        """
        Sets layout of the wxFrame window
        """
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        # ROW 0 --------------------------------------------------------------------------------------------------------
        grid_sizer_1 = wx.GridBagSizer(0, 0)
        sizer_3 = wx.StaticBoxSizer(wx.StaticBox(self.panel_2, wx.ID_ANY, "Optional Attributes"), wx.VERTICAL)
        label_1 = wx.StaticText(self.panel_2, wx.ID_ANY, "Test and Validation Suite")
        bitmap_1 = wx.StaticBitmap(self.panel_2, wx.ID_ANY, wx.Bitmap("Fluke Logo.png", wx.BITMAP_TYPE_ANY))
        label_1.SetFont(wx.Font(20, wx.FONTFAMILY_DECORATIVE, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_BOLD, 0, ""))
        grid_sizer_1.Add(label_1, (0, 0), (1, 4), wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        grid_sizer_1.Add(bitmap_1, (0, 4), (1, 1), 0, 10)
        # ROW 2 --------------------------------------------------------------------------------------------------------
        static_line_1 = wx.StaticLine(self.panel_2, wx.ID_ANY)
        static_line_1.SetMinSize((526, 2))
        grid_sizer_1.Add(static_line_1, (1, 0), (1, 5), wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM | wx.TOP, 10)
        # ROW 3 --------------------------------------------------------------------------------------------------------
        label_2 = wx.StaticText(self.panel_2, wx.ID_ANY, "Available Tests")
        grid_sizer_1.Add(label_2, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        grid_sizer_1.Add(self.choice, (2, 1), (1, 3), wx.ALL, 5)
        grid_sizer_1.Add(self.button_1, (2, 4), (1, 1), wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        # ROW 4 --------------------------------------------------------------------------------------------------------
        label_3 = wx.StaticText(self.panel_2, wx.ID_ANY, "Import Spec File")
        grid_sizer_1.Add(label_3, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        grid_sizer_1.Add(self.text_ctrl_1, (3, 1), (1, 3), wx.ALL, 5)
        grid_sizer_1.Add(self.button_2, (3, 4), (1, 1), wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        # ROW 5 --------------------------------------------------------------------------------------------------------
        label_4 = wx.StaticText(self.panel_2, wx.ID_ANY, "Project Name")
        grid_sizer_1.Add(label_4, (4, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        grid_sizer_1.Add(self.text_ctrl_2, (4, 1), (1, 3), wx.ALL, 5)
        label_5 = wx.StaticText(self.panel_2, wx.ID_ANY, "(optional)")
        grid_sizer_1.Add(label_5, (4, 4), (1, 1), wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        # ROW 6 --------------------------------------------------------------------------------------------------------
        sizer_3.Add(self.checkbox_1, 0, wx.ALL, 5)
        sizer_3.Add(self.checkbox_2, 0, wx.ALL, 5)
        sizer_3.Add(self.checkbox_3, 0, wx.ALL, 5)
        grid_sizer_1.Add(sizer_3, (5, 0), (1, 4), wx.EXPAND | wx.TOP, 10)
        # ROW 8 --------------------------------------------------------------------------------------------------------
        # <-----------> SPACE! <----------->
        # ROW 8 --------------------------------------------------------------------------------------------------------
        grid_sizer_1.Add(self.button_6, (6, 0), (1, 2), wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM | wx.RIGHT | wx.TOP, 10)
        grid_sizer_1.Add(self.button_3, (6, 2), (1, 1),
                         wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.BOTTOM | wx.RIGHT | wx.TOP, 10)
        grid_sizer_1.Add(self.button_4, (6, 3), (1, 1),
                         wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.BOTTOM | wx.RIGHT | wx.TOP, 10)
        grid_sizer_1.Add(self.button_5, (6, 4), (1, 1), wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        # Right side ---------------------------------------------------------------------------------------------------
        grid_sizer_1.Add(self.text_ctrl_3, (0, 5), (6, 2), wx.LEFT | wx.RIGHT, 10)
        grid_sizer_1.Add(self.text_ctrl_4, (6, 5), (1, 1), wx.ALIGN_CENTER_VERTICAL | wx.ALL, 10)
        grid_sizer_1.Add(self.button_7, (6, 6), (1, 1), wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM | wx.RIGHT | wx.TOP, 10)

        grid_sizer_1.Add(self.grid_1, (7, 0), (1, 7), wx.EXPAND | wx.RIGHT | wx.TOP, 10)

        self.panel_2.SetSizer(grid_sizer_1)
        sizer_2.Add(self.panel_2, 1, wx.ALL | wx.EXPAND, 10)
        self.panel_1.SetSizer(sizer_2)
        sizer_1.Add(self.panel_1, 1, wx.EXPAND, 0)
        self.SetSizer(sizer_1)

        self.Layout()
        self.Centre()

    def OnOpenScriptWizard(self, e):
        title = f'Script Wizard {self.frame_number}'
        scriptWizard_Frame = wizard_script.WizardFrame(title=title, parent=wx.GetTopLevelParent(self))
        scriptWizard_Frame.SetChoices(self.config)
        scriptWizard_Frame.Show()
        self.frame_number += 1

    def onRun2(self, e):
        """
        Instantiates class Thread from threading module with a target worker function and proceeds to start the thread
        :param e: event e waits for button press from 'Run Measurement'
        """
        t = Thread(target=self.__onRun)
        t.start()

    def __onRun(self):
        """
        IMPLEMENTING RUN -----------------------------------------------------------------------------------------------
        Starts a Popen process from the 'subprocess' module where both stdout and stdin of the executed shell script
        are redirected to the main thread via the PIPE pipeline. PIPE defines a class to abstract thec concept of a
        pipeline — a sequence of converters from one file to another.

        > stdout is 'piped' to the text ctrl object of the main thread GUI window
        > the text_ctrl object where the user enters and then sends a command is 'piped' to stdin of the shell process
        > stderr is piped to STDOUT, which is the standard output of the main thread. Never use stderr=PIPE unless it's
          intended to be read from the stream. Otherwise, the child process may hang if the corresponding OS pipe
          buffer fills up.

        METHOD FOR UPDATING TEXTUAL PROGRESS BAR -----------------------------------------------------------------------
        In traditional stdout.write implementation, the progress bar relies on the carriage return to set the insertion
        point of a new write at the beginning of the line of text. So when a new update of the progress bar requires to
        be written, the new line can then overwrite the previous update of the progress bar. Unfortunately, this
        behavior cannot be carried over into wx.Text_Ctrl. Instead, we rely on the .Replace(*args) method, which
        replaces the text starting at the first position up to (but not including) the character at the last position
        with the given text. To implement this, the arguments passed were left, left+500, and the string object 'line'.
        The parameter 'left' finds the number of characters so far occupying the text buffer and subtracts the length of
        the previous line. Meanwhile, the conditional statement ensures the previous line will always be the updated
        progress bar.

        > Note - to find the length of the previous line (the last update to the progress bar), the line must first be
                 decoded from 'utf-8' to ensure all characters are counted correctly. Otherwise, extra characters can
                 end up being inappropriately counted since stdout from the subprocess is a binary sequence of bytes and
                 when not decoded first, results in a Unicode string of characters.

                 For instance, the character '█', counts as 1 character in utf-8, but without decoding would result in
                 the utf-8 literal character string: '\xe2\x96\x88'. The additional characters would clearly contribute
                 to an incorrect count.

                 Unicode    Char    UTF-8           Name
                 ---------------------------------------------
                 U+2588     █       \xe2\x96\x88    FULL BLOCK

        IMPLEMENTING wx.CallAfter --------------------------------------------------------------------------------------
        Do:         wx.CallAfter(self.text_ctrl_3.Replace, left, left+500, line)
        Instead of: wx.CallAfter(self.text_ctrl_3.Replace(left, left+500, line))

        The second method calls a method/function myself and passing the result to CallAfter. The first
        call will work, but fails later on because the result of .Replace(...) is passed rather than the
        reference.

        def CallAfter(callableObj, *args, **kw):

        The callable object is .Replace and *args are the arguments 'left, left+500, and line' passed

        FOR MORE INFORMATION -------------------------------------------------------------------------------------------
        + stdout textual progress bar:      https://stackoverflow.com/a/34325723
        + piping carriage return to stdout: https://stackoverflow.com/a/4622718
        + Replace():                        https://stackoverflow.com/a/12823557
        + Replace() / TextCtrl widgets:     https://docs.wxwidgets.org/2.8/wx_wxtextctrl.html#wxtextctrlreplace
        + wx.CallAfter:                     https://stackoverflow.com/a/24651853
        + wx.CallAfter:                     https://wiki.wxpython.org/CallAfter

        Running from Windows command line (CMD) produces UnicodeDecodeError --------------------------------------------
            > Python 3 is UTF-8 by default, but the environment in which it is operating is not - it has a default
              encoding of cp1252.

            > You can set the PYTHONIOENCODING environment variable to UTF-8 to override the default encoding, or change
              the environment to use UTF-8.

            > Prior to running the script, enter: 'SET PYTHONIOENCODING=utf8' into the command line (CMD)

            > (system variable may still be ignored)
              http://www.tiernok.com/posts/python-3-6-unicode-output-for-windows-console.html
            > https://stackoverflow.com/a/32146284/3382269

        Run Perl script in Python Subprocess
        https://stackoverflow.com/a/4682198/3382269
            var = "/some/file/path/"
            pipe = subprocess.Popen(["perl", "./uireplace.pl", var], stdin=subprocess.PIPE)
            pipe.stdin.write(var)
            pipe.stdin.close()
        """

        choice = self.choice.GetStringSelection()
        if choice != '':
            print(f'Now running {choice}.py')
            path = '.\\test scripts\\'  # the dot at the beginning ensures folder path begins in  running directory
            self.p = Popen([sys.executable or 'python', f'{path + choice}.py'], stdout=PIPE, stdin=PIPE, stderr=STDOUT)

            row = 0  # on Run, new data is appended at the zeroth row
            prevLine = b''
            for line in iter(self.p.stdout.readline, b''):
                if prevLine.startswith(b'Progress'):

                    line = line + b'\n'
                    left = max(0, self.text_ctrl_3.GetInsertionPoint() - len(prevLine.decode('utf-8')) - 2)
                    wx.CallAfter(self.text_ctrl_3.Replace, left, left + 500, line)
                    prevLine = line
                else:
                    wx.CallAfter(self.text_ctrl_3.WriteText, line)
                    prevLine = line

                if line.startswith(b'[TABLE] [') and line.endswith(b']\r\n\n'):
                    data = json.loads(line.split(b' ', 1)[1])
                    self.grid_1.write_list_to_row(row, data)
                    row += 1
                else:
                    pass
        else:
            pass

    def send_Command(self, e):
        """
        Retrieves the user input from the text ctrl object and writes to the stdin of the shell script subprocess.

        subprocess.communicate cannot be used to send stdin more than once. With '.communicate' a command is sent and
        stdin is then flushed then an EOF is sent. This closes stdin pipeline.

        subprocess.stdin.write() is used to overcome the restrictions of '.communicate' by ensuring an EOF is not sent
        after the command. However, with this approach, 'deadlocks' are possible where any of the other OS pipe buffers
        filling up could block the child process. Consequently, subprocess.stdin.flush() is sent on each write loop to
        force the buffer to remain empty.

        A deadlock will result from either:
        > 1 ->  Not adding a newline to the output you send to a subprocess--when the subprocess is trying to read line
                oriented input, i.e. the subprocess is looking for a newline while reading from stdin.

        > 2 ->  Not flushing the output, which means the other side never sees any data to read, so the other side hangs
                waiting for data.

        Error checking on each write using errno.
        > Note that errno.EPIPE is "Broken pipe" and errno.EINVAL is "Invalid argument".

        :param e: event e waits for button press from 'Enter'
        """
        command = self.text_ctrl_4.GetValue()
        if not command == '':
            print(f'trying command: {command}')
            try:
                line = f'\n[INPUT]: {command}\n\n'
                wx.CallAfter(self.text_ctrl_3.write, line)
                self.p.stdin.write(f'{command}\n'.encode())
                time.sleep(10e-3)
                self.p.stdin.flush()
                self.text_ctrl_4.Clear()
            except IOError as e:
                if e.errno != errno.EPIPE and e.errno != errno.EINVAL:
                    raise
        else:
            pass

    def onRefresh(self, e):
        self.__onRefresh()

    def __onRefresh(self):
        """
        Scans the running directory for test scripts
        (This list is used as the available choices in combo_box_1

        :return: list of test files in the running directory with the .py file extension and omitting python applications
        """
        test_files = [".".join(file.split(".")[:-1]) for file in os.listdir(os.curdir + '\\test scripts')
                      if os.path.isfile(file) and file.endswith('.py')
                      and file != 'MainLauncher.py' or file != 'instruments.py']

        self.choice.SetItems(test_files)
        return test_files

    def OnBrowse(self, e):
        """
        A file dialog is dispalyed and files are filtered to show only files with the wildcard '.csv' file extension.
        The file path to the selected file is retrieved and displayed in the text ctrl object

        :param e: event e waits for button press from 'Browse...'
        """
        with wx.FileDialog(self, "Open XYZ file", wildcard="CSV files (*.csv)|*.csv",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return  # the user changed their mind

            # Proceed loading the file chosen by the user
            path = fileDialog.GetPath()
        self.text_ctrl_1.SetValue(path)

    def OnConf(self, e):
        """
        Displays the 'Configuration Settings' dialog options.
        > A 'modal' dialog blocks program flow and user input on other windows until it is dismissed.
        > A 'modeless' dialog behaves more like a frame where program flow continues and input in other windows is still
          possible

        :param e: event e waits for button press 'Configuration Settings'
        """
        confDialog = wizard_instrument.MyDialog(self)
        confDialog.ShowModal()
        confDialog.Destroy()
        self.config = confDialog.GetConfig()

    def OnClear(self, e):
        """
        Resets text_ctrl boxes, combo boxes, and checkboxes to default.

        :param e: event e waits for button press from 'Clear'
        """
        self.text_ctrl_1.Clear()
        self.text_ctrl_2.Clear()
        self.text_ctrl_3.Clear()
        self.text_ctrl_4.Clear()
        self.choice.SetSelection(-1)
        self.checkbox_1.SetValue(0)
        self.checkbox_2.SetValue(0)
        self.checkbox_3.SetValue(0)

    def OnExit(self, e):
        """
        Closes the application.

        :param e: event e waits for button press 'Close' or when the frame exits (top right)
        """
        self.Close()


class MyApp(wx.App):
    def OnInit(self):
        self.frame = MyFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(self.frame)
        self.frame.Show()
        return True


if __name__ == '__main__':
    app = MyApp(0)
    app.MainLoop()
