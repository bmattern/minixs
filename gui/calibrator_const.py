import wx

ID_MAIN_FRAME       = wx.NewId()
ID_DATASET_NAME     = wx.NewId()
ID_EXPOSURE_LIST    = wx.NewId()
ID_READ_ENERGIES    = wx.NewId()
ID_SELECT_EXPOSURES = wx.NewId()
ID_APPEND_ROW       = wx.NewId()
ID_DELETE_ROW       = wx.NewId()
ID_CLEAR_ENERGIES   = wx.NewId()
ID_CLEAR_EXPOSURES  = wx.NewId()
ID_DISPERSIVE_DIR   = wx.NewId()
ID_EXPOSURE_SLIDER  = wx.NewId()
ID_CALIBRATE        = wx.NewId()
ID_FILTER_EMISSION  = wx.NewId()
ID_IMAGE_PANEL      = wx.NewId()

ID_VIEW_TYPE        = wx.NewId()
ID_SHOW_XTALS       = wx.NewId()

ID_IMPORT_XTALS     = wx.NewId()
ID_EXPORT_XTALS     = wx.NewId()

ID_LOAD_SCAN        = wx.NewId()

WILDCARD_CALIB = "Calibration Files (*.calib)|*.calib|Data Files (*.dat)|*.dat|Text Files (*.txt)|*.txt|All Files|*"
WILDCARD_EXPOSURE = "TIF Files (*.tif)|*.tif|All Files|*"
WILDCARD_XTAL = "Crystal Files (*.xtal)|*.xtal|Calibration Files (*.calib)|*.calib|Text Files (*.txt)|*.txt|All Files|*"
WILDCARD_XTAL_EXPORT = "Crystal Files (*.xtal)|*.xtal"
WILDCARD_SCAN = "Scan Files (*.nnnn)|*.????|Text Files (*.txt)|*.txt|All Files|*"


STATUS_COORDS  = 0
STATUS_MESSAGE = 1
