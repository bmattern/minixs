import wx
import os
from const import *
import minixs as mx
from minixs.gui.wildcards import *
from minixs.gui.file_dialog import FileDialog
from minixs.gui.image_view import EVT_COORDS
from minixs.gui.image_tools import Crosshair, CircleTool, RangeTool
from matplotlib.cm import jet, gray
from matplotlib.colors import Normalize

BG_VALID = '#ffffff'
BG_INVALID = '#ffdddd'

ERROR_ENERGY    = 0x1
ERROR_NORM      = 0x2
ERROR_CALIB     = 0x4
ERROR_EXPOSURES = 0x8
ERROR_FILTERS   = 0x10

class KillzoneController(object):
  def __init__(self, view, model):
    """
    Initialize
    """
    self.view = view
    self.model = model

    self.dialog_dirs = {
        'last': '',
        }

    self.calib = ''
    self.exposure = mx.exposure.Exposure()

    self.individual_range = [0,1]
    self.exposure_num = 0

    self.changed = False
    self.error = 0

    # setup image view tools
    self.view.image_view.zoom_on_wheel = True
    self.crosshair = Crosshair(self.view.image_view)
    self.crosshair.ToggleDirection(Crosshair.HORIZONTAL | Crosshair.VERTICAL, True)

    self.circle_tool = CircleTool(self.view.image_view)
    self.circle_tool.SetActive(True)

    self.view.tools.radius_spin.SetValue(self.circle_tool.radius)

    self.range_tool = RangeTool(self.view.image_view)
    self.range_tool.SetMultiple(True)

    self.view.image_view.SetFocus()

    a = wx.AboutDialogInfo()
    a.SetName("miniXS XES Killzone Selector")
    a.SetDescription("Mini X-ray Spectrometer Killzone Selector")
    a.SetVersion("0.0.1")
    a.SetCopyright("(c) Seidler Group 2011")
    a.AddDeveloper("Brian Mattern (bmattern@uw.edu)")
    self.about_info = a

    self.BindCallbacks()

    wx.FutureCall(0, self.UpdateImageView)

  def BindCallbacks(self):
    """
    Connect up event handlers
    """
    callbacks = [
        (wx.EVT_CLOSE, [ (ID_MAIN_FRAME, self.OnClose) ]),
        (wx.EVT_MENU, [
          (wx.ID_EXIT, self.OnExit),
          (wx.ID_OPEN, self.OnOpen),
          (wx.ID_SAVE, self.OnSave),
          (wx.ID_ABOUT, self.OnAbout),
          ]),
        (wx.EVT_BUTTON, [
          (ID_EXPOSURE_ADD, self.OnAddExposures),
          (ID_EXPOSURE_DEL, self.OnDeleteSelected),
          ]),
        (wx.EVT_SPINCTRL, [
          (ID_INDIVIDUAL_MIN, self.OnIndividualMin),
          (ID_INDIVIDUAL_MAX, self.OnIndividualMax),
          (ID_INDIVIDUAL_EXP, self.OnIndividualExp),
          (ID_CIRCLE_RADIUS, self.OnCircleRadius),
          ]),
        (wx.EVT_RADIOBOX, [
          (ID_SELECT_MODE, self.OnSelectionMode),
          ]),
        #(wx.EVT_KEY_DOWN, [
        #  (ID_EXPOSURE_VIEW, self.OnImageKeyDown),
        #  ]),
        (EVT_COORDS, [ (ID_EXPOSURE_VIEW, self.OnImageCoords), ]),
        ]

    for event, bindings in callbacks:
      for id, callback in bindings:
        self.view.Bind(event, callback, id=id)

    self.view.image_view.Bind(wx.EVT_KEY_DOWN, self.OnImageKeyDown)

  def OnImageKeyDown(self, evt):
    bindings = {
        wx.WXK_LEFT: self.PreviousExposure,
        wx.WXK_RIGHT: self.NextExposure,
        wx.WXK_UP: self.IncreaseRadius,
        wx.WXK_DOWN: self.DecreaseRadius,
        wx.WXK_PAGEUP: self.ZoomIn,
        wx.WXK_PAGEDOWN: self.ZoomOut,
        }
    cb = bindings.get(evt.KeyCode)
    if cb: cb()

  def PreviousExposure(self):
    self.SelectExposure(self.exposure_num - 1)

  def NextExposure(self):
    self.SelectExposure(self.exposure_num + 1)

  def IncreaseRadius(self):
    self.SetRadius(self.GetRadius() + 1)

  def DecreaseRadius(self):
    self.SetRadius(self.GetRadius() - 1)

  def ZoomIn(self):
    zoom = self.GetZoom()

    if zoom == -2:
      zoom = 1
    else:
      zoom += 1
    self.SetZoom(zoom)

  def ZoomOut(self):
    zoom = self.GetZoom()
    if zoom == 1:
      zoom = -2
    else:
      zoom -= 1
    self.SetZoom(zoom)

  def GetRadius(self):
    return self.circle_tool.radius

  def SetRadius(self, radius):
    if radius < 2: radius = 2
    self.circle_tool.SetRadius(radius)
    self.view.tools.radius_spin.SetValue(radius)

  def GetZoom(self):
    return self.view.image_view.zoom

  def SetZoom(self, zoom):
    self.view.image_view.SetZoom(zoom)

  def SelectExposure(self, num, from_spinbox=False):
    num_exposures = len(self.model.exposure_files)
    if num_exposures == 0:
      return
    num %= num_exposures
    self.exposure_num = num
    filename = self.model.exposure_files[num]
    self.exposure.load(filename)

    self.circle_tool.circles = self.model.killzones[filename]['circles']
    self.range_tool.rects = self.model.killzones[filename]['rects']

    if not from_spinbox:
      self.view.SetExposureNum(self.exposure_num + 1)
    self.UpdateImageView()

  def OnClose(self, evt):
    """
    Window close handler

    Checks if model has changed since last save and notifies user
    if it has.
    """
    if not evt.CanVeto():
      self.view.Destroy()
      return True

    self.view.Destroy()

  def OnExit(self, evt):
    """
    File > Exit handler
    """
    self.view.Close()

  def OnSave(self, evt):
    header_only = False
    filename = FileDialog(
        self.view,
        self.dialog_dirs,
        'xes',
        'Enter a filename to save to',
        wildcard=WILDCARD_DATA,
        save=True
        )

    if not filename:
      return

    # check if file exists
    if os.path.exists(filename):
      errdlg = wx.MessageDialog(self.view, "This will overwrite the file:\n%s" % filename, "Warning", wx.OK | wx.CANCEL | wx.ICON_WARNING)
      ret = errdlg.ShowModal()
      errdlg.Destroy()

      if ret != wx.ID_OK:
        return

    # save the file
    self.model.save(filename)

  def OnOpen(self, evt):
    filename = FileDialog(
        self.view,
        self.dialog_dirs,
        'xes',
        'Select an xes file to open',
        wildcard=WILDCARD_DATA
        )

    if not filename:
      return

    self.load(filename)
    self.UpdateImageView()

  def ModelToView(self):
    for f in self.model.exposure_files:
      base = os.path.basename(f)
      self.view.exposure_listbox.AppendAndEnsureVisible(base)
    self.view.SetExposureCount(len(self.model.exposure_files))
    self.SelectExposure(0)

  def OnAbout(self, evt):
    """
    Help > About handler
    """
    wx.AboutBox(self.about_info)

  def UpdateImageView(self):
    if len(self.model.exposure_files):
      p = Normalize(*self.individual_range)(self.exposure.pixels)
      self.view.image_view.SetPixels(p, gray)

  def UpdateCoordStatus(self, cx, cy):
    if cx is None or cy is None:
      self.view.SetStatusText('', STATUS_COORDS)
      return

    cx = int(cx)
    cy = int(cy)
    try:
      if not self.exposure.loaded:
        return
      z = "%d" % self.exposure.pixels[cy,cx]
    except IndexError:
      z = "N/A"

    s = ("(%d, %d) -> "% (cx,cy)) + z
    self.view.SetStatusText(s, STATUS_COORDS)

  def OnAddExposures(self, evt):
    filenames = FileDialog(
        self.view,
        self.dialog_dirs,
        'exposure',
        'Select exposure file(s)',
        wildcard=WILDCARD_EXPOSURE,
        multiple=True
        )

    if not filenames:
      return

    invalid_files = []

    for f in filenames:
      try:
        self.AppendExposure(f)
      except IOError:
        invalid_files.append(f)
        continue

    if invalid_files:
      errmsg = "The following files were not recognized:\n\n  " + '\n  '.join(invalid_files)
      errdlg = wx.MessageDialog(self.view,  errmsg, "Error", wx.OK | wx.ICON_WARNING)
      errdlg.ShowModal()
      errdlg.Destroy()

  def OnDeleteSelected(self, evt):
    cur = self.model.exposure_files[self.exposure_num]
    sel = list(self.view.exposure_listbox.GetSelections())
    # run through indices backwards and remove from lists
    sel.sort(reverse=True)
    for i in sel:
      f = self.model.exposure_files[i]
      del(self.model.exposure_files[i])
      del(self.model.killzones[f])
      self.view.exposure_listbox.Delete(i)

    try:
      self.SelectExposure(self.model.exposure_files.index(cur))
    except ValueError:
      self.SelectExposure(0)

    # XXX if current exposure was deleted, select another one!

  def AppendExposure(self, f):
    self.model.exposure_files.append(f)
    self.model.killzones[f] = {'rects': [], 'circles': []}
    base = os.path.basename(f)
    self.view.exposure_listbox.AppendAndEnsureVisible(base)
    self.view.SetExposureCount(len(self.model.exposure_files))
    self.SelectExposure(self.exposure_num)

  def OnIndividualMin(self, evt):
    self.individual_range[0] = evt.GetInt()
    self.UpdateImageView()

  def OnIndividualMax(self, evt):
    self.individual_range[1] = evt.GetInt()
    self.UpdateImageView()

  def OnIndividualExp(self, evt):
    self.SelectExposure(evt.GetInt() - 1)

  def OnCircleRadius(self, evt):
    self.circle_tool.SetRadius(evt.GetInt())

  def OnSelectionMode(self, evt):
    mode = evt.GetString()
    if mode == 'Circle':
      self.circle_tool.SetActive(True)
      self.range_tool.SetActive(False)
      self.crosshair.SetActive(False)
    elif mode == 'Rectangle':
      self.circle_tool.SetActive(False)
      self.range_tool.SetActive(True)
      self.crosshair.SetActive(True)

  def OnImageCoords(self, evt):
    x, y = evt.x, evt.y
    self.UpdateCoordStatus(x,y)

  def Changed(self):
    """
    Something has changed since last save
    """
    self.changed = True

  def load(self, filename):
    # XXX handle errors...
    self.model.load(filename)
    self.ModelToView()
