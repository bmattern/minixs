import wx
import wx.lib.newevent

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

    self.tools = []
    self.active_tool = None

  def SetPixels(self, pixels, colormap):
    if pixels is None:
      self.bitmap = None
    else:
      h,w = pixels.shape[0:2]
      p = colormap(pixels, bytes=True)[:,:,0:3]
      self.bitmap = wx.BitmapFromBuffer(w, h, p.tostring())
    self.Refresh()

  def OnLeftDown(self, evt):
    for tool in self.tools:
      if tool.active:
        tool.OnLeftDown(evt)

  def OnLeftUp(self, evt):
    for tool in self.tools:
      if tool.active:
        tool.OnLeftUp(evt)

  def OnRightDown(self, evt):
    for tool in self.tools:
      if tool.active:
        tool.OnRightDown(evt)

  def OnRightUp(self, evt):
    for tool in self.tools:
      if tool.active:
        tool.OnRightUp(evt)

  def OnMotion(self, evt):
    for tool in self.tools:
      if tool.active:
        tool.OnMotion(evt)

  def OnEnterWindow(self, evt):
    for tool in self.tools:
      if tool.active:
        tool.OnEnterWindow(evt)

  def OnLeaveWindow(self, evt):
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

  def AddTool(self, tool):
    self.tools.append(tool)

  def SetActiveTool(self, tool):
    if tool not in self.tools:
      self.AddTool(tool)

    self.active_tool = tool
