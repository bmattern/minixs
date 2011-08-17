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

    #grid = wx.FlexGridSizer(cols=2, vgap=VPAD, hgap=HPAD)
    grid = wx.GridBagSizer(vgap=VPAD, hgap=HPAD)

    label = wx.StaticText(self, wx.ID_ANY, 'Min')
    spin = wx.SpinCtrl(self, ID_INDIVIDUAL_MIN)
    spin.SetRange(0,32768)
    grid.Add(label, (0,0))
    grid.Add(spin, (0,1))
    self.min = spin

    label = wx.StaticText(self, wx.ID_ANY, 'Max')
    spin = wx.SpinCtrl(self, ID_INDIVIDUAL_MAX)
    spin.SetRange(0,32768)
    grid.Add(label, (1,0))
    grid.Add(spin, (1,1))
    self.max = spin

    label = wx.StaticText(self, wx.ID_ANY, 'Exp #')
    spin = wx.SpinCtrl(self, ID_INDIVIDUAL_EXP)
    spin.SetRange(0,0)
    grid.Add(label, (2,0))
    grid.Add(spin, (2,1))
    self.exp = spin

    choices = ['Circle', 'Rectangle']
    radio = wx.RadioBox(self, ID_SELECT_MODE, 'Selection Type:', choices=choices, majorDimension=1)
    grid.Add(radio, (3,0), span=(1,2), flag=wx.EXPAND)
    self.view_mode = radio

    label = wx.StaticText(self, wx.ID_ANY, 'Radius:')
    spin = wx.SpinCtrl(self, ID_CIRCLE_RADIUS)
    spin.SetRange(2,100)
    grid.Add(label, (4,0))
    grid.Add(spin, (4,1))
    self.radius_spin = spin

    self.SetSizerAndFit(grid)

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

class KillzonePanel(wx.Panel):
  def __init__(self, *args, **kwargs):
    wx.Panel.__init__(self, *args, **kwargs)

    vbox = wx.BoxSizer(wx.VERTICAL)

    # first row
    exposure_selector = ExposureSelectorPanel(self, wx.ID_ANY)
    self.exposure_listbox = exposure_selector.exposure_listbox

    vbox.Add(exposure_selector, 1, wx.EXPAND | wx.BOTTOM, VPAD)

    line = wx.StaticLine(self, wx.ID_ANY, style=wx.LI_HORIZONTAL)
    vbox.Add(line, 0, wx.EXPAND | wx.BOTTOM, VPAD)
    
    # second row
    hbox = wx.BoxSizer(wx.HORIZONTAL)

    #filter_panel = FilterPanel(self, wx.ID_ANY)
    #hbox.Add(filter_panel, 1, wx.EXPAND | wx.RIGHT, HPAD)

    image_view = ImageView(self, ID_EXPOSURE_VIEW, size=(487,195), style=wx.BORDER_SUNKEN)

    self.image_view = image_view
    hbox.Add(image_view, 1, wx.EXPAND | wx.RIGHT, HPAD)

    tools_panel= ToolsPanel(self, wx.ID_ANY)
    hbox.Add(tools_panel, 0, wx.EXPAND | wx.RIGHT, HPAD)
    self.tools = tools_panel

    vbox.Add(hbox, 2, wx.EXPAND | wx.BOTTOM, VPAD)

    self.SetSizerAndFit(vbox)


class KillzoneView(MenuFrame):
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
    panel = KillzonePanel(self, wx.ID_ANY)
    box.Add(panel, 1, wx.EXPAND | wx.LEFT | wx.TOP, HPAD)

    self.exposure_listbox = panel.exposure_listbox
    self.tools = panel.tools
    self.image_view = panel.image_view

    self.SetSizerAndFit(box)

  def SetExposureCount(self, num):
    self.tools.exp.SetRange(1, num)

  def SetExposureNum(self, num):
    self.tools.exp.SetValue(num)

  def SetIndividualMinMax(self, min, max):
    self.tools.min.SetInt(min)
    self.tools.max.SetInt(max)
