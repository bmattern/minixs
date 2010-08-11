from numpy import zeros, arange, sqrt, where, loadtxt, savetxt, unique, argmin
from itertools import izip
import calibrate
import exposure
import sys

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


def process_all(calibfile, scanfile, base_image, image_nums, E_column=0, I0_column=6, low_cutoff=0, high_cutoff=1000, low_energy=None, high_energy=None, energy_step = 0.5):

  calib = loadtxt(calibfile)

  if low_energy is None:
    low_energy = calib[where(calib > 0)].min()

  if high_energy is None:
    high_energy = calib.max()


  Es, I0s = calibrate.read_scan_info(scanfile)
  filenames = calibrate.gen_image_names(base_image, image_nums)
  exposures = [ exposure.Exposure(filename) for filename in filenames ]

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


def rixs_pfy_cut(rixs, energy):
  energies = unique(rixs[:,0])
 
  i = argmin(abs(energies - energy))

  return rixs[where(rixs[:,0] == energies[i])]

