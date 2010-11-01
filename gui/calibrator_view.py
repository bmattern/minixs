import wx
from frame import MenuFrame
from image_view import ImageView

from calibrator_const import *
from matplotlib import cm

from minixs import DIRECTION_NAMES

import minixs.filter as filter
import filter_view

HPAD = 10
VPAD = 5

class LoadEnergiesPanel(wx.Panel):
  def __init__(self, *args, **kwargs):
    wx.Panel.__init__(self, *args, **kwargs)

    self.grid = wx.FlexGridSizer(2, 3, HPAD, VPAD)

    # text file
    label = wx.StaticText(self, wx.ID_ANY, 'Text File:')
    self.grid.Add(label, 0, wx.ALIGN_CENTER_VERTICAL)

    self.file_entry = wx.TextCtrl(self)
    self.grid.Add(self.file_entry, 1, wx.EXPAND)

    b = wx.Button(self, ID_LOAD_SCAN, '...')
    self.grid.Add(b)

    # column
    label = wx.StaticText(self, wx.ID_ANY, 'Column:')
    self.grid.Add(label, 0, wx.ALIGN_CENTER_VERTICAL)

    self.combo = wx.ComboBox(self, wx.ID_ANY, style=wx.CB_READONLY)
    self.grid.Add(self.combo, 1, wx.EXPAND)

    self.grid.AddGrowableCol(1, 1)

    self.SetSizerAndFit(self.grid)

  def fill_column_names(self, filename):
    columns = util.read_scan_column_names(filename)
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
    return (self.file_entry.GetValue(), self.combo.GetSelection())

class LoadEnergiesDialog(wx.Dialog):
  def __init__(self, *args, **kwargs):
    wx.Dialog.__init__(self, *args, **kwargs)

    vbox = wx.BoxSizer(wx.VERTICAL)

    self.panel = LoadEnergiesPanel(self)
    vbox.Add(self.panel, 1, wx.EXPAND | wx.ALL, VPAD)

    hbox = wx.StdDialogButtonSizer()

    b = wx.Button(self, wx.ID_CANCEL, 'Cancel')
    hbox.AddButton(b)

    b = wx.Button(self, wx.ID_OK, 'Add')
    hbox.AddButton(b)

    hbox.Realize()

    vbox.Add(hbox, 0, wx.EXPAND|wx.ALL, VPAD)

    self.SetSizerAndFit(vbox)

  def set_filename(self, filename):
    self.panel.file_entry.SetValue(filename)
    self.panel.fill_column_names(filename)

  def get_info(self):
    return self.panel.get_info()


class FilterPanel(wx.Panel):

  def __init__(self, *args, **kwargs):
    wx.Panel.__init__(self, *args, **kwargs)


    grid = wx.FlexGridSizer(len(filter_view.REGISTRY), 2, HPAD, VPAD)
    self.checks = {}
    self.views = {}

    for fltr, view_class, id in filter_view.REGISTRY:
      check = wx.CheckBox(self, id, fltr.name)

      view = view_class(self, id, filter=fltr)
      if fltr.name in FILTER_DEFAULTS.keys():
        val, enabled = FILTER_DEFAULTS[fltr.name]

        check.SetValue(enabled)
        view.Enable(enabled)
        view.SetValue(val)
      else:
        check.SetValue(False)
        view.Enable(False)

      grid.Add(check)
      grid.Add(view)

      self.checks[id] = check
      self.views[id] = view

    """
    check = wx.CheckBox(self, ID_FILTER_EMISSION, 'Filter Emission')
    choice = wx.Choice(self, ID_FILTER_EMISSION, choices=FILTER_EMISSION_TYPE_NAMES)
    choice.Enable(False)
    grid.Add(check)
    grid.Add(choice)
    self.filter_emission_check = check
    self.filter_emission_choice = choice
    """

    label = wx.StaticText(self, wx.ID_ANY, 'Dispersive Dir.')
    choice = wx.Choice(self, ID_DISPERSIVE_DIR, choices=DIRECTION_NAMES)
    grid.Add(label, 0, wx.ALIGN_CENTER_VERTICAL)
    grid.Add(choice)
    self.dispersive_direction = choice

    self.SetSizerAndFit(grid)

  def set_filter_value(self, filter_type, value):
    self.views[filter_type].SetValue(int(value))

  def set_filter_enabled(self, filter_type, enabled):
    self.checks[filter_type].SetValue(enabled)
    self.views[filter_type].Enable(enabled)

  def set_filters(self, filters):
    fmap = {}
    for f in filters:
      fmap[f.__class__] = f

    for ftype, view_class, id in filter_view.REGISTRY:
      if ftype in fmap:
        enabled = True
        val = fmap[ftype].get_val()
      else:
        enabled = False
        val = FILTER_DEFAULTS[ftype.name][1]

      self.checks[id].SetValue(enabled)
      self.views[id].Enable(enabled)
      self.views[id].SetValue(val)

  def get_filters(self):
    return [ 
        (
          self.views[i].filter.name,
          self.checks[i].GetValue(),
          self.views[i].GetValue()
        ) for i in filter_view.filter_ids()
      ]

class ExposurePanel(wx.Panel):
  def __init__(self, *args, **kwargs):
    wx.Panel.__init__(self, *args, **kwargs)

    vbox = wx.BoxSizer(wx.VERTICAL)

    label = wx.StaticText(self, wx.ID_ANY, 'No Exposures Loaded')
    vbox.Add(label, 0, wx.EXPAND | wx.BOTTOM, VPAD)
    self.label = label

    panel = ImageView(self, ID_IMAGE_PANEL, size=(487,195))
    vbox.Add(panel, 0, wx.EXPAND | wx.BOTTOM, VPAD)
    self.image_view = panel

    slider = wx.Slider(self, ID_EXPOSURE_SLIDER, 0,0,1)
    slider.Enable(False)
    vbox.Add(slider, 0, wx.EXPAND)
    self.slider = slider

    self.SetSizerAndFit(vbox)

  def SetPixels(self, pixels, colormap=cm.Greys_r):
    self.image_view.SetPixels(pixels, colormap)

import wx.lib.mixins.listctrl as listmix
class ExposureList(wx.ListCtrl,
                   listmix.ListCtrlAutoWidthMixin,
                   listmix.TextEditMixin
                   ):
  def __init__(self, *args, **kwargs):
    wx.ListCtrl.__init__(self, *args, **kwargs)
    listmix.ListCtrlAutoWidthMixin.__init__(self)
    listmix.TextEditMixin.__init__(self)

    self.InsertColumn(0, 'Incident Energy', width=200)
    self.InsertColumn(1, 'Exposure File', width=200)

    self.num_rows = 0
    self.num_energies = 0
    self.num_exposures = 0

  def FindLastEmptyItem(self, column):
    count = self.GetItemCount()
    # find last empty energy
    i = count
    while i >= 0:
      text = self.GetItem(i,column).GetText()
      if text != '':
        break

      i -= 1
    index = i+1

    return index

  def AppendEnergy(self, energy):
    s = '%.2f' % energy

    count = self.GetItemCount()
    index = self.FindLastEmptyItem(0)

    if index >= count:
      self.InsertStringItem(index, '')

    self.SetStringItem(index, 0, s)
    self.EnsureVisible(index)

  def AppendExposure(self, exposure):
    count = self.GetItemCount()
    index = self.FindLastEmptyItem(1)

    if index >= count:
      self.InsertStringItem(index, '')

    self.SetStringItem(index, 1, exposure)
    self.EnsureVisible(index)

  def AppendRow(self):
    """Add empty row to end of listctrl"""
    self.InsertStringItem(self.num_rows, '')
    self.num_rows += 1

  def DeleteRow(self, index=None):
    if index is None and self.GetItemCount() == 1:
      self.DeleteItem(0)

    if index is None:
      index = self.GetFirstSelected()
      while index != -1:
        self.DeleteItem(index)
        index = self.GetFirstSelected()
    else:
      self.DeleteItem(index)

  def ClearEnergies(self):
    for i in range(self.GetItemCount()):
      self.SetStringItem(i, 0, '')
    self.num_energies = 0

  def ClearExposures(self):
    for i in range(self.GetItemCount()):
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
    valid = True
    for row in strings:
      e,f = row
      if e == '' and f == '':
        continue
      if e == '' or f == '':
        valid = False
        continue
      energies.append(float(e))
      files.append(f)

    return (valid, energies, files)

class ToolsPanel(wx.Panel):
  def __init__(self, *args, **kwargs):
    wx.Panel.__init__(self, *args, **kwargs)

    vbox = wx.BoxSizer(wx.VERTICAL)

    choices = ['Exposures', 'Calibration Matrix']
    radio = wx.RadioBox(self, ID_VIEW_TYPE, 'View', choices=choices,
        majorDimension=1)
    vbox.Add(radio, 0, wx.EXPAND | wx.BOTTOM, VPAD)
    self.view_type = radio

    check = wx.CheckBox(self, ID_SHOW_XTALS, 'Show Crystals')
    check.SetValue(True)
    vbox.Add(check)

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


    # buttons to control exposure list
    hbox = wx.BoxSizer(wx.HORIZONTAL)

    # exposures list
    listctrl = ExposureList(self, ID_EXPOSURE_LIST,
        style=wx.LC_REPORT|wx.LC_HRULES|wx.LC_VRULES,
        size=(200,200))
    hbox.Add(listctrl, 1, wx.EXPAND | wx.RIGHT, HPAD)
    self.exposure_list = listctrl

    vbox2= wx.BoxSizer(wx.VERTICAL)

    button = wx.Button(self, ID_READ_ENERGIES, "Read Energies...")
    vbox2.Add(button, 1, wx.EXPAND | wx.BOTTOM, VPAD)

    button = wx.Button(self, ID_SELECT_EXPOSURES, "Select Exposures...")
    vbox2.Add(button, 1, wx.EXPAND | wx.BOTTOM, VPAD)

    button = wx.Button(self, ID_APPEND_ROW, "Append Row")
    vbox2.Add(button, 1, wx.EXPAND | wx.BOTTOM, VPAD)

    button = wx.Button(self, ID_DELETE_ROW, "Delete Row(s)")
    vbox2.Add(button, 1, wx.EXPAND | wx.BOTTOM, VPAD)

    button = wx.Button(self, ID_CLEAR_ENERGIES, "Clear Energies")
    vbox2.Add(button, 1, wx.EXPAND | wx.BOTTOM, VPAD)

    button = wx.Button(self, ID_CLEAR_EXPOSURES, "Clear Exposures")
    vbox2.Add(button, 1, wx.EXPAND)

    hbox.Add(vbox2, 0, wx.EXPAND)

    vbox.Add(hbox, 1, wx.EXPAND | wx.BOTTOM, VPAD)

    # add filters and image view
    hbox = wx.BoxSizer(wx.HORIZONTAL)

    panel = FilterPanel(self, wx.ID_ANY)
    hbox.Add(panel, 0, wx.RIGHT, HPAD)
    self.filter_panel = panel

    panel = ExposurePanel(self, wx.ID_ANY)
    hbox.Add(panel, 0, wx.RIGHT, HPAD)
    self.exposure_panel = panel

    panel = ToolsPanel(self, wx.ID_ANY)
    hbox.Add(panel, 1)
    self.tools_panel = panel

    vbox.Add(hbox, 0, wx.EXPAND | wx.BOTTOM, VPAD)

    # load calibrate button
    button = wx.Button(self, ID_CALIBRATE, "Calibrate")
    vbox.Add(button, 0, wx.EXPAND)
    self.calibrate_button = button

    self.SetSizerAndFit(vbox)

class CalibratorView(MenuFrame):
  def __init__(self, *args, **kwargs):
    kwargs['menu_info'] = [
        ('&File', [
          ('&Open...', wx.ID_OPEN, 'Load Calibration'),
          ('&Save...', wx.ID_SAVE, 'Save Calibration'),
          ('', None, None), # separator
          ('&Import Crystals...', ID_IMPORT_XTALS, 'Import Crystals'),
          ('&Export Crystals...', ID_EXPORT_XTALS, 'Export Crystals'),
          ('', None, None), # separator
          ('E&xit', wx.ID_EXIT, 'Terminate this program'),
          ]),
        ('&Help', [
          ('&About', wx.ID_ABOUT, 'About this program')
          ]),
        ]
    MenuFrame.__init__(self, *args, **kwargs)
    bar = self.CreateStatusBar()
    bar.SetFieldsCount(2)
    bar.SetStatusWidths([-1, -3])

    box = wx.BoxSizer(wx.VERTICAL)
    self.panel = CalibratorPanel(self, wx.ID_ANY)
    box.Add(self.panel, 1, wx.EXPAND | wx.ALL, VPAD)

    self.SetSizerAndFit(box)

    # provide shortcuts for gui elements that controller needs access to
    self.image_view = self.panel.exposure_panel.image_view
    self.exposure_list = self.panel.exposure_list
    self.dataset_name = self.panel.dataset_name
    self.exposure_panel = self.panel.exposure_panel
    self.exposure_label = self.exposure_panel.label
    self.exposure_slider = self.exposure_panel.slider
    self.view_type = self.panel.tools_panel.view_type
    self.calibrate_button = self.panel.calibrate_button

  def get_filters(self):
    return self.panel.filter_panel.get_filters()

