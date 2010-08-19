from numpy import zeros, arange, logical_and, roll, isnan, where, asarray
from numpy import loadtxt, savetxt
from numpy import sqrt, unique, argmin, log

from scipy import polyfit, polyval
from itertools import izip, product as iproduct
import sys

from PIL import Image


VERTICAL = 0
HORIZONTAL = 1

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


class Exposure:
  def __init__(self, filename = None):
    if filename is not None:
      self.load(filename)

  def load(self, filename):
    self.filename = filename

    self.image = Image.open(filename)
    self.pixels = asarray(self.image).copy()
    self.info = self.parse_description(self.image.tag.get(270))

  def load_multi(self, filenames):
    self.filenames = filenames
    self.pixels = None
    for f in filenames:
      im = Image.open(f)
      p = asarray(im)
      if self.pixels is None:
        self.pixels = p.copy()
      else:
        self.pixels += p

  def parse_description(self, desc):
    try:
      # split into lines and strip off '#'
      info = [line[2:] for line in desc.split('\r\n')][:-1]
    except:
      info = []
    return info

  def filter_low_high(self, low, high):
    mask = logical_and(self.pixels >= low, self.pixels <= high)
    self.pixels *= mask

  def filter_neighbors(self, cutoff):
    nbors = (-1,0,1)
    mask = sum([
      roll(roll(self.pixels>0,i,0),j,1)
      for i,j in iproduct(nbors,nbors)
      if i != 0 or j != 0
      ], 0) >= cutoff
    self.pixels *= mask

  def filter_bad_pixels(self, bad_pixels):
    for x,y in bad_pixels:
      self.pixels[y,x] = 0


class Calibrator:
  """Calibrates camera display using elastic scan images"""

  def __init__(self, energies, image_files, direction):
    self.energies = energies
    self.image_files = image_files
    self.direction = direction

    self.load_images()

  def load_images(self):
    self.images = [Exposure(image_file) for image_file in self.image_files]

  def filter_images(self, low, high, nborCutoff, bad_pixels = []):
    for im in self.images:
      im.filter_low_high(low, high)
      im.filter_neighbors(nborCutoff)
      im.filter_bad_pixels(bad_pixels)

  def calibrate_elastic(self, im, inc_energy, ev_per_pixel=.75):
    p = im.pixels
    local_max = logical_and(p >= roll(p,-1,self.direction), p > roll(p, 1, self.direction))

    # pick out highest peak to get rid of noise
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


SCAN_COLUMN_WIDTH = 21

class ScanFile:
  def __init__(self, filename=None):
    if filename:
      self.load(filename)

  def load(self, filename):
    self.filename = filename

    #read in headers
    with open(filename) as f:
      self.headers = []
      for line in f:
        if line[0] != '#':
          # rewind to beginning of this line
          f.seek(-len(line), 1)
          break

        # strip off '#' and newline
        self.headers.append(line)

    column_names = self.headers[-1]
    self.columns = [column_names[i:i+SCAN_COLUMN_WIDTH].strip() for i in xrange(1,len(column_names)-2, SCAN_COLUMN_WIDTH)]

    # load in data
    self.data = loadtxt(filename)

  def save(self, filename=None, fmt=None):
    if not filename:
      filename = self.filename

    assert filename, "A filename must be provided in order to save"

    if fmt is None:
      fmt = '%%%d.8f' % SCAN_COLUMN_WIDTH

    with open(filename, 'w') as f:
      for line in self.headers:
        f.write(line)

      # numpy cannot save with dos newlines...
      #savetxt(f, self.data, fmt=fmt, delimiter=' ')

      # so, save by hand
      for row in self.data:
        for val in row:
          f.write(fmt % val)
          f.write(' ')
        f.write('\r\n')

def emission_spectrum(calib, exposure, low_energy, high_energy, energy_step, I0):
  """Calculate emission spectrum from exposure and calibration matrix

  Return:
    array of (emission_energy, I, sigma, raw_counts, num_pixels)
      I = raw_counts / num_pixels / I0
      sigma = sqrt(raw_counts) / num_pixels / I0

  """
  energies = arange(low_energy, high_energy, energy_step)
  spectrum = zeros((len(energies), 5))
  spectrum[:,0] = energies + energy_step / 2.
  for E,counts in izip(calib.flat,exposure.pixels.flat):
    binnum = (E - low_energy) / energy_step

    # skip pixels outside of desired range
    if binnum < 0 or binnum >= len(energies):
      continue

    spectrum[binnum][3] += counts
    spectrum[binnum][4] += 1

  # calculate normalized intensity and uncertainty
  i = where(spectrum[:,4] > 0)
  spectrum[i,1] = (spectrum[i,4]>0) * spectrum[i,3] / spectrum[i,4] / I0
  spectrum[i,2] = (spectrum[i,4]>0) * sqrt(spectrum[i,3]) / spectrum[i,4] / I0

  sys.stdout.write(".")
  sys.stdout.flush()
  return spectrum


def process_all(calibfile, scanfile, base_image, image_nums, E_column=0, I0_column=6, low_cutoff=0, high_cutoff=1000, low_energy=None, high_energy=None, energy_step = 0.5, zero_pad=3):

  calib = loadtxt(calibfile)

  if low_energy is None:
    low_energy = calib[where(calib > 0)].min()

  if high_energy is None:
    high_energy = calib.max()


  Es, I0s = read_scan_info(scanfile, [E_column, I0_column])
  filenames = gen_file_list(base_image, image_nums, zero_pad)
  exposures = [ Exposure(filename) for filename in filenames ]

  for e in exposures:
    e.filter_low_high(low_cutoff, high_cutoff)
    e.filter_neighbors(1)

  spectra = [ emission_spectrum(calib, e, low_energy, high_energy, energy_step, I0) for e, I0 in izip(exposures, I0s) ]

  return spectra

def build_rixs(spectra, energies):
  total_length = sum([len(s) for s in spectra])
  full_spectrum = zeros((total_length, 6))

  i = 0
  for s,E in izip(spectra, energies):
    full_spectrum[i:i+len(s),0] = E
    full_spectrum[i:i+len(s),1:] = s
    i += len(s)

  return full_spectrum

def save_rixs(filename, rixs):
  with open(filename, 'w') as f:
    f.write("#    E_incident      E_emission       Intensity           Sigma          Counts      Num_pixels\n")

    fmt = ('% 15.2f', '% 15.2f', '% 15.8e','% 15.8e','% 15d', '% 15d')
    savetxt(f, rixs, fmt=fmt)


def rixs_xes_cut(rixs, energy):
  energies = unique(rixs[:,0])
 
  i = argmin(abs(energies - energy))

  return rixs[where(rixs[:,0] == energies[i])]

def rixs_pfy_cut(rixs, energy):
  energies = unique(rixs[:,1])
 
  i = argmin(abs(energies - energy))

  return rixs[where(rixs[:,1] == energies[i])]


def rixs2d(rixs):
  inc_energies = unique(rixs[:,0])
  emit_energies = unique(rixs[:,1])

  rixs2d = zeros((len(emit_energies), len(inc_energies)))

  for row in rixs:
    i = where(inc_energies == row[0])[0]
    j = where(emit_energies == row[1])[0]
    rixs2d[j,i] = row[2]

  return rixs2d

def plot_rixs(rixs, start=0, end=-1, plot_log=False, aspect=1):
  incE = unique(rixs[:,0])
  emitE = unique(rixs[:,1])
  r2d = rixs2d(rixs)
  if plot_log:
    r2d = log(r2d)

  from matplotlib.pyplot import imshow, figure
  figure()
  imshow(
      r2d[:,start:end],
      extent=(incE[start],incE[end],emitE[-1],emitE[0]),
      aspect=aspect)
