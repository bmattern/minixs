"""
XES Spectrum processing code
"""

import numpy as np

from calibrate import Calibration
from exposure import Exposure
from misc import read_scan_info, gen_file_list
from constants import *
from filter import  get_filter_by_name

from itertools import izip

def process_spectrum(cal, exposure, energies, I0, direction, xtals):
  """Interpolated emission spectrum

  Parameters
  ----------
  cal : calibration matrix
  exposure : spectrum Exposure
  energies : list of emission energies for desired spectrum
  I0 : intensity normalization value
  direction: dispersive direction (minixs.HORIZONTAL or minixs.VERTICAL)
  xtals: list of crystal rects
  """

  intensity = np.zeros(energies.shape)
  mask = np.zeros(energies.shape)
  num_pixels = np.zeros(energies.shape)

  #variance = np.zeros(energies.shape)
  #y_i = np.zeros(energies.shape)
  #var_i = np.zeros(energies.shape)

  for xtal in xtals:
    (x1,y1), (x2,y2) = xtal

    if direction == DOWN or direction == UP:
      i1, i2 = x1, x2
    else:
      i1, i2 = y1, y2

    for i in range(i1,i2):

      # select one row/column of calibration matrix and correspond row/column of spectrum exposure
      # XXX this is untested for UP and RIGHT, but *should* be correct
      if direction == DOWN:
        dE = cal[y1:y2,i]
        dI = exposure.pixels[y1:y2,i]
      elif direction == UP:
        dE = cal[y2-1:y1-1:-1,i]
        dI = exposure.pixels[y2-1:y1-1:-1,i]
      elif direction == RIGHT:
        dE = cal[i, x1:x2]
        dI = exposure.pixels[i, x1:x2]
      elif direction == LEFT:
        dE = cal[i, x2-1:x1-1:-1]
        dI = exposure.pixels[i, x2-1:x1-1:-1]
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

  sys.stdout.write(".")
  sys.stdout.flush()
  return spectrum

def process_all(calibfile, scanfile, base_image, image_nums, E_column=0, I0_column=6, low_cutoff=0, high_cutoff=1000, low_energy=None, high_energy=None, energy_step = 0.5, zero_pad=3):

  calib = np.loadtxt(calibfile)

  if low_energy is None:
    low_energy = calib[np.where(calib > 0)].min()

  if high_energy is None:
    high_energy = calib.max()


  Es, I0s = read_scan_info(scanfile, [E_column, I0_column])
  filenames = gen_file_list(base_image, image_nums, zero_pad)

  print "Directory: %s" % os.path.dirname(filenames[0])
  print "Files %s to %s" % (os.path.basename(filenames[0]),
      os.path.basename(filenames[-1]))
  exposures = [ Exposure(filename) for filename in filenames ]

  for e in exposures:
    e.filter_low_high(low_cutoff, high_cutoff)
    e.filter_neighbors(1)

  spectra = [ emission_spectrum(calib, e, low_energy, high_energy, energy_step, I0) for e, I0 in izip(exposures, I0s) ]

  return spectra


def interp_poisson(x, y, var, xp, yp, left=None, right=None):
  """
  Linearly interpolate points and calculate Poisson variance
  """
  i = -1
  n = len(xp)

  if y is None:
    y = zeros(len(x))

  if var is None:
    var = zeros(len(x))

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


class EmissionSpectrum:
  def __init__(self):
    self.dataset_name = ""
    self.calibration_file = ""
    self.incident_energy = 0
    self.I0 = 1
    self.exposure_files = []
    self.filters = []

    spectrum = np.array([]).reshape(0,5)
    self.set_spectrum(spectrum)

    self.filename = None

    self.load_errors = []

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
    else:
      self.filename = filename

    with open(filename, 'w') as f:
      f.write("# minIXS XES Spectrum\n#\n")
      f.write("# Dataset: %s\n" % self.dataset_name)
      f.write("# Calibration File: %s\n" % self.calibration_file)
      f.write("# Incident Energy: %.2f\n" % self.incident_energy)
      f.write("# I0: %.2f\n" % self.I0)
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
        f.write("# E_emission    Intensity  Uncertainty  Raw_Counts   Num_Pixels\n")
        if len(self.spectrum.shape) == 2 and self.spectrum.shape[1] == 5:
          np.savetxt(f, self.spectrum, fmt=('%12.2f','%.6e','%.6e','% 11d',' % 11d'))
        elif len(self.spectrum) > 0:
          raise Exception("Invalid shape for spectrum array")
      

  def load(self, filename=None, header_only=False):
    if filename is None:
      filename = self.filename
    else:
      self.filename = filename

    with open(filename, 'r') as f:
      pos = f.tell()
      line = f.readline()

      in_exposures = False
      in_filters = False

      while line:
        if line[0] == "#":
          if in_exposures:
            ef = line[2:].strip()
            if ef:
              self.exposure_files.append(ef)
            else:
              in_exposures = False

          elif in_filters:
            if line[2:].strip() == '':
              in_filters = False
            else:
              name,val = line[2:].split(':')
              name = name.strip()
              fltr = get_filter_by_name(name)
              if fltr == None:
                self.load_errors.append("Unknown Filter: '%s' (Ignoring)" % name)
              else:
                fltr.set_str(val.strip())
                self.filters.append(fltr)

          elif line[2:10] == 'Dataset:':
            self.dataset_name = line[11:].strip()
          elif line[2:19] == 'Calibration File:':
            self.calibration_file = line[20:].strip()
          elif line[2:18] == 'Incident Energy:':
            self.incident_energy = float(line[19:].strip())
          elif line[2:5] == 'I0:':
            self.I0 = float(line[6:].strip())
          elif line[2:10] == 'Filters:':
            self.filters = []
            in_filters = True
          elif line[2:12] == 'Exposures:':
            self.exposure_files = []
            in_exposures = True
          else:
            pass
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

    return len(self.load_errors) == 0

  def process(self, emission_energies=None):
    calibration = Calibration()
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
                                calibration.xtals)

    self.set_spectrum(spectrum) 
