import wx
import os
from const import *
import minixs as mx
from minixs.gui.wildcards import *
from minixs.gui.file_dialog import FileDialog
from matplotlib.cm import jet, gray
from matplotlib.colors import Normalize

class ProcessorController(object):
  def __init__(self, view, model):
    """
    Initialize
    """
    self.view = view
    self.model = model

    self.dialog_dirs = {
        'last': '',
        }

    self.calib = ''
    self.combined_exposure = mx.exposure.Exposure()
    self.exposures = []

    self.combined_range = [0,100]
    self.individual_range = [0,100]
    self.exposure_num = 0

    self.changed = False
    self.spectrum_invalid = True

    a = wx.AboutDialogInfo()
    a.SetName("miniXS XES Processor")
    a.SetDescription("Mini X-ray Spectrometer Emission Spectrum Processor")
    a.SetVersion("0.0.1")
    a.SetCopyright("(c) Seidler Group 2011")
    a.AddDeveloper("Brian Mattern (bmattern@uw.edu)")
    self.about_info = a

    self.BindCallbacks()

    wx.FutureCall(0, self.SetViewMode)

  def BindCallbacks(self):
    """
    Connect up event handlers
    """
    callbacks = [
        (wx.EVT_CLOSE, [ (ID_MAIN_FRAME, self.OnClose) ]),
        (wx.EVT_MENU, [
          (wx.ID_EXIT, self.OnExit),
          (wx.ID_OPEN, self.OnOpen),
          (wx.ID_SAVE, self.OnSave),
          (wx.ID_ABOUT, self.OnAbout),
          ]),
        (wx.EVT_TEXT, [
          (ID_DATASET, self.OnDataset),
          (ID_ENERGY, self.OnEnergy),
          (ID_NORM, self.OnNorm),
          ]),
        (wx.EVT_BUTTON, [
          (ID_CALIB_LOAD, self.OnLoadCalibration),
          (ID_EXPOSURE_ADD, self.OnAddExposures),
          (ID_EXPOSURE_DEL, self.OnDeleteSelected),
          (ID_PROCESS, self.OnProcess),
          ]),
        (wx.EVT_RADIOBOX, [
          (ID_VIEW_MODE, self.OnViewMode),
          ]),
        (wx.EVT_SPINCTRL, [
          (ID_INDIVIDUAL_MIN, self.OnIndividualMin),
          (ID_INDIVIDUAL_MAX, self.OnIndividualMax),
          (ID_INDIVIDUAL_EXP, self.OnIndividualExp),
          (ID_COMBINED_MIN, self.OnCombinedMin),
          (ID_COMBINED_MAX, self.OnCombinedMax),
          ]),
        ]

    for event, bindings in callbacks:
      for id, callback in bindings:
        self.view.Bind(event, callback, id=id)


  def OnClose(self, evt):
    """
    Window close handler

    Checks if model has changed since last save and notifies user
    if it has.
    """
    if not evt.CanVeto():
      self.view.Destroy()
      return True

    self.view.Destroy()

  def OnExit(self, evt):
    """
    File > Exit handler
    """
    self.view.Close()

  def OnSave(self, evt):
    pass

  def OnOpen(self, evt):
    pass


  def OnAbout(self, evt):
    """
    Help > About handler
    """
    wx.AboutBox(self.about_info)

  def OnDataset(self, evt):
    self.model.dataset_name = evt.GetString()

  def OnEnergy(self, evt):
    s = evt.GetString()
    if s:
      try:
        self.model.incident_energy = float(s)
      except ValueError:
        #XXX make the box reddish or something to indicate bad value
        pass

    else:
      self.model.incident_energy = 0

  def OnNorm(self, evt):
    s = evt.GetString()
    if s:
      try:
        self.model.I0 = float(s)
      except ValueError:
        #XXX make the box reddish or something to indicate bad value
        pass
    else:
      self.model.I0 = 1

  def OnLoadCalibration(self, evt):
    filename = FileDialog(
        self.view,
        self.dialog_dirs,
        'calib',
        'Select a calibration file to open',
        wildcard=WILDCARD_CALIB
        )

    calib = mx.calibrate.load(filename)

    if not calib: return

    self.calib = calib
    self.model.calibration_file = filename

    if calib.load_errors:
      errmsg = "Warning: the following errors were encountered while loading the calibration file:\n\n  %s.\n\nThese may or may not prevent this calibration matrix from being used." % '\n  '.join(calib.load_errors)
      errdlg = wx.MessageDialog(self.view,  errmsg, "Error", wx.OK | wx.ICON_WARNING)
      errdlg.ShowModal()
      errdlg.Destroy()

    self.SetViewMode(VIEW_MODE_CALIB)

  def SetViewMode(self, mode=VIEW_MODE_COMBINED):
    self.view_mode = mode

    if mode == VIEW_MODE_COMBINED:
      print 'combined'
      if self.combined_exposure.loaded:
        p = Normalize(0,100)(self.combined_exposure.pixels)
        self.view.image_view.SetPixels(p, gray)
      else:
        print 'not yet loaded'

    elif mode == VIEW_MODE_INDIVIDUAL:
      print 'individual'
      if self.exposures:
        p = Normalize(0,100)(self.exposures[self.exposure_num].pixels)
        self.view.image_view.SetPixels(p, gray)
      else:
        print 'no exposures'
    elif mode == VIEW_MODE_CALIB:
      print 'calib'
      if self.calib:
        p = Normalize(*self.calib.energy_range())(self.calib.calibration_matrix)
        self.view.image_view.SetPixels(p, jet)
      else:
        pass
    elif mode == VIEW_MODE_SPECTRUM:
      print 'spectrum'
      pass

    self.view.view_mode.SetSelection(mode)
    self.view.tools.SetMode(mode)

  def OnAddExposures(self, evt):
    filenames = FileDialog(
        self.view,
        self.dialog_dirs,
        'exposure',
        'Select exposure file(s)',
        wildcard=WILDCARD_EXPOSURE,
        multiple=True
        )

    if not filenames:
      return

    # XXX add a timer for the exposure loading?
    for f in filenames:
      self.model.exposure_files.append(f)
      base = os.path.basename(f)
      self.view.exposure_listbox.AppendAndEnsureVisible(base)
      self.exposures.append(mx.exposure.Exposure(f))

    self.combined_exposure.load_multi(self.model.exposure_files)
    self.view.SetExposureCount(len(self.exposures))
    

    self.SetViewMode(VIEW_MODE_COMBINED)

  def OnDeleteSelected(self, evt):
    sel = list(self.view.exposure_listbox.GetSelections())
    # run through indices backwards and remove from lists
    sel.sort(reverse=True)
    for i in sel:
      del(self.model.exposure_files[i])
      del(self.exposures[i])
      self.view.exposure_listbox.Delete(i)

    self.combined_exposure.load_multi(self.model.exposure_files)
  
  def OnProcess(self, evt):
    self.model.process()
    print self.model.spectrum.shape
    pass

  def OnViewMode(self, evt):
    mode = self.view.view_mode.GetSelection()
    self.SetViewMode(mode)

  def OnIndividualMin(self, evt):
    pass

  def OnIndividualMax(self, evt):
    pass

  def OnIndividualExp(self, evt):
    self.exposure_num = evt.GetInt() - 1
    self.SetViewMode(self.view_mode)

  def OnCombinedMin(self, evt):
    pass

  def OnCombinedMax(self, evt):
    pass

  def UpdateImageView(self):
    pass

  def InvalidateSpectrum(self):
    """
    Spectrum needs to be reprocessed
    """
    self.spectrum_invalid = True

  def Changed(self):
    """
    Something has changed since last save
    """
    self.changed = True
