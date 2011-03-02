import wx
import view
from minixs import filter
from minixs.gui import filter_view

class ProcessorApp(wx.App):
  def __init__(self, *args, **kwargs):
    wx.App.__init__(self, *args, **kwargs)
    self.SetAppName('minixs')

    v = view.ProcessorView(None, wx.ID_ANY, 'miniXS XES Processor')
    
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
