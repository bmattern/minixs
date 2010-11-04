import wx
import minixs.filter as filter
import filter_view

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

STATUS_COORDS  = 0
STATUS_MESSAGE = 1

"""
FILTER_MIN  = 0
FILTER_MAX  = 1
FILTER_LOW  = 2
FILTER_HIGH = 3
FILTER_NBOR = 4
NUM_FILTERS = 5

FILTER_NAMES = [
    'Min Visible',
    'Max Visible',
    'Low Cutoff',
    'High Cutoff',
    'Neighbors'
    ]

FILTER_EMISSION_TYPE_FE_KBETA = 0
FILTER_EMISSION_TYPE_NAMES = [
    "Fe Kbeta"
    ]

FILTER_IDS = [ wx.NewId() for n in FILTER_NAMES ]
"""

FILTER_DEFAULTS = {
    'Min Visible': (0, True),
    'Max Visible': (1000, False),
    'Low Cutoff': (5, True),
    'High Cutoff': (10000, False),
    'Neighbors': (2, True),
    'Emission Filter': (0, False)
    }

