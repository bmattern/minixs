import wx

class Tool(object):
  def __init__(self, parent):
    self.parent = parent
    self.parent.AddTool(self)

    self.active = False
    self.visible = True

  def SetActive(self, active):
    self.active = active

  def SetVisible(self, visible):
    self.visible = visible

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


class RangeTool(Tool):
  VERTICAL = 1
  HORIZONTAL = 2

  ACTION_NONE = 0
  ACTION_RESIZE_L = 0x01
  ACTION_RESIZE_R = 0x02
  ACTION_RESIZE_T = 0x04
  ACTION_RESIZE_B = 0x08
  ACTION_MOVE     = 0x10
  ACTION_PROPOSED = 0x100

  ACTION_RESIZE_TL = ACTION_RESIZE_T | ACTION_RESIZE_L
  ACTION_RESIZE_TR = ACTION_RESIZE_T | ACTION_RESIZE_R
  ACTION_RESIZE_BL = ACTION_RESIZE_B | ACTION_RESIZE_L
  ACTION_RESIZE_BR = ACTION_RESIZE_B | ACTION_RESIZE_R

  ACTION_RESIZE = ACTION_RESIZE_L | ACTION_RESIZE_R | \
                  ACTION_RESIZE_T | ACTION_RESIZE_B

  def __init__(self, *args, **kwargs):
    Tool.__init__(self, *args, **kwargs)

    self.rects = []
    self.active_rect = None

    self.multiple = False
    self.direction = self.VERTICAL | self.HORIZONTAL

    self.action = ACTION_NONE

    self.brush = wx.Brush(wx.Colour(127,127,127,50))
    self.pen = wx.Pen('#ffff22', 1, wx.DOT_DASH)
    self.active_pen = wx.Pen('#33dd33', 1, wx.DOT_DASH)

  def DetermineAction(self, x, y):
    off = 4
    action = self.ACTION_NONE
    active_rect = None

    # run through rects backwards (newest are on top)
    for rect in self.rects[::-1]:
      (x1,y1),(x2,y2) = rect

      # check if within offset of a rect edge, if so, resize
      if y1 - off < y < y2 + off:
        if abs(x1 - x) < off:
          action |= self.ACTION_RESIZE_L
          active_rect = rect
        elif abs(x2 - x) < off:
          action |= self.ACTION_RESIZE_R
      if x1 - off < x < x2 + off:
        if abs(y1 - y) < off:
          action |= self.ACTION_RESIZE_T
        elif abs(y2 - y) < off:
          action |= self.ACTION_RESIZE_B

      # not close to edge, but within rect => move
      if action == self.ACTION_NONE:
        if x1 < x < x2 and y1 < y < y2:
          action = self.ACTION_MOVE

      # only perform actions commensurate with direction
      mask = ACTION_NONE
      if self.direction & self.VERTICAL:
        mask |= self.ACTION_RESIZE_T
        mask |= self.ACTION_RESIZE_B
      if self.direction & self.HORIZONTAL:
        mask |= self.ACTION_RESIZE_L
        mask |= self.ACTION_RESIZE_R
      action &= ~mask

      if action != self.ACTION_NONE:
        return (rect, action)

    return (None, self.ACTION_NONE)

  def ToogleDirection(self, direction, on=None):
    """
    Toggle range direction

    Parameters
    ----------
      direction: Crosshair.VERTICAL or .HORIZONTAL
      on: True for on, False for off, or None for toggle 

    Note: the directions can be bitwise or'd together. (e.g. RangeTool.VERTICAL | RangeTool.HORIZONTAL)
    """

    if on is None:
      self.direction ^= direction
    elif on:
      self.direction |= direction
    else:
      self.direction &= ~direction

  def OnLeftDown(self, evt):
    x, y = evt.GetPosition()
    w, h = self.parent.GetSize()

    if self.direction & self.VERTICAL:
      y1 = y2 = y
    else:
      y1 = 0
      y2 = h
    if self.direction & self.HORIZONTAL:
      x1 = x2 = x
    else:
      x1 = 0
      x2 = w

    r = [[x1, y1], [x2, y2]]
    if self.multiple:
      self.rects.append(r)
    else:
      self.rects = [r]

    self.active_rect = r
    self.parent.Refresh()

  def OnLeftUp(self, evt):
    (x1,y1), (x2,y2) = self.active_rect

    # normalize rect coords so x1<x2 and y1<y2
    if x2 < x1:
      self.active_rect[0][0], self.active_rect[1][0] = x2, x1
    if y2 < y1:
      self.active_rect[0][1], self.active_rect[1][1] = y2, y1

    # don't keep rects with vanishing size
    if abs(x2 - x1) < 2 or abs(y2 - y1) < 2:
      self.rects.remove(self.active_xtal)
      self.Refresh()

    self.active_rect = None
    self.parent.Refresh()

  def OnMotion(self, evt):
    if self.active_rect is not None:
      x, y = evt.GetPosition()

      if self.direction & self.HORIZONTAL:
        self.active_rect[1][0] = x
      if self.direction & self.VERTICAL:
        self.active_rect[1][1] = y

      self.parent.Refresh()

  def OnPaint(self, evt):
    dc = wx.PaintDC(self.parent)
    gcdc = wx.GCDC(dc)

    dc.SetBrush(wx.TRANSPARENT_BRUSH)
    gcdc.SetBrush(self.brush)
    gcdc.SetPen(wx.TRANSPARENT_PEN)

    for r in self.rects:
      if r == self.active_rect:
        dc.SetPen(self.active_pen)
      else:
        dc.SetPen(self.pen)

      (x1,y1),(x2,y2) = r 
      dc.DrawRectangle(x1,y1,x2-x1,y2-y1)
      gcdc.DrawRectangle(x1,y1,x2-x1,y2-y1)

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
    dc.SetLogicalFunction(wx.INVERT)

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
