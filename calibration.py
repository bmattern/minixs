from numpy import * #XXX fix this
import os, sys
from itertools import izip
from exposure import Exposure
from constants import *


def find_maxima(pixels, direction, window_size = 3):
  """
  Find locations of local maxima of `pixels` array in `direction`.

  The location is calculated as the first moment in a window of half width
  `window_size` centered at a local maximum.

  Parameters
  ----------
  p : pixel array from an elastic exposure
  direction: minixs.DIRECTION_* indicating dispersive direction
  window_size : size in pixels around max for windowed average

  Returns
  -------
  xy : array of x, y and energy coordinates
  """

  # convert direction to axis (XXX make this a function call somewhere)
  rolldir = direction % 2

  # shorten expressions below by aliasing pixels array
  p = pixels

  # build mask of local maxima locations
  local_max = logical_and(p >= roll(p,-1,rolldir), p > roll(p, 1, rolldir))

  # perform windowed averaging to find average col value in local peak
  colMoment = zeros(p.shape)
  norm = zeros(p.shape)

  # build vector of indices along column (row) 
  cols = arange(0,p.shape[rolldir])
  if direction == VERTICAL:
    cols.shape = (len(cols),1)

  # find first moments about local maxima
  for i in range(-window_size,window_size+1):
    colMoment += local_max * roll(cols * p, i, rolldir)
    norm += local_max * roll(p, i, rolldir)

  # calculate average
  windowedAvg = colMoment / norm
  windowedAvg[isnan(windowedAvg)] = 0

  # we only want the locations of actual maxima
  index = where(windowedAvg > 0)
 
  # pull out the pixel locations of the peak centers
  if direction == VERTICAL:
    y = windowedAvg[index]
    x = index[1]
  else:
    x = windowedAvg[index]
    y = index[0]

  # return N x 2 array of peak locations
  return vstack([x,y]).T

class Calibrator:
  """Calibrates camera display using elastic scan images"""

  def __init__(self, energies, image_files, direction):
    self.energies = energies
    self.image_files = image_files
    self.direction = direction

    print "Directory: %s" % os.path.dirname(image_files[0])
    print "Files %s to %s" % (os.path.basename(image_files[0]),
        os.path.basename(image_files[-1]))

    self.load_images()

  def load_images(self):
    self.images = [Exposure(image_file) for image_file in self.image_files]

  def filter_images(self, low, high, nborCutoff, bad_pixels = []):
    for im in self.images:
      im.filter_low_high(low, high)
      im.filter_neighbors(nborCutoff)
      im.filter_bad_pixels(bad_pixels)

  def find_maxima(self, p, inc_energy, window_size = 3):
    """Find local maxima in an elastic scan

    Finds the center of each peak in the dispersive direction

    Parameters
    ----------
    p : pixel array from an elastic exposure
    inc_energy : the incident energy for this elastic exposure
    window_size : size in pixels around max for windowed average

    Returns
    -------
    xyz : array of x, y and energy coordinates
    """

    xy = find_maxima(p, self.direction, window_size)
    z = inc_energy * ones((len(xy), 1))

    return hstack([xy,z])

  def calibrate(self, xtals):
    """Fits a 2d cubic function to each crystal

    Parameters
    ----------

    xtals: list of rects for each crystal

    The crystals should be specified as ((x1,y1),(x2,y2))
    where (x1,y1) is the top left of the rect and (x2,y2) is the bottom
    right.
    """

    self.calib = zeros(self.images[0].pixels.shape)

    points = vstack([
      self.find_maxima(im.pixels,energy)
      for im,energy in izip(self.images, self.energies)
      ])

    lin_res = []
    rms_res = []

    for xtal in xtals:
      (x1,y1),(x2,y2) = xtal

      index = where(logical_and(
          logical_and(
            points[:,0] >= x1,
            points[:,0] < x2),
          logical_and(
            points[:,1] >= y1,
            points[:,1] < y2
            )
          ))
      x,y,z = points[index].T

      if len(x) == 0:
        print "Warning: No points in xtal ", xtal
        continue

      # fit to quadratic
      #A = vstack([x**2, y**2, x*y, x, y, ones(x.shape)]).T
      A = vstack([x**3,y**3,x**2*y,x*y**2,x**2, y**2, x*y, x, y, ones(x.shape)]).T
      fit, r = linalg.lstsq(A,z)[0:2]
      
      rms_res.append(sqrt(r / len(z))[0])

      lin_res.append( sum(z - dot(A, fit)) / len(z) )

      # fill in pixels with fit values
      xx, yy = meshgrid(arange(x1,x2), arange(y1,y2))
      xx = ravel(xx)
      yy = ravel(yy)
      zz = dot(vstack([xx**3,yy**3,xx**2*yy,xx*yy**2,xx**2,yy**2,xx*yy,xx,yy,ones(xx.shape)]).T,fit).T

      self.calib[yy,xx] = zz

    return points, lin_res, rms_res
      
  def kill_regions(self, regions):
    """Mask out regions of calibration matrix"""
    for r in regions:
      x1,y1 = r[0]
      x2,y2 = r[1]
      self.calib[y1:y2,x1:x2] = 0

  def save(self, filename):
    savetxt(filename, self.calib)

