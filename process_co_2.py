import minixs 
import time
import os, sys
from numpy import array, append, average, loadtxt, arange
from itertools import izip

"""
minIXS calibration and processing script

minixs.py must either be in this directory or somewhere included in sys.path (which can be set by the PYTHONPATH environment variable)

Configurable parameters are all located at the top of this file.
"""

######################################
# Configurable parameters
######################################

DIR = "/home/bmattern/research/Ravel_Co/Powder/"

# dispersive direction in image
direction = minixs.HORIZONTAL

# zero padding on pilatus image files
zero_pad = 5

# calibration parameters
calib_root = DIR + 'calib2_'  # pilatus file name base
calib_nums = range(1,55)  # pilatus file numbers (range() includes lower bound, but not upper bound!)

calib_scans = minixs.gen_file_list(
    DIR + 'calib2.', # scan root
    range(1,4), # list of scan numbers
    4, # zero pad to this many digits
    '' # no extension after the number
    )
calib_scan_energy_column = 0

calib_filter_low  = 10 # ignore pixels with counts below this value
calib_filter_high = 10000  # ignore pixels with counts above this (bad pixels?)
calib_filter_neighbors = 1 # ignore pixels without at least this many neighbors

calib_filename = DIR + 'calibration2.dat'  # filename to save calibration matrix as

# spectrum parameters
spec_root = DIR + 'rxes_'  # spectrum pilatus filename base
spec_nums = range(1,168)      # spectrum image numbers
spec_scan = DIR + 'rxes.0001' # spectrum scan file

spec_scan_energy_column = 0
spec_scan_I0_column = 6

spec_filter_low = 0
spec_filter_high = 100000

spec_low_energy = 7605   # minimum emission energy to include in spectrum
spec_high_energy = 7680 # maximum emission energy to include
spec_energy_step = 0.7   # emission energy bin size

spec_filename = DIR + 'rxes2.dat'  # file to save spectrum to


# The following two parameters are used for both calibration and spectrum processing

# a list of bad pixels (note that the top left pixel is 0,0)
bad_pixels = [
    (14, 185)
]

# regions to kill (ignore completely)
kill_regions = [
    ]

# crystal boundaries
xtals = [
    ((15,0),(119,195)),
    ((134,0),(230,195)),
    ((251,0),(343,195)),
    ((357,0),(457,195))
    ]

# whether to process or calibrate or both
# if these are True and an output file exists, the program will ask before overwriting
do_calibration = False 
do_process = True

#####################################

def ask_yn_question(question):
  ret = False
  valid = False
  while not valid:
    sys.stdout.write(question)
    response = sys.stdin.readline().strip().lower()
    if response[0] == 'y':
      valid = True
      ret = True
    elif response[0] == 'n':
      valid = True
      ret = False
    else:
      print "I didn't understand your response. Please try again."
  return ret



if do_calibration and os.path.exists(calib_filename):
  do_calibration = ask_yn_question("Calibration matrix exists. Recalibrate? (y/n): ")
      
if do_calibration: 
  calib_files = minixs.gen_file_list(calib_root, calib_nums, zero_pad)

  energies = array([])
  for s in calib_scans:
    energies = append(energies,
        minixs.read_scan_info(s, [calib_scan_energy_column])[0]
        )

  print "Calibration"
  t1 = time.time()

  c = minixs.Calibrator(energies, calib_files, direction)

  c.filter_images(calib_filter_low, calib_filter_high, calib_filter_neighbors, bad_pixels)

  points, lin_res, rms_res = c.calibrate(xtals)
  c.save(calib_filename)

  t2 = time.time()
  print "  finished in %.2f s"  % (t2 - t1,)
  print ""
  print "Average RMS deviation of fit: ", average(rms_res)
  print "Average linear deviation of fit: ", average(lin_res)
else:
  print "Skipping calibration."


if do_process and os.path.exists(spec_filename):
  do_process = ask_yn_question("Processed data file exists. Reprocess? (y/n): ")

if do_process:
  inc_energies, I0s = minixs.read_scan_info(spec_scan,
      [spec_scan_energy_column, spec_scan_I0_column])

  t1 = time.time()

  print "Process spectra"
  calib = loadtxt(calib_filename)

  if spec_low_energy is None:
    spec_low_energy = calib[where(calib > 0)].min()

  if spec_high_energy is None:
    spec_high_energy = calib.max()

  energies = arange(
      spec_low_energy,
      spec_high_energy + spec_energy_step,
      spec_energy_step)

  Es, I0s = minixs.read_scan_info(spec_scan, [spec_scan_energy_column, spec_scan_I0_column])
  filenames = minixs.gen_file_list(spec_root, spec_nums, zero_pad)

  print "Directory: %s" % os.path.dirname(filenames[0])
  print "Files %s to %s" % (os.path.basename(filenames[0]),
      os.path.basename(filenames[-1]))
  exposures = [ minixs.Exposure(filename) for filename in filenames ]

  for e in exposures:
    e.filter_low_high(spec_filter_low, spec_filter_high)
    e.filter_bad_pixels(bad_pixels)

  spectra = [ minixs.emission_spectrum2(calib, e, energies, I0, direction, xtals) for e, I0 in izip(exposures, I0s) ]

  t2 = time.time()
  print"  finished in %.2f s" % (t2 - t1,)

  rixs = minixs.build_rixs(spectra, inc_energies)
  minixs.save_rixs(spec_filename, rixs)


