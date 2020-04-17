def main():
    ACI_ranges = ['1.2mA', '12mA', '120mA', '1.2A', '3A']

    print('running test02!')
    print('\nSelect from the following ranges: ' + str(ACI_ranges))
    user_input = input()
    for i, item in enumerate(ACI_ranges):
        if user_input == item:
            print(f'You selected {item}!')
        else:
            pass

    print('"nighthawk" or "DOD" spec range?')
    spec_range_input = input()
    print('done!')


if __name__ == '__main__':
    main()

# import subprocess
# import time
# import wx
#
# from threading import Thread
#
#
# class PingThread(Thread):
#
#     def __init__(self, text_ctrl):
#         Thread.__init__(self)
#         self.text_ctrl = text_ctrl  # this is the log
#         self.sentinel = True
#         self.start()
#
#     def run(self):
#         proc = subprocess.Popen("ping www.google.com",
#                                 shell=True,
#                                 stdout=subprocess.PIPE)
#         while self.sentinel:
#             line = proc.stdout.readline()
#             if line.strip() == "":
#                 pass
#             else:
#                 wx.CallAfter(self.text_ctrl.write, line)
#
#             if not line: break
#
#         proc.kill()
#
#
# class MyFrame(wx.Frame):
#
#     def __init__(self):
#         wx.Frame.__init__(self, None, title='Redirecter')
#         self.ping_thread = None
#
#         main_sizer = wx.BoxSizer(wx.VERTICAL)
#
#         panel = wx.Panel(self)
#
#         self.log = wx.TextCtrl(panel, style=wx.TE_MULTILINE)  # text ctrl created here named log
#
#         ping_btn = wx.Button(panel, label='Ping')
#         ping_btn.Bind(wx.EVT_BUTTON, self.on_ping)
#
#         main_sizer.Add(self.log, 1, wx.ALL | wx.EXPAND, 5)
#         main_sizer.Add(ping_btn, 0, wx.ALL, 5)
#         panel.SetSizer(main_sizer)
#
#         self.Bind(wx.EVT_CLOSE, self.on_close)
#
#         self.Show()
#
#     def on_ping(self, event):
#         self.ping_thread = PingThread(self.log)  # pass reference to log into pingThread
#
#     def on_close(self, event):
#         if self.ping_thread:
#             self.ping_thread.sentinel = False
#             self.ping_thread.join()
#         self.Destroy()
#
#
# if __name__ == '__main__':
#     app = wx.App(False)
#     frame = MyFrame()
#     app.MainLoop()
