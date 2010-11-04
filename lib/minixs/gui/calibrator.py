from minixs.calibrate import Calibration
import wx
import os, imp

from calibrator_controller import CalibratorController
from calibrator_view import CalibratorView
from calibrator_const import *

import minixs.filter as filter
import filter_view

from glob import glob

class CalibratorModel(Calibration):
  def __init__(self):
    Calibration.__init__(self)

class CalibratorApp(wx.App):
  def __init__(self, *args, **kwargs):
    wx.App.__init__(self, *args, **kwargs)

    self.SetAppName('minixs')

    self.setup_configuration()
    self.load_filter_plugins()

    model = CalibratorModel()
    view = CalibratorView(None, ID_MAIN_FRAME, "minIXS Calibrator")
    controller = CalibratorController(view, model)

    view.Show()

  def setup_configuration(self):
    # setup data directory
    datadir = wx.StandardPaths.Get().GetUserDataDir()
    self.datadir = datadir
    if not os.path.exists(datadir):
      os.makedirs(datadir)

    # create config object and set as global config obj
    conffile = os.path.join(datadir, 'config')
    conf = wx.FileConfig(localFilename=conffile)
    wx.Config.Set(conf)

  def load_filter_plugins(self):
    conf = wx.Config.Get()
    filterdir = conf.Read('calibrator/filter_dir', os.path.join(self.datadir, 'filters'))
    if not os.path.exists(filterdir):
      os.makedirs(filterdir)

    # load up all .py files in filterdir
    filter_files = glob(os.path.join(filterdir, '*.py'))
    for filename in filter_files:
      modname = os.path.splitext(os.path.split(filename)[-1])[0]
      m = imp.load_source(modname, filename)
      if hasattr(m, 'register_filters'):
        m.register_filters()
      if hasattr(m, 'register_filter_views'):
        m.register_filter_views()

def main():
  # register built in filters
  # XXX these should be split out into a system filter directory...
  for f in filter.REGISTRY:
    view_class = getattr(filter_view, f.view_name)
    filter_view.register(f, view_class)

  # set up application
  app = CalibratorApp()

  # run it
  app.MainLoop()
