import wx
import minixs
from matplotlib import cm
import os, sys

dialog_directory = ''

def read_scan_column_names(scanfile):
  with open(scanfile) as f:
    last = None

    for line in f:
      if line[0] != "#":
        num = len(line.split())

        if last is None:
          num = len(line.split())
          return [ str(i) for i in range(1,num+1) ]

        else:
          last = last[1:]
          cols = last.split()

          # if whitespace separated headers aren't correct, try fixed width
          if len(cols) != num:
            w = 20
            cols = [ last[w*i:w*(i+1)].strip() for i in range(0,len(last)/20) ]
          if len(cols) != num:
            return [ str(i) for i in range(1,num+1) ]

          return [ "%d: %s" % (i,s) for i,s in zip(range(1,num+1), cols) ]

      last = line

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

  def fill_column_names(self):
    columns = read_scan_column_names(os.path.join(self.directory, self.filename))
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

    self.add_cb = None
    self.cancel_cb = None

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

  def set_add_cb(self, add_cb):
    self.add_cb = add_cb

  def set_cancel_cb(self, cancel_cb):
    self.cancel_cb = cancel_cb

  def OnAdd(self, evt):
    filename, column = self.panel.get_info()

    if self.add_cb:
      self.add_cb(filename, column)

  def OnCancel(self, evt):
    if self.cancel_cb:
      self.cancel_cb()

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
    wx.Panel.__init__(self, *args, **kwargs)
    self.bitmap = None

    self.SetEvtHandlerEnabled(True)

    self.xtals = []
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
    p = (cm.Greys_r(pixels)[:,:,0:3] * 255).astype('uint8')
    self.bitmap = wx.BitmapFromBuffer(w, h, p.tostring())
    self.Refresh()

  def set_xtals(self, xtals):
    self.xtals = xtals
    self.Refresh()

  def OnLeftDown(self, evt):
    if self.action == ACTION_NONE:
      x,y = evt.GetPosition()

      off = 4
      resize_dir = 0

      for xtal in self.xtals:
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
        self.xtals.append(xtal)
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
      for xtal in self.xtals:
        x,y = evt.GetPosition()
        (x1,y1), (x2,y2) = xtal

        if x1 <= x <= x2 and y1 <= y <= y2:
          self.xtals.remove(xtal)
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
      for xtal in self.xtals:
        (x1,y1), (x2,y2) = xtal
        dc.DrawRectangle(x1,y1,x2-x1,y2-y1)

class CalibrationInputPanel(wx.Panel):
  def __init__(self, *args, **kwargs):
    wx.Panel.__init__(self, *args, **kwargs)

    vbox = wx.BoxSizer(wx.VERTICAL)

    style = wx.LC_REPORT | wx.LC_HRULES | wx.LC_VRULES
    l = wx.ListCtrl(self, wx.ID_ANY, style=style)
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

    self.num_energies = 0
    self.num_exposures = 0
    self.num_rows = 0
    self.energies = []
    self.exposures = []


    # XXX for testing only

    energies = [ 7604.99256633,  7609.99840914,  7615.01108544,  7620.00586552,
        7625.00743927,  7629.99100963,  7635.00617806,  7640.00330303,
        7645.00720891,  7649.99296363,  7655.01043838,  7660.00972158,
        7664.99072539,  7670.00352365,  7674.99800186,  7679.99922059,
        7685.00719331,  7689.99671692]
    for e in energies:
      self.AppendEnergy(e)

    for f in minixs.gen_file_list('calib2_', range(1,19), 5):
      self.AppendExposure('data', f)

  def OnLoad(self, evt):
    if self.load_cb:
      self.load_cb(self.energies, self.exposures)

  def AppendEnergy(self, energy):
    self.energies.append(energy)
    s = '%.2f' % energy

    if self.num_energies < self.num_rows:
      self.listctrl.SetStringItem(self.num_energies, 0, s)
    else:
      self.listctrl.InsertStringItem(self.num_rows, s)
      self.num_rows += 1

    self.num_energies += 1

  def AppendExposure(self, directory, filename):
    self.exposures.append((directory, filename))
    
    if self.num_exposures >= self.num_rows:
      self.listctrl.InsertStringItem(self.num_rows, '')
      self.num_rows += 1

    self.listctrl.SetStringItem(self.num_exposures, 1, filename)
    self.num_exposures += 1

  def OnLoadEnergies(self, evt):
    dlg = LoadEnergiesDialog(None)
    ret = dlg.ShowModal()

    if ret == wx.ID_OK:
      filename, column = dlg.get_info()

      energies = minixs.read_scan_info(filename, [column])[0]

      for e in energies:
        #s = '%.2f' % e
        #self.listctrl.InsertStringItem(sys.maxint, s)
        self.AppendEnergy(e)

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
        self.AppendExposure(directory, f)

  def OnClearEnergies(self, evt):
    for i in range(self.num_rows):
      self.listctrl.SetStringItem(i, 0, '')
    self.energies = []
    self.num_energies = 0

  def OnClearExposures(self, evt):
    for i in range(self.num_rows):
      self.listctrl.SetStringItem(i, 1, '')
    self.exposures = []
    self.num_exposures = 0

class FilterPanel(wx.Panel):

  def __init__(self, *args, **kwargs):
    wx.Panel.__init__(self, *args, **kwargs)

    controls = [
        ('Min Visible',  self.OnMinChange,       0,     True),
        ('Max Visible',  self.OnMaxChange,       1000,  False),
        ('Low Cutoff',   self.OnLowChange,       0,     False),
        ('High Cutoff',  self.OnHighChange,      10000, False),
        ('Neighbors',    self.OnNeighborsChange, 1,     True )
      ]

    grid = wx.FlexGridSizer(len(controls), 2, 9, 25)

    self.controls = []

    for text, cb, val, checked in controls:
      check = wx.CheckBox(self, wx.ID_ANY, text)
      check.SetValue(checked)
      check.Bind(wx.EVT_CHECKBOX, self.OnCheckChange)
      grid.Add(check)

      spin = wx.SpinCtrl(self, wx.ID_ANY, '')
      spin.Bind(wx.EVT_SPIN, cb)
      spin.SetValue(val)
      if not checked:
        spin.Disable()

      self.controls.append((check,spin))

      grid.Add(spin)


    self.SetSizerAndFit(grid)

  def OnCheckChange(self, evt):
    src = evt.GetEventObject()
    for check, spin in self.controls:
      if check == src:
        spin.Enable(check.IsChecked())
        break

  def OnMinChange(self, evt):
    self.OnControlChange(check,spin)

  def OnMaxChange(self, evt):
    self.OnControlChange(check,spin)

  def OnLowChange(self, evt):
    self.OnControlChange(check,spin)

  def OnHighChange(self, evt):
    self.OnControlChange(check,spin)

  def OnNeighborsChange(self, evt):
    self.OnControlChange(check,spin)

class CalibrationViewPanel(wx.Panel):
  def __init__(self, *args, **kwargs):
    wx.Panel.__init__(self, *args, **kwargs)

class MainPanel(wx.Panel):
  def __init__(self, *args, **kwargs):
    wx.Panel.__init__(self, *args, **kwargs)

    self.exposure = minixs.Exposure()

    vbox = wx.BoxSizer(wx.VERTICAL)

    self.input_panel = CalibrationInputPanel(self)
    self.input_panel.load_cb = self.OnLoad
    vbox.Add(self.input_panel, 1, wx.EXPAND)
  
    hbox = wx.BoxSizer(wx.HORIZONTAL)

    label = wx.StaticText(self, wx.ID_ANY, 'No Files Loaded')
    hbox.Add(label, 1, wx.EXPAND)
    self.label = label

    label = wx.StaticText(self, wx.ID_ANY, '')
    hbox.Add(label, 0, wx.EXPAND | wx.ALIGN_RIGHT)
    self.coord_label = label

    vbox.Add(hbox, 0, wx.EXPAND)

    image = ImagePanel(self, size=(487,195))
    image.coord_cb = self.OnCoord
    vbox.Add(image, 1, wx.EXPAND)
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

    filters = FilterPanel(self, wx.ID_ANY)
    vbox.Add(filters, 1, wx.EXPAND)

    self.SetSizerAndFit(vbox)

  def OnCoord(self, x, y):
    s = "(% 3d,% 3d)" % (x,y)
    self.coord_label.SetLabel(s)

  def OnLoad(self, energies, files):
    self.energies = energies
    self.files = files

    self.slider.SetMax(len(self.files))
    self.slider.SetMin(1)
    self.slider.SetValue(1)

    self.SetExposureIndex(0)

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
        f.write("# minIXS Crystal Boundary definitions\n")
        f.write("# x1\ty1\tx2\ty2\n")
        for (x1,y1),(x2,y2) in self.image.xtals:
          f.write("%d\t%d\t%d\t%d\n" % (x1,y1,x2,y2))

  def OnLoadXtals(self, evt):
    global dialog_directory
    dlg = wx.FileDialog(self, 'Load Crystal Boundaries', dialog_directory, style=wx.FD_OPEN)
    ret = dlg.ShowModal()

    if ret == wx.ID_OK:
      directory = dlg.GetDirectory()
      dialog_directory = directory
      filename = dlg.GetFilename()

      path = os.path.join(directory, filename)
      with open(path) as f:
        xtals = []
        for line in f:
          if line[0] == "#": 
            continue
          x1,y1,x2,y2 = [int(s.strip()) for s in line.split()]
          xtals.append([[x1,y1],[x2,y2]])
        self.image.set_xtals(xtals)

  def OnCalibrate(self, evt):
    pass

  def SetExposureIndex(self, i):
    d,f = self.files[i]
    self.exposure.load(os.path.join(d,f))
    self.image.set_pixels(self.exposure.pixels)

    text = "%d/%d (%s) %.2f eV" % (i+1, len(self.files), f, self.energies[i])
    self.label.SetLabel(text)

class MainFrame(wx.Frame):
  def __init__(self, *args, **kwargs):

    wx.Frame.__init__(self, *args, **kwargs)
    self.CreateStatusBar()
    self.create_menu_bar()

    self.panel = MainPanel(self)

  def create_menu_bar(self):

    menubar = wx.MenuBar()

    menu = wx.Menu()
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

  def on_exit(self, event):
    self.Close(True)
    

if __name__ == "__main__":
  app = wx.App(False)
  frame = MainFrame(None, wx.ID_ANY, "minIXS processor", size=(500,800))
  frame.Show(True)

  app.MainLoop()