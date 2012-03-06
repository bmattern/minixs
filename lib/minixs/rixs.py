import minixs as mx
from emission import process_spectrum
import numpy as np
from itertools import izip
from parser import Parser, FLOAT, STRING, LIST

class InvalidParameters(Exception): pass

class RIXS(object):
  """
  A RIXS Spectrum is a 2D spectrum of intensity vs incident and emitted photon energies.

  In the miniXES context, this is simply a set of emission spectra taken at varying incident energies.
  This class takes a list of energies, incident fluxes (I0) and Pilatus exposures and converts into
  a normalized RIXS spectrum by processing each exposure in turn and dividing the resulting intensities
  by the corresponding I0 value.
  """
  def __init__(self, filename=None):
    self.dataset_name = ""
    self.calibration_file = ""
    self.energies = []
    self.I0s = []
    self.exposure_files = []
    self.filters = []
    self.spectrum = np.array([]) 
    self.filename = None
    if filename:
      self.load(filename)

  def save(self, filename=None, headers_only=False):
    """
    Save RIXS file

    Parameters:
      filename - either filename or file handle to save to
    """
    with mx.misc.to_filehandle(filename, "w") as (f, filename):
      if filename is None:
        filename = self.filename
      else:
        self.filename = filename

      f.write("# miniXS RIXS Spectrum\n#\n")
      f.write("# Dataset: %s\n" % self.dataset_name)
      f.write("# Calibration File: %s\n" % self.calibration_file)
      f.write("# Incident Energies / I0s / Exposures:\n")
      for energy, I0, ef in izip(self.energies, self.I0s, self.exposure_files):
        f.write("#   %12.2f %12.2f %s\n" % (energy, I0, ef))
      f.write("#\n")

      if self.filters:
        f.write("# Filters:\n")
        for fltr in self.filters:
          f.write('#   %s: %s\n' % (fltr.name, fltr.get_str()))
        f.write("#\n")

      if headers_only:
        return

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

      header = []

      parser = Parser({
        'Spectrometer': STRING,
        'Dataset': STRING,
        'Calibration File': STRING,
        'Incident Energies / I0s / Exposures': (LIST, (FLOAT, FLOAT, STRING)),
        'Filters': (LIST, STRING),
        })

      while line:
        if line[0] == "#":
          header.append(line[2:])
        elif header_only:
          return
        else:
          f.seek(pos)
          self.spectrum = np.loadtxt(f)
          if len(self.spectrum.shape) == 1:
            self.spectrum.shape = (1,self.spectrum.shape[0])

        pos = f.tell()
        line = f.readline()

    parsed = parser.parse(header)
    if parser.errors:
      self.load_errors += parser.errors

    self.dataset_name = parsed.get('Dataset', '')

    exposure_info = parsed.get('Incident Energies / I0s / Exposures', [])
    self.energies = [ei[0] for ei in exposure_info]
    self.I0s = [ei[1] for ei in exposure_info]
    self.exposure_files = [ei[2] for ei in exposure_info]

    self.calibration_file = parsed.get('Calibration', None)

    self.filters = []
    for filter_line in parsed.get('Filters', []):
      name,val = filter_line.split(':')
      name = name.strip()
      fltr = mx.filter.get_filter_by_name(name)
      if fltr == None:
        self.load_errors.append("Unknown Filter: '%s' (Ignoring)" % name)
      else:
        fltr.set_str(val.strip())
        self.filters.append(fltr)

  def _validate_before_processing(self):
    self.errors = []

    if not self.calibration_file:
      self.errors.append("Missing calibration_file.")
    if not self.energies:
      self.errors.append("Incident energies have not been set.")
    if not self.I0s:
      self.errors.append("I0 values have not been set.")
    if not self.exposure_files:
      self.errors.append("Exposure files have not been set.")
    if not (len(self.exposure_files) == len(self.I0s) == len(self.exposure_files)):
      self.errors.append("The number of exposures, energies and I0 values are not all the same.")

    return len(self.errors) == 0


  def process(self, emission_energies=None, progress_callback=None, skip_columns=[]):
    """
    Process this RIXS spectrum

    Preconditions:
      self.calibration_file is set to calibration filename
      self.exposure_files is list of exposure filenames
      self.energies is list of incident energies corresponding to exposure_files
      self.I0s is list of incident fluxes corresponding to exposure_files

    Parameters:
      emission_energies - list of points for emission energy grid
      progress_callback - callback to call after each exposure is processed
      skip_columns - list of columns (for vertical dispersive dir) or rows (for horizontal) to skip entirely

    Raises:
      InvalidParameters if any of the preconditions is not met. In this case, self.errors is set to a list of human readable error messages.
    """
    if not self._validate_before_processing():
      raise InvalidParameters()

    calibration = mx.calibrate.Calibration()

    if not calibration.load(self.calibration_file):
      self.errors.append("Invalid calibration file:\n  " + "\n  ".join(calibration.load_errors))
      raise InvalidParameters()

    # generate emission energies from range of calibration matrix
    if emission_energies is None:
      Emin,Emax = calibration.energy_range()
      emission_energies = np.arange(Emin,Emax,0.1)

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
    """
    Convert to a 2D matrix of intensities

    Returns:
      (incident, emitted, spectrum)

      incident - incident energy values (x-axis)
      emitted - emitted energy values (y-axis)
      spectrum - 2d array of intensities
    """
    inc_energies = np.unique(self.spectrum[:,0])
    emit_energies = np.unique(self.spectrum[:,1])

    i = len(inc_energies)
    return (inc_energies, emit_energies, self.spectrum[:,2].reshape((i,len(self.spectrum)/i)).T)


