import os, sys
import minixs as mx
import minixs.info as mxinfo
import wx
import wxmpl
import util
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

class LoadEnergiesPanel(wx.Panel):
  def __init__(self, *args, **kwargs):
    if 'directory' in kwargs.keys():
      self.directory = kwargs['directory']
      del(kwargs['directory'])
    else:
      self.directory = ''

    wx.Panel.__init__(self, *args, **kwargs)

    self.grid = wx.FlexGridSizer(2, 3, HPAD, VPAD)

    label = wx.StaticText(self, wx.ID_ANY, 'Text File:')
    self.grid.Add(label, 0, wx.ALIGN_CENTER_VERTICAL)

    self.file_entry = wx.TextCtrl(self)
    self.grid.Add(self.file_entry, 1, wx.EXPAND)

    b = wx.Button(self, wx.ID_ANY, '...')
    b.Bind(wx.EVT_BUTTON, self.OnChoose)
    self.grid.Add(b)

    label = wx.StaticText(self, wx.ID_ANY, 'Column:')
    self.grid.Add(label, 0, wx.ALIGN_CENTER_VERTICAL)

    self.combo = wx.ComboBox(self, wx.ID_ANY, style=wx.CB_READONLY)
    self.grid.Add(self.combo, 1, wx.EXPAND)

    self.grid.AddGrowableCol(1, 1)

    self.SetSizerAndFit(self.grid)

  def OnChoose(self, evt):
    dlg = wx.FileDialog(self, 'Select a text file', self.directory, style=wx.FD_OPEN)
    ret = dlg.ShowModal()

    if ret == wx.ID_OK:
      self.directory = dlg.GetDirectory()
      self.filename = dlg.GetFilename()

      self.file_entry.SetValue(self.filename)
      self.fill_column_names()

    dlg.Destroy()

  def fill_column_names(self):
    columns = util.read_scan_column_names(os.path.join(self.directory, self.filename))
    sel = self.combo.GetSelection()
    if columns:
      self.combo.SetItems(columns)

      if sel == -1:
        for i in range(len(columns)):
          if 'energy' in columns[i].lower():
            self.combo.SetSelection(i)
            break
      else:
        self.combo.SetSelection(-1) # force update even if sel is same
        self.combo.SetSelection(sel)

  def get_info(self):
    return (self.directory, self.filename, self.combo.GetSelection())

class LoadEnergiesDialog(wx.Dialog):
  def __init__(self, *args, **kwargs):
    directory = ''
    if 'directory' in kwargs.keys():
      directory = kwargs['directory']
      del(kwargs['directory'])

    wx.Dialog.__init__(self, *args, **kwargs)

    vbox = wx.BoxSizer(wx.VERTICAL)

    self.panel = LoadEnergiesPanel(self, directory=directory)
    vbox.Add(self.panel, 1, wx.EXPAND | wx.BOTTOM, VPAD)

    hbox = wx.StdDialogButtonSizer()

    b = wx.Button(self, wx.ID_CANCEL, 'Cancel')
    hbox.AddButton(b)

    b = wx.Button(self, wx.ID_OK, 'Add')
    hbox.AddButton(b)

    hbox.Realize()

    vbox.Add(hbox, 0, wx.EXPAND)

    self.SetSizerAndFit(vbox)

  def get_info(self):
    return self.panel.get_info()


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

  def get_filter_info(self):
    return [ (self.checks[i].GetValue(), self.spins[i].GetValue()) for i in range(NUM_FILTERS) ]

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

import wx.lib.mixins.listctrl as listmix
class ExposureList(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
  def __init__(self, *args, **kwargs):
    wx.ListCtrl.__init__(self, *args, **kwargs)
    listmix.ListCtrlAutoWidthMixin.__init__(self)

    self.InsertColumn(0, 'Incident Energy', width=200)
    self.InsertColumn(1, 'Exposure File', width=200)

    self.num_rows = 0
    self.num_energies = 0
    self.num_exposures = 0

  def AppendEnergy(self, energy):
    s = '%.2f' % energy
    print s

    if self.num_energies >= self.num_rows:
      self.InsertStringItem(self.num_rows, 'hmm')
      self.num_rows += 1

    self.SetStringItem(self.num_energies, 0, s)
    self.EnsureVisible(self.num_energies)

    self.num_energies += 1

  def AppendExposure(self, exposure):
    if self.num_exposures >= self.num_rows:
      self.InsertStringItem(self.num_rows, '')
      self.num_rows += 1

    self.SetStringItem(self.num_exposures, 1, exposure)
    self.EnsureVisible(self.num_exposures)

    self.num_exposures += 1

  def ClearEnergies(self):
    for i in range(self.num_energies):
      self.SetStringItem(i, 0, '')
    self.num_energies = 0

  def ClearExposures(self):
    for i in range(self.num_exposures):
      self.SetStringItem(i, 1, '')
    self.num_exposures = 0

  def GetData(self):
    nr = self.GetItemCount()
    nc = self.GetColumnCount()
    strings = [
        [self.GetItem(i,j).GetText() for j in range(nc)]
        for i in range(nr)
        ]

    energies = []
    files = []
    for row in strings:
      e,f = row
      if e == '' and f == '':
        continue
      if e == '' or f == '':
        raise ValueError("Empty cells are not allowed")
      energies.append(float(e))
      files.append(f)

    return (energies, files)

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
    listctrl = ExposureList(self, ID_EXPOSURE_LIST,
        style=wx.LC_REPORT|wx.LC_HRULES|wx.LC_VRULES)
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
  CHANGED_FILTERS = 1
  CHANGED_EXPOSURES = 2

  def __init__(self, view, model):
    self.view = view
    self.model = model

    self.changed_flag = 0
    self.changed_timeout = None

    self.dialog_dirs = {
        'last': '',
        'exposures': '',
        'energies': '',
        'open': '',
        'save': ''
        }

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
    if not self.dialog_dirs['energies']:
      self.dialog_dirs['energies'] = self.dialog_dirs['last']

    dlg = LoadEnergiesDialog(self.view, directory=self.dialog_dirs['energies'])
    ret = dlg.ShowModal()

    if ret == wx.ID_OK:
      directory, filename, column = dlg.get_info()
      self.dialog_dirs['energies'] = self.dialog_dirs['last'] = directory

      energies = mx.read_scan_info(os.path.join(directory, filename),
          [column])[0]

      for e in energies:
        self.view.panel.exposure_list.AppendEnergy(e)

      self.changed(self.CHANGED_EXPOSURES)

    dlg.Destroy()

  def OnClearEnergies(self, evt):
    self.view.panel.exposure_list.ClearEnergies()
    self.changed(self.CHANGED_EXPOSURES)

  def OnSelectExposures(self, evt):
    if not self.dialog_dirs['exposures']:
      self.dialog_dirs['exposures'] = self.dialog_dirs['last']

    dlg = wx.FileDialog(self.view, 'Select Exposure Files',
        self.dialog_dirs['exposures'],
        style=wx.FD_MULTIPLE)

    ret = dlg.ShowModal()
    if ret == wx.ID_OK:
      directory = dlg.GetDirectory()
      self.dialog_dirs['exposures'] = self.dialog_dirs['last'] = directory
      filenames = dlg.GetFilenames()

      for filename in filenames:
        self.view.panel.exposure_list.AppendExposure(filename)

      self.changed(self.CHANGED_EXPOSURES)

    dlg.Destroy()

  def OnClearExposures(self, evt):
    self.view.panel.exposure_list.ClearExposures()
    self.changed(self.CHANGED_EXPOSURES)

  def OnLoadExposures(self, evt):
    self.changed(self.CHANGED_EXPOSURES)

  def OnFilterSpin(self, evt):
    self.filter_info = self.view.panel.filter_panel.get_filter_info()
    self.changed(self.CHANGED_FILTERS)

  def OnFilterCheck(self, evt):
    i = FILTER_IDS.index(evt.Id)
    self.view.panel.filter_panel.set_filter_enabled(i, evt.Checked())
    self.filter_info = self.view.panel.filter_panel.get_filter_info()
    self.changed(self.CHANGED_FILTERS)

  def changed(self, flag):
    self.changed_flag |= flag
    delay = 1000./30.

    if self.changed_timeout is None:
      self.changed_timeout = wx.CallLater(delay, self.OnChangeTimeout)
    elif not self.changed_timeout.IsRunning():
      self.changed_timeout.Restart(delay)

  def OnChangeTimeout(self):
    print "Changed: ", self.changed_flag

    if self.changed_flag & self.CHANGED_EXPOSURES:
      pass

    if self.changed_flag & self.CHANGED_FILTERS:
      pass

    self.changed_flag = 0

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
