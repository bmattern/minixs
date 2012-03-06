FILE_UNKNOWN     = 0
FILE_CALIBRATION = 1
FILE_XTALS       = 2
FILE_XES         = 3
FILE_RIXS        = 4

FILE_TYPES = {
    'calibration matrix': FILE_CALIBRATION,
    'crystal boundaries': FILE_XTALS,
    'xes spectrum': FILE_XES,
    'rixs spectrum': FILE_RIXS,
    'emission spectrum': FILE_XES,
    }


def determine_filetype(path):
  with open(path) as f:
    line = f.readline()
    return determine_filetype_from_header(line)

def determine_filetype_from_header(header):
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

class InvalidFileError(Exception):
  pass
