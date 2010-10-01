import wx
from image_view import ImageView
from image_tools import RangeTool, Crosshair, EVT_RANGE_CHANGED, EVT_RANGE_ACTION_CHANGED

if __name__ == "__main__":

  ID_HRANGE = wx.NewId()
  ID_VRANGE = wx.NewId()
  ID_BLINE = wx.NewId()
  ID_MULTIPLE  = wx.NewId()

  class DemoFrame(wx.Frame):
    def __init__(self, *args, **kwargs):
      wx.Frame.__init__(self, *args, **kwargs)

      box = wx.BoxSizer()
      p = DemoPanel(self, wx.ID_ANY)
      box.Add(p, 0, wx.EXPAND | wx.ALL, 5)

      self.SetSizerAndFit(box)

  ID_IMAGE_VIEW = wx.NewId()

  class DemoPanel(wx.Panel):
    def __init__(self, *args, **kwargs):
      wx.Panel.__init__(self, *args, **kwargs)

      vbox = wx.BoxSizer(wx.VERTICAL)

      im = ImageView(self, ID_IMAGE_VIEW, size=(400,300))
      vbox.Add(im, 1, wx.EXPAND | wx.BOTTOM)
      self.image = im

      self.box_tool = RangeTool(im)
      self.box_tool.direction = 0
      self.box_tool.active = True
      self.crosshair = Crosshair(im)

      c = wx.CheckBox(self, ID_HRANGE, 'Horizontal Range')
      vbox.Add(c, 0, wx.EXPAND | wx.BOTTOM, 5)

      c = wx.CheckBox(self, ID_VRANGE, 'Vertical Range')
      vbox.Add(c, 0, wx.EXPAND | wx.BOTTOM, 5)

      c = wx.CheckBox(self, ID_MULTIPLE, 'Multiple')
      vbox.Add(c, 0, wx.EXPAND)

      self.Bind(EVT_RANGE_ACTION_CHANGED, self.OnRangeActionChanged)
      self.Bind(EVT_RANGE_CHANGED, self.OnRangeChanged)
      self.Bind(wx.EVT_CHECKBOX, self.OnCheck)

      self.SetSizerAndFit(vbox)

    def OnRangeActionChanged(self, evt):
      print evt.action

    def OnRangeChanged(self, evt):
      print evt.range

    def OnCheck(self, evt):
      id = evt.GetId()
      checked = evt.IsChecked()

      if id == ID_VRANGE:
        self.crosshair.SetActive(dir != 0)
        self.crosshair.ToogleDirection(Crosshair.HORIZONTAL, checked)
        self.box_tool.ToogleDirection(RangeTool.VERTICAL, checked)

      elif id == ID_HRANGE:
        self.crosshair.SetActive(dir != 0)
        self.crosshair.ToogleDirection(Crosshair.VERTICAL, checked)
        self.box_tool.ToogleDirection(RangeTool.HORIZONTAL, checked)

      elif id == ID_MULTIPLE:
        self.box_tool.SetMultiple(checked)

  a = wx.App()
  f = DemoFrame(None)

  f.Show()
  a.MainLoop()
