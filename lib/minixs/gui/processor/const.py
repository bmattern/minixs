import wx


VIEW_MODE_COMBINED   = 0
VIEW_MODE_INDIVIDUAL = 1
VIEW_MODE_CALIB      = 2
VIEW_MODE_SPECTRUM   = 3

ID_MAIN_FRAME      = wx.NewId()

ID_DATASET         = wx.NewId()
ID_ENERGY          = wx.NewId()
ID_NORM            = wx.NewId()

ID_CALIB           = wx.NewId()
ID_CALIB_LOAD      = wx.NewId()
ID_SPECTROMETER    = wx.NewId()

ID_EXPOSURE_LIST   = wx.NewId()
ID_EXPOSURE_ADD    = wx.NewId()
ID_EXPOSURE_DEL    = wx.NewId()

ID_EXPOSURE_VIEW   = wx.NewId()

ID_FILTER_ADD      = wx.NewId()
ID_FILTER_REMOVE   = wx.NewId()

ID_VIEW_MODE       = wx.NewId()

ID_PROCESS         = wx.NewId()

ID_INDIVIDUAL_MIN  = wx.NewId()
ID_INDIVIDUAL_MAX  = wx.NewId()
ID_INDIVIDUAL_EXP  = wx.NewId()

ID_COMBINED_MIN    = wx.NewId()
ID_COMBINED_MAX    = wx.NewId()

STATUS_COORDS  = 0
STATUS_MESSAGE = 1
