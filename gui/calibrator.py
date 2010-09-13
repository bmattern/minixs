import wx
import minixs as mx
from matplotlib import cm, colors
from numpy import where
import os, sys

import util

import dataset
from dataset import CalibrationInfo, InvalidFileError

dialog_directory = ''

class LoadEnergiesPanel(wx.Panel):
  def __init__(self, *args, **kwargs):
    wx.Panel.__init__(self, *args, **kwargs)

    self.grid = wx.FlexGridSizer(3, 3, 9, 25)

    label = wx.StaticText(self, wx.ID_ANY, 'Text File:')
    self.grid.Add(label, 0, wx.CENTER)

    self.file_entry = wx.TextCtrl(self)
    self.grid.Add(self.file_entry, 1, wx.EXPAND)

    b = wx.Button(self, wx.ID_ANY, '...')
    b.Bind(wx.EVT_BUTTON, self.OnChoose)
    self.grid.Add(b)

    label = wx.StaticText(self, wx.ID_ANY, 'Column:')
    self.grid.Add(label)

    self.combo = wx.ComboBox(self, wx.ID_ANY, style=wx.CB_READONLY)
    self.grid.Add(self.combo, 1, wx.EXPAND)

    self.grid.AddGrowableCol(1, 1)

    self.SetSizerAndFit(self.grid)

  def OnChoose(self, evt):
    global dialog_directory
    dlg = wx.FileDialog(self, 'Select a text file', dialog_directory, style=wx.FD_OPEN)
    ret = dlg.ShowModal()

    if ret == wx.ID_OK:
      self.directory = dlg.GetDirectory()
      dialog_directory = self.directory
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
        self.combo.SetSelection(-1)
        self.combo.SetSelection(sel)

  def get_info(self):
    return (os.path.join(self.directory, self.filename), self.combo.GetSelection())

class LoadEnergiesDialog(wx.Dialog):
  def __init__(self, *args, **kwargs):
    wx.Dialog.__init__(self, *args, **kwargs)

    vbox = wx.BoxSizer(wx.VERTICAL)

    self.panel = LoadEnergiesPanel(self)
    vbox.Add(self.panel, 1, wx.EXPAND)

    hbox = wx.StdDialogButtonSizer()

    b = wx.Button(self, wx.ID_CANCEL, 'Cancel')
    #b.Bind(wx.EVT_BUTTON, self.OnCancel)
    hbox.AddButton(b)

    b = wx.Button(self, wx.ID_OK, 'Add')
    #b.Bind(wx.EVT_BUTTON, self.OnAdd)
    hbox.AddButton(b)

    hbox.Realize()

    vbox.Add(hbox, 0, wx.EXPAND)

    self.SetSizerAndFit(vbox)

  def get_info(self):
    return self.panel.get_info()

ACTION_NONE = 0
ACTION_RESIZE = 1

RESIZE_L = 0x01
RESIZE_R = 0x02
RESIZE_T = 0x04
RESIZE_B = 0x08

RESIZE_TL = RESIZE_T | RESIZE_L
RESIZE_TR = RESIZE_T | RESIZE_R
RESIZE_BL = RESIZE_B | RESIZE_L
RESIZE_BR = RESIZE_B | RESIZE_R

class ImagePanel(wx.Panel):
  def __init__(self, *args, **kwargs):
    self.info = kwargs['info']
    del(kwargs['info'])

    wx.Panel.__init__(self, *args, **kwargs)
    self.bitmap = None

    self.SetEvtHandlerEnabled(True)

    self.bad_pixels = []

    self.Bind(wx.EVT_PAINT, self.OnPaint)
    self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
    self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
    self.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)
    self.Bind(wx.EVT_MOTION, self.OnMotion)

    self.action = ACTION_NONE
    self.resize_dir = 0
    self.resize_xtal = None

    self.coord_cb = None

  def set_pixels(self, pixels):
    h,w = pixels.shape
    p = cm.Greys_r(pixels, bytes=True)[:,:,0:3]
    self.bitmap = wx.BitmapFromBuffer(w, h, p.tostring())
    self.Refresh()

  def OnLeftDown(self, evt):
    if self.action == ACTION_NONE:
      x,y = evt.GetPosition()

      off = 4
      resize_dir = 0

      for xtal in self.info.xtals:
        (x1,y1),(x2,y2) = xtal

        if y1 - off < y < y2 + off:
          if abs(x1 - x) < off:
            resize_dir |= RESIZE_L
          elif abs(x2 - x) < off:
            resize_dir |= RESIZE_R
        if x1 - off < x < x2 + off:
          if abs(y1 - y) < off:
            resize_dir |= RESIZE_T
          elif abs(y2 - y) < off:
            resize_dir |= RESIZE_B

        if resize_dir != 0:
          self.resize_dir = resize_dir
          self.resize_xtal = xtal
          break

      if not self.resize_xtal:
        xtal = [[x,y],[x+1,y+1]]
        self.info.xtals.append(xtal)
        self.resize_xtal = xtal
        self.resize_dir = RESIZE_BR

      self.action = ACTION_RESIZE

  def OnLeftUp(self, evt):
    if self.action == ACTION_RESIZE:
      (x1,y1), (x2,y2) = self.resize_xtal

      if x2 < x1:
        self.resize_xtal[0][0], self.resize_xtal[1][0] = x2, x1
      if y2 < y1:
        self.resize_xtal[0][1], self.resize_xtal[1][1] = y2, y1
          
      self.resize_xtal = None
      self.action = ACTION_NONE

  def OnRightUp(self, evt):
    if self.action == ACTION_NONE:
      for xtal in self.info.xtals:
        x,y = evt.GetPosition()
        (x1,y1), (x2,y2) = xtal

        if x1 <= x <= x2 and y1 <= y <= y2:
          self.info.xtals.remove(xtal)
          self.Refresh()
          break


  def OnMotion(self, evt):
    x,y = evt.GetPosition()

    if self.coord_cb:
      self.coord_cb(x,y)

    if self.action == ACTION_RESIZE:

      if self.resize_dir & RESIZE_L:
        self.resize_xtal[0][0] = x
      elif self.resize_dir & RESIZE_R:
        self.resize_xtal[1][0] = x
      if self.resize_dir & RESIZE_T:
        self.resize_xtal[0][1] = y
      elif self.resize_dir & RESIZE_B:
        self.resize_xtal[1][1] = y

      self.Refresh()

  def OnPaint(self, evt):
    dc = wx.PaintDC(self)
    if self.bitmap:
      dc.DrawBitmap(self.bitmap, 0, 0)

      dc.SetBrush(wx.Brush('#aa0000', wx.TRANSPARENT))
      dc.SetPen(wx.Pen('#33dd33', 1, wx.DOT_DASH))
      for xtal in self.info.xtals:
        (x1,y1), (x2,y2) = xtal
        dc.DrawRectangle(x1,y1,x2-x1,y2-y1)

import wx.lib.mixins.listctrl as listmix

class CalibrationListCtrl(wx.ListCtrl, 
                       listmix.ListCtrlAutoWidthMixin,
                       listmix.TextEditMixin):
  
  def __init__(self, *args, **kwargs):
    wx.ListCtrl.__init__(self, *args, **kwargs)
    listmix.ListCtrlAutoWidthMixin.__init__(self)
    listmix.TextEditMixin.__init__(self)

  def SetStringItem(self, index, column, data, update_store = True):
    wx.ListCtrl.SetStringItem(self, index, column, data)

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

class CalibrationInputPanel(wx.Panel):
  def __init__(self, *args, **kwargs):
    self.info = kwargs['info']
    del(kwargs['info'])

    wx.Panel.__init__(self, *args, **kwargs)

    self.num_energies = 0
    self.num_exposures = 0
    self.num_rows = 0

    vbox = wx.BoxSizer(wx.VERTICAL)

    hbox = wx.BoxSizer(wx.HORIZONTAL)
    label = wx.StaticText(self, wx.ID_ANY, 'Dataset Name:')
    text = wx.TextCtrl(self, wx.ID_ANY, '')
    text.Bind(wx.EVT_TEXT, self.OnDatasetText)
    hbox.Add(label, 0, wx.ALIGN_CENTER_VERTICAL)
    hbox.Add(text, 1)
    vbox.Add(hbox, 0, wx.EXPAND | wx.DOWN, 5)
    self.dataset_textctrl = text


    style = wx.LC_REPORT | wx.LC_HRULES | wx.LC_VRULES
    l = CalibrationListCtrl(self, wx.ID_ANY, style=style)
    l.InsertColumn(0, 'Incident Energy', width=200)
    l.InsertColumn(1, 'Exposure File', width=200)
    self.listctrl = l

    vbox.Add(self.listctrl, 1, wx.EXPAND)

    hbox = wx.BoxSizer(wx.HORIZONTAL)
    b = wx.Button(self, wx.ID_ANY, 'Read Energies...')
    b.Bind(wx.EVT_BUTTON, self.OnLoadEnergies)
    hbox.Add(b, 1)
    b = wx.Button(self, wx.ID_ANY, 'Select Exposures..')
    b.Bind(wx.EVT_BUTTON, self.OnSelectExposures)
    hbox.Add(b, 1)
    vbox.Add(hbox, 0, wx.EXPAND)

    hbox = wx.BoxSizer(wx.HORIZONTAL)
    b = wx.Button(self, wx.ID_ANY, 'Clear Energies')
    b.Bind(wx.EVT_BUTTON, self.OnClearEnergies)
    hbox.Add(b, 1)
    b = wx.Button(self, wx.ID_ANY, 'Clear Exposures')
    b.Bind(wx.EVT_BUTTON, self.OnClearExposures)
    hbox.Add(b, 1)
    vbox.Add(hbox, 0, wx.EXPAND)

    b = wx.Button(self, wx.ID_ANY, 'LOAD')
    b.Bind(wx.EVT_BUTTON, self.OnLoad)
    vbox.Add(b, 0, wx.EXPAND)


    self.SetSizerAndFit(vbox)

    self.load_cb = None

  def OnDatasetText(self, evt):
    self.info.dataset_name = self.dataset_textctrl.GetValue()

  def OnLoad(self, evt):
    if self.load_cb:
      try:
        self.info.energies, self.info.exposure_files = self.listctrl.GetData()
      except ValueError as e:
        dlg = wx.MessageDialog(self, e.message, 'Error', wx.OK | wx.ICON_ERROR)
        dlg.ShowModal()
        dlg.Destroy()
        return

      self.load_cb()

  def AppendEnergy(self, energy):
    s = '%.2f' % energy

    if self.num_energies < self.num_rows:
      self.listctrl.SetStringItem(self.num_energies, 0, s)
    else:
      self.listctrl.InsertStringItem(self.num_rows, s)
      self.num_rows += 1

    self.num_energies += 1

  def AppendExposure(self, path):
    if self.num_exposures >= self.num_rows:
      self.listctrl.InsertStringItem(self.num_rows, '')
      self.num_rows += 1

    self.listctrl.SetStringItem(self.num_exposures, 1, path)
    self.num_exposures += 1

  def OnLoadEnergies(self, evt):
    dlg = LoadEnergiesDialog(None)
    ret = dlg.ShowModal()

    if ret == wx.ID_OK:
      filename, column = dlg.get_info()

      energies = mx.read_scan_info(filename, [column])[0]

      for e in energies:
        self.AppendEnergy(e)

    dlg.Destroy()

  def OnSelectExposures(self, evt):
    global dialog_directory
    dlg = wx.FileDialog(self, 'Select Exposure Files', dialog_directory,
        style=wx.FD_MULTIPLE)
    ret = dlg.ShowModal()
    if ret == wx.ID_OK:
      directory = dlg.GetDirectory()
      dialog_directory = directory
      filenames = dlg.GetFilenames()

      for f in filenames:
        self.AppendExposure(os.path.join(directory, f))

    dlg.Destroy()

  def OnClearEnergies(self, evt):
    for i in range(self.num_rows):
      self.listctrl.SetStringItem(i, 0, '')
    self.num_energies = 0

  def OnClearExposures(self, evt):
    for i in range(self.num_rows):
      self.listctrl.SetStringItem(i, 1, '')
    self.num_exposures = 0

  def OnInfoChanged(self):
    self.OnClearEnergies(None)
    self.OnClearExposures(None)
    
    for e in self.info.energies:
      self.AppendEnergy(e)

    for f in self.info.exposure_files:
      self.AppendExposure(f)

    self.dataset_textctrl.SetValue(self.info.dataset_name)

FILTER_MIN  = 0
FILTER_MAX  = 1
FILTER_LOW  = 2
FILTER_HIGH = 3
FILTER_NBOR = 4

class FilterPanel(wx.Panel):
  filter_names = [
      'Min Visible',
      'Max Visible',
      'Low Cutoff',
      'High Cutoff',
      'Neighbors'
      ]

  def __init__(self, *args, **kwargs):
    self.info = kwargs['info']
    del(kwargs['info'])

    wx.Panel.__init__(self, *args, **kwargs)

    control_info = [
        (self.filter_names[FILTER_MIN],  0,     True),
        (self.filter_names[FILTER_MAX],  1000,  False),
        (self.filter_names[FILTER_LOW],  2,     True),
        (self.filter_names[FILTER_HIGH], 10000, False),
        (self.filter_names[FILTER_NBOR], 1,     True )
      ]

    self.controls = []
    self.filter_cb = None

    grid = wx.FlexGridSizer(len(control_info), 2, 9, 25)

    for text, val, checked in control_info:
      check = wx.CheckBox(self, wx.ID_ANY, text)
      check.SetValue(checked)
      check.Bind(wx.EVT_CHECKBOX, self.OnCheckChange)
      grid.Add(check)

      spin = wx.SpinCtrl(self, wx.ID_ANY, '', max=10000)
      spin.Bind(wx.EVT_SPINCTRL, self.OnSpinChange)
      spin.SetValue(val)
      if not checked:
        spin.Disable()

      self.controls.append((check,spin))

      grid.Add(spin)

    grid.Add(wx.StaticText(self, wx.ID_ANY, 'Dispersive Dir.'))
    combo = wx.ComboBox(self, wx.ID_ANY, style=wx.CB_READONLY, 
        choices=mx.DIRECTION_NAMES)
    combo.Bind(wx.EVT_COMBOBOX, self.OnComboChange)
    grid.Add(combo)
    self.dispersive_combo = combo

    self.SetSizerAndFit(grid)

  def OnCheckChange(self, evt):
    src = evt.GetEventObject()
    for check, spin in self.controls:
      if check == src:
        spin.Enable(check.IsChecked())
        break

    self.UpdateFilters()

  def OnSpinChange(self, evt):
    self.UpdateFilters()

  def OnComboChange(self, evt):
    val = self.dispersive_combo.GetValue()
    if val in mx.DIRECTION_NAMES:
      self.info.dispersive_direction = mx.DIRECTION_NAMES.index(val)
    else:
      self.info.dispersive_direction = -1

  def UpdateFilters(self):
    if self.filter_cb:
      vals = [ (c.IsChecked(), int(s.GetValue())) for c,s in self.controls]
      self.filter_cb(vals)

    self.info.filters = [ (self.filter_names[i], vals[i][1]) for i in range(len(vals)) if vals[i][0] is True ]
      
  def OnLoadExposures(self):
    files = self.info.exposure_files
    i = len(files) / 2
    e1 = mx.Exposure(files[i])
    e2 = mx.Exposure(files[i+1])

    disp = mx.determine_dispersive_direction(e1,e2, sep=30)
    self.info.dispersive_direction = disp
    self.dispersive_combo.SetValue(mx.DIRECTION_NAMES[disp])
    
    self.UpdateFilters()

  def GetFilters(self):
    filters = []
    for i in range(len(self.controls)):
      check, spin = self.controls[i]
      if check.IsChecked():
        filters.append((self.filter_names[i], spin.GetValue()))
    return filters

  def GetDispersiveDir(self):
    return mx.DIRECTION_NAMES.index(self.dispersive_combo.GetValue())

  def OnInfoChanged(self):
    for i in range(len(self.controls)):
      self.controls[i][0].SetValue(False)
      self.controls[i][1].Enable(False)

    for name,val in self.info.filters:
      if name in self.filter_names:
        i = self.filter_names.index(name)
        self.controls[i][0].SetValue(True)
        self.controls[i][1].Enable(True)
        self.controls[i][1].SetValue(val)

    self.dispersive_combo.SetValue(mx.DIRECTION_NAMES[self.info.dispersive_direction])

class CalibrationViewPanel(wx.Panel):
  def __init__(self, *args, **kwargs):
    self.info = kwargs['info']
    del(kwargs['info'])

    wx.Panel.__init__(self, *args, **kwargs)

    self.exposure = mx.Exposure()
    self.filters = None
    self.update_filters_flag = False

    self.Bind(wx.EVT_IDLE, self.OnIdle)

    vbox = wx.BoxSizer(wx.VERTICAL)

    hbox = wx.BoxSizer(wx.HORIZONTAL)
    label = wx.StaticText(self, wx.ID_ANY, 'No Files Loaded')
    hbox.Add(label, 1, wx.EXPAND)
    self.label = label

    label = wx.StaticText(self, wx.ID_ANY, '')
    hbox.Add(label, 0, wx.EXPAND | wx.ALIGN_RIGHT, 10)
    self.coord_label = label

    vbox.Add(hbox, 0, wx.EXPAND)

    image = ImagePanel(self, size=(487,195), info=self.info)
    image.coord_cb = self.OnCoord
    vbox.Add(image, 0)
    self.image = image

    slider = wx.Slider(self, wx.ID_ANY, 1,1,2)
    slider.Bind(wx.EVT_SLIDER, self.OnSlider)
    vbox.Add(slider, 0, wx.EXPAND)
    self.slider = slider

    hbox = wx.BoxSizer(wx.HORIZONTAL)

    b = wx.Button(self, wx.ID_OPEN, "Load Xtals...")
    b.Bind(wx.EVT_BUTTON, self.OnLoadXtals)
    hbox.Add(b)

    b = wx.Button(self, wx.ID_SAVE, "Save Xtals...")
    b.Bind(wx.EVT_BUTTON, self.OnSaveXtals)
    hbox.Add(b)

    b = wx.Button(self, wx.ID_SAVE, "CALIBRATE")
    b.Bind(wx.EVT_BUTTON, self.OnCalibrate)
    hbox.Add(b)

    vbox.Add(hbox, 0, wx.EXPAND)

    self.SetSizerAndFit(vbox)

  def OnLoadExposures(self):
    self.slider.SetMax(len(self.info.exposure_files))
    self.slider.SetMin(1)
    self.slider.SetValue(1)

    self.SetExposureIndex(0)


  def OnCoord(self, x, y):
    if self.exposure.loaded:
      z = self.exposure.raw[y,x]
      s = "(% 3d,% 3d) [% 4d]" % (x,y, z)
      self.coord_label.SetLabel(s)

  def OnSlider(self, evt):
    i = self.slider.GetValue() - 1
    self.SetExposureIndex(i)

  def OnSaveXtals(self, evt):
    global dialog_directory
    dlg = wx.FileDialog(self, 'Save Crystal Boundaries', dialog_directory, style=wx.FD_SAVE)
    ret = dlg.ShowModal()

    if ret == wx.ID_OK:
      directory = dlg.GetDirectory()
      dialog_directory = directory
      filename = dlg.GetFilename()

      path = os.path.join(directory, filename)
      with open(path, 'w') as f:
        f.write("# minIXS crystal boundaries\n")
        f.write("# x1\ty1\tx2\ty2\n")
        for (x1,y1),(x2,y2) in self.image.xtals:
          f.write("%d\t%d\t%d\t%d\n" % (x1,y1,x2,y2))

    dlg.Destroy()

  def OnLoadXtals(self, evt):
    global dialog_directory
    dlg = wx.FileDialog(self, 'Load Crystal Boundaries', dialog_directory, style=wx.FD_OPEN)
    ret = dlg.ShowModal()

    if ret == wx.ID_OK:
      directory = dlg.GetDirectory()
      dialog_directory = directory
      filename = dlg.GetFilename()

      path = os.path.join(directory, filename)

      t = dataset.determine_filetype(path)
      print t

      if t == dataset.FILE_XTALS:
        with open(path) as f:
          xtals = []
          for line in f:
            if line[0] == "#": 
              continue
            x1,y1,x2,y2 = [int(s.strip()) for s in line.split()]
            xtals.append([[x1,y1],[x2,y2]])
          self.info.xtals = xtals

      elif t == dataset.FILE_CALIBRATION:
        ci = CalibrationInfo()
        ci.load(path, header_only=True)
        self.info.xtals = ci.xtals

      else:
        errdlg = wx.MessageDialog(self, "Unkown Filetype", "Error", wx.OK | wx.ICON_ERROR)
        errdlg.ShowModal()
        errdlg.Destroy()

    print self.info.xtals
    self.image.Refresh()
    dlg.Destroy()

  def OnCalibrate(self, evt):
    c = mx.Calibrator(self.info.energies, self.info.exposure_files, self.info.dispersive_direction)

    do_low, low_val = self.filters[FILTER_LOW]
    do_high, high_val = self.filters[FILTER_HIGH]
    do_nbor, nbor_val = self.filters[FILTER_NBOR]
    if not do_low: low_val = None
    if not do_high: high_val = None
    if not do_nbor: nbor_val = 0

    c.filter_images(low_val, high_val, nbor_val, self.image.bad_pixels)
    c.calibrate(self.info.xtals)

    self.info.calibration_matrix = c.calib

  def OnFilterChange(self, values):
    self.filters = values
    self.UpdateFilters()

  def SetExposureIndex(self, i):
    self.exposure_index = i
    self.exposure.load(self.info.exposure_files[i])
    self.UpdateFilters()

    f = os.path.basename(self.info.exposure_files[i])
    text = "%d/%d (%s) %.2f eV" % (i+1, len(self.info.exposure_files), f, self.info.energies[i])
    self.label.SetLabel(text)

  def UpdateFilters(self):
    if not self.exposure or not self.exposure.loaded:
      return
    
    self.update_filters_flag = True

  def OnIdle(self, evt):
    if not self.update_filters_flag:
      return

    self.update_filters_flag = False

    self.exposure.pixels = self.exposure.raw.copy()

    p = self.exposure.pixels
    if self.filters:
      do_min, min_val = self.filters[FILTER_MIN]
      do_max, max_val = self.filters[FILTER_MAX]
      do_low, low_val = self.filters[FILTER_LOW]
      do_high, high_val = self.filters[FILTER_HIGH]
      do_nbor, nbor_val = self.filters[FILTER_NBOR]

      if not do_low: low_val = None
      if not do_high: high_val = None
      if do_low or do_high: self.exposure.filter_low_high(low_val, high_val)

      if do_nbor: self.exposure.filter_neighbors(nbor_val)

      p = self.exposure.pixels
      if not do_min: min_val = p.min()
      if not do_max: max_val = p.max()

      p = colors.Normalize(min_val, max_val)(p)

    self.image.set_pixels(p)

  def OnInfoChanged(self):
    self.Refresh()

class MainPanel(wx.Panel):
  def __init__(self, *args, **kwargs):
    self.info = kwargs['info']
    del(kwargs['info'])

    wx.Panel.__init__(self, *args, **kwargs)

    vbox = wx.BoxSizer(wx.VERTICAL)

    self.input_panel = CalibrationInputPanel(self, info=self.info)
    vbox.Add(self.input_panel, 1, wx.EXPAND | wx.DOWN, 10)

    hbox = wx.BoxSizer(wx.HORIZONTAL)

    filters = FilterPanel(self, wx.ID_ANY, info=self.info)
    hbox.Add(filters, 0)
    self.filter_panel = filters

    self.view_panel = CalibrationViewPanel(self, info=self.info)
    hbox.Add(self.view_panel, 0)

    vbox.Add(hbox, 1, wx.EXPAND)

    border = wx.BoxSizer()
    border.Add(vbox, 1, wx.ALL, 10)

    self.SetSizerAndFit(border)

    self.input_panel.load_cb = self.OnLoadExposures
    filters.filter_cb = self.view_panel.OnFilterChange
    filters.UpdateFilters()

  def OnLoadExposures(self):
    self.view_panel.OnLoadExposures()
    self.filter_panel.OnLoadExposures()

class CalibrationFrame(wx.Frame):
  def __init__(self, *args, **kwargs):

    wx.Frame.__init__(self, *args, **kwargs)
    self.CreateStatusBar()
    self.create_menu_bar()

    self.info = CalibrationInfo()
    self.panel = MainPanel(self, info=self.info)

  def create_menu_bar(self):

    menubar = wx.MenuBar()

    menu = wx.Menu()

    menu_item = menu.Append(wx.ID_OPEN, "&Open...", "Load Calibration Setup")
    self.Bind(wx.EVT_MENU, self.on_load, menu_item)

    menu_item = menu.Append(wx.ID_SAVE, "&Save...", "Save Calibration Setup")
    self.Bind(wx.EVT_MENU, self.on_save, menu_item)


    menu_item = menu.Append(wx.ID_ABOUT, "&About", "Information about minIXS")
    self.Bind(wx.EVT_MENU, self.on_about, menu_item)

    menu.AppendSeparator()
    menu_item = menu.Append(wx.ID_EXIT, "E&xit", "Terminate this program")
    self.Bind(wx.EVT_MENU, self.on_exit, menu_item)
    menubar.Append(menu, "&File")

    self.SetMenuBar(menubar)

  def on_about(self, event):
    dlg = wx.MessageDialog(self, "Data processor for minIXS XES spectra", "About minIXS", wx.OK)
    dlg.ShowModal()
    dlg.Destroy()

  def on_save(self, evt):
    global dialog_directory
    dlg = wx.FileDialog(self, 'Save Calibration Information', dialog_directory, style=wx.FD_SAVE)
    ret = dlg.ShowModal()

    if ret == wx.ID_OK:
      directory = dlg.GetDirectory()
      dialog_directory = directory
      filename = dlg.GetFilename()

      path = os.path.join(directory, filename)

      self.info.save(path)

    dlg.Destroy()

  def on_load(self, evt):
    global dialog_directory
    dlg = wx.FileDialog(self, 'Select calibration file', dialog_directory, style=wx.FD_OPEN)
    ret = dlg.ShowModal()

    if ret == wx.ID_OK:
      d = dlg.GetDirectory()
      dialog_directory = d 
      f = dlg.GetFilename()
      path = os.path.join(d,f)

      try:
        self.info.load(path)
      except InvalidFileError:
        msgdlg = wx.MessageDialog(self, "Invalid file selected", 'Error', wx.OK | wx.ICON_ERROR)
        msgdlg.ShowModal()
        msgdlg.Destroy()
        return

      self.panel.input_panel.OnInfoChanged()
      self.panel.view_panel.OnInfoChanged()
      self.panel.filter_panel.OnInfoChanged()

    dlg.Destroy()

  def on_exit(self, event):
    self.Close(True)

if __name__ == "__main__":
  app = wx.App(False)
  frame = CalibrationFrame(None, wx.ID_ANY, "minIXS processor", size=(800,600))
  frame.Show(True)

  app.MainLoop()
