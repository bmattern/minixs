import wx
import view, controller
from const import *

from minixs import filter, emission
from minixs.gui import filter_view

class ProcessorApp(wx.App):
  def __init__(self, *args, **kwargs):
    wx.App.__init__(self, *args, **kwargs)
    self.SetAppName('minixs')

    v = view.ProcessorView(None, ID_MAIN_FRAME, 'miniXS XES Processor')
    m = emission.EmissionSpectrum()
    c = controller.ProcessorController(v, m)
    
    v.Show()

def main():

  for f in filter.REGISTRY:
    if hasattr(f, 'view_name'):
      view_class = getattr(filter_view, f.view_name)
      filter_view.register(f, view_class)

  app =  ProcessorApp()
  app.MainLoop()

if __name__ == "__main__":
  main()
