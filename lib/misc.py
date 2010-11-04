from minixs import ScanFile
from numpy import where, min, argmin, sum, average, abs, roll
from itertools import izip, product as iproduct
from scanfile import ScanFile

def gen_rects(horizontal_bounds=None, vertical_bounds=None):
  """Convert lists of horizontal and vertical boundary locations into rectangles"""
  return [
      ((l,t),(r,b))
      for (l,r) in izip(horizontal_bounds[0:-1], horizontal_bounds[1:])
      for (t,b) in izip(vertical_bounds[0:-1], vertical_bounds[1:])
      ]

def gen_file_list(prefix, vals, zero_pad=3, suffix='.tif'):
  """Generate a list of numerically sequenced file names"""
  fmt = '%s%%0%dd%s' % (prefix, zero_pad, suffix)
  return [fmt % val for val in vals]

def read_scan_info(scanfile, columns):
  """Read a subset of columns from a scan file

  The default columns correspond to the typical Mono Energy an I0 columns.
  The returned list is transposed so that the following works:

  c0, c6 = read_scan_info("scanfile.0001", [0,6])
  """

  s = ScanFile(scanfile)
  return s.data[:,columns].transpose()

def determine_dispersive_direction(e1, e2, threshold=.75, sep=20):
  """Given two exposures with increasing energy, determine
  the dispersive direction on the camera"""

  p1 = e1.pixels.copy()
  p2 = e2.pixels.copy()

  p1[where(p1 > 10000)] = 0
  p2[where(p2 > 10000)] = 0

  tests = [
      (0, (1,sep)), # DOWN
      (1, (-sep,-1)), # LEFT
      (0, (-sep,-1)),   # UP
      (1, (1,sep))    # RIGHT
      ]

  diffs = [
      min([ sum(abs(p2 - roll(p1,i,axis)))
            for i in range(i1,i2) ])
      for axis, (i1,i2) in tests ]

  if min(diffs) / average(diffs) < threshold:
    return argmin(diffs)

  return -1

