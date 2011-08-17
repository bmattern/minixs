import wx
import view, controller
from const import *

from minixs import filter, emission
from minixs.gui import filter_view
from minixs.killzone import KillzoneList

class KillzoneApp(wx.App):
  def __init__(self, *args, **kwargs):
    wx.App.__init__(self, *args, **kwargs)
    self.SetAppName('minixs')

    v = view.KillzoneView(None, ID_MAIN_FRAME, 'miniXS XES Killzone')
    m = KillzoneList()
    c = controller.KillzoneController(v, m)

    self.controller = c

    #self.load_dummy_data()
    
    v.Show()

  def load_dummy_data(self):
    import minixs as mx
    import os
    import glob

    files = glob.glob("/home/bmattern/cur/data/MnO/*.tif")
    files.sort()
    for f in files:
      self.controller.AppendExposure(f)
    self.controller.SelectExposure(0)

def main():

  for f in filter.REGISTRY:
    if hasattr(f, 'view_name'):
      view_class = getattr(filter_view, f.view_name)
      filter_view.register(f, view_class)

  app =  KillzoneApp()
  app.MainLoop()

if __name__ == "__main__":
  main()
