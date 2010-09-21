import minixs as mx
import minixs.info as mxinfo
import wx
import wxmpl
from frame import MenuFrame

HPAD = 10
VPAD = 5

ID_DATASET_NAME     = wx.NewId()
ID_EXPOSURE_LIST    = wx.NewId()
ID_READ_ENERGIES    = wx.NewId()
ID_SELECT_EXPOSURES = wx.NewId()
ID_CLEAR_ENERGIES   = wx.NewId()
ID_CLEAR_EXPOSURES  = wx.NewId()

class CalibratorModel(object):
  def __init__(self):
    calib = mxinfo.CalibrationInfo()

class CalibratorPanel(wx.Panel):
  def __init__(self, *args, **kwargs):
    wx.Panel.__init__(self, *args, **kwargs)

    vbox = wx.BoxSizer(wx.VERTICAL)

    # dataset name box
    hbox = wx.BoxSizer(wx.HORIZONTAL)
    label = wx.StaticText(self, wx.ID_ANY, "Dataset Name: ")
    entry = wx.TextCtrl(self, ID_DATASET_NAME)
    hbox.Add(label, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, HPAD)
    hbox.Add(entry, 1, 0 )
    vbox.Add(hbox, 0, wx.EXPAND | wx.BOTTOM, VPAD)
    self.dataset_name = entry

    # exposures list
    listctrl = wx.ListCtrl(self, ID_EXPOSURE_LIST,
        style=wx.LC_REPORT|wx.LC_HRULES|wx.LC_VRULES)
    listctrl.InsertColumn(0, 'Incident Energy', width=200)
    listctrl.InsertColumn(1, 'Exposure File', width=200)
    vbox.Add(listctrl, 0, wx.EXPAND | wx.BOTTOM, VPAD)
    self.exposure_list = listctrl

    # buttons to control exposure list
    hbox = wx.BoxSizer(wx.HORIZONTAL)

    button = wx.Button(self, ID_READ_ENERGIES, "Read Energies...")
    hbox.Add(button, 1, wx.EXPAND | wx.RIGHT, HPAD)

    button = wx.Button(self, ID_SELECT_EXPOSURES, "Select Exposures...")
    hbox.Add(button, 1, wx.EXPAND | wx.RIGHT, HPAD)

    button = wx.Button(self, ID_CLEAR_ENERGIES, "Clear Energies")
    hbox.Add(button, 1, wx.EXPAND | wx.RIGHT, HPAD)

    button = wx.Button(self, ID_CLEAR_EXPOSURES, "Clear Exposures")
    hbox.Add(button, 1, wx.EXPAND)

    vbox.Add(hbox, 0, wx.EXPAND | wx.BOTTOM, VPAD)


    self.SetSizerAndFit(vbox)

class CalibratorFrame(MenuFrame):
  def __init__(self, *args, **kwargs):
    kwargs['menu_info'] = [
        ('&File', [
          ('&Open', wx.ID_OPEN, 'Load File'),
          ('', None, None), # separator
          ('E&xit', wx.ID_EXIT, 'Terminate this program'),
          ]),
        ('&Help', [
          ('&About', wx.ID_ABOUT, 'About this program')
          ]),
        ]
    MenuFrame.__init__(self, *args, **kwargs)
    self.CreateStatusBar()

    box = wx.BoxSizer(wx.VERTICAL)
    self.panel = CalibratorPanel(self, wx.ID_ANY)
    box.Add(self.panel, 1, wx.EXPAND | wx.ALL, VPAD)

    self.SetSizerAndFit(box)

class CalibratorController(object):
  def __init__(self, view, model):
    self.view = view
    self.model = model

    self.BindCallbacks()

  def BindCallbacks(self):
    self.view.Bind(wx.EVT_MENU, self.OnExit, id=wx.ID_EXIT)
    self.view.Bind(wx.EVT_MENU, self.OnOpen, id=wx.ID_OPEN)
    self.view.Bind(wx.EVT_MENU, self.OnAbout, id=wx.ID_ABOUT)

  def OnOpen(self, evt):
    pass

  def OnExit(self, evt):
    self.view.Close(True)

  def OnAbout(self, evt):
    pass

class CalibratorApp(wx.App):
  def __init__(self, *args, **kwargs):
    wx.App.__init__(self, *args, **kwargs)

    model = CalibratorModel()
    view = CalibratorFrame(None, wx.ID_ANY, "minIXS Calibrator")
    controller = CalibratorController(view, model)

    view.Show()

if __name__ == "__main__":
  app = CalibratorApp()
  app.MainLoop()
