import os, sys
import minixs as mx
import numpy as np
import minixs.info as mxinfo
import wx


PADDING = 10

ID_CALIB = wx.NewId()
ID_CALIB_LOAD = wx.NewId()
ID_CALIB_VIEW = wx.NewId()

ID_EXPOSURE_LIST = wx.NewId()
ID_EXPOSURE_ADD = wx.NewId()
ID_EXPOSURE_DEL = wx.NewId()


class ProcessorApp(wx.App):
  def __init__(self, *args, **kwargs):
    wx.App.__init__(self, *args, **kwargs)


    model = ProcessorModel()
    view = ProcessorFrame(None)
    controller = ProcessorController(view, model)

    view.Show()


class ProcessorFrame(wx.Frame):
  def __init__(self, *args, **kwargs):
    wx.Frame.__init__(self, *args, **kwargs)

    menu_info = [
        ('&File', [
          ('&Open', wx.ID_OPEN, 'Load XES File'),
          ('&Save', wx.ID_SAVE, 'Save XES File'),
          ('', None, None),
          ('E&xit', wx.ID_EXIT, 'Terminate this program'),
          ]),
        ('&Help', [
          ('&About', wx.ID_ABOUT, 'About this program')
          ]),
        ]
    self.CreateMenuBar(menu_info)
    self.panel = ProcessorPanel(self, wx.ID_ANY)
    self.CreateStatusBar()

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

class CalibrationMatrixSelector(wx.Panel):
  def __init__(self, *args, **kwargs):
    wx.Panel.__init__(self, *args, **kwargs)

    hbox = wx.BoxSizer(wx.HORIZONTAL)
    label = wx.StaticText(self, wx.ID_ANY, "Calibration Matrix:")
    hbox.Add(label, 0, wx.ALIGN_CENTER_VERTICAL, PADDING)

    entry = wx.TextCtrl(self, ID_CALIB)
    hbox.Add(entry, 1, wx.EXPAND, PADDING)
    self.calibration_filename_entry = entry

    button = wx.Button(self, ID_CALIB_LOAD, "...")
    hbox.Add(button, 0, 0, PADDING)
    self.load_calibration_button = button

    button = wx.Button(self, ID_CALIB_VIEW, "View")
    hbox.Add(button, 0, 0, PADDING)
    self.view_calibration_button = button

    self.SetSizerAndFit(hbox)

class ExposureSelector(wx.Panel):
  def __init__(self, *args, **kwargs):
    wx.Panel.__init__(self, *args, **kwargs)

    hbox = wx.BoxSizer(wx.HORIZONTAL)
    label = wx.StaticText(self, wx.ID_ANY, "Spectrum Images:")
    hbox.Add(label, 0, wx.ALIGN_TOP, PADDING)

    listbox = wx.ListBox(self, ID_EXPOSURE_LIST)
    hbox.Add(listbox, 1, wx.EXPAND, PADDING)
    self.listbox = listbox

    vbox = wx.BoxSizer(wx.VERTICAL)
    button = wx.Button(self, ID_EXPOSURE_ADD, "Add Files...")
    vbox.Add(button, 0, 0, PADDING)
    button = wx.Button(self, ID_EXPOSURE_DEL, "Delete Selected")
    vbox.Add(button, 0, 0, PADDING)

    hbox.Add(vbox, 0, 0, PADDING)

    self.SetSizerAndFit(hbox)

class ProcessorPanel(wx.Panel):
  def __init__(self, *args, **kwargs):
    wx.Panel.__init__(self, *args, **kwargs)

    self.CreateGUI()

  def CreateGUI(self):
    vbox = wx.BoxSizer(wx.VERTICAL)

    calibration_panel = CalibrationMatrixSelector(self, wx.ID_ANY)
    vbox.Add(calibration_panel, 0, wx.EXPAND, PADDING)

    exposure_panel = ExposureSelector(self, wx.ID_ANY)
    vbox.Add(exposure_panel, 0, wx.EXPAND, PADDING)

    self.SetSizerAndFit(vbox)

class XESFileDialog(wx.FileDialog):
  def __init__(self, parent, message, directory, style):
    wildcard = "XES Data Files (*.xes)|*.xes|Text Files (*.txt,*.dat)|*.txt,*.dat"

    wx.FileDialog.__init__(self,
        parent,
        message,
        directory,
        wildcard=wildcard,
        style=style,
        )

class ProcessorModel(object):
  def __init__(self):
    self.calibration = mxinfo.CalibrationInfo()
    self.xes = mxinfo.XESInfo()

  def load(self, filename):
    xes = mxinfo.XESInfo()
    xes.load(filename)

    self.xes = xes

    calibration = mxinfo.CalibrationInfo()
    calibration.load(self.xes.calibration_filename)
    self.calibration = calibration

class ProcessorController(object):
  def __init__(self, view, model):

    self.view = view
    self.model = model

    self.open_directory = ''
    self.save_directory = ''

    self.BindCallbacks()

  def BindCallbacks(self):
    self.view.Bind(wx.EVT_MENU, self.OnMenuOpen, id=wx.ID_OPEN)
    self.view.Bind(wx.EVT_MENU, self.OnMenuSave, id=wx.ID_SAVE)
    self.view.Bind(wx.EVT_MENU, self.OnMenuExit, id=wx.ID_EXIT)
    self.view.Bind(wx.EVT_MENU, self.OnMenuAbout, id=wx.ID_ABOUT)

  def OnMenuOpen(self, evt):
    if self.open_directory is None:
      self.open_directory = self.save_directory

    dlg = XESFileDialog(self.view, "Select an XES data file to open", self.open_directory, wx.FD_OPEN)
    ret = dlg.ShowModal()

    if ret == wx.ID_OK:
      directory = dlg.GetDirectory()
      filename = dlg.GetFilename()

      self.open_directory = directory
      self.model.load(os.path.join(directory, filename))

      # XXX update view

  def OnMenuSave(self, evt):
    if self.save_directory is None:
      self.save_directory = self.open_directory
    dlg = XESFileDialog("Select a file to save XES data to", self.save_directory, wx.FD_SAVE)
    ret = dlg.ShowModel()

    if ret == wx.ID_OK:
      directory = dlg.GetDirectory()
      filename = dlg.GetFilename()

      self.save_directory = directory
      self.model.save(os.path.join(directory, filename))

  def OnMenuExit(self, evt):
    pass

  def OnMenuAbout(self, evt):
    pass



if __name__ == "__main__":
  app = ProcessorApp()
  app.MainLoop()
