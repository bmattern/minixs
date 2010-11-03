"""
XES Spectrum processing code
"""

def emission_spectrum(cal, exposure, energies, I0, direction, xtals):
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

  intensity = zeros(energies.shape)
  #variance = zeros(energies.shape)
  mask = zeros(energies.shape)
  #y_i = zeros(energies.shape)
  #var_i = zeros(energies.shape)
  cols = zeros(energies.shape)

  for xtal in xtals:
    (x1,y1), (x2,y2) = xtal

    if direction == DOWN or direction == UP:
      i1, i2 = x1, x2
    else:
      i1, i2 = y1, y2

    for i in range(i1,i2):
      if direction == DOWN or direction == UP:
        # for now, use quicker method that overestimates statistical error
        y_i = interp(energies, cal[y1:y2,i], exposure.pixels[y1:y2,i],-1,-1)

        # the following is much slower, but gets the statistical error correct
        #interp_poisson(energies, y_i, var_i, cal[:,i], exposure.pixels[:,i],-1,-1)
      else:
        y_i = interp(energies, cal[i,x2:x1:-1], exposure.pixels[i,x2:x1:-1],-1,-1)

      mask *= 0
      mask[where(y_i >= 0)] = 1
      intensity += y_i * mask
      #variance += var_i * mask
      cols += mask

  norm = cols.copy()
  norm[where(norm == 0)] = 1
  spectrum = vstack([energies, intensity/I0/norm, sqrt(intensity)/I0/norm, intensity, cols]).T

  return spectrum


def binned_emission_spectrum(calib, exposure, low_energy, high_energy, energy_step, I0):
  """
  Calculate emission spectrum from exposure and calibration matrix

  Return:
    array of (emission_energy, I, sigma, raw_counts, num_pixels)
      I = raw_counts / num_pixels / I0
      sigma = sqrt(raw_counts) / num_pixels / I0

  """

  if low_energy is None:
    low_energy = calib[where(calib > 0)].min()
  if high_energy is None:
    high_energy = calib.max()

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
