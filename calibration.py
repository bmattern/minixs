from numpy import * #XXX fix this
import os, sys
from itertools import izip
from exposure import Exposure
from constants import *

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

    rolldir = self.direction % 2

    local_max = logical_and(p >= roll(p,-1,rolldir), p > roll(p, 1, rolldir))

    # perform windowed averaging to find average col value in local peak
    colMoment = zeros(p.shape)
    norm = zeros(p.shape)

    cols = arange(0,p.shape[rolldir])
    if self.direction == VERTICAL:
      cols.shape = (len(cols),1)

    for i in range(-window_size,window_size+1):
      colMoment += local_max * roll(cols * p, i, rolldir)
      norm += local_max * roll(p, i, rolldir)

    windowedAvg = colMoment / norm
    windowedAvg[isnan(windowedAvg)] = 0

    index = where(windowedAvg > 0)

    if self.direction == VERTICAL:
      y = windowedAvg[index]
      x = index[1]
    else:
      x = windowedAvg[index]
      y = index[0]

    z = inc_energy * ones(x.shape)

    ret = vstack([x,y,z]).T
    return ret

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
      

  def calibrate_elastic(self, im, inc_energy, ev_per_pixel=.75):
    p = im.pixels
    local_max = logical_and(p >= roll(p,-1,self.direction), p > roll(p, 1, self.direction))

    # pick out highest peak to get rid of noise?
    # XXX this only works if there is a single crystal in the dispersive direction, and currently only for vertical spectra

    """
    local_max = zeros(p.shape)
    maxima = p.argmax(0)
    for i in range(len(maxima)):
      local_max[maxima[i],i] = 1
    """

    # perform windowed averaging to find average col value in local peak
    colMoment = zeros(p.shape)
    norm = zeros(p.shape)

    cols = arange(0,p.shape[self.direction])
    if self.direction == VERTICAL:
      cols.shape = (len(cols),1)

    for i in range(-3,4):
      colMoment += local_max * roll(cols * p, i, self.direction)
      norm += local_max * roll(p, i, self.direction)

    windowedAvg = colMoment / norm
    windowedAvg[isnan(windowedAvg)] = 0


    return ((windowedAvg - cols) * ev_per_pixel + inc_energy) * local_max

  def build_calibration_matrix(self, ev_per_pixel=.75):
    # XXX for now, get working for horizontal crystals, then alter for vertical

    self.calib = zeros(self.images[0].pixels.shape)

    # run through images, detect rings and set energy on rings in calib
    for im, inc_energy in izip(self.images, self.energies):

      c = self.calibrate_elastic(im, inc_energy, ev_per_pixel)
      mask = where(c > 0)
      self.calib[mask] = c[mask]

  def interpolate_xtal(self, xtal_rect):
    (x1,y1),(x2,y2) = xtal_rect
    xtal = self.calib[y1:y2,x1:x2]

    if self.direction == HORIZONTAL:
      xtal = xtal.transpose()

    for row in xtal:
      x = where(row > 1)[0]
      if len(x) == 0:
        continue

      y = row[x]
      order = 2
      if len(x) <=2:
        order = len(x)-1

      fit = polyfit(x,y, order)
      xfit = range(x[0], x[-1]+1)
      yfit = polyval(fit, xfit)

      row[xfit] = yfit

  def kill_regions(self, regions):
    """Mask out regions of calibration matrix"""
    for r in regions:
      x1,y1 = r[0]
      x2,y2 = r[1]
      self.calib[y1:y2,x1:x2] = 0

  def interpolate_rects(self, xtal_rects, direction):
    for xtal_rect in xtal_rects:
      self.interpolate_xtal(xtal_rect, direction)

  def interpolate(self, single_xtal=False):
    """
    Interpolate between calibrated points

    If single_xtal is True, then the code assumes one crystal in the dispersive direction.
    Otherwise, it finds crystal boundaries by finding points where energy jumps the opposite direction as expected
    """
    
    if self.direction == VERTICAL:
      calib = self.calib.transpose()
    else:
      calib = self.calib

    k = 0
    for row in calib:
      k += 1
      i = where(row > 1)[0]

      #skip rows with too little information
      if len(i) < 3:
        row[:] = 0
        continue

      if single_xtal:
        xtals = [i]
        num_xtals = 1
      else:
        # find right edges of crystal regions (for this row)
        if self.direction == VERTICAL:
          right = where(row[i] >= row[roll(i,-1)])[0]
        else:
          right = where(row[i] < row[roll(i,-1)])[0]

        right = filter(lambda r: r > 0, right)
        if len(right) == 0:
          row[:] = 0
          continue

        left = roll(right,1) + 1
        left[0] = 0

        num_xtals = len(right)

        xtals = [ i[l:r+1] for l,r in izip(left,right) ]

      if len(xtals) == 0:
        row[:] = 0
        continue

      for x in xtals:
        xfit = range(x[0], x[-1]+1)

        # skip regions with too few points (should this be higher than 2?)
        if len(x) <= 2:
          row[xfit] = 0
          print "skipping xtal in row %d" % k
          print right
          print left
          print x
          continue

        y = row[x]
        order = 2

        fit = polyfit(x,y, order)
        yfit = polyval(fit, xfit)

        row[xfit] = yfit

  def save(self, filename):
    savetxt(filename, self.calib)

