from numpy import zeros, arange, logical_and, roll, isnan, where, savetxt
from scipy import polyfit, polyval
from itertools import izip
from exposure import Exposure
from scan import ScanFile
import sys


VERTICAL = 0
HORIZONTAL = 1

def build_rects(horizontal_bounds=None, vertical_bounds=None):
  return [
      ((l,t),(r,b))
      for (l,r) in izip(horizontal_bounds[0:-1], horizontal_bounds[1:])
      for (t,b) in izip(vertical_bounds[0:-1], vertical_bounds[1:])
      ]



def gen_image_names(prefix, vals, zero_pad=3,suff='.tif'):
  fmt = '%s%%0%dd%s' % (prefix, zero_pad, suff)
  return [fmt % val for val in vals]

def read_scan_info(scanfile, E_column=0, I0_column=6):
  s = ScanFile(scanfile)
  return s.data[:,E_column], s.data[:,I0_column]


class Calibrate:
  def __init__(self, energies, I0s, image_files, direction):
    self.energies = energies
    self.I0s = I0s
    self.image_files = image_files
    self.direction = direction

    self.load_images()

  def load_images(self):
    self.images = [Exposure(image_file) for image_file in self.image_files]

  def filter_images(self, low, high, nborCutoff):
    for im in self.images:
      im.filter_low_high(low, high)
      im.filter_neighbors(nborCutoff)

  def calibrate_elastic(self, im, inc_energy, ev_per_pixel=.75):
    p = im.pixels
    local_max = logical_and(p >= roll(p,-1,self.direction), p > roll(p, 1, self.direction))

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

    #XXX should this be estimated somehow instead of hard coded?
    ev_per_pixel = .75

    # run through images, detect rings and set energy on rings in calib
    for im, inc_energy in izip(self.images, self.energies):

      c = self.calibrate_elastic(im, inc_energy, ev_per_pixel)
      mask = where(c > 0)
      self.calib[mask] = c[mask]

  def kill_regions(self, regions):
    for r in regions:
      x1,y1 = r[0]
      x2,y2 = r[1]
      self.calib[y1:y2,x1:x2] = 0

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

  def interpolate_rects(self, xtal_rects, direction):
    for xtal_rect in xtal_rects:
      self.interpolate_xtal(xtal_rect, direction)

  def interpolate(self):
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

      # find right edges of crystal regions (for this row)
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

