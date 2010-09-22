import wx

class MenuFrame(wx.Frame):
  def __init__(self, *args, **kwargs):

    if 'menu_info' in kwargs.keys():
      menu_info = kwargs['menu_info']
      del(kwargs['menu_info'])
    else:
      menu_info = None

    wx.Frame.__init__(self, *args, **kwargs)

    if menu_info:
      self.CreateMenuBar(menu_info)

  def CreateMenuBar(self, menu_info):
    menubar = wx.MenuBar()

    for menu_name, items in menu_info:
      menu = wx.Menu()

      for label, id, description in items:

        if label == '':
          menu.AppendSeparator()
        
        else:
          menu_item = menu.Append(id, label, description)

      menubar.Append(menu, menu_name)

    self.SetMenuBar(menubar)
