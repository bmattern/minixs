import minixs as mx
import numpy as np
from itertools import izip
from filter import get_filter_by_name

FILE_UNKNOWN     = -1
FILE_CALIBRATION = 0
FILE_XTALS       = 1
FILE_XES         = 2
FILE_RIXS        = 3

FILE_TYPES = [
    'calibration matrix',
    'crystal boundaries',
    'XES spectrum',
    'RIXS spectrum'
    ]

def determine_filetype(path):
  with open(path) as f:
    line = f.readline()
    if line[0] != "#":
      return FILE_UNKNOWN

    s = line[2:]

    if not s.startswith('minIXS'):
      return 0

    t = s[7:].strip()
    if t in FILE_TYPES:
      return FILE_TYPES.index(t)

    return FILE_UNKNOWN

class InvalidFileError(Exception):
  pass

class XESInfo:
  def __init__(self):
    self.dataset_name = ""
    self.calibration_file = ""
    self.energy = 0
    self.I0 = 0
    self.exposure_files = []
    self.spectrum = np.array([]) 
    self.filename = None

  def set_energy(self, energy):
    self.energy = energy

  def set_I0(self, I0):
    self.I0 = I0

  def set_exposure_files(self, exposure_files):
    self.exposure_files = exposure_files

  def set_spectrum(self, spectrum):
    self.spectrum = spectrum
 
  def save(self, filename=None, header_only=False):
    if filename is None:
      filename = self.filename
    else:
      self.filename = filename

    with open(filename, 'w') as f:
      f.write("# minIXS XES Spectrum\n#\n")
      f.write("# Dataset: %s\n" % self.dataset_name)
      f.write("# Calibration File: %s\n" % self.calibration_file)
      f.write("# Incident Energy: %.2f\n" % self.energy)
      f.write("# I0: %.2f\n" % self.I0)
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

      while line:
        if line[0] == "#":
          if in_exposures:
            ef = line[2:].strip()
            if ef:
              self.exposure_files.append(ef)
            else:
              in_exposures = False

          elif line[2:10] == 'Dataset:':
            self.dataset_name = line[11:].strip()
          elif line[2:19] == 'Calibration File:':
            self.calibration_file = line[20:].strip()
          elif line[2:18] == 'Incident Energy:':
            self.energy = float(line[19:].strip())
          elif line[2:5] == 'I0:':
            self.I0 = float(line[6:].strip())
          elif line[2:12] == 'Exposures:':
            self.exposure_files = []
            in_exposures = True
          else:
            pass
        elif header_only:
          return
        else:
          f.seek(pos)
          self.spectrum = np.loadtxt(f)
          if len(self.spectrum.shape) == 1:
            self.spectrum.shape = (1,self.spectrum.shape[0])

        pos = f.tell()
        line = f.readline()

class RIXSInfo:
  def __init__(self):
    self.dataset_name = ""
    self.calibration_file = ""
    self.energies = []
    self.I0s = []
    self.exposure_files = []
    self.spectrum = np.array([]) 
    self.filename = None

  def save(self, filename=None):
    if filename is None:
      filename = self.filename
    else:
      self.filename = filename

    with open(filename, 'w') as f:
      f.write("# minIXS RIXS Spectrum\n#\n")
      f.write("# Dataset: %s\n" % self.dataset_name)
      f.write("# Calibration File: %s\n" % self.calibration_file)
      f.write("# Incident Energies / I0s / Exposures:\n")
      for energy, I0, ef in izip(self.energies, self.I0s, self.exposure_files):
        f.write("#   %12.2f %12.2f %s\n" % (energy, I0, ef))
      f.write("#\n")

      f.write("# E_incident   E_emission    Intensity  Uncertainty  Raw_Counts   Num_Pixels\n")
      if len(self.spectrum.shape) == 2 and self.spectrum.shape[1] == 6:
        fmt=('%12.2f', '%12.2f','%.6e','%.6e','% 11d',' % 11d')
        np.savetxt(f, self.spectrum, fmt=fmt)
      elif len(self.spectrum) > 0:
        raise Exception("Invalid shape for RIXS spectrum array")
      

  def load(self, filename=None, header_only=False):
    if filename is None:
      filename = self.filename
    else:
      self.filename = filename

    with open(filename, 'r') as f:
      pos = f.tell()
      line = f.readline()

      in_exposures = False

      while line:
        if line[0] == "#":

          # parse exposures
          if in_exposures:
            bits = line[2:].split(None, 3)
            if not bits:
              in_exposures = False
            elif len(bits) > 0:
              energy = float(bits[0].strip())
              I0 = float(bits[1].strip())
              ef = ' '.join(bits[2:]).strip()
              if ef:
                self.energies.append(energy)
                self.I0s.append(I0)
                self.exposure_files.append(ef)
            else:
              raise Exception("Invalid Format")

          elif line[2:10] == 'Dataset:':
            self.dataset_name = line[11:].strip()
          elif line[2:19] == 'Calibration File:':
            self.calibration_file = line[20:].strip()
          elif line[2:38] == 'Incident Energies / I0s / Exposures:':
            self.exposure_files = []
            in_exposures = True
          else:
            pass
        elif header_only:
          return
        else:
          f.seek(pos)
          self.spectrum = np.loadtxt(f)
          if len(self.spectrum.shape) == 1:
            self.spectrum.shape = (1,self.spectrum.shape[0])

        pos = f.tell()
        line = f.readline()

class DataSet:
  def __init__(self):
    self.name = ""
    self.description = ""

