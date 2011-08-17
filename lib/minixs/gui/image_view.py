import wx
import wx.lib.newevent
from wx.lib.scrolledpanel import ScrolledPanel

from mouse_event import *

EventCoords, EVT_COORDS = wx.lib.newevent.NewCommandEvent()


class ScrolledImageView(ScrolledPanel):
  def __init__(self, *args, **kwargs):
    ScrolledPanel.__init__(self, args[0], wx.ID_ANY, size=kwargs['size'])

    box = wx.BoxSizer()
    image_view = ImageView(self, *args[1:], **kwargs)
    self.image_view = image_view
    self.SetSizer(box)

    self.SetAutoLayout(True)
    self.SetupScrolling()

class ImageView(wx.Panel):
  def __init__(self, *args, **kwargs):
    wx.Panel.__init__(self, *args, **kwargs)
    self.bitmap = None

    self.SetEvtHandlerEnabled(True)

    self.Bind(wx.EVT_PAINT, self.OnPaint)
    self.Bind(wx.EVT_SIZE, self.OnSize)
    self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBG)
    self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
    self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
    self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)
    self.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)
    self.Bind(wx.EVT_MIDDLE_DOWN, self.OnMiddleDown)
    self.Bind(wx.EVT_MIDDLE_UP, self.OnMiddleUp)
    self.Bind(wx.EVT_MOTION, self.OnMotion)
    self.Bind(wx.EVT_ENTER_WINDOW, self.OnEnterWindow)
    self.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeaveWindow)
    self.Bind(wx.EVT_MOUSEWHEEL, self.OnMouseWheel)

    self.tools = []
    self.active_tool = None

    self.panning = False

    self.zoom_on_wheel = False
    self.zoom = 1
    self.zoom_min = -10
    self.zoom_max = 10
    self.set_zoom_delay = 10
    self.set_zoom_timeout = None

    self.pan = [0, 0]
    self.pan_min = [0,0]
    self.pan_max = [0,0]

    self.queue_zoom_pan = None

  def GetBitmapSize(self):
    if self.bitmap:
      return self.raw_image.GetSize()
    else:
      return (0,0)

  def SetPixels(self, pixels, colormap):
    if pixels is None:
      self.raw_image = None
      self.bitmap = None
      self.Refresh()
    else:
      h,w = pixels.shape[0:2]
      p = colormap(pixels, bytes=True)[:,:,0:3]
      self.raw_image = wx.ImageFromBuffer(w, h, p.tostring())
      self.SetZoom(self.zoom, force=True, immediate=True)


  def _SetZoomActual(self):
    zoom = self.zoom
    if zoom > 0:
      w = self.raw_image.Width * zoom
      h = self.raw_image.Height * zoom
    elif zoom < 0:
      w = -self.raw_image.Width / zoom
      h = -self.raw_image.Height / zoom
    else:
      raise ValueError("Zoom level cannot be 0.")

    self.zoom = zoom

    scaled = self.raw_image.Scale(w, h)

    self.bitmap = wx.BitmapFromImage(scaled)
    self.UpdatePanBounds()

    if self.queue_zoom_pan:
      self.SetPan(*self.queue_zoom_pan)
      self.queue_zoom_pan = None

    self.Refresh()
    self.set_zoom_timeout = None


  def SetZoom(self, zoom, force=False, immediate=False):
    if zoom > self.zoom_max:
      zoom = self.zoom_max

    if zoom < self.zoom_min:
      zoom = self.zoom_min

    if not force and zoom == self.zoom:
      return

    self.zoom = zoom

    if immediate:
      self._SetZoomActual()
    elif not self.set_zoom_timeout:
      self.set_zoom_timeout = wx.CallLater(self.set_zoom_delay, self._SetZoomActual)

  def SetPan(self, pan_x = None, pan_y = None):
    if pan_x is not None:
      self.pan[0] = pan_x

    if pan_y is not None:
      self.pan[1] = pan_y

    self.Refresh()

  def UpdatePanBounds(self):
    if not self.bitmap:
      self.pan_min = [0,0]
      self.pan_max = [0,0]
      return

    px, py = self.pan
    imw, imh = self.bitmap.GetSize()
    bw, bh = self.GetSize()

    if bw < imw:
      xmin = bw - imw
      xmax = 0
    else:
      xmin = 0
      xmax = bw - imw

    if bh < imh:
      ymin = bh - imh
      ymax = 0
    else:
      ymin = 0
      ymax = bh - imh

    self.pan_min = [xmin, ymin]
    self.pan_max = [xmax, ymax]

    if px < xmin: px = xmin
    if px > xmax: px = xmax
    if py < ymin: py = ymin
    if py > ymax: py = ymax

    self.SetPan(px, py)

  def CoordBitmapToScreen(self,x,y):
    px, py = self.pan
    if self.zoom > 0:
      return (x*self.zoom + px, y*self.zoom + py)
    else:
      return (-x/float(self.zoom) + px, -y/float(self.zoom) + py)

  def CoordScreenToBitmap(self,sx,sy):
    px, py = self.pan
    sx -= px
    sy -= py
    if self.zoom > 0:
      return (sx/float(self.zoom), sy/float(self.zoom))
    else:
      return (-sx*self.zoom, -sy*self.zoom)

  def PostEventCoords(self, x, y):
    evt = EventCoords(self.Id, x=x, y=y)
    wx.PostEvent(self, evt)

  def OnLeftDown(self, evt):
    if not self.bitmap:
      return

    if mouse_event_modifier_mask(evt) & MOD_CTRL:
      self.panning = True
      self.pan_prev = None

    for tool in self.tools:
      if tool.active:
        tool.OnLeftDown(evt)

  def OnLeftUp(self, evt):
    self.panning = False

    if not self.bitmap:
      return

    for tool in self.tools:
      if tool.active:
        tool.OnLeftUp(evt)

  def OnRightDown(self, evt):
    if not self.bitmap:
      return

    for tool in self.tools:
      if tool.active:
        tool.OnRightDown(evt)

  def OnRightUp(self, evt):
    if not self.bitmap:
      return

    for tool in self.tools:
      if tool.active:
        tool.OnRightUp(evt)

  def OnMiddleDown(self, evt):
    if not self.bitmap:
      return

    for tool in self.tools:
      if tool.active:
        tool.OnMiddleDown(evt)

  def OnMiddleUp(self, evt):
    if not self.bitmap:
      return

    for tool in self.tools:
      if tool.active:
        tool.OnMiddleUp(evt)

  def OnMotion(self, evt):
    if not self.bitmap:
      return

    x, y = evt.GetPosition()
    if self.panning:
      if self.pan_prev:
        self.SetPan(
          self.pan[0] + x - self.pan_prev[0],
          self.pan[1] + y - self.pan_prev[1]
          )
        self.Refresh()
      self.pan_prev = (x,y)

    x, y = self.CoordScreenToBitmap(x, y)
    self.PostEventCoords(x, y)


    for tool in self.tools:
      if tool.active:
        tool.OnMotion(evt)

  def OnEnterWindow(self, evt):
    self.SetFocus()
    for tool in self.tools:
      if tool.active:
        tool.OnEnterWindow(evt)

  def OnLeaveWindow(self, evt):
    self.PostEventCoords(None, None)

    for tool in self.tools:
      if tool.active:
        tool.OnLeaveWindow(evt)

  def OnPaint(self, evt):
    dc = wx.BufferedPaintDC(self)
    self.Draw(evt, dc)

  def OnSize(self, evt):
    dc = wx.BufferedPaintDC(self)
    self.Draw(evt, dc)

  def OnEraseBG(self, evt):
    pass

  def Draw(self, evt, dc):
    dc.Clear()
    if self.bitmap:
      dc.DrawBitmap(self.bitmap, self.pan[0], self.pan[1])

    for tool in self.tools:
      if tool.visible:
        tool.OnPaint(evt, dc)

  def OnMouseWheel(self, evt):
    if not self.zoom_on_wheel:
      return

    if not self.bitmap:
      return

    rot = evt.GetWheelRotation()

    orig_zoom = zoom = self.zoom
    if rot > 0:
      zoom += 1
      if zoom == -1:
        zoom = 1

    elif rot < 0:
      zoom -= 1
      if zoom == 0:
        zoom = -2

    x,y = evt.GetPosition()
    bx, by = self.CoordScreenToBitmap(x,y)

    self.SetZoom(zoom)

    # pan so that pixel under mouse stays under mouse
    bx2,by2 = self.CoordScreenToBitmap(x,y)
    px, py = self.pan
    scale = float(zoom)
    if scale < 0: scale = -1.0/scale
    px += (bx2-bx)*scale
    py += (by2-by)*scale
    self.queue_zoom_pan = (px,py)

  def SetPan(self, px, py):
    mx,my = self.pan_min
    if px < mx: px = mx
    if py < my: py = my

    mx,my = self.pan_max
    if px > mx: px = mx
    if py > my: py = my

    self.pan = [px,py]
    self.Refresh()

  def AddTool(self, tool):
    self.tools.append(tool)

  def SetActiveTool(self, tool):
    if tool not in self.tools:
      self.AddTool(tool)

    self.active_tool = tool
