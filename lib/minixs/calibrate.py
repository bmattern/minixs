"""
Calibration functions
"""

from exposure import Exposure
from emission import EmissionSpectrum, process_spectrum
from itertools import izip
from filter import get_filter_by_name
from constants import *
from gauss import gauss_leastsq, gauss_model
from parser import Parser, STRING, INT, FLOAT, LIST
from filetype import InvalidFileError
from spectrometer import Spectrometer

import os
import numpy as np

def load(filename):
  """
  Load a calibration matrix from a file
  """
  c = Calibration()
  c.load(filename)
  return c

def find_maxima(pixels, direction, window_size = 3):
  """
  Find locations of local maxima of `pixels` array in `direction`.

  The location is calculated as the first moment in a window of half width
  `window_size` centered at a local maximum.

  Parameters
  ----------
  pixels : pixel array from an elastic exposure
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
  local_max = np.logical_and(p >= np.roll(p,-1,rolldir), p > np.roll(p, 1, rolldir))

  # perform windowed averaging to find average col value in local peak
  colMoment = np.zeros(p.shape)
  norm = np.zeros(p.shape)

  # build vector of indices along column (row) 
  cols = np.arange(0,p.shape[rolldir])
  if rolldir == VERTICAL:
    cols.shape = (len(cols),1)

  # find first moments about local maxima
  for i in range(-window_size,window_size+1):
    colMoment += local_max * np.roll(cols * p, i, rolldir)
    norm += local_max * np.roll(p, i, rolldir)

  # calculate average
  windowedAvg = colMoment / norm
  windowedAvg[np.isnan(windowedAvg)] = 0

  # we only want the locations of actual maxima
  index = np.where(windowedAvg > 0)
 
  # pull out the pixel locations of the peak centers
  if rolldir == VERTICAL:
    y = windowedAvg[index]
    x = index[1]
  else:
    x = windowedAvg[index]
    y = index[0]

  # return N x 2 array of peak locations
  return np.vstack([x,y]).T


def find_combined_maxima(exposures, energies, direction):
  """
  Build array of all maxima locations and energies in a list of exposures

  Parameters
  ----------
    exposures: a list of Exposure objects
    energies:  a list of corresponding energies (must be same length as `exposures`)
    direction: the dispersive direction

  Returns
  -------
    Nx3 array with columns giving x,y,energy for each maximum
  """
  points = []

  for exposure, energy in izip(exposures, energies):
    # extract locations of peaks
    xy = find_maxima(exposure.pixels, direction)
    z = energy * np.ones((len(xy), 1))
    xyz = np.hstack([xy,z])
    points.append(xyz)

  return np.vstack(points)


FIT_QUADRATIC = 1
FIT_CUBIC   = 2
FIT_QUARTIC = 3
FIT_ELLIPSOID = 4

def fit_region(region, points, dest, fit_type = FIT_QUARTIC, return_fit=False):
  """
  Fit a smooth function to points that lie in region bounded by `region`

  Parameters
  ----------
    region - a rectangle defining the boundary of region to fit: [(x1,y1), (x2,y2)]
    points - an N x 3 array of data points
    dest - an array to store fit data in
    fit_type - type of fit to perform, ether FIT_QUADRATIC or FIT_CUBIC

  Returns
  -------
    Nothing

  The points array should contain three columns giving respectively x,y and z
  values of data points.  The x and y values should be between 0 and the width
  and height of `dest` respectively. They are in units of pixels, but may be
  real valued.  The z values can take any values.

  The entries in `points` with x,y coordinates falling within the bounds
  specified by `region` are fit to the model specified by `fit_type` using linear
  least squares. This model is then evaluated at all integral values of x and y
  in this range, with the result being stored in the corresponding location of
  `dest`.

  This is intended to be called for several different non-overlapping values of
  `region` with the same list of `points` and `dest`.

  Fit Types
  ---------
    FIT_QUADRATIC: z = Ax^2 + By^2 + Cxy + Dx + Ey + F
    FIT_CUBIC: z = Ax^3 + By^3 + Cx^2y + Dxy^2 + Ex^2 + Fy^2 + Gxy + Hx + Iy + J
  """

  # boundary coordinates
  (x1,y1),(x2,y2) = region

  # extract points inside this xtal region
  index = np.where(np.logical_and(
      np.logical_and(
        points[:,0] >= x1,
        points[:,0] < x2),
      np.logical_and(
        points[:,1] >= y1,
        points[:,1] < y2
        )
      ))
  x,y,z = points[index].T

  # if we have no points in this region, we can't fit anything
  # XXX this should pass the warning up to higher level code instead
  #     of printing it out to stdout
  if len(x) == 0:
    print "Warning: No points in region: ", region
    return

  # build points to evaluate fit at
  xxd, yyd = np.meshgrid(np.arange(x1,x2), np.arange(y1,y2))
  xxd = np.ravel(xxd)
  yyd = np.ravel(yyd)
  xx = xxd.astype('double')
  yy = yyd.astype('double')

  if fit_type == FIT_QUADRATIC:
    # fit to quadratic: z = Ax^2 + By^2 + Cxy + Dx + Ey + F
    A = np.vstack([x**2, y**2, x*y, x, y, np.ones(x.shape)]).T
    fit, r = np.linalg.lstsq(A,z)[0:2]

    # calculate residues
    rms_res = np.sqrt(r / len(z))[0]
    lin_res = sum(z - np.dot(A, fit)) / len(z)

    # evaluate at all points
    zz = np.dot(
           np.vstack([xx**2,yy**2,xx*yy,xx,yy,np.ones(xx.shape)]).T,
           fit
         ).T

  elif fit_type == FIT_CUBIC:
    # fit to cubic:
    #   Ax^3 + By^3 + Cx^2y + Dxy^2 + Ex^2 + Fy^2 + Gxy + Hx + Iy + J = z
    A = np.vstack([x**3,y**3,x**2*y,x*y**2,x**2, y**2, x*y, x, y, np.ones(x.shape)]).T
    fit, r = np.linalg.lstsq(A,z)[0:2]

    # calculate residues
    rms_res = np.sqrt(r / len(z))[0]
    lin_res = sum(z - np.dot(A, fit)) / len(z)

    # evaluate at all points
    zz = np.dot(
           np.vstack([
             xx**3, yy**3, xx**2*yy, xx*yy**2,
             xx**2, yy**2, xx*yy,
             xx, yy,
             np.ones(xx.shape)
           ]).T,
           fit
         ).T

  elif fit_type == FIT_QUARTIC:
    # fit to quartic:
    A = np.vstack([
      x**4,
      y**4,
      x**2 * y**2,
      # intentionally skip all terms with cubes
      x**2 * y,
      x * y**2,
      x**2,
      y**2,
      x * y,
      x,
      y,
      np.ones(x.shape)
      ]).T
    fit, r = np.linalg.lstsq(A,z)[0:2]

    # calculate residues
    rms_res = np.sqrt(r / len(z)) #[0]
    lin_res = sum(z - np.dot(A, fit)) / len(z)

    # evaluate at all points
    zz = np.dot(
           np.vstack([
             xx**4, yy**4, xx**2 * yy**2,
             xx**2 * yy, xx * yy**2,
             xx**2, yy**2, xx * yy,
             xx, yy,
             np.ones(xx.shape)
           ]).T,
           fit
         ).T

  elif fit_type == FIT_ELLIPSOID:
    raise Exception("Fit method not yet implemented.")
    # XXX this doesn't seem to work...
    # Fit to ellipsoid:
    # Ax^2 + By^2 + Cz^2 + Dxy + Eyz + Fzx + Gx + Hy + Iz = 1
    data = np.vstack([
      x*x,
      y*y,
      z*z,
      x*y,
      y*z,
      z*x,
      x,
      y,
      z
      ]).T

    w = np.ones(x.shape)
    fit, r = np.linalg.lstsq(data,w)[0:2]

    #rms_res = np.sqrt(r / len(w))[0]
    lin_res = (w - np.dot(data, fit)).sum() / len(w)
    rms_res = np.sqrt(((w - np.dot(data, fit))**2).sum() / len(w))

    # now solve for z in terms of x and y to evaluate
    A,B,C,D,E,F,G,H,I = fit
    a = C
    b = E*yy + F*xx + I
    c = A*xx**2 + B*yy**2 + D*xx*yy + G*xx + H*yy - 1
    zz = (-b + np.sqrt(b**2 - 4*a*c)) / (2*a)

  # fill the calibration matrix with values from fit
  dest[yyd,xxd] = zz

  if return_fit:
    return lin_res, rms_res, fit
  else:
    return lin_res, rms_res

def calibrate(filtered_exposures, energies, regions, dispersive_direction, fit_type=FIT_QUARTIC, return_diagnostics=False):
  """
  Build calibration matrix from parameters in Calibration object

  Parameters
  ----------
    filtered_exposures: list of loaded and cleaned up Exposure objects
    energies: list of energies corresponding to exposures 
    regions: list of regions containing individual spectra
    dispersive_direction: direction of increasing energy on camera (minixs.const.{DOWN,UP,LEFT,RIGHT})

  Optional Parameters
  -------------------
    fit_type: type of fit (see fit_region() for more)
    return_diagnostics: whether to return extra information (residues and points used for fit)

  Returns
  -------
    calibration_matrix, [lin_res, rms_res, points]

    calibration_matrix: matrix of energies assigned to each pixel

    lin_res: average linear deviation of fit
    rms_res: avg root mean square residue of fit
    points: extracted maxima used for fit

    The last 3 of these are only returned if `return_diagnostics` is True.
  """
  # locate maxima
  points = find_combined_maxima(filtered_exposures, energies, dispersive_direction)

  # create empty calibration matrix
  calibration_matrix = np.zeros(filtered_exposures[0].pixels.shape)

  # fit smooth shape for each crystal, storing fit residues
  lin_res = []
  rms_res = []
  fits = []
  for region in regions:
    lr, rr, fit = fit_region(region, points, calibration_matrix, fit_type, return_fit=True)
    lin_res.append(lr)
    rms_res.append(rr)
    fits.append(fit)

  if return_diagnostics:
    return (calibration_matrix, (lin_res, rms_res, points, fits))
  else:
    return calibration_matrix

class Calibration:
  """
  A calibration matrix and all corresponding information
  """

  def __init__(self):
    self.dataset_name = ""
    self.dispersive_direction = DOWN
    self.energies = []
    self.exposure_files = []
    self.filters = []
    self.xtals = []
    self.calibration_matrix = np.array([])
    self.spectrometer = None

    self.filename = None

    self.load_errors = []

  def save(self, filename=None, header_only=False):
    if filename is None:
      filename = self.filename
    else:
      self.filename = filename

    with open(filename, 'w') as f:
      f.write("# miniXS calibration matrix\n#\n")
      if self.spectrometer is not None:
        if self.spectrometer.tag:
          f.write("# Spectrometer: %s\n" % self.spectrometer.tag)
        else:
          f.write("# Spectrometer: %s\n" % self.spectrometer.filename)
      f.write("# Dataset: %s\n" % self.dataset_name)
      f.write("# Dispersive Direction: %s\n" % DIRECTION_NAMES[self.dispersive_direction])
      f.write("#\n")
      f.write("# Energies and Exposures:\n")
      for en, ex in izip(self.energies, self.exposure_files):
        f.write("#   %5.2f %s\n" % (en,ex))
      f.write("#\n")

      f.write("# Filters:\n")
      for fltr in self.filters:
        f.write('#   %s: %s\n' % (fltr.name, fltr.get_str()))
      f.write("#\n")

      f.write("# Xtal Boundaries:\n")
      for (x1,y1), (x2,y2) in self.xtals:
        f.write("#   %3d %3d %3d %3d\n" % (x1,y1,x2,y2))
      f.write("#\n")

      if (not header_only and
          self.calibration_matrix is not None and
          len(self.calibration_matrix) > 0 and 
          len(self.calibration_matrix.shape) == 2):
        f.write("# %d x %d matrix follows\n" % self.calibration_matrix.shape)

        np.savetxt(f, self.calibration_matrix, fmt='%.3f')

  def load(self, filename=None, header_only=False):
    """
    Load calibration information from saved file

    Parameters
    ----------
      filename: name of file to load
      header_only: whether to load only the header or full data

    Returns
    -------
      True if load was successful
      False if load encountered an error

      Error messages are stored as strings in the list `Calibration.load_errors`.
    """
    self.load_errors = []

    if filename is None:
      filename = self.filename
    else:
      self.filename = filename

    parser = Parser({
      'Spectrometer': STRING,
      'Dataset': STRING,
      'Dispersive Direction': STRING,
      'Energies and Exposures': (LIST, (FLOAT, STRING)),
      'Filters': (LIST, STRING),
      'Xtal Boundaries': (LIST, (INT, INT, INT, INT)),
      })

    header = []
    with open(filename, 'r') as f:
      line = f.readline()
      #XXX this should be done elsewhere...
      if line.strip().lower() != '# minixs calibration matrix':
        raise InvalidFileError()

      pos = f.tell()
      line = f.readline()
      while line:
        if line[0] == "#":
          header.append(line[2:])
        elif header_only:
          break
        else:
          f.seek(pos)
          self.calibration_matrix = np.loadtxt(f)
          if len(self.calibration_matrix.shape) == 1:
            self.calibration_matrix.shape = (1,self.spectrum.shape[0])
          break

        pos = f.tell()
        line = f.readline()

    # parse
    parsed = parser.parse(header)
    if parser.errors:
      self.load_errors += parser.errors

    sname = parsed.get('Spectrometer')
    if sname:
      try:
        if sname == os.path.basename(sname):
          spect = Spectrometer(sname)
        else:
          spect = Spectrometer()
          spect.load(sname)

        self.spectrometer = spect
      except Exception as e:
        self.load_errors.append("Error loading spectrometer: %s" % str(e))

    self.dataset = parsed.get('Dataset', '')

    # check dispersive direction
    dirname = parsed.get('Dispersive Direction', DOWN)
    if dirname in DIRECTION_NAMES:
      self.dispersive_direction = DIRECTION_NAMES.index(dirname)
    else:
      self.load_errors.append("Unknown Dispersive Direction: '%s', using default." % dirname)

    # split up energies and exposure files
    key = 'Energies and Exposures'
    if key in parsed.keys():
      self.energies = [ee[0] for ee in parsed[key]]
      self.exposure_files= [ee[1] for ee in parsed[key]]

    # read in filters
    for filter_line in parsed.get('Filters', []):
      name,val = filter_line.split(':')
      name = name.strip()
      fltr = get_filter_by_name(name)
      if fltr == None:
        self.load_errors.append("Unknown Filter: '%s' (Ignoring)" % name)
      else:
        fltr.set_str(val.strip())
        self.filters.append(fltr)

    self.xtals = [
        [[x1,y1],[x2,y2]]
        for x1,y1,x2,y2 in parsed.get('Xtal Boundaries', [])
        ]

    return len(self.load_errors) == 0

  def calibrate(self, fit_type=FIT_QUARTIC):
    # load exposure files
    exposures = [Exposure(f) for f in self.exposure_files]
    
    # apply filters
    for exposure, energy in izip(exposures, self.energies):
      for f in self.filters:
        f.filter(exposure.pixels, energy)

    # calibrate
    self.calibration_matrix, diagnostics = calibrate(exposures,
                                                     self.energies,
                                                     self.xtals,
                                                     self.dispersive_direction,
                                                     fit_type,
                                                     return_diagnostics=True)

    # store diagnostic info
    self.lin_res, self.rms_res, self.fit_points, self.fits = diagnostics

  def xtal_mask(self):
    """
    Generate a mask of the xtal regions

    Returns
    -------
      An binary array of the same shape as the calibration matrix with 0's outside of xtal regions and 1's inside
    """

    if self.calibration_matrix is None:
      return None

    mask = np.zeros(self.calibration_matrix.shape, dtype=np.bool)
    for (x1,y1),(x2,y2) in self.xtals:
      mask[y1:y2,x1:x2] = 1

    return mask

  def energy_range(self):
    """
    Find min and max energies in calibration matrix

    Returns
    -------
      (min_energy, max_energy)
    """
    return (self.calibration_matrix[np.where(self.calibration_matrix > 0)].min(), self.calibration_matrix.max())

  def diagnose(self, return_spectra=False, filters=None):
    """
    Process all calibration exposures and fit to gaussians, returning parameters of fit

    Parameters
    ----------
    return_spectra: whether to return processed calibration spectra

    Returns
    -------
    (diagnostics, [processed_spectra])

    diagnostics: an array with one row for each calibration exposure
                 the columns are:
                   incident beam energy
                   amplitude
                   E0
                   sigma

                 the best Gaussian fit to the data is given by:
                   exp(-(E-E0)**2/(2*sigma**2))

    if `return_spectra` is True, then a list of XES spectra will be returned (one for each calibration exposure)
    """

    emin, emax = self.energy_range()
    emission_energies = np.arange(emin, emax, .2)

    diagnostics = np.zeros((len(self.energies), 4))

    if return_spectra:
      spectra = []

    for i in range(len(self.energies)):
      if i % 10 == 0:
        print i
      energy = self.energies[i]
      exposure = Exposure(self.exposure_files[i])
      if filters is not None:
        exposure.apply_filters(energy, filters)

      s = process_spectrum(self.calibration_matrix, exposure, emission_energies, 1, self.dispersive_direction, self.xtals)
      x = s[:,0]
      y = s[:,1]

      fit, ier = gauss_leastsq((x,y), (y.max(), energy, 1.0))

      if not (0 < ier < 5):
        continue

      diagnostics[i,0] = energy
      diagnostics[i,1:] = fit

      if return_spectra:
        xes = EmissionSpectrum()
        xes.incident_energy = energy
        xes.exposure_files = [exposure.filename]
        xes.set_spectrum(s)
        spectra.append(xes)

    diagnostics = diagnostics[np.where(diagnostics[:,0] != 0)]

    if return_spectra:
      return (diagnostics, spectra)
    else:
      return diagnostics
