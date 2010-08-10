from numpy import zeros, arange, logical_and, roll, isnan, where
from scipy import polyfit, polyval
from itertools import izip
from exposure import Exposure
from scan import ScanFile
import sys

def gen_image_names(prefix, vals, zero_pad=3,suff='.tif'):
  fmt = '%s%%0%dd%s' % (prefix, zero_pad, suff)
  return [fmt % val for val in vals]

def read_scan_info(scanfile, E_column=0, I0_column=6):
  s = ScanFile(scanfile)
  return s.data[:,E_column], s.data[:,I0_column]


class Calibrate:
  def __init__(self, energies, I0s, image_files):
    self.energies = energies
    self.I0s = I0s
    self.image_files = image_files

    self.load_images()

  def load_images(self):
    self.images = [Exposure(image_file) for image_file in self.image_files]

  def filter_images(self, low, high, nborCutoff):
    for im in self.images:
      im.filter_low_high(low, high)
      im.filter_neighbors(nborCutoff)

  def build_calibration_matrix(self, direction):
    # XXX for now, get working for horizontal crystals, then alter for vertical

    self.calib = zeros(self.images[0].pixels.shape)

    #XXX should this be estimated somehow instead of hard coded?
    ev_per_pixel = .75

    # run through images, detect rings and set energy on rings in calib
    for im, inc_energy in izip(self.images, self.energies):
      p = im.pixels
      local_max = logical_and(p >= roll(p,-1,1), p > roll(p, 1, 1))

      # perform windowed averaging to find average col value in local peak
      colMoment = zeros(p.shape)
      norm = zeros(p.shape)

      cols = arange(0,p.shape[1])

      for i in range(-3,4):
        colMoment += local_max * roll(cols * p, i, 1)
        norm += local_max * roll(p, i, 1)

      windowedAvg = colMoment / norm
      windowedAvg[isnan(windowedAvg)] = 0

      self.cols = cols
      self.windowedAvg = windowedAvg

      self.calib += ((windowedAvg - cols) * ev_per_pixel + inc_energy) * local_max

  def kill_regions(self, regions):
    for r in regions:
      x1,y1 = r[0]
      x2,y2 = r[1]
      self.calib[y1:y2,x1:x2] = 0

  def interpolate(self):
    for row in self.calib:
      i = where(row > 1)[0]

      if len(i) == 0:
        continue

      # find right edges of crystal regions (for this row)
      right = where(row[i] < row[roll(i,-1)])[0]
      left = where(row[i] > row[roll(i,1)])[0]
      left = roll(right,1) + 1
      left[0] = 0

      num_xtals = len(right)

      xtals = [ i[l:r+1] for l,r in izip(left,right) ]

      for x in xtals:
        sys.stdout.flush()
        y = row[x]
        order = 2
        if len(x) <=2:
          order = len(x)-1

        fit = polyfit(x,y, order)
        xfit = range(x[0], x[-1]+1)
        yfit = polyval(fit, xfit)

        row[xfit] = yfit

  def save(self, filename):
    savetxt(filename, c.calib)
