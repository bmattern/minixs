import minixs as mx
import os

FILE_UNKNOWN     = 0
FILE_CALIBRATION = 1
FILE_XTALS       = 2
FILE_XES         = 3
FILE_RIXS        = 4
FILE_EXPOSURE    = 5

FILE_TYPES = {
    'calibration matrix': FILE_CALIBRATION,
    'crystal boundaries': FILE_XTALS,
    'xes spectrum': FILE_XES,
    'rixs spectrum': FILE_RIXS,
    'emission spectrum': FILE_XES,
    }

def determine_filetype(path):
  """
  Determine file type from extension or header

  Returns one of:
    FILE_UNKNOWN, FILE_CALIBRATION, FILE_XTALS, FILE_XES, FILE_RIXS, FILE_EXPOSURE
  """
  if os.path.splitext(path)[-1].lower() in ['.tif', '.tiff']:
    return FILE_EXPOSURE

  with open(path) as f:
    line = f.readline()
    return determine_filetype_from_header(line)

def determine_filetype_from_header(header):
  """
  Determine file type from first header line

  Returns one of:
    FILE_UNKNOWN, FILE_CALIBRATION, FILE_XTALS, FILE_XES, FILE_RIXS
  """
  if len(header) == 0 or header[0] != "#":
    return FILE_UNKNOWN

  s = header[2:].strip().lower()

  valid_prefix = False

  # check prefix of header from most recent to oldest
  for pref in ["minixes", "minixs"]:
    if s.startswith(pref):
      s = s[len(pref):].strip()
      valid_prefix = True
      break

  if not valid_prefix:
    return FILE_UNKNOWN

  return FILE_TYPES.get(s, FILE_UNKNOWN)

def load(filename):
  """
  Load a file after determining its type

  Parameters:
    filename - filename to load
  Returns:
    object of corresponding type. one of:
      mx.calibrate.Calibration
      mx.emission.EmissionSpectrum
      mx.rixs.RIXS
      mx.exposure.Exposure
  """

  ftype = determine_filetype(filename)
  cl = {
      FILE_CALIBRATION: mx.calibrate.Calibration,
      FILE_XES: mx.emission.EmissionSpectrum,
      FILE_RIXS: mx.rixs.RIXS,
      FILE_EXPOSURE: mx.exposure.Exposure,
      }.get(ftype, None)
  if cl:
    return cl(filename)
  else:
    raise InvalidFileError

class InvalidFileError(Exception):
  pass
