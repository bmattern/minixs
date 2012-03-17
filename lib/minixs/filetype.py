FILE_UNKNOWN     = -1
FILE_CALIBRATION = 0
FILE_XTALS       = 1
FILE_XES         = 2
FILE_RIXS        = 3

FILE_TYPES = [
    'calibration matrix',
    'crystal boundaries',
    'XES spectrum',
    'RIXS spectrum'
    ]

def determine_filetype(path):
  with open(path) as f:
    line = f.readline()
    if len(line) == 0 or line[0] != "#":
      return FILE_UNKNOWN

    s = line[2:]

    if not s.lower().startswith('minixs'):
      return 0

    t = s[7:].strip()
    if t in FILE_TYPES:
      return FILE_TYPES.index(t)

    return FILE_UNKNOWN

class InvalidFileError(Exception):
  pass
