import minixs.info as mxinfo
import wx

from calibrator_controller import CalibratorController
from calibrator_view import CalibratorView
from calibrator_const import *

import minixs.filter as filter
import filter_view

class CalibratorModel(mxinfo.CalibrationInfo):
  def __init__(self):
    mxinfo.CalibrationInfo.__init__(self)

class CalibratorApp(wx.App):
  def __init__(self, *args, **kwargs):
    wx.App.__init__(self, *args, **kwargs)

    model = CalibratorModel()
    view = CalibratorView(None, ID_MAIN_FRAME, "minIXS Calibrator")
    controller = CalibratorController(view, model)

    view.Show()

if __name__ == "__main__":

  # register filters
  for f in filter.REGISTRY:
    view_class = getattr(filter_view, f.view_name)
    filter_view.register(f, view_class)

  app = CalibratorApp()
  app.MainLoop()
