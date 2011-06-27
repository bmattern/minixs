import wx

from wx.lib.scrolledpanel import ScrolledPanel
from minixs import filter
from minixs import spectrometer
from minixs.gui.frame import MenuFrame
from minixs.gui.image_view import ImageView
from minixs.gui import filter_view

from const import *

import matplotlib
matplotlib.use('WXAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import \
    FigureCanvasWxAgg as FigureCanvas,  \
    NavigationToolbar2WxAgg

HPAD = 10
VPAD = 5


class Panel(wx.Panel):
  def __init__(self, *args, **kwargs):
    wx.Panel.__init__(self, *args, **kwargs)

class ToolsPanel(wx.Panel):
  def __init__(self, *args, **kwargs):
    wx.Panel.__init__(self, *args, **kwargs)

    vbox = wx.BoxSizer(wx.VERTICAL)

    self.pages = []
    page = ToolsPanelCombined(self, wx.ID_ANY)
    self.pages.append(page)
    self.combined_min = page.min
    self.combined_max = page.max
    self.selected_page = page
    vbox.Add(page, 1, wx.EXPAND)

    page = ToolsPanelIndividual(self, wx.ID_ANY)
    self.pages.append(page)
    self.individual_min = page.min
    self.individual_max = page.max
    self.individual_exp = page.exp
    page.Hide()
    vbox.Add(page, 1, wx.EXPAND)

    self.vbox = vbox
    self.SetSizerAndFit(vbox)

  def SetMode(self, mode):
    self.mode = mode

    if self.selected_page:
      self.selected_page.Hide()

    if mode < len(self.pages):
      page = self.pages[mode]
      page.Show()
    else:
      page = None

    self.selected_page = page

    self.Layout()
    self.Fit()
    self.SetMinSize(self.GetSize())

class ToolsPanelCombined(wx.Panel):
  def __init__(self, *args, **kwargs):
    wx.Panel.__init__(self, *args, **kwargs)

    grid = wx.FlexGridSizer(cols=2, vgap=VPAD, hgap=HPAD)

    label = wx.StaticText(self, wx.ID_ANY, 'Min')
    spin = wx.SpinCtrl(self, ID_COMBINED_MIN)
    spin.SetRange(0,32768)
    grid.Add(label)
    grid.Add(spin)
    self.min = spin

    label = wx.StaticText(self, wx.ID_ANY, 'Max')
    spin = wx.SpinCtrl(self, ID_COMBINED_MAX)
    spin.SetRange(0,32768)
    grid.Add(label)
    grid.Add(spin)
    self.max = spin

    self.SetSizerAndFit(grid)

class ToolsPanelIndividual(wx.Panel):
  def __init__(self, *args, **kwargs):
    wx.Panel.__init__(self, *args, **kwargs)

    grid = wx.FlexGridSizer(cols=2, vgap=VPAD, hgap=HPAD)

    label = wx.StaticText(self, wx.ID_ANY, 'Min')
    spin = wx.SpinCtrl(self, ID_INDIVIDUAL_MIN)
    spin.SetRange(0,32768)
    grid.Add(label)
    grid.Add(spin)
    self.min = spin

    label = wx.StaticText(self, wx.ID_ANY, 'Max')
    spin = wx.SpinCtrl(self, ID_INDIVIDUAL_MAX)
    spin.SetRange(0,32768)
    grid.Add(label)
    grid.Add(spin)
    self.max = spin

    label = wx.StaticText(self, wx.ID_ANY, 'Exp #')
    spin = wx.SpinCtrl(self, ID_INDIVIDUAL_EXP)
    spin.SetRange(0,0)
    grid.Add(label)
    grid.Add(spin)
    self.exp = spin

    self.SetSizerAndFit(grid)

class ViewModePanel(wx.Panel):
  def __init__(self, *args, **kwargs):
    wx.Panel.__init__(self, *args, **kwargs)

    vbox = wx.BoxSizer(wx.VERTICAL)

    choices = ['Combined Exposures', 'Individual Exposures', 'Calibration Matrix', 'Processed Spectrum']
    radio = wx.RadioBox(self, ID_VIEW_MODE, 'View', choices=choices,
        majorDimension=1)
    vbox.Add(radio, 0, wx.EXPAND | wx.BOTTOM, VPAD)
    self.view_mode = radio

    tools = ToolsPanel(self, wx.ID_ANY)
    vbox.Add(tools, 0, wx.EXPAND | wx.BOTTOM, VPAD)
    self.tools = tools

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
    elif evt.Id == ID_FILTER_REMOVE:
      self.filter_list.RemoveFilter(0)

class FilterList(ScrolledPanel):
  def __init__(self, *args, **kwargs):
    ScrolledPanel.__init__(self, *args, **kwargs)

    self.grid = wx.FlexGridSizer(cols=4, vgap=VPAD, hgap=HPAD)
    #self.grid.AddGrowableCol(2, 1)
    self.SetSizer(self.grid)

    self.filter_views = []
    self.SetAutoLayout(True)
    self.SetupScrolling(True, True)


  def AddFilter(self, index):
    fltr, view_class, id = filter_view.REGISTRY[index]
    label = wx.StaticText(self, wx.ID_ANY, fltr.name)
    view = view_class(self, id, filter=fltr)

    b = wx.Button(self, wx.ID_ANY, 'X', size=(20, 20))
    sb = wx.SpinButton(self, wx.ID_ANY, style=wx.SP_VERTICAL)

    self.grid.Add(sb, wx.ALIGN_CENTER_VERTICAL)
    self.grid.Add(label, wx.ALIGN_CENTER_VERTICAL)
    self.grid.Add(view, wx.ALIGN_CENTER_VERTICAL)
    self.grid.Add(b, wx.ALIGN_CENTER_VERTICAL)

    self.filter_views.append((b,sb,label,view))

    self.SetupScrolling(False, True)

  def RemoveFilter(self, index):
    for w in self.filter_views[index]:
      self.grid.Remove(w)
      w.Destroy()
    del(self.filter_views[index])
    self.SetupScrolling(False, True)


class ExposureView(wx.Panel):
  def __init__(self, *args, **kwargs):
    wx.Panel.__init__(self, *args, **kwargs)

    vbox = wx.BoxSizer(wx.VERTICAL)

    self.image_view = ImageView(self, ID_EXPOSURE_VIEW, size=(487,195), style=wx.BORDER_SUNKEN)
    vbox.Add(self.image_view, 1, wx.EXPAND)

    self.figure = Figure()
    self.plot = FigureCanvas(self, wx.ID_ANY, self.figure)
    self.plot.SetSize((487,195))
    self.plot.SetWindowStyle(wx.BORDER_SUNKEN)
    vbox.Add(self.plot, 1, wx.EXPAND)
    self.plot.Hide()

    self.toolbar = NavigationToolbar2WxAgg(self.plot)
    vbox.Add(self.toolbar, 0, wx.EXPAND)
    self.plot.Hide()

    self.SetSizerAndFit(vbox)

  def SetViewMode(self, mode):
    if mode == VIEW_MODE_SPECTRUM:
      self.image_view.Hide()
      self.plot.Show()
      self.toolbar.Show()
    else:
      self.image_view.Show()
      self.plot.Hide()
      self.toolbar.Hide()

    self.Layout()

class ExposureSelectorPanel(wx.Panel):
  def __init__(self, *args, **kwargs):
    wx.Panel.__init__(self, *args, **kwargs)

    vbox = wx.BoxSizer(wx.VERTICAL)

    # exposure selector
    label = wx.StaticText(self, wx.ID_ANY, "Exposures:")
    vbox.Add(label, 0, wx.BOTTOM, VPAD)

    listbox = wx.ListBox(self, ID_EXPOSURE_LIST, style=wx.LB_EXTENDED)
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


    label = wx.StaticText(self, wx.ID_ANY, "Spectrometer:")
    choice = wx.Choice(self, ID_SPECTROMETER)
    grid.Add(label, 1, wx.ALIGN_CENTER_VERTICAL)
    grid.Add(choice, 1, wx.EXPAND)
    self.spectrometer_choice = choice

    grid.AddGrowableCol(1, 1)

    vbox.Add(grid, 0, wx.EXPAND | wx.BOTTOM, VPAD)

    # calibration matrix info
    hbox = wx.BoxSizer(wx.HORIZONTAL)
    label = wx.StaticText(self, wx.ID_ANY, "Calibration Matrix:")
    hbox.Add(label, 1, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, HPAD)

    entry = wx.TextCtrl(self, ID_CALIB, style=wx.TE_READONLY)
    entry.SetEditable(False)
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
    hbox.Add(info, 0, wx.EXPAND | wx.RIGHT, HPAD)

    line = wx.StaticLine(self, wx.ID_ANY, style=wx.LI_VERTICAL)
    hbox.Add(line, 0, wx.EXPAND | wx.RIGHT, HPAD)

    exposure_selector = ExposureSelectorPanel(self, wx.ID_ANY)
    self.exposure_listbox = exposure_selector.exposure_listbox
    hbox.Add(exposure_selector, 2, wx.EXPAND | wx.RIGHT, HPAD)

    vbox.Add(hbox, 1, wx.EXPAND | wx.BOTTOM, VPAD)

    line = wx.StaticLine(self, wx.ID_ANY, style=wx.LI_HORIZONTAL)
    vbox.Add(line, 0, wx.EXPAND | wx.BOTTOM, VPAD)
    
    # second row
    hbox = wx.BoxSizer(wx.HORIZONTAL)

    #filter_panel = FilterPanel(self, wx.ID_ANY)
    #hbox.Add(filter_panel, 1, wx.EXPAND | wx.RIGHT, HPAD)

    exposure_view = ExposureView(self, wx.ID_ANY)

    self.dataset_entry = info.dataset_entry
    self.energy_entry = info.energy_entry
    self.norm_entry = info.norm_entry
    self.spectrometer_choice = info.spectrometer_choice
    self.calibration_file_entry = info.calibration_file_entry

    self.image_view = exposure_view.image_view
    self.plot = exposure_view.plot
    self.exposure_view = exposure_view
    self.figure = exposure_view.figure
    hbox.Add(exposure_view, 1, wx.EXPAND | wx.RIGHT, HPAD)

    mode_panel = ViewModePanel(self, ID_VIEW_MODE)
    hbox.Add(mode_panel, 0, wx.EXPAND | wx.RIGHT, HPAD)
    self.view_mode = mode_panel.view_mode
    self.tools = mode_panel.tools

    vbox.Add(hbox, 2, wx.EXPAND | wx.BOTTOM, VPAD)

    b = wx.Button(self, ID_PROCESS, 'Process Spectrum')
    vbox.Add(b, 0, wx.EXPAND | wx.BOTTOM, VPAD)
    self.process_button = b


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
    panel = ProcessorPanel(self, wx.ID_ANY)
    print "view"
    box.Add(panel, 1, wx.EXPAND | wx.LEFT | wx.TOP, HPAD)

    self.dataset_entry = panel.dataset_entry
    self.energy_entry = panel.energy_entry
    self.norm_entry = panel.norm_entry
    self.calibration_file_entry = panel.calibration_file_entry
    self.spectrometer_choice = panel.spectrometer_choice

    self.exposure_listbox = panel.exposure_listbox
    self.image_view = panel.image_view
    self.view_mode = panel.view_mode
    self.tools = panel.tools
    self.plot = panel.plot
    self.exposure_view = panel.exposure_view
    self.figure = panel.figure
    self.axes = self.figure.add_axes([.1,.1,.8,.8])

    self.SetSizerAndFit(box)

  def SetExposureCount(self, num):
    self.tools.individual_exp.SetRange(1, num)

  def SetIndividualMinMax(self, min, max):
    self.tools.individual_min.SetInt(min)
    self.tools.individual_max.SetInt(max)

  def SetCombinedMinMax(self, min, max):
    self.tools.combined_min.SetInt(min)
    self.tools.combined_max.SetInt(max)

  def SetViewMode(self, mode):
    self.tools.SetMode(mode)
    self.exposure_view.SetViewMode(mode)
    self.view_mode.SetSelection(mode)

  def SetSpectrometer(self, index):
    self.spectrometer_choice.SetSelection(index)

  def SetSpectrometerNames(self, names):
    self.spectrometer_choice.SetItems(names)

