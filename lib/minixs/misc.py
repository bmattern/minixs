"""
Miscellanous functions
"""

import numpy as np
from itertools import izip
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

  p1[np.where(p1 > 10000)] = 0
  p2[np.where(p2 > 10000)] = 0

  tests = [
      (0, (1,sep)), # DOWN
      (1, (-sep,-1)), # LEFT
      (0, (-sep,-1)),   # UP
      (1, (1,sep))    # RIGHT
      ]

  diffs = [
      np.min([ np.sum(np.abs(p2 - np.roll(p1,i,axis)))
            for i in np.arange(i1,i2) ])
      for axis, (i1,i2) in tests ]

  if np.min(diffs) / np.average(diffs) < threshold:
    return np.argmin(diffs)

  return -1

def _find_boundaries(p, axis):
  """
  Helper function for find_xtal_boundaries
  """
  flat = p.sum(1-axis)

  # find boundaries
  mask = 1 * (flat > p.shape[1-axis])
  diffs = np.diff(mask)
  b1 = list(np.where(diffs==1)[0])
  b2 = list(np.where(diffs==-1)[0])

  # if nothing was found, xtals cover entire face
  if len(b1) == 0:
    b1 = [0]
  if len(b2) == 0:
    b2 = [p.shape[axis]]
  
  if b1[0] > b2[0]:
    b1.insert(0,0)
  if b2[-1] < b1[-1]:
    b2.append(p.shape[axis])

  return b1,b2

def find_xtal_boundaries(filtered_exposures, shrink=1):
  """
  From a full set of filtered calibration exposures, determine crystal boundaries

  Parameters
  ----------
    filtered_exposures: a list of Exposures
    shrink: the number of pixels to shrink determined boundary (default 1)

  The `shrink` parameter can be used to avoid edge effects or slight aparallelism.
  """
  # combine exposures into one
  p = filtered_exposures[0].pixels.copy()
  for e in filtered_exposures[1:]:
    np.add(p,e.pixels,p)

  x1s,x2s = _find_boundaries(p, 1)
  #y1s,y2s = _find_boundaries(p, 0)
  y1s = [2]
  y2s = [193]


  if len(x1s) != len(x2s) or len(y1s) != len(y2s):
    return None

  xtals = []
  for x1,x2 in izip(x1s, x2s):
    for y1,y2 in izip(y1s, y2s):
      xtals.append([[x1+shrink,y1+shrink],[x2-shrink,y2-shrink]])

  return xtals

def find_edges(pixels, direction=0, sign=-1, thresh=5):
  """
  Find edges of regions with pixels above thresh
  """
  return np.where(np.diff((pixels.max(direction)>thresh)*1) == sign)[direction]

def find_xtal_regions2(filtered_exposures, direction, thresh):
  r = [find_edges(e.pixels, direction, -1, thresh) for e in filtered_exposures]
  print r
  l = [find_edges(e.pixels, direction, +1, thresh) for e in filtered_exposures]

  return l,r

def collection_angle_correction(ci, d, return_theta=False):
  """
  Calculate angular spread in dispersive direction (in radians) for each pixel

  This should by used to correct for the fact that different pixels bin different energy widths (or alternatively cover different solid angles).

  This code has not been fully verified, so do not use at this time.
 
  Parameters
  ----------
    ci: Calibration object containing calibration matrix and xtals
    d:  lattice spacing
    return_theta: if True, return a matrix of angle values for each pixel
  """
  cac =  np.zeros(ci.calibration_matrix.shape)
  if return_theta:
    fulltheta =  np.zeros(ci.calibration_matrix.shape)

  E0 = np.pi * 1973.26 / d

  for xtal in ci.xtals:
    (x1,y1),(x2,y2) = xtal
    E = ci.calibration_matrix[y1:y2,x1:x2]

    dE = (np.roll(E,-1,0) - np.roll(E,1,0)) / 2.
    # fix up end points by extrapolation
    dE[0] = 2*dE[1] - dE[2]
    dE[-1] = 2*dE[-2] - dE[-3]

    theta = np.arccos(E0 / E)
    dtheta = dE / E / np.tan(theta)
 
    if return_theta:
      fulltheta[y1:y2, x1:x2] = theta
    cac[y1:y2, x1:x2] = dtheta

  if return_theta:
    return fulltheta, cac
  else:
    return cac

def writable(fname):
  return hasattr(fname, 'write')

from contextlib import contextmanager
@contextmanager
def to_filehandle(fname_or_fh, flag="r"):
  """
  Either open a new file or use existing filehandle for IO
  """
  try:
    if writable(fname_or_fh):
      fh = fname_or_fh
      own_fh = False
      fname_or_fh = None
    else:
      fh = open(fname_or_fh, flag)
      own_fh = True
    yield fh, fname_or_fh
  finally:
    if own_fh:
      fh.close()
