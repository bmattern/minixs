import minixs as mx
from emission import process_spectrum
import numpy as np
from itertools import izip

class RIXS:
  def __init__(self):
    self.dataset_name = ""
    self.calibration_file = ""
    self.energies = []
    self.I0s = []
    self.exposure_files = []
    self.filters = []
    self.spectrum = np.array([]) 
    self.filename = None

  def save(self, filename=None):
    if filename is None:
      filename = self.filename
    else:
      self.filename = filename

    with open(filename, 'w') as f:
      f.write("# miniXS RIXS Spectrum\n#\n")
      f.write("# Dataset: %s\n" % self.dataset_name)
      f.write("# Calibration File: %s\n" % self.calibration_file)
      f.write("# Incident Energies / I0s / Exposures:\n")
      for energy, I0, ef in izip(self.energies, self.I0s, self.exposure_files):
        f.write("#   %12.2f %12.2f %s\n" % (energy, I0, ef))
      f.write("#\n")

      f.write("# E_incident   E_emission    Intensity  Uncertainty  Raw_Counts   Num_Pixels\n")
      if len(self.spectrum.shape) == 2 and self.spectrum.shape[1] == 6:
        fmt=('%12.2f', '%12.2f','%.6e','%.6e','% 11d',' % 11d')
        fmt = ' '.join(fmt)
        last_energy = None
        for row in self.spectrum:
          energy = row[0]

          # place empty line between inc. energies
          if last_energy is not None and energy != last_energy:
            f.write("\n")
          last_energy = energy

          f.write(fmt % tuple(row))
          f.write("\n")

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

  def process(self, emission_energies=None, progress_callback=None, skip_columns=[]):
    calibration = mx.calibrate.Calibration()
    calibration.load(self.calibration_file)

    # generate emission energies from range of calibration matrix
    if emission_energies is None:
      Emin = calibration.calibration_matrix[np.where(calibration.calibration_matrix > 0)].min()
      Emax = calibration.calibration_matrix.max()

      emission_energies = np.arange(Emin,Emax,.1)

    # create rixs array
    stride = len(emission_energies)
    spectrum = np.zeros((stride * len(self.energies), 6))

    # process each xes exposure and add to end of rixs array
    for i, energy in enumerate(self.energies):
      if progress_callback:
        progress_callback(i, energy)

      exposure = mx.exposure.Exposure(self.exposure_files[i])

      for f in self.filters:
        f.filter(exposure.pixels, energy)

      xes = process_spectrum(calibration.calibration_matrix,
                             exposure,
                             emission_energies,
                             self.I0s[i],
                             calibration.dispersive_direction,
                             calibration.xtals,
                             skip_columns=skip_columns)

      spectrum[i*stride:(i+1)*stride,0] = energy
      spectrum[i*stride:(i+1)*stride,1:] = xes

    self.spectrum = spectrum

  def matrix_form(self):
    inc_energies = np.unique(self.spectrum[:,0])
    emit_energies = np.unique(self.spectrum[:,1])

    rixs2d = np.zeros((len(emit_energies), len(inc_energies)))

    i = len(inc_energies)
    return (inc_energies, emit_energies, self.spectrum[:,2].reshape((i,len(self.spectrum)/i)).T)


