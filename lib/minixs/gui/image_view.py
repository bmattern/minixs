import wx
import wx.lib.newevent

EventCoords, EVT_COORDS = wx.lib.newevent.NewCommandEvent()

class ImageView(wx.Panel):
  def __init__(self, *args, **kwargs):
    wx.Panel.__init__(self, *args, **kwargs)
    self.bitmap = None

    self.SetEvtHandlerEnabled(True)

    self.Bind(wx.EVT_PAINT, self.OnPaint)
    self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
    self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
    self.Bind(wx.EVT_RIGHT_UP, self.OnRightDown)
    self.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)
    self.Bind(wx.EVT_MOTION, self.OnMotion)
    self.Bind(wx.EVT_ENTER_WINDOW, self.OnEnterWindow)
    self.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeaveWindow)
    self.Bind(wx.EVT_MOUSEWHEEL, self.OnMouseWheel)

    self.tools = []
    self.active_tool = None

    self.zoom = 1

  def GetBitmapSize(self):
    if self.bitmap:
      return self.bitmap.GetSize()
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
      self.SetZoom(self.zoom, force=True)

  def SetZoom(self, zoom, force=False):
    # XXX use timer to prevent slow down when zooming quickly through several levels
    if not force and zoom == self.zoom:
      return

    self.zoom = zoom

    w = self.raw_image.Width * self.zoom
    h = self.raw_image.Height * self.zoom
    scaled = self.raw_image.Scale(w, h)

    self.bitmap = wx.BitmapFromImage(scaled)
    self.Refresh()

  def CoordBitmapToScreen(self,x,y):
    return (x*self.zoom, y*self.zoom)

  def CoordScreenToBitmap(self,sx,sy):
    return (sx/float(self.zoom), sy/float(self.zoom))

  def PostEventCoords(self, x, y):
    evt = EventCoords(self.Id, x=x, y=y)
    wx.PostEvent(self, evt)

  def OnLeftDown(self, evt):
    if not self.bitmap:
      return

    for tool in self.tools:
      if tool.active:
        tool.OnLeftDown(evt)

  def OnLeftUp(self, evt):
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

  def OnMotion(self, evt):
    if not self.bitmap:
      return

    x, y = evt.GetPosition()
    self.PostEventCoords(x, y)

    for tool in self.tools:
      if tool.active:
        tool.OnMotion(evt)

  def OnEnterWindow(self, evt):
    for tool in self.tools:
      if tool.active:
        tool.OnEnterWindow(evt)

  def OnLeaveWindow(self, evt):
    self.PostEventCoords(None, None)

    for tool in self.tools:
      if tool.active:
        tool.OnLeaveWindow(evt)

  def OnPaint(self, evt):
    dc = wx.PaintDC(self)
    if self.bitmap:
      dc.DrawBitmap(self.bitmap, 0, 0)

    for tool in self.tools:
      if tool.visible:
        tool.OnPaint(evt)

  def OnMouseWheel(self, evt):
    #return # Not yet fully implemented, so disable for now

    if not self.bitmap:
      return

    rot = evt.GetWheelRotation()
    print rot
    zoom = self.zoom
    if rot > 0:
      zoom += 1
    elif rot < 0:
      zoom -= 1

    if zoom < 1:
      zoom = 1

    print zoom

    self.SetZoom(zoom)

    # pan so that pixel under mouse stays under mouse
    x,y = evt.GetPosition()



  def AddTool(self, tool):
    self.tools.append(tool)

  def SetActiveTool(self, tool):
    if tool not in self.tools:
      self.AddTool(tool)

    self.active_tool = tool
