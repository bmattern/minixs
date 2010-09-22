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
ID_LOAD_EXPOSURES   = wx.NewId()
ID_DISPERSIVE_DIR   = wx.NewId()
ID_EXPOSURE_SLIDER  = wx.NewId()

class CalibratorModel(object):
  def __init__(self):
    calib = mxinfo.CalibrationInfo()


FILTER_MIN  = 0
FILTER_MAX  = 1
FILTER_LOW  = 2
FILTER_HIGH = 3
FILTER_NBOR = 4
NUM_FILTERS = 5

FILTER_NAMES = [
    'Min Visible',
    'Max Visible',
    'Low Cutoff',
    'High Cutoff',
    'Neighbors'
    ]

FILTER_IDS = [ wx.NewId() for n in FILTER_NAMES ]

class FilterPanel(wx.Panel):
  def __init__(self, *args, **kwargs):
    wx.Panel.__init__(self, *args, **kwargs)

    filter_defaults = [
        (0, True),       # min vis
        (1000, False),   # max vis
        (5, True),       # low cut
        (10000, False),  # high cut
        (2, True)        # neighbors
        ]

    grid = wx.FlexGridSizer(NUM_FILTERS, 2, HPAD, VPAD)
    self.checks = []
    self.spins = []

    for i, name in enumerate(FILTER_NAMES):
      val, enabled = filter_defaults[i]
      id = FILTER_IDS[i]
      check = wx.CheckBox(self, id, name)
      check.SetValue(enabled)
      spin = wx.SpinCtrl(self, id, '', max=100000)
      spin.SetValue(val)
      spin.Enable(enabled)

      grid.Add(check)
      grid.Add(spin)

      self.checks.append(check)
      self.spins.append(spin)

    label = wx.StaticText(self, wx.ID_ANY, 'Dispersive Dir.')
    choice = wx.Choice(self, ID_DISPERSIVE_DIR, choices=mx.DIRECTION_NAMES)
    grid.Add(label, 0, wx.ALIGN_CENTER_VERTICAL)
    grid.Add(choice)

    self.SetSizerAndFit(grid)

  def set_filter_value(self, filter_type, value):
    self.spins[filter_type].SetValue(int(value))

  def set_filter_enabled(self, filter_type, enabled):
    self.checks[filter_type].SetValue(enabled)
    self.spins[filter_type].Enable(enabled)

class ImagePanel(wx.Panel):
  def __init__(self, *args, **kwargs):
    wx.Panel.__init__(self, *args, **kwargs)


class ExposuresPanel(wx.Panel):
  def __init__(self, *args, **kwargs):
    wx.Panel.__init__(self, *args, **kwargs)

    vbox = wx.BoxSizer(wx.VERTICAL)

    label = wx.StaticText(self, wx.ID_ANY, 'No Exposures Loaded')
    vbox.Add(label, 0, wx.EXPAND | wx.BOTTOM, VPAD)
    self.label = label

    panel = ImagePanel(self, wx.ID_ANY)
    vbox.Add(panel, 0, wx.EXPAND | wx.BOTTOM, VPAD)
    self.image_panel = panel

    slider = wx.Slider(self, ID_EXPOSURE_SLIDER, 1,1,2)
    vbox.Add(slider, 0, wx.EXPAND)
    self.slider = slider

    self.SetSizerAndFit(vbox)


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
    vbox.Add(listctrl, 1, wx.EXPAND | wx.BOTTOM, VPAD)
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

    # load exposures button
    button = wx.Button(self, ID_LOAD_EXPOSURES, "Load Exposures")
    vbox.Add(button, 0, wx.EXPAND | wx.BOTTOM, VPAD)
   
    # add filters and image view
    hbox = wx.BoxSizer(wx.HORIZONTAL)

    panel = FilterPanel(self, wx.ID_ANY)
    hbox.Add(panel, 0, wx.RIGHT, HPAD)
    self.filter_panel = panel

    panel = ExposuresPanel(self, wx.ID_ANY)
    hbox.Add(panel, 1)
    self.exposures_panel = panel

    vbox.Add(hbox, 0, wx.EXPAND)

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
    callbacks = [
        (wx.EVT_MENU, [
          (wx.ID_EXIT, self.OnExit),
          (wx.ID_OPEN, self.OnOpen),
          (wx.ID_ABOUT, self.OnAbout),
          ]),
        (wx.EVT_TEXT, [
          (ID_DATASET_NAME, self.OnDatasetName),
          ]),
        (wx.EVT_BUTTON, [
          (ID_READ_ENERGIES, self.OnReadEnergies),
          (ID_CLEAR_ENERGIES, self.OnClearEnergies),
          (ID_SELECT_EXPOSURES, self.OnSelectExposures),
          (ID_CLEAR_EXPOSURES, self.OnClearExposures),
          (ID_LOAD_EXPOSURES, self.OnLoadExposures),
          ]),
        ]

    for event, bindings in callbacks:
      for id, callback in bindings:
        self.view.Bind(event, callback, id=id)

    for id in FILTER_IDS:
      self.view.Bind(wx.EVT_SPINCTRL, self.OnFilterSpin, id=id)
      self.view.Bind(wx.EVT_CHECKBOX, self.OnFilterCheck, id=id)


  def OnOpen(self, evt):
    pass

  def OnExit(self, evt):
    self.view.Close(True)

  def OnAbout(self, evt):
    pass

  def OnDatasetName(self, evt):
    self.model.dataset_name = evt.GetString()

  def OnReadEnergies(self, evt):
    pass

  def OnClearEnergies(self, evt):
    pass

  def OnSelectExposures(self, evt):
    pass

  def OnClearExposures(self, evt):
    pass

  def OnLoadExposures(self, evt):
    pass

  def OnFilterSpin(self, evt):
    pass

  def OnFilterCheck(self, evt):
    i = FILTER_IDS.index(evt.Id)
    self.view.panel.filter_panel.set_filter_enabled(i, evt.Checked())

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
