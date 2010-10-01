import minixs      as mx
import minixs.info as mxinfo
import numpy       as np
import os, sys
import util
import wx

from image_view       import EVT_COORDS
from image_tools      import RangeTool, Crosshair, EVT_RANGE_CHANGED, EVT_RANGE_ACTION_CHANGED
from matplotlib       import cm, colors

from calibrator_const import *
from wildcards        import *

class CalibratorController(object):
  UPDATE_FILTERS = 1
  UPDATE_EXPOSURES = 2
  UPDATE_SELECTED_EXPOSURE = 4

  def __init__(self, view, model):
    self.view = view
    self.model = model

    self.show_calibration_matrix = False

    self.update_view_flag = 0
    self.update_view_timeout = None

    self.changed = False

    self.selected_exposure = 1
    self.exposures = []
    self.energies = []

    self.raw_pixels = None

    self.crosshair = Crosshair(self.view.panel.exposure_panel.image_view)
    self.crosshair.SetActive(True)
    self.crosshair.ToggleDirection(Crosshair.HORIZONTAL | Crosshair.VERTICAL, True)

    self.range_tool = RangeTool(self.view.panel.exposure_panel.image_view)
    self.range_tool.ToggleDirection(RangeTool.HORIZONTAL | RangeTool.VERTICAL, True)
    self.range_tool.SetMultiple(True)

    self.CalibrationValid(False)

    self.dialog_dirs = {
        'last': '',
        }

    a = wx.AboutDialogInfo()
    a.SetName("minIXS Calibrator")
    a.SetDescription("Mini Inelastic X-ray Spectrometer Calibrator")
    a.SetVersion("0.0.1")
    a.SetCopyright("(c) Seidler Group 2010")
    a.AddDeveloper("Brian Mattern (bmattern@uw.edu)")
    self.about_info = a

    self.BindCallbacks()

  def BindCallbacks(self):
    callbacks = [
        (wx.EVT_CLOSE, [ (ID_MAIN_FRAME, self.OnClose) ]),
        (wx.EVT_MENU, [
          (wx.ID_EXIT, self.OnExit),
          (wx.ID_OPEN, self.OnOpen),
          (wx.ID_SAVE, self.OnSave),
          (ID_IMPORT_XTALS, self.OnImportXtals),
          (ID_EXPORT_XTALS, self.OnExportXtals),
          (wx.ID_ABOUT, self.OnAbout),
          ]),
        (wx.EVT_TEXT, [
          (ID_DATASET_NAME, self.OnDatasetName),
          ]),
        (wx.EVT_BUTTON, [
          (ID_READ_ENERGIES, self.OnReadEnergies),
          (ID_SELECT_EXPOSURES, self.OnSelectExposures),
          (ID_APPEND_ROW, self.OnAppendRow),
          (ID_DELETE_ROW, self.OnDeleteRow),
          (ID_CLEAR_ENERGIES, self.OnClearEnergies),
          (ID_CLEAR_EXPOSURES, self.OnClearExposures),
          (ID_CALIBRATE, self.OnCalibrate),
          ]),
        (wx.EVT_LIST_END_LABEL_EDIT, [
          (ID_EXPOSURE_LIST, self.OnListEndLabelEdit),
          ]),
        (wx.EVT_SLIDER, [
          (ID_EXPOSURE_SLIDER, self.OnExposureSlider),
          ]),
        (wx.EVT_CHECKBOX, [
          (ID_FILTER_EMISSION, self.OnFilterEmissionCheck),
          (ID_SHOW_XTALS, self.OnShowXtals),
          ]),
        (wx.EVT_RADIOBOX, [
          (ID_VIEW_TYPE, self.OnViewType),
          ]),
        (wx.EVT_CHOICE, [
          (ID_FILTER_EMISSION, self.OnFilterEmissionChoice),
          (ID_DISPERSIVE_DIR, self.OnDispersiveDir),
          ]),
        (EVT_RANGE_ACTION_CHANGED, [ (ID_IMAGE_PANEL, self.OnImageAction), ]),
        (EVT_RANGE_CHANGED, [ (ID_IMAGE_PANEL, self.OnImageXtals), ]),
        (EVT_COORDS, [ (ID_IMAGE_PANEL, self.OnImageCoords), ]),
        ]

    for event, bindings in callbacks:
      for id, callback in bindings:
        self.view.Bind(event, callback, id=id)

    for id in FILTER_IDS:
      self.view.Bind(wx.EVT_SPINCTRL, self.OnFilterSpin, id=id)
      self.view.Bind(wx.EVT_CHECKBOX, self.OnFilterCheck, id=id)

  def model_to_view(self):
    self.view.panel.dataset_name.SetValue(self.model.dataset_name)

    self.view.panel.filter_panel.dispersive_direction.SetSelection(self.model.dispersive_direction)

    # set exposures and energies
    self.view.panel.exposure_list.ClearExposures()
    self.view.panel.exposure_list.ClearEnergies()
    for f in self.model.exposure_files:
      self.view.panel.exposure_list.AppendExposure(f)
    for e in self.model.energies:
      self.view.panel.exposure_list.AppendEnergy(e)

    # set filters
    filters = [(False, val) for enabled,val in self.view.panel.filter_panel.filter_defaults]

    self.view.panel.filter_panel.filter_emission_check.SetValue(False)
    self.view.panel.filter_panel.filter_emission_choice.Enable(False)
    for name, val in self.model.filters:
      if name == 'Filter Emission':
        self.view.panel.filter_panel.filter_emission_check.SetValue(True)
        self.view.panel.filter_panel.filter_emission_choice.Enable()
        self.view.panel.filter_panel.filter_emission_choice.SetSelection(val)
      else:
        i = FILTER_NAMES.index(name)
        filters[i] = (True, val)

    self.view.panel.filter_panel.set_filters(filters)

    # set xtals
    self.range_tool.rects = self.model.xtals

  def view_to_model(self):
    self.model.dataset_name = self.view.panel.dataset_name.GetValue()
    self.model.dispersive_direction = self.view.panel.filter_panel.dispersive_direction.GetSelection()

    # get energies and exposures
    valid, energies, exposure_files = self.view.panel.exposure_list.GetData()
    self.exposure_list_valid = valid

    self.model.energies = energies
    self.model.exposure_files = exposure_files

    # get filters
    self.model.filters = []
    filters = self.view.panel.filter_panel.get_filters()
    for i, (enabled, val) in enumerate(filters):
      if enabled:
        self.model.filters.append( (FILTER_NAMES[i], val) )
    self.model.filters.append((
        'Filter Emission',
        self.view.panel.filter_panel.filter_emission_choice.GetSelection()
        ))

    # get xtals
    self.model.xtals = self.range_tool.rects

  def OnOpen(self, evt):
    filename = self.FileDialog(
        'open',
        'Select a calibration file to open',
        wildcard=WILDCARD_CALIB
        )

    if (filename):
      self.model.load(filename)
      self.model_to_view()
      self.UpdateView(self.UPDATE_EXPOSURES | self.UPDATE_FILTERS)
      if self.show_calibration_matrix:
        self.ShowCalibrationMatrix()
      self.CalibrationValid(True)
      self.Changed(False)

  def OnSave(self, evt):
    header_only = False
    if self.calibration_valid == False:
      errdlg = wx.MessageDialog(self.view, "Warning: You have changed parameters since last calibrating. Saving now will only save the parameters, and not the matrix itself.", "Error", wx.OK | wx.CANCEL | wx.ICON_WARNING)
      ret = errdlg.ShowModal()
      errdlg.Destroy()

      if ret == wx.ID_OK:
        header_only = True
      else:
        return

    filename = self.FileDialog(
        'save',
        'Select file to save calibration to',
        wildcard=WILDCARD_CALIB,
        save=True
        )
    if filename:
      self.view_to_model()
      self.model.save(filename, header_only=header_only)

  def OnImportXtals(self, evt):
    filename = self.FileDialog(
        'xtals',
        'Select file to import crystals from',
        wildcard=WILDCARD_XTAL,
        )

    if not filename:
      return

    t = mxinfo.determine_filetype(filename)

    if t == mxinfo.FILE_XTALS:
      with open(filename) as f:
        xtals = []
        for line in f:
          if line[0] == "#": 
            continue
          x1,y1,x2,y2 = [int(s.strip()) for s in line.split()]
          xtals.append([[x1,y1],[x2,y2]])
        self.model.xtals = xtals

    elif t == mxinfo.FILE_CALIBRATION:
      ci = mxinfo.CalibrationInfo()
      ci.load(filename, header_only=True)
      self.model.xtals = ci.xtals

    else:
      errdlg = wx.MessageDialog(self.view, "Unknown Filetype", "Error", wx.OK | wx.ICON_ERROR)
      errdlg.ShowModal()
      errdlg.Destroy()

    self.range_tool.rects = self.model.xtals
    self.view.panel.exposure_panel.image_view.Refresh()
    self.CalibrationValid(False)
    self.Changed()

  def OnExportXtals(self, evt):
    filename = self.FileDialog(
        'xtals',
        'Select file to export crystals to',
        wildcard=WILDCARD_XTAL_EXPORT,
        save=True
        )

    if not filename:
      return

    if os.path.exists(filename):
      qdlg = wx.MessageDialog(self.view, "Overwrite File?", "Warning", wx.YES | wx.NO | wx.ICON_WARNING)
      ret = qdlg.ShowModal()
      qdlg.Destroy()
      if ret == wx.NO:
        return

    with open(filename, 'w') as f:
      f.write("# minIXS crystal boundaries\n")
      f.write("# x1\ty1\tx2\ty2\n")
      for (x1,y1),(x2,y2) in self.model.xtals:
        f.write("%d\t%d\t%d\t%d\n" % (x1,y1,x2,y2))

  def OnClose(self, evt):
    if not evt.CanVeto():
      self.view.Destroy()
      return True

    if self.changed:
      message = "There are unsaved changes. Continuing will exit without saving these."
      errdlg = wx.MessageDialog(self.view, message, "Warning", wx.OK | wx.CANCEL | wx.ICON_WARNING)
      ret = errdlg.ShowModal()
      errdlg.Destroy()

      if ret != wx.ID_OK:
        evt.Veto()
        return False

    self.view.Destroy()

  def OnExit(self, evt):
    self.view.Close()

  def OnAbout(self, evt):
    wx.AboutBox(self.about_info)

  def OnDatasetName(self, evt):
    self.model.dataset_name = evt.GetString()
    self.Changed()

  def OnReadEnergies(self, evt):
    dlg = LoadEnergiesDialog(self.view)
    dlg.Bind(wx.EVT_BUTTON, self.OnLoadScan, id=ID_LOAD_SCAN)
    self.scan_dialog = dlg
    ret = dlg.ShowModal()

    if ret == wx.ID_OK:
      filename, column = dlg.get_info()
      energies = mx.read_scan_info(filename, [column])[0]

      for e in energies:
        self.view.panel.exposure_list.AppendEnergy(e)

      self.UpdateView(self.UPDATE_EXPOSURES)
      self.CalibrationValid(False)
      self.Changed()

    dlg.Destroy()
    self.scan_dialog = None

  def OnLoadScan(self, evt):
    filename = self.FileDialog(
        'scan',
        'Select a text file',
        wildcard=WILDCARD_SCAN
        )

    if filename:
      self.scan_dialog.set_filename(filename)

  def OnClearEnergies(self, evt):
    self.view.panel.exposure_list.ClearEnergies()
    self.UpdateView(self.UPDATE_EXPOSURES)
    self.CalibrationValid(False)
    self.Changed()

  def OnSelectExposures(self, evt):
    filenames = self.FileDialog(
        'exposures',
        'Select Exposure Files',
        wildcard=WILDCARD_EXPOSURE,
        multiple=True
        )
    for f in filenames:
      self.view.panel.exposure_list.AppendExposure(f)

    if filenames:
      self.UpdateView(self.UPDATE_EXPOSURES)
      self.CalibrationValid(False)

  def OnAppendRow(self, evt):
    self.view.panel.exposure_list.AppendRow()
    self.Changed()

  def OnDeleteRow(self, evt):
    self.view.panel.exposure_list.DeleteRow()
    self.Changed()

  def OnImageAction(self, evt):
    action = evt.action

    status = ""
    if evt.range is None:
      if evt.in_window:
        status = "L: Click and drag to define crystal boundary"
      else:
        status == ""
    elif action & RangeTool.ACTION_PROPOSED:
      if action & RangeTool.ACTION_MOVE:
        status = "L: Move crystal  R: Delete crystal"
      elif action & RangeTool.ACTION_RESIZE:
        status = "L: Resize crystal  R: Delete crystal"

    self.view.SetStatusText(status, STATUS_MESSAGE)

  def OnImageXtals(self, evt):
    self.CalibrationValid(False)
    self.Changed()

  def OnImageCoords(self, evt):
    x, y = evt.x, evt.y
    if x == None and y == None:
      coords = ''
    else:
      coords = "%3d,%3d" % (evt.x, evt.y)
      if self.raw_pixels is not None:
        h, w = self.raw_pixels.shape
        if x >= 0 and x < w and y >= 0 and y < h:
          z = self.raw_pixels[evt.y,evt.x]
          if z == int(z):
            coords += " -> %d" % z
          else:
            coords += " -> %.2f" % z

    self.view.SetStatusText(coords, STATUS_COORDS)
    pass

  def FileDialog(self, type, title, wildcard='', save=False, multiple=False):
    """
    Show a file dialog and return selected path(s)
    """
    if type not in self.dialog_dirs.keys() or not self.dialog_dirs[type]:
      self.dialog_dirs[type] = self.dialog_dirs['last']

    style = 0
    if save:
      style |= wx.FD_SAVE
    else:
      style |= wx.FD_OPEN
    if multiple:
      style |= wx.FD_MULTIPLE

    dlg = wx.FileDialog(self.view, title,
        self.dialog_dirs[type],
        wildcard=wildcard,
        style=style)

    ret = dlg.ShowModal()

    paths = []
    if ret == wx.ID_OK:
      directory = dlg.GetDirectory()
      self.dialog_dirs[type] = self.dialog_dirs['last'] = directory
      filenames = dlg.GetFilenames()

      paths = [os.path.join(directory, f) for f in filenames]

    dlg.Destroy()

    if not paths:
      return None

    if multiple:
      return paths
    else:
      return paths[0]

  def OnClearExposures(self, evt):
    self.view.panel.exposure_list.ClearExposures()
    self.UpdateView(self.UPDATE_EXPOSURES)
    self.CalibrationValid(False)
    self.Changed()

  def OnListEndLabelEdit(self, evt):
    self.UpdateView(self.UPDATE_EXPOSURES)
    self.CalibrationValid(False)
    self.Changed()

  def OnFilterSpin(self, evt):
    self.UpdateView(self.UPDATE_FILTERS)
    self.CalibrationValid(False)
    self.Changed()

  def OnFilterCheck(self, evt):
    i = FILTER_IDS.index(evt.Id)
    self.view.panel.filter_panel.set_filter_enabled(i, evt.Checked())
    self.UpdateView(self.UPDATE_FILTERS)
    self.CalibrationValid(False)
    self.Changed()

  def OnFilterEmissionCheck(self, evt):
    self.view.panel.filter_panel.filter_emission_choice.Enable(evt.Checked())
    self.UpdateView(self.UPDATE_FILTERS)
    self.CalibrationValid(False)
    self.Changed()

  def OnFilterEmissionChoice(self, evt):
    self.UpdateView(self.UPDATE_FILTERS)
    self.CalibrationValid(False)
    self.Changed()

  def OnDispersiveDir(self, evt):
    self.CalibrationValid(False)
    self.Changed()

  def OnExposureSlider(self, evt):
    i = evt.GetInt()
    self.SelectExposure(i)

  def OnViewType(self, evt):
    if evt.GetInt() == 1:
      self.ShowCalibrationMatrix()
      self.view.panel.exposure_panel.slider.Enable(False)
    else:
      self.show_calibration_matrix = False
      self.UpdateView(self.UPDATE_SELECTED_EXPOSURE)
      if len(self.exposures) > 1:
        self.view.panel.exposure_panel.slider.Enable(True)

  def OnShowXtals(self, evt):
    show = evt.Checked()
    self.range_tool.SetVisible(show)
    self.range_tool.SetActive(show)

  def OnCalibrate(self, evt):
    self.view_to_model()
    valid, errors = self.Validate()

    if not valid:
      errors = [ '% 2d) %s' % (i+1, err) for i, err in enumerate(errors) ]
      message = 'The following must be fixed before calibrating:\n\n' + '\n\n'.join(errors)
      errdlg = wx.MessageDialog(self.view, message, "Error", wx.OK | wx.ICON_ERROR)
      errdlg.ShowModal()
      errdlg.Destroy()
      self.calibration_invalid = True
      return

    self.view.SetStatusText("Calibrating... Please Wait...", STATUS_MESSAGE)

    c = mx.Calibrator(self.model.energies, self.model.exposure_files, self.model.dispersive_direction)

    for energy, exposure in zip(c.energies, c.images):
      self.ApplyFilters(energy, exposure)

    c.calibrate(self.model.xtals)
    self.model.calibration_matrix = c.calib

    #XXX check that calib seems reasonable (monotonic, etc)
    # also, report residues from fit
    self.CalibrationValid(True)
    self.Changed()

    self.ShowCalibrationMatrix()

    self.view.SetStatusText("", STATUS_MESSAGE)

  def Validate(self):
    errors = []
    valid = True

    if not self.exposure_list_valid:
      valid = False
      errors.append("The exposure list is invalid. Make sure that each row contains an energy and an exposure filename.")

    if len(self.model.energies) < 2:
      valid = False
      errors.append("At least two calibration exposures are required for calibration. A larger number of exposures will give a better fit.")

    if len(self.model.xtals) < 1:
      valid = False
      errors.append("Define the boundary of at least one crystal.")

    intersecting = False
    for xa in self.model.xtals:
      if intersecting:
        break

      for xb in self.model.xtals:
        if xa == xb:
          continue
        if util.xtals_intersect(xa, xb):
          valid = False
          errors.append("Crystal boundaries may not overlap.")
          intersecting = True
          break

    return valid, errors

  def ShowCalibrationMatrix(self):
    self.show_calibration_matrix = True

    self.view.panel.exposure_panel.label.SetLabel("Calibration Matrix")
    c = self.model.calibration_matrix
    self.raw_pixels = c
    if len(c) == 0:
      self.view.panel.exposure_panel.SetPixels(None)
      return
    nonzero = c[np.where(c>0)]
    if len(nonzero) == 0:
      min_cal = 0
    else:
      min_cal = c[np.where(c>0)].min()
    max_cal = c.max()
    p = colors.Normalize(min_cal, max_cal)(c)
    self.view.panel.exposure_panel.SetPixels(p, cm.jet)

    self.view.panel.tools_panel.view_type.SetSelection(1)

  def SelectExposure(self, num):
    num_exposures = len(self.exposures)
    if num > num_exposures:
      num = num_exposures

    self.selected_exposure = num
    self.UpdateView(self.UPDATE_SELECTED_EXPOSURE)

  def FilterEmission(self, energy, exposure, emission_type):
    if emission_type == FILTER_EMISSION_TYPE_FE_KBETA:
      if energy >= 7090:
        z = 1.3214 * energy - 9235.82 - 12
        exposure.pixels[0:z,:] = 0
    else:
      raise ValueError("Unimplemented Emission Filter")

  def ApplyFilters(self, energy, exposure):
    min_vis = None
    max_vis = None
    low_cutoff = None
    high_cutoff = None
    neighbors = None

    filter_emission = self.view.panel.filter_panel.filter_emission_check.GetValue()

    if filter_emission:
      emission_type = self.view.panel.filter_panel.filter_emission_choice.GetSelection()
      self.FilterEmission(energy, exposure, emission_type)

    self.filters = self.view.panel.filter_panel.get_filters()

    for i, (enabled, val) in enumerate(self.filters):
      if not enabled:
        continue

      if i == FILTER_MIN:
        min_vis = val
      elif i == FILTER_MAX:
        max_vis = val
      elif i == FILTER_LOW:
        low_cutoff = val
      elif i == FILTER_HIGH:
        high_cutoff = val
      elif i == FILTER_NBOR:
        neighbors = val

    exposure.filter_low_high(low_cutoff, high_cutoff)
    if neighbors:
      exposure.filter_neighbors(neighbors)

    p = exposure.pixels
    if min_vis is None: min_vis = p.min()
    if max_vis is None: max_vis = p.max()
    p = colors.Normalize(min_vis, max_vis)(p)
    return p

  def CalibrationValid(self, valid):
    self.calibration_valid = valid
    self.view.panel.calibrate_button.Enable(not valid)

  def Changed(self, changed=True):
    """Set whether data has changed since last save"""
    self.changed = changed
    #XXX indicate somehow that save is required

  def UpdateView(self, flag):
    self.update_view_flag |= flag
    delay = 1000./30.

    if self.update_view_timeout is None:
      self.update_view_timeout = wx.CallLater(delay, self.OnUpdateViewTimeout)
    elif not self.update_view_timeout.IsRunning():
      self.update_view_timeout.Restart(delay)

  def OnUpdateViewTimeout(self):
    if self.show_calibration_matrix:
      return

    if self.update_view_flag & self.UPDATE_EXPOSURES:
      # update list of exposures
      valid, self.energies, self.exposures = self.view.panel.exposure_list.GetData()
      self.exposure_list_valid = valid

      # set status text to indicate whether list is valid or not
      if not valid:
        self.view.SetStatusText("Exposure List Invalid", STATUS_MESSAGE)
      else:
        self.view.SetStatusText("", STATUS_MESSAGE)

      # update slider
      num_exposures = len(self.exposures)

      show_xtals = (num_exposures >= 1)
      self.range_tool.SetActive(show_xtals)
      self.range_tool.SetVisible(show_xtals)

      if num_exposures <= 1:
        self.view.panel.exposure_panel.slider.Enable(False)
        self.view.panel.exposure_panel.slider.SetRange(0,1)
        self.view.panel.exposure_panel.slider.SetValue(0)
      else:
        self.view.panel.exposure_panel.slider.Enable(True)
        self.view.panel.exposure_panel.slider.SetRange(1,num_exposures)

    if self.update_view_flag & (self.UPDATE_EXPOSURES|self.UPDATE_SELECTED_EXPOSURE|self.UPDATE_FILTERS):
      # get index of selected exposure and ensure it is within range
      i = self.selected_exposure - 1
      if i >= len(self.exposures):
        i = len(self.exposures) - 1
      if i == -1:
        # no exposures
        self.view.panel.exposure_panel.label.SetLabel("No Exposures Loaded...")
        self.raw_pixels = None
        self.view.panel.exposure_panel.SetPixels(None)
      else:
        filename = self.exposures[i]
        energy = self.energies[i]

        e = mx.Exposure(filename)
        self.raw_pixels = e.pixels.copy()
        p = self.ApplyFilters(energy, e)
        self.view.panel.exposure_panel.SetPixels(p)

        text = '%d/%d %s - %.2f eV' % (self.selected_exposure, len(self.exposures), os.path.basename(filename), energy)
        self.view.panel.exposure_panel.label.SetLabel(text)

    self.update_view_flag = 0
