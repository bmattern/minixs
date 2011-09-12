from minixs.progress import ProgressIndicator
import wx

class WxProgressIndicator(ProgressIndicator):
  def __init__(self, name, title):
    ProgressIndicator.__init__(self, name)

    self.dialog = wx.ProgressDialog(title, name, maximum=100, style=wx.PD_APP_MODAL | wx.PD_AUTO_HIDE)
    self.dialog.Show()

    w,h = self.dialog.GetSize()
    self.dialog.SetSize((300, h))


  def do_update(self):
    self.dialog.Update(int(self.progress * 100), self.msg)

  def __del__(self):
    self.dialog.Destroy()
