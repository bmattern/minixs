import minixs.info as mxinfo
import wx

from calibrator_controller import CalibratorController
from calibrator_view import CalibratorFrame
from calibrator_const import *

class CalibratorModel(mxinfo.CalibrationInfo):
  def __init__(self):
    mxinfo.CalibrationInfo.__init__(self)

class CalibratorApp(wx.App):
  def __init__(self, *args, **kwargs):
    wx.App.__init__(self, *args, **kwargs)

    model = CalibratorModel()
    view = CalibratorFrame(None, ID_MAIN_FRAME, "minIXS Calibrator")
    controller = CalibratorController(view, model)

    view.Show()

if __name__ == "__main__":
  app = CalibratorApp()
  app.MainLoop()
