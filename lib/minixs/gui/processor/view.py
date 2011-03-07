import wx
from wx.lib.scrolledpanel import ScrolledPanel
from minixs import filter
from minixs.gui.frame import MenuFrame
from minixs.gui.image_view import ImageView
from minixs.gui import filter_view

HPAD = 10
VPAD = 5

ID_DATASET = wx.NewId()
ID_ENERGY = wx.NewId()
ID_NORM = wx.NewId()

ID_CALIB = wx.NewId()
ID_CALIB_LOAD = wx.NewId()
ID_CALIB_VIEW = wx.NewId()

ID_EXPOSURE_LIST = wx.NewId()
ID_EXPOSURE_ADD = wx.NewId()
ID_EXPOSURE_DEL = wx.NewId()

ID_EXPOSURE_VIEW = wx.NewId()

ID_FILTER_ADD = wx.NewId()
ID_FILTER_REMOVE= wx.NewId()

ID_VIEW_MODE = wx.NewId()

ID_EXPOSURE_SLIDER = wx.NewId()


class Panel(wx.Panel):
  def __init__(self, *args, **kwargs):
    wx.Panel.__init__(self, *args, **kwargs)

class ViewModePanel(wx.Panel):
  def __init__(self, *args, **kwargs):
    wx.Panel.__init__(self, *args, **kwargs)

    vbox = wx.BoxSizer(wx.VERTICAL)

    choices = ['Combined Exposures', 'Individual Exposures', 'Calibration Matrix', 'Processed Spectrum']
    radio = wx.RadioBox(self, wx.ID_ANY, 'View', choices=choices,
        majorDimension=1)
    vbox.Add(radio, 0, wx.EXPAND | wx.BOTTOM, VPAD)

    self.SetSizerAndFit(vbox)


class FilterPanel(wx.Panel):
  def __init__(self, *args, **kwargs):
    wx.Panel.__init__(self, *args, **kwargs)

    vbox = wx.BoxSizer(wx.VERTICAL)

    label = wx.StaticText(self, wx.ID_ANY, 'Filters:')
    vbox.Add(label, 0, wx.EXPAND | wx.BOTTOM, VPAD)

    filter_list = FilterList(self, wx.ID_ANY, style=wx.BORDER_SUNKEN)
    vbox.Add(filter_list, 1, wx.EXPAND | wx.BOTTOM, VPAD)
    self.filter_list = filter_list

    filter_names = [f[0].name for f in filter_view.REGISTRY]
    filter_choice = wx.Choice(self, wx.ID_ANY, choices=filter_names)
    self.filter_choice = filter_choice
    vbox.Add(filter_choice, 0, wx.EXPAND | wx.BOTTOM, VPAD)

    hbox = wx.BoxSizer(wx.HORIZONTAL)

    button = wx.Button(self, ID_FILTER_ADD, 'Add Filter')
    hbox.Add(button, 1, wx.EXPAND | wx.RIGHT, HPAD)

    button = wx.Button(self, ID_FILTER_REMOVE, 'Remove Filter')
    hbox.Add(button, 1, wx.EXPAND | wx.RIGHT, HPAD)

    vbox.Add(hbox, 0, wx.EXPAND | wx.BOTTOM, VPAD)

    self.Bind(wx.EVT_BUTTON, self.OnButton)

    self.SetSizerAndFit(vbox)

    self.i = 0

  def OnButton(self, evt):
    print evt.Id
    if evt.Id == ID_FILTER_ADD:
      i = self.filter_choice.GetSelection()
      self.filter_list.AddFilter(i % len(filter_view.REGISTRY))
    else:
      self.filter_list.RemoveFilter(0)

class FilterList(ScrolledPanel):
  def __init__(self, *args, **kwargs):
    ScrolledPanel.__init__(self, *args, **kwargs)

    self.grid = wx.FlexGridSizer(cols=2, vgap=VPAD, hgap=HPAD)
    self.SetSizer(self.grid)

    self.filter_views = []
    self.SetAutoLayout(True)
    self.SetupScrolling(False, True)


  def AddFilter(self, index):
    fltr, view_class, id = filter_view.REGISTRY[index]
    label = wx.StaticText(self, wx.ID_ANY, fltr.name)
    view = view_class(self, id, filter=fltr)

    self.filter_views.append((label,view))
    self.grid.Add(label, wx.ALIGN_CENTER_VERTICAL)
    self.grid.Add(view, wx.ALIGN_CENTER_VERTICAL)
    self.SetupScrolling(False, True)

  def RemoveFilter(self, index):
    label,view = self.filter_views[index]
    del(self.filter_views[index])
    self.grid.Remove(label)
    self.grid.Remove(view)
    label.Destroy()
    view.Destroy()
    self.SetupScrolling(False, True)


class ExposureView(wx.Panel):
  def __init__(self, *args, **kwargs):
    wx.Panel.__init__(self, *args, **kwargs)

    vbox = wx.BoxSizer(wx.VERTICAL)

    self.image_view = ImageView(self, ID_EXPOSURE_VIEW, size=(487,195), style=wx.BORDER_SUNKEN)
    vbox.Add(self.image_view, wx.EXPAND)

    slider = wx.Slider(self, ID_EXPOSURE_SLIDER, 0,0,1)
    slider.Enable(False)
    vbox.Add(slider, 0, wx.EXPAND)

    self.SetSizerAndFit(vbox)


class ExposureSelectorPanel(wx.Panel):
  def __init__(self, *args, **kwargs):
    wx.Panel.__init__(self, *args, **kwargs)

    vbox = wx.BoxSizer(wx.VERTICAL)

    # exposure selector
    label = wx.StaticText(self, wx.ID_ANY, "Exposures:")
    vbox.Add(label, 0, wx.BOTTOM, VPAD)

    listbox = wx.ListBox(self, ID_EXPOSURE_LIST)
    vbox.Add(listbox, 1, wx.EXPAND | wx.BOTTOM, VPAD)
    self.exposure_listbox = listbox

    hbox = wx.BoxSizer(wx.HORIZONTAL)
    button = wx.Button(self, ID_EXPOSURE_ADD, "Add...")
    hbox.Add(button, 0, wx.RIGHT, HPAD)
    button = wx.Button(self, ID_EXPOSURE_DEL, "Delete Selected")
    hbox.Add(button, 0, 0, HPAD)

    vbox.Add(hbox, 0, wx.EXPAND | wx.BOTTOM, VPAD)

    self.SetSizerAndFit(vbox)

class InfoPanel(wx.Panel):
  def __init__(self, *args, **kwargs):
    wx.Panel.__init__(self, *args, **kwargs)

    vbox = wx.BoxSizer(wx.VERTICAL)
    grid = wx.FlexGridSizer(3,2, VPAD, HPAD)

    label = wx.StaticText(self, wx.ID_ANY, "Dataset Name:")
    entry = wx.TextCtrl(self, ID_DATASET)
    grid.Add(label, 1, wx.ALIGN_CENTER_VERTICAL)
    grid.Add(entry, 1, wx.EXPAND)
    self.dataset_entry = entry

    label = wx.StaticText(self, wx.ID_ANY, "Incident Energy:")
    entry = wx.TextCtrl(self, ID_ENERGY)
    grid.Add(label, 1, wx.ALIGN_CENTER_VERTICAL)
    grid.Add(entry, 1, wx.EXPAND)
    self.energy_entry = entry

    label = wx.StaticText(self, wx.ID_ANY, "Normalization (I0):")
    entry = wx.TextCtrl(self, ID_NORM)
    grid.Add(label, 1, wx.ALIGN_CENTER_VERTICAL)
    grid.Add(entry, 1, wx.EXPAND)
    self.norm_entry = entry

    grid.AddGrowableCol(1, 1)

    vbox.Add(grid, 0, wx.EXPAND | wx.BOTTOM, VPAD)

    # calibration matrix info
    hbox = wx.BoxSizer(wx.HORIZONTAL)
    label = wx.StaticText(self, wx.ID_ANY, "Calibration Matrix:")
    hbox.Add(label, 1, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, HPAD)

    entry = wx.TextCtrl(self, ID_CALIB, style=wx.TE_READONLY)
    hbox.Add(entry, 2, wx.EXPAND | wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, HPAD)
    self.calibration_file_entry = entry

    button = wx.Button(self, ID_CALIB_LOAD, "...")
    hbox.Add(button, 0, 0, HPAD)
    self.load_calibration_button = button

    """
    button = wx.Button(self, ID_CALIB_VIEW, "View")
    hbox.Add(button, 0, 0, HPAD)
    self.view_calibration_button = button
    """

    vbox.Add(hbox, 0, wx.EXPAND | wx.BOTTOM, VPAD)

    self.SetSizerAndFit(vbox)

class ProcessorPanel(wx.Panel):
  def __init__(self, *args, **kwargs):
    wx.Panel.__init__(self, *args, **kwargs)

    vbox = wx.BoxSizer(wx.VERTICAL)

    # first row
    hbox = wx.BoxSizer(wx.HORIZONTAL)

    info = InfoPanel(self, wx.ID_ANY)
    hbox.Add(info, 3, wx.EXPAND | wx.RIGHT, HPAD)

    line = wx.StaticLine(self, wx.ID_ANY, style=wx.LI_VERTICAL)
    hbox.Add(line, 0, wx.EXPAND | wx.RIGHT, HPAD)

    exposure_selector = ExposureSelectorPanel(self, wx.ID_ANY)
    hbox.Add(exposure_selector, 2, wx.EXPAND | wx.RIGHT, HPAD)

    vbox.Add(hbox, 1, wx.EXPAND | wx.BOTTOM, VPAD)

    line = wx.StaticLine(self, wx.ID_ANY, style=wx.LI_HORIZONTAL)
    vbox.Add(line, 0, wx.EXPAND | wx.BOTTOM, VPAD)
    
    # second row
    hbox = wx.BoxSizer(wx.HORIZONTAL)

    filter_panel = FilterPanel(self, wx.ID_ANY)
    hbox.Add(filter_panel, 1, wx.EXPAND | wx.RIGHT, HPAD)

    exposure_view = ExposureView(self, wx.ID_ANY)
    hbox.Add(exposure_view, 0, wx.EXPAND | wx.RIGHT, HPAD)

    mode_panel = ViewModePanel(self, ID_VIEW_MODE)
    hbox.Add(mode_panel, 0, wx.EXPAND | wx.RIGHT, HPAD)

    vbox.Add(hbox, 0, wx.EXPAND | wx.BOTTOM, VPAD)

    self.SetSizerAndFit(vbox)


class ProcessorView(MenuFrame):
  def __init__(self, *args, **kwargs):
    kwargs['menu_info'] = [
        ('&File', [
          ('&Open...', wx.ID_OPEN, 'Load Emission Spectrum'),
          ('&Save...', wx.ID_SAVE, 'Save Emission Spectrum'),
          ('', None, None),
          ('E&xit', wx.ID_EXIT, 'Terminate this program'),
          ]),
        ('&Help', [
          ('&About', wx.ID_ABOUT, 'About this program'),
          ])
        ]
    MenuFrame.__init__(self, *args, **kwargs)
    bar = self.CreateStatusBar()
    bar.SetFieldsCount(2)
    bar.SetStatusWidths([-1,-3])

    box = wx.BoxSizer(wx.VERTICAL)
    self.panel = ProcessorPanel(self, wx.ID_ANY)
    print "view"
    box.Add(self.panel, 1, wx.EXPAND | wx.LEFT | wx.TOP, HPAD)

    self.SetSizerAndFit(box)
