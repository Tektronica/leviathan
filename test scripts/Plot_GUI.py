import wx
from ObjectListView2 import ObjectListView, ColumnDefn


class Results(object):
    """"""

    def __init__(self, tin, zip_code, plus4, name, address):
        """Constructor"""
        self.tin = tin
        self.zip_code = zip_code
        self.plus4 = plus4
        self.name = name
        self.address = address


class ProvPanel(wx.Panel):
    """"""

    def __init__(self, parent):
        """Constructor"""
        wx.Panel.__init__(self, parent=parent)

        mainSizer = wx.BoxSizer(wx.VERTICAL)

        self.test_data = [Results("123456789", "50158", "0065", "Patti Jones",
                                  "111 Centennial Drive"),
                          Results("978561236", "90056", "7890", "Brian Wilson",
                                  "555 Torque Maui"),
                          Results("456897852", "70014", "6545", "Mike Love",
                                  "304 Cali Bvld")
                          ]
        self.resultsOlv = ObjectListView(self,
                                         style=wx.LC_REPORT | wx.SUNKEN_BORDER)

        self.setResults()

        toggleBtn = wx.Button(self, label="Toggle Checks")
        toggleBtn.Bind(wx.EVT_BUTTON, self.onToggle)

        mainSizer.Add(self.resultsOlv, 1, wx.EXPAND | wx.ALL, 5)
        mainSizer.Add(toggleBtn, 0, wx.CENTER | wx.ALL, 5)
        self.SetSizer(mainSizer)

    def onToggle(self, event):
        """
        Toggle the check boxes
        """
        objects = self.resultsOlv.GetObjects()
        for obj in objects:
            print
            self.resultsOlv.IsChecked(obj)
            self.resultsOlv.ToggleCheck(obj)
        self.resultsOlv.RefreshObjects(objects)

    def setResults(self):
        """"""
        self.resultsOlv.SetColumns([
            ColumnDefn("TIN", "left", 100, "tin"),
            ColumnDefn("Zip", "left", 75, "zip_code"),
            ColumnDefn("+4", "left", 50, "plus4"),
            ColumnDefn("Name", "left", 150, "name"),
            ColumnDefn("Address", "left", 200, "address")
        ])
        self.resultsOlv.CreateCheckStateColumn()
        self.resultsOlv.SetObjects(self.test_data)


class ProvFrame(wx.Frame):
    """"""

    def __init__(self):
        """Constructor"""
        title = "OLV Checkbox Tutorial"
        wx.Frame.__init__(self, parent=None, title=title,
                          size=(1024, 768))
        panel = ProvPanel(self)


if __name__ == "__main__":
    app = wx.App(False)
    frame = ProvFrame()
    frame.Show()
    app.MainLoop()