import wx
import wx.lib.newevent

EventRangeActionChanged, EVT_RANGE_ACTION_CHANGED = wx.lib.newevent.NewCommandEvent()
EventRangeChanged, EVT_RANGE_CHANGED = wx.lib.newevent.NewCommandEvent()

class Tool(object):
  def __init__(self, parent):
    self.parent = parent
    self.parent.AddTool(self)

    self.active = False
    self.visible = True

  def SetActive(self, active):
    self.active = active

  def SetVisible(self, visible):
    if visible == self.visible:
      return

    self.visible = visible
    self.parent.Refresh()

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
  """
  A tool to allow selecting one or more ranges in one or more directions
  """
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
    """
    Initialize tool
    """
    Tool.__init__(self, *args, **kwargs)

    self.rects = []
    self.active_rect = None

    self.multiple = False
    self.direction = self.VERTICAL | self.HORIZONTAL

    self.action = self.ACTION_NONE

    self.brush = wx.Brush(wx.Colour(127,127,127,50))
    self.pen = wx.Pen('#ffff22', 1, wx.DOT_DASH)
    self.active_pen = wx.Pen('#33dd33', 1, wx.DOT_DASH)
    self.action_pen = wx.Pen('#22ffff', 2, wx.SOLID)

    self.range_changed = False
    self.post_range_change_immediate = False

  def RangeChanged(self):
    if self.post_range_change_immediate:
      self.PostEventRangeChanged()
    else:
      self.range_changed = True

  def PostEventRangeChanged(self):
    """
    Send event indicating that selected range has changed
    """
    evt = EventRangeChanged(self.parent.Id, range=self.rects)
    wx.PostEvent(self.parent, evt)

  def PostEventRangeActionChanged(self, in_window):
    """
    Send event indicating that current action has changed
    """
    evt = EventRangeActionChanged(self.parent.Id,
        action=self.action,
        range=self.active_rect,
        in_window=in_window)
    wx.PostEvent(self.parent, evt)

  def DetermineAction(self, x, y):
    """
    Determine action to perform based on the provided location

    Parameters
    ----------
      x: x coordinate
      y: y coordinate

    Returns
    -------
      (rect, action)

      rect: the rectangle to act on
      action: the action to perform (a bitmask of self.ACTION_*)
    """

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
      mask = self.ACTION_MOVE
      if self.direction & self.VERTICAL:
        mask |= self.ACTION_RESIZE_T
        mask |= self.ACTION_RESIZE_B
      if self.direction & self.HORIZONTAL:
        mask |= self.ACTION_RESIZE_L
        mask |= self.ACTION_RESIZE_R
      action &= mask

      if action != self.ACTION_NONE:
        return (rect, action)

    return (None, self.ACTION_NONE)

  def SetMultiple(self, multiple):
    self.multiple = multiple

  def SetDirection(self, direction):
    self.direction = direction
    self.parent.Refresh()

  def ToggleDirection(self, direction, on=None):
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
    """
    Handle left mouse down
    """
    x, y = evt.GetPosition()
    x, y = self.parent.CoordScreenToBitmap(x,y)

    w, h = self.parent.GetBitmapSize()

    if self.action & self.ACTION_PROPOSED:
      self.action &= ~self.ACTION_PROPOSED
      self.action_start = (x,y)
    else:
      if self.direction & self.VERTICAL:
        y1 = y
        y2 = y + 1
      else:
        y1 = 0
        y2 = h
      if self.direction & self.HORIZONTAL:
        x1 = x
        x2 = x + 1
      else:
        x1 = 0
        x2 = w

      rect = [[x1,y1],[x2,y2]]
      if self.multiple:
        self.rects.append(rect)
      else:
        self.rects = [rect]

      self.active_rect = rect
      self.action = self.ACTION_NONE
      if self.direction & self.HORIZONTAL:
        self.action |= self.ACTION_RESIZE_R
      if self.direction & self.VERTICAL:
        self.action |= self.ACTION_RESIZE_B

    self.parent.Refresh()

  def OnLeftUp(self, evt):
    """
    Handle left mouse up
    """
    x,y = evt.GetPosition()
    x,y = self.parent.CoordScreenToBitmap(x,y)
    (x1,y1), (x2,y2) = self.active_rect

    if self.action & self.ACTION_RESIZE:
      # normalize rect coords so x1<x2 and y1<y2
      if x2 < x1:
        self.active_rect[0][0], self.active_rect[1][0] = x2, x1
      if y2 < y1:
        self.active_rect[0][1], self.active_rect[1][1] = y2, y1

      # don't keep rects with vanishing size
      if abs(x2 - x1) < 2 or abs(y2 - y1) < 2:
        self.rects.remove(self.active_rect)
        self.parent.Refresh()

    rect, action = self.DetermineAction(x, y)
    if action != self.ACTION_NONE:
      action |= self.ACTION_PROPOSED
    self.active_rect = rect
    self.action = action 

    if self.range_changed:
      self.PostEventRangeChanged()
      self.range_changed = False

    self.parent.Refresh()

  def OnRightUp(self, evt):
    """
    Handle right mouse up
    """
    if self.action & self.ACTION_PROPOSED:
      self.rects.remove(self.active_rect)
      self.active_rect = None
      self.action = self.ACTION_NONE
      self.PostEventRangeChanged()
      self.parent.Refresh()

  def OnMotion(self, evt):
    """
    Handle mouse motion
    """
    x, y = evt.GetPosition()
    print x,y,
    x, y = self.parent.CoordScreenToBitmap(x,y)
    print " -> ", x, y

    w, h = self.parent.GetBitmapSize()

    # not currently performing an action
    if self.action == self.ACTION_NONE or self.action & self.ACTION_PROPOSED:
      rect, action = self.DetermineAction(x,y)

      needs_refresh = False
      if self.action & ~self.ACTION_PROPOSED != action or rect != self.active_rect:
        needs_refresh = True

      if rect:
        action |= self.ACTION_PROPOSED

      if action != self.action or rect != self.active_rect or rect is None:
        self.action = action
        self.active_rect = rect

        self.PostEventRangeActionChanged(in_window=True)

      if needs_refresh:
        self.parent.Refresh()

    elif self.action & self.ACTION_RESIZE:
      # clamp mouse to within panel
      if x < 0: x = 0
      if x > w: x = w
      if y < 0: y = 0
      if y > h: y = h

      if self.action & self.ACTION_RESIZE_L:
        self.active_rect[0][0] = x
      elif self.action & self.ACTION_RESIZE_R:
        self.active_rect[1][0] = x
      if self.action & self.ACTION_RESIZE_T:
        self.active_rect[0][1] = y
      elif self.action & self.ACTION_RESIZE_B:
        self.active_rect[1][1] = y

      self.RangeChanged()
      self.parent.Refresh()

    elif self.action & self.ACTION_MOVE:
      (x1, y1), (x2, y2) = self.active_rect
      xs,ys = self.action_start
      dx, dy = x - xs, y - ys

      if dx < -x1: dx = -x1
      if dy < -y1: dy = -y1
      if dx > w-x2: dx = w-x2
      if dy > h-y2: dy = h-y2

      if self.direction & self.HORIZONTAL:
        self.active_rect[0][0] += dx
        self.active_rect[1][0] += dx
      if self.direction & self.VERTICAL:
        self.active_rect[0][1] += dy
        self.active_rect[1][1] += dy
      self.action_start = (x,y)

      self.RangeChanged()
      self.parent.Refresh()

  def OnEnterWindow(self, evt):
    """
    Handle entering window
    """
    pass

  def OnLeaveWindow(self, evt):
    """
    Handle leaving window
    """
    if self.action & self.ACTION_PROPOSED or self.action == self.ACTION_NONE:
      self.action = self.ACTION_NONE
      self.active_rect = None

      self.PostEventRangeActionChanged(in_window=False)
      self.parent.Refresh()

  def OnPaint(self, evt):
    """
    Draw tool
    """
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

      # transform coords
      x1,y1 = self.parent.CoordBitmapToScreen(x1,y1)
      x2,y2 = self.parent.CoordBitmapToScreen(x2,y2)

      gcdc.DrawRectangle(x1,y1,x2-x1,y2-y1)
      dc.DrawRectangle(x1,y1,x2-x1+1,y2-y1+1)

      if self.active_rect and self.action & self.ACTION_RESIZE and self.action & self.ACTION_PROPOSED:

        dc.SetPen(self.action_pen)
        (x1,y1),(x2,y2) = self.active_rect
        x1,y1 = self.parent.CoordBitmapToScreen(x1,y1)
        x2,y2 = self.parent.CoordBitmapToScreen(x2,y2)

        if self.action & self.ACTION_RESIZE_L:
          dc.DrawLine(x1,y1,x1,y2)
        if self.action & self.ACTION_RESIZE_R:
          dc.DrawLine(x2,y1,x2,y2)
        if self.action & self.ACTION_RESIZE_T:
          dc.DrawLine(x1,y1,x2,y1)
        if self.action & self.ACTION_RESIZE_B:
          dc.DrawLine(x1,y2,x2,y2)


class Crosshair(Tool):
  VERTICAL = 1
  HORIZONTAL = 2

  def __init__(self, *args, **kwargs):
    Tool.__init__(self, *args, **kwargs)

    self.direction = self.VERTICAL | self.HORIZONTAL
    self.pos = None

    self.pen = wx.Pen('#222222', 1, wx.SOLID)

  def SetDirection(self, direction):
    self.direction = direction
    self.parent.Refresh()

  def ToggleDirection(self, direction, on=None):
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

