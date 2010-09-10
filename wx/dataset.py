import minixs as mx
import numpy as np
from itertools import izip

class InvalidFileError(Exception):
  pass

class CalibrationInfo:

  def __init__(self):
    self.dataset_name = ""
    self.dispersive_direction = mx.DOWN
    self.energies = []
    self.exposure_files = []
    self.filters = []
    self.xtals = []
    self.calibration_matrix = np.array([])

    self.filename = None

  def save(self, filename=None):
    if filename is None:
      filename = self.filename
    else:
      self.filename = filename

    with open(filename, 'w') as f:
      f.write("# minIXS calibration matrix\n#\n")
      f.write("# Dataset: %s\n" % self.dataset_name)
      f.write("# Dispersive Direction: %s\n" % mx.DIRECTION_NAMES[self.dispersive_direction])
      f.write("#\n")
      f.write("# Energies and Exposures:\n")
      for en, ex in izip(self.energies, self.exposure_files):
        f.write("#   %5.2f %s\n" % (en,ex))
      f.write("#\n")

      f.write("# Filters:\n")
      for fltr in self.filters:
        f.write('#   %s: %d\n' % fltr)
      f.write("#\n")

      f.write("# Xtal Boundaries:\n")
      for (x1,y1), (x2,y2) in self.xtals:
        f.write("#   %3d %3d %3d %3d\n" % (x1,y1,x2,y2))
      f.write("#\n")

      if self.calibration_matrix and len(self.calibration_matrix.shape) == 2:
        f.write("# %d x %d matrix follows\n" % self.calibration_matrix.shape)

        np.savetxt(f, self.calibration_matrix, fmt='%.3f')

  def load(self, filename=None, header_only=False):
    if filename is None:
      filename = self.filename
    else:
      self.filename = filename

    with open(filename, 'r') as f:
      pos = f.tell()
      line = f.readline()

      if line.strip() != '# minIXS calibration matrix':
        raise InvalidFileError()

      in_exposures = False
      in_filters = False
      in_xtals = False

      while line:
        if line[0] == "#":

          if in_exposures:
            if line[2:].strip() == '':
              in_exposures = False
            else:
              energy, ef = line[2:].split()
              energy = float(energy.strip())
              ef = ef.strip()

              self.energies.append(energy)
              self.exposure_files.append(ef)

          elif in_filters:
            if line[2:].strip() == '':
              in_filters = False
            else:
              name,val = line[2:].split(':')
              name = name.strip()
              val = int(val.strip())
              self.filters.append((name,val))

          elif in_xtals:
            if line[2:].strip() == '':
              in_xtals = False
            else:
              x1,y1,x2,y2 = [int(s.strip()) for s in line[2:].split()]
              self.xtals.append([[x1,y1],[x2,y2]])

          elif line[2:10] == 'Dataset:':
            self.dataset_name = line[11:].strip()
          elif line[2:23] == 'Dispersive Direction:':
            dirname = line[24:].strip()
            print dirname
            if dirname in mx.DIRECTION_NAMES:
              self.dispersive_direction = mx.DIRECTION_NAMES.index(dirname)
          elif line[2:25] == 'Energies and Exposures:':
            self.energies = []
            self.exposure_files = []
            in_exposures = True
          elif line[2:10] == 'Filters:':
            self.filters = []
            in_filters = True
          elif line[2:18] == 'Xtal Boundaries:':
            self.xtals = []
            in_xtals = True
          else:
            pass
        elif header_only:
          return
        else:
          f.seek(pos)
          self.calibration_matrix = np.loadtxt(f)
          if len(self.calibration_matrix.shape) == 1:
            self.calibration_matrix.shape = (1,self.spectrum.shape[0])
          return

        pos = f.tell()
        line = f.readline()

class XESInfo:
  def __init__(self):
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
 
  def save(self, filename=None):
    if filename is None:
      filename = self.filename
    else:
      self.filename = filename

    with open(filename, 'w') as f:
      f.write("# minIXS XES Spectrum\n#\n")
      f.write("# Dataset: %s\n" % self.dataset_name)
      f.write("# Energy: %.2f\n" % self.energy)
      f.write("# I0: %.2f\n" % self.I0)
      f.write("# Exposures:\n")
      for ef in self.exposure_files:
        f.write("#   %s\n" % ef)
      f.write("#\n")
      f.write("# E_emission    Intensity  Uncertainty  Raw_Counts   Num_Pixels\n")
      np.savetxt(f, self.spectrum, fmt=('%12.2f','%.6e','%.6e','% 11d',' % 11d'))

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
          elif line[2:9] == 'Energy:':
            self.energy = float(line[10:].strip())
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

class DataSet:
  def __init__(self):
    self.name = ""
    self.description = ""

