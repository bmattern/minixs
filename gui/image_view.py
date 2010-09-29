import wx

class Tool(object):
  def __init__(self, parent):
    self.parent = parent
    self.parent.AddTool(self)

    self.active = False

  def SetActive(self, active):
    self.active = active

  def OnLeftDown(self, evt):
    pass

  def OnLeftUp(self, evt):
    pass

  def OnRightDown(self, evt):
    pass

  def OnRightUp(self, evt):
    pass

  def OnMotion(self, evt):
    pass

  def OnEnterWindow(self, evt):
    pass

  def OnLeaveWindow(self, evt):
    pass

  def OnPaint(self, evt):
    pass

class BoxTool(Tool):
  def __init__(self, *args, **kwargs):
    Tool.__init__(self, *args, **kwargs)

    self.rects = []
    self.active_rect = None

    self.brush = wx.Brush('#aa0000', wx.SOLID)
    self.pen = wx.Pen('#ffff22', 1, wx.DOT_DASH)
    self.active_pen = wx.Pen('#33dd33', 1, wx.DOT_DASH)

  def OnLeftDown(self, evt):
    x, y = evt.GetPosition()
    r = [x, y, x, y]
    self.rects.append(r)
    self.active_rect = r
    self.parent.Refresh()

  def OnLeftUp(self, evt):
    self.active_rect = None
    self.parent.Refresh()

  def OnMotion(self, evt):
    if self.active_rect is not None:
      x, y = evt.GetPosition()
      self.active_rect[2] = x
      self.active_rect[3] = y
      self.parent.Refresh()

  def OnPaint(self, evt):
    dc = wx.PaintDC(self.parent)
    for r in self.rects:
      if r == self.active_rect:
        dc.SetPen(self.active_pen)
      else:
        dc.SetPen(self.pen)

      x1,y1,x2,y2 = r 
      dc.DrawRectangle(x1,y1,x2-x1,y2-y1)

class Crosshair(Tool):
  VERTICAL = 1
  HORIZONTAL = 2

  def __init__(self, *args, **kwargs):
    Tool.__init__(self, *args, **kwargs)

    self.direction = 0
    self.pos = None

    self.pen = wx.Pen('#222222', 1, wx.SOLID)

  def SetDirection(self, direction):
    self.direction = direction
    self.parent.Refresh()

  def ToogleDirection(self, direction, on=None):
    """
    Toggle crosshair direction

    Parameters
    ----------
      direction: Crosshair.VERTICAL or .HORIZONTAL
      on: True for on, False for off, or None for toggle 

    Note: the directions can be bitwise or'd together. (e.g. Crosshair.VERTICAL | Crosshair.HORIZONTAL)
    """

    if on is None:
      self.direction ^= direction
    elif on:
      self.direction |= direction
    else:
      self.direction &= ~direction

  def OnLeftDown(self, evt):
    pass

  def OnMotion(self, evt):
    self.pos = evt.GetPosition()
    self.parent.Refresh()

  def OnLeaveWindow(self, evt):
    self.pos = None
    self.parent.Refresh()

  def OnPaint(self, evt):
    if self.pos is None:
      return

    dc = wx.PaintDC(self.parent)

    w, h = self.parent.GetSize()
    dc.SetPen(self.pen)

    if self.direction & self.VERTICAL:
      x1 = x2 = self.pos[0]
      y1 = 0
      y2 = h
      dc.DrawLine(x1,y1,x2,y2)

    if self.direction & self.HORIZONTAL:
      y1 = y2 = self.pos[1]
      x1 = 0
      x2 = w
      dc.DrawLine(x1,y1,x2,y2)

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

    for t in self.tools:
      t.OnPaint(evt)

  def AddTool(self, tool):
    self.tools.append(tool)

  def SetActiveTool(self, tool):
    if tool not in self.tools:
      self.AddTool(tool)

    self.active_tool = tool


if __name__ == "__main__":

  ID_HLINE = wx.NewId()
  ID_VLINE = wx.NewId()
  ID_BLINE = wx.NewId()
  ID_BOX  = wx.NewId()

  class DemoFrame(wx.Frame):
    def __init__(self, *args, **kwargs):
      wx.Frame.__init__(self, *args, **kwargs)

      box = wx.BoxSizer()
      p = DemoPanel(self, wx.ID_ANY)
      box.Add(p, 0, wx.EXPAND | wx.ALL, 5)

      self.SetSizerAndFit(box)

  class DemoPanel(wx.Panel):
    def __init__(self, *args, **kwargs):
      wx.Panel.__init__(self, *args, **kwargs)

      vbox = wx.BoxSizer(wx.VERTICAL)

      im = ImageView(self, size=(400,300))
      vbox.Add(im, 1, wx.EXPAND | wx.BOTTOM)
      self.image = im

      self.box_tool = BoxTool(im)
      self.crosshair = Crosshair(im)

      c = wx.CheckBox(self, ID_HLINE, 'Horizontal')
      vbox.Add(c, 0, wx.EXPAND | wx.BOTTOM, 5)

      c = wx.CheckBox(self, ID_VLINE, 'Vertical')
      vbox.Add(c, 0, wx.EXPAND | wx.BOTTOM, 5)

      c = wx.CheckBox(self, ID_BOX, 'Box')
      vbox.Add(c, 0, wx.EXPAND)

      self.Bind(wx.EVT_CHECKBOX, self.OnCheck)

      self.SetSizerAndFit(vbox)

    def OnCheck(self, evt):
      id = evt.GetId()
      checked = evt.IsChecked()

      if id == ID_VLINE:
        self.crosshair.SetActive(dir != 0)
        self.crosshair.ToogleDirection(Crosshair.VERTICAL, checked)

      elif id == ID_HLINE:
        self.crosshair.SetActive(dir != 0)
        self.crosshair.ToogleDirection(Crosshair.HORIZONTAL, checked)

      elif id == ID_BOX:
        self.box_tool.SetActive(checked)

  a = wx.App()
  f = DemoFrame(None)

  f.Show()
  a.MainLoop()
