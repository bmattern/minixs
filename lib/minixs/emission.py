"""
XES Spectrum processing code
"""

import os
import numpy as np
import minixs as mx

import calibrate
from exposure import Exposure
from filter import  get_filter_by_name
from parser import Parser, STRING, FLOAT, LIST

from itertools import izip

def load(filename):
  """Load EmissionSpectrum from file"""
  xes = EmissionSpectrum()
  xes.load(filename)
  return xes

def process_spectrum(cal, exposure, energies, I0, direction, xtals, solid_angle=None, skip_columns=[], killzone_mask=None):
  """Interpolated emission spectrum

  Parameters
  ----------
  cal : calibration matrix
  exposure : spectrum Exposure
  energies : list of emission energies for desired spectrum
  I0 : intensity normalization value
  direction: dispersive direction (minixs.HORIZONTAL or minixs.VERTICAL)
  xtals: list of crystal rects [ [(10,5), (200, 120)], [...] ]
  solid_angle: an array giving the solid angle subtended by each pixel

  If solid_angle is not given, then it is effectively an array of ones
  """

  intensity = np.zeros(energies.shape)
  mask = np.zeros(energies.shape)
  num_pixels = np.zeros(energies.shape)

  #variance = np.zeros(energies.shape)
  #y_i = np.zeros(energies.shape)
  #var_i = np.zeros(energies.shape)

  for xtal in xtals:
    (x1,y1), (x2,y2) = xtal

    if direction == mx.DOWN or direction == mx.UP:
      i1, i2 = x1, x2
    else:
      i1, i2 = y1, y2

    for i in range(i1,i2):
      if i in skip_columns:
        #sys.stderr.write("skipping %d\n" % i)
        continue

      # if any part of this row/column has been killzoned, skip it
      if killzone_mask is not None:
        if direction == mx.DOWN or direction == mx.UP:
          if np.any(killzone_mask[y1:y2,i]):
            continue
        else:
          if np.any(killzone_mask[i,x1:x2]):
            continue

      # select one row/column of calibration matrix and correspond row/column of spectrum exposure
      # XXX this is untested for UP and RIGHT, but *should* be correct
      if direction == mx.DOWN:
        dE = cal[y1:y2,i]
        dI = exposure.pixels[y1:y2,i]
        if solid_angle is not None:
          dS = solid_angle[y1:y2,i]
      elif direction == mx.UP:
        dE = cal[y2-1:y1-1:-1,i]
        dI = exposure.pixels[y2-1:y1-1:-1,i]
        if solid_angle is not None:
          dS = solid_angle[y2-1:y1-1:-1,i]
      elif direction == mx.RIGHT:
        dE = cal[i, x1:x2]
        dI = exposure.pixels[i, x1:x2]
        if solid_angle is not None:
          dS = solid_angle[i, x1:x2]
      elif direction == mx.LEFT:
        dE = cal[i, x2-1:x1-1:-1]
        dI = exposure.pixels[i, x2-1:x1-1:-1]
        if solid_angle is not None:
          dS = solid_angle[i, x2-1:x1-1:-1]
      else:
        raise Exception("Invalid direction.")

      # XXX: the following uses a quick method that overestimates statistical error
      #      to correctly propogate error, use interp_poisson() (which is much slower at the moment)
      #      this should be made optional so that one can do quick processing at the beamline
      #      and then get correct errorbars later
      #      (i should also characterize how incorrect the errors are...)
      #      example: interp_poisson(energies, y_i, var_i, dE, dI,-1,-1)
      y_i = np.interp(energies, dE, dI,-1,-1)
      mask *= 0
      mask[np.where(y_i >= 0)] = 1
      intensity += y_i * mask
      if solid_angle is not None:
        s_i = np.interp(energies, dE, dS, -1,-1)
        num_pixels += mask * s_i
      else:
        num_pixels += mask

      #variance += var_i * mask

  # if num_pixels is 0, then intensity will also be 0, so divide by 1 instead of 0 to avoid NaN
  norm = num_pixels.copy()
  norm[np.where(norm == 0)] = 1

  # create N x 5 array with columns: energy, normalized intensity, uncertainty, raw counts, number of rows/columns contributing
  return np.vstack([energies, intensity/I0/norm, np.sqrt(intensity)/I0/norm, intensity, num_pixels]).T

def binned_emission_spectrum(calib, exposure, low_energy, high_energy, energy_step, I0):
  """
  Calculate emission spectrum from exposure and calibration matrix

  Return:
    array of (emission_energy, I, sigma, raw_counts, num_pixels)
      I = raw_counts / num_pixels / I0
      sigma = sqrt(raw_counts) / num_pixels / I0

  """

  if low_energy is None:
    low_energy = calib[np.where(calib > 0)].min()
  if high_energy is None:
    high_energy = calib.max()

  energies = np.arange(low_energy, high_energy, energy_step)
  spectrum = np.zeros((len(energies), 5))
  spectrum[:,0] = energies + energy_step / 2.
  for E,counts in izip(calib.flat,exposure.pixels.flat):
    binnum = (E - low_energy) / energy_step

    # skip pixels outside of desired range
    if binnum < 0 or binnum >= len(energies):
      continue

    spectrum[binnum][3] += counts
    spectrum[binnum][4] += 1

  # calculate normalized intensity and uncertainty
  i = np.where(spectrum[:,4] > 0)
  spectrum[i,1] = (spectrum[i,4]>0) * spectrum[i,3] / spectrum[i,4] / I0
  spectrum[i,2] = (spectrum[i,4]>0) * np.sqrt(spectrum[i,3]) / spectrum[i,4] / I0

  return spectrum

def interp_poisson(x, y, var, xp, yp, left=None, right=None):
  """
  Linearly interpolate points and calculate Poisson variance

  This propogates the uncertainties through the interpolation, which really
  can't be the right thing to do. (The propogated uncertainty is by definition
  smaller than either of the original uncertainties...)
  """

  i = -1
  n = len(xp)

  if y is None:
    y = np.zeros(len(x))

  if var is None:
    var = np.zeros(len(x))

  if left is None:
    left = yp[0]
  if right is None:
    right = yp[-1]

  for j in xrange(len(x)):
    if i >= n-1:
      y[j] = right
      continue

    skip = False
    while x[j] > xp[i+1]:
      i += 1
      if i >= n-1:
        y[j] = right
        skip = True
        break

    if skip:
      continue

    if i == -1:
      y[j] = left
    else:
      f = (x[j] - xp[i]) / (xp[i+1] - xp[i])
      y[j] = (1-f) * yp[i] + f * yp[i+1]
      var[j] = (1-f)*(1-f)*yp[i] + f*f*yp[i+1]

  return y,var


class EmissionSpectrum(object):
  def __init__(self, filename=None):
    self.dataset_name = ""
    self.calibration_file = ""
    self.incident_energy = 0
    self.I0 = 1
    self.solid_angle_map_file = None
    self.solid_angle_map = None
    self.exposure_files = []
    self.filters = []

    spectrum = np.array([]).reshape(0,5)
    self.set_spectrum(spectrum)

    self.filename = None

    self.load_errors = []

    if filename:
      self.load(filename)

  def set_incident_energy(self, incident_energy):
    self.incident_energy = incident_energy

  def set_I0(self, I0):
    self.I0 = I0

  def set_exposure_files(self, exposure_files):
    self.exposure_files = exposure_files

  def set_spectrum(self, spectrum):
    self.spectrum = spectrum

    self.emission = self.spectrum[:,0]
    self.intensity = self.spectrum[:,1]
    self.uncertainty = self.spectrum[:,2]
    self.raw_counts = self.spectrum[:,3]
    self.num_pixels = self.spectrum[:,4]
 
  def save(self, filename=None, header_only=False):
    if filename is None:
      filename = self.filename

      self.filename = file
    with mx.misc.to_filehandle(filename, "w") as (f, filename):
      if filename:
        self.filename = filename

      f.write("# miniXS XES Spectrum\n#\n")
      f.write("# Dataset: %s\n" % self.dataset_name)
      f.write("# Calibration File: %s\n" % self.calibration_file)
      f.write("# Incident Energy: %.2f\n" % self.incident_energy)
      f.write("# I0: %.2f\n" % self.I0)
      if self.solid_angle_map_file:
        f.write("# Solid Angle Map: %s\n" % self.solid_angle_map_file)
      if self.filters:
        f.write("# Filters:\n")
        for fltr in self.filters:
          f.write('#   %s: %s\n' % (fltr.name, fltr.get_str()))
        f.write("#\n")

      f.write("# Exposures:\n")
      for ef in self.exposure_files:
        f.write("#   %s\n" % ef)
      f.write("#\n")

      if not header_only:
        if len(self.spectrum) > 0 and (len(self.spectrum.shape) != 2 and self.spectrum.shape[1] != 5):
          raise Exception("Invalid shape for spectrum array")

        if self.solid_angle_map is None:
          f.write("# E_emission    Intensity  Uncertainty  Raw_Counts   Num_Pixels\n")
          np.savetxt(f, self.spectrum, fmt=('%12.2f','%.6e','%.6e','% 11d',' % 11d'))
        else:
          f.write("# E_emission    Intensity  Uncertainty  Raw_Counts   Solid_Angle\n")
          np.savetxt(f, self.spectrum, fmt=('%12.2f','%.6e','%.6e','% 11d',' %.6e'))

  def load(self, filename=None, header_only=False):
    if filename is None:
      filename = self.filename
    else:
      self.filename = filename

    headers = []
    with open(filename, 'r') as f:
      pos = f.tell()
      line = f.readline()

      while line:
        if line[0] == "#":
          headers.append(line[2:])
        elif header_only:
          break
        else:
          f.seek(pos)
          spectrum = np.loadtxt(f)
          if len(self.spectrum.shape) == 1:
            spectrum.shape = (1,spectrum.shape[0])

          self.set_spectrum(spectrum)

        pos = f.tell()
        line = f.readline()

    parser = Parser({
      'Dataset': STRING,
      'Calibration File': STRING,
      'Incident Energy': FLOAT,
      'I0': FLOAT,
      'Solid Angle Map': STRING,
      'Filters': (LIST, STRING),
      'Exposures': (LIST, STRING)
      })
    parsed = parser.parse(headers)
    self.load_errors += parser.errors

    self.dataset_name = parsed.get('Dataset')
    self.calibration_file = parsed.get('Calibration File')
    self.incident_energy = parsed.get('Incident Energy', 0.0)
    self.I0 = parsed.get('I0', 0.0)
    solid_angle_map = parsed.get('Solid Angle Map')
    if solid_angle_map:
      self.load_solid_angle_map(solid_angle_map)
    self.exposure_files = parsed.get('Exposures')

    # load filters
    for filter_line in parsed.get('Filters', []):
      name,val = filter_line.split(':')
      name = name.strip()
      fltr = get_filter_by_name(name)
      if fltr == None:
        self.load_errors.append("Unknown Filter: '%s' (Ignoring)" % name)
      else:
        fltr.set_str(val.strip())
        self.filters.append(fltr)

    return len(self.load_errors) == 0

  def load_solid_angle_map(self, map_file):
    try:
      if os.path.exists(map_file):
        map_file = os.path.abspath(map_file)
        map = np.loadtxt(map_file)
      else:
        path = os.path.join(os.path.dirname(__file__), 'data', map_file)
        map = np.loadtxt(path)
    except IOError:
      raise IOError("Solid Angle Map File not found: '%s'. This must either be a full path, or relative to the minixs data directory." % map_file)

    self.solid_angle_map_file = map_file
    self.solid_angle_map = map

  def process(self, emission_energies=None, skip_columns=[], killzone_mask=None):
    calibration = calibrate.Calibration()
    calibration.load(self.calibration_file)

    exposure = Exposure()
    exposure.load_multi(self.exposure_files)

    for f in self.filters:
      f.filter(exposure.pixels, self.incident_energy)

    # generate emission energies from range of calibration matrix
    if emission_energies is None:
      Emin = calibration.calibration_matrix[np.where(calibration.calibration_matrix > 0)].min()
      Emax = calibration.calibration_matrix.max()

      emission_energies = np.arange(Emin,Emax,.1)

    spectrum = process_spectrum(calibration.calibration_matrix,
                                exposure,
                                emission_energies,
                                self.I0,
                                calibration.dispersive_direction,
                                calibration.xtals,
                                self.solid_angle_map,
                                skip_columns=skip_columns,
                                killzone_mask=killzone_mask)

    self.set_spectrum(spectrum) 

  def process_binned(self, E1, E2, Estep, killzone_mask=None):
    calib = calibrate.load(self.calibration_file)

    # zero out killzones of calibration matrix
    # (this causes those pixels to be ignored)
    if killzone_mask is not None:
      calib.calibration_matrix[killzone_mask] = 0

    exposure = Exposure()
    exposure.load_multi(self.exposure_files)
    exposure.apply_filters(self.incident_energy, self.filters)
    spectrum = binned_emission_spectrum(calib.calibration_matrix,
                                        exposure,
                                        E1,
                                        E2,
                                        Estep,
                                        self.I0)
    self.set_spectrum(spectrum)

