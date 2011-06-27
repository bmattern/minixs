import wx
import os
from const import *
import minixs as mx
from minixs.gui.wildcards import *
from minixs.gui.file_dialog import FileDialog
from matplotlib.cm import jet, gray
from matplotlib.colors import Normalize

BG_VALID = '#ffffff'
BG_INVALID = '#ffdddd'

ERROR_ENERGY    = 0x1
ERROR_NORM      = 0x2
ERROR_CALIB     = 0x4
ERROR_EXPOSURES = 0x8
ERROR_FILTERS   = 0x10

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

    self.spectrometer_tags, self.spectrometer_names = mx.spectrometer.list_spectrometers(include_names = True)
    self.spectrometer_names.append("Other")
    self.view.SetSpectrometerNames(self.spectrometer_names)
    self.view.SetSpectrometer(len(self.spectrometer_names) - 1)

    self.combined_range = [0,100]
    self.individual_range = [0,100]
    self.exposure_num = 0

    self.changed = False
    self.spectrum_invalid = True
    self.error = 0

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
    header_only = False
    if self.spectrum_invalid == True:
      errdlg = wx.MessageDialog(self.view, "Warning: You have changed parameters since last processing the spectrum. Saving now will only save the parameters, and not the spectrum itself.", "Error", wx.OK | wx.CANCEL | wx.ICON_WARNING)
      ret = errdlg.ShowModal()
      errdlg.Destroy()

      if ret == wx.ID_OK:
        header_only = True
      else:
        return

    filename = FileDialog(
        self.view,
        self.dialog_dirs,
        'xes',
        'Enter a filename to save to',
        wildcard=WILDCARD_XES,
        save=True
        )

    if not filename:
      return

    # check if file exists
    if os.path.exists(filename):
      errdlg = wx.MessageDialog(self.view, "This will overwrite the file:\n%s" % filename, "Warning", wx.OK | wx.CANCEL | wx.ICON_WARNING)
      ret = errdlg.ShowModal()
      errdlg.Destroy()

      if ret != wx.ID_OK:
        return

    # save the file
    self.model.save(filename, header_only=header_only)

  def OnOpen(self, evt):
    filename = FileDialog(
        self.view,
        self.dialog_dirs,
        'xes',
        'Select an xes file to open',
        wildcard=WILDCARD_XES
        )

    if not filename:
      return

    self.load(filename)
    self.SetViewMode(VIEW_MODE_SPECTRUM)

  def ModelToView(self):

    self.view.dataset_entry.SetValue(self.model.dataset_name)
    self.view.energy_entry.SetValue(str(self.model.incident_energy))
    self.view.norm_entry.SetValue(str(self.model.I0))

    self.exposures = []
    for f in self.model.exposure_files:
      base = os.path.basename(f)
      self.view.exposure_listbox.AppendAndEnsureVisible(base)
      self.exposures.append(mx.exposure.Exposure(f))
    self.combined_exposure.load_multi(self.model.exposure_files)
    self.view.SetExposureCount(len(self.exposures))
    self.SetCalibrationFilename(self.model.calibration_file)
    self.view.axes.cla()
    self.view.axes.plot(self.model.emission, self.model.intensity)

  def OnAbout(self, evt):
    """
    Help > About handler
    """
    wx.AboutBox(self.about_info)

  def OnDataset(self, evt):
    self.model.dataset_name = evt.GetString()

  def OnEnergy(self, evt):
    s = evt.GetString()
    valid = True
    if s:
      try:
        self.model.incident_energy = float(s)
        self.error &= ~ERROR_ENERGY
      except ValueError:
        self.error |= ERROR_ENERGY
        valid = False
    else:
      self.model.incident_energy = 0

    evt.GetEventObject().SetOwnBackgroundColour(BG_VALID if valid else BG_INVALID)

  def OnNorm(self, evt):
    s = evt.GetString()
    valid = True
    if s:
      try:
        self.model.I0 = float(s)
        self.error &= ~ERROR_NORM
      except ValueError:
        self.error |= ERROR_NORM
        valid = False
    else:
      self.model.I0 = 1

    evt.GetEventObject().SetOwnBackgroundColour(BG_VALID if valid else BG_INVALID)
    self.InvalidateSpectrum()

  def OnLoadCalibration(self, evt):
    filename = FileDialog(
        self.view,
        self.dialog_dirs,
        'calib',
        'Select a calibration file to open',
        wildcard=WILDCARD_CALIB
        )

    if not filename:
      return

    self.SetCalibrationFilename(filename)
    if len(self.exposures) == 0:
      self.SetViewMode(VIEW_MODE_CALIB)

  def SetCalibrationFilename(self, filename):
    try:
      calib = mx.calibrate.load(filename)
    except mx.filetype.InvalidFileError:
      errmsg = "The selected file was not a valid calibration file." 
      errdlg = wx.MessageDialog(self.view,  errmsg, "Error", wx.OK | wx.ICON_WARNING)
      errdlg.ShowModal()
      errdlg.Destroy()
      return

    self.calib = calib
    self.model.calibration_file = filename

    self.view.calibration_file_entry.SetValue(os.path.basename(filename))

    if calib.load_errors:
      errmsg = "Warning: the following errors were encountered while loading the calibration file:\n\n  %s.\n\nThese may or may not prevent this calibration matrix from being used." % '\n  '.join(calib.load_errors)
      errdlg = wx.MessageDialog(self.view,  errmsg, "Error", wx.OK | wx.ICON_WARNING)
      errdlg.ShowModal()
      errdlg.Destroy()

  def SetViewMode(self, mode=VIEW_MODE_COMBINED):
    self.view_mode = mode

    if mode == VIEW_MODE_COMBINED:
      print 'combined'
      if self.combined_exposure.loaded:
        p = Normalize(*self.combined_range)(self.combined_exposure.pixels)
        self.view.image_view.SetPixels(p, gray)
      else:
        print 'not yet loaded'

    elif mode == VIEW_MODE_INDIVIDUAL:
      print 'individual'
      if self.exposures:
        p = Normalize(*self.individual_range)(self.exposures[self.exposure_num].pixels)
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

    #self.view.view_mode.SetSelection(mode)
    self.view.SetViewMode(mode)

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

    invalid_files = []

    for f in filenames:
      try:
        e = mx.exposure.Exposure(f)
      except IOError:
        invalid_files.append(f)
        continue

      self.model.exposure_files.append(f)
      base = os.path.basename(f)
      self.view.exposure_listbox.AppendAndEnsureVisible(base)
      self.exposures.append(e)

    self.combined_exposure.load_multi(self.model.exposure_files)
    self.view.SetExposureCount(len(self.exposures))

    if invalid_files:
      errmsg = "The following files were not recognized:\n\n  " + '\n  '.join(invalid_files)
      errdlg = wx.MessageDialog(self.view,  errmsg, "Error", wx.OK | wx.ICON_WARNING)
      errdlg.ShowModal()
      errdlg.Destroy()

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
    if self.model.validate():
      self.model.process()
      self.spectrum_invalid = False
      self.view.axes.cla()
      self.view.axes.plot(self.model.emission, self.model.intensity)
      self.SetViewMode(VIEW_MODE_SPECTRUM)
    else:
      errors = '\n'.join('%4d. %s' % (i+1,err) for i,err in enumerate(self.model.validation_errors))
      errmsg = "The following errors prevented this spectrum from being processed:\n\n%s\n" % errors
      dlg = wx.MessageDialog(self.view, errmsg, 'Error', wx.OK | wx.ICON_ERROR)
      dlg.ShowModal()

  def OnViewMode(self, evt):
    mode = self.view.view_mode.GetSelection()
    self.SetViewMode(mode)

  def OnIndividualMin(self, evt):
    self.individual_range[0] = evt.GetInt()
    self.UpdateImageView()

  def OnIndividualMax(self, evt):
    self.individual_range[1] = evt.GetInt()
    self.UpdateImageView()

  def OnIndividualExp(self, evt):
    self.exposure_num = evt.GetInt() - 1
    self.SetViewMode(self.view_mode)

  def OnCombinedMin(self, evt):
    self.combined_range[0] = evt.GetInt()
    self.UpdateImageView()

  def OnCombinedMax(self, evt):
    self.combined_range[1] = evt.GetInt()
    self.UpdateImageView()

  def UpdateImageView(self):
    self.SetViewMode(self.view_mode)

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

  def load(self, filename):
    # XXX handle errors...
    self.model.load(filename)
    self.ModelToView()
