import minixs 
import time
import os, sys
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
calib_nums = range(1,19)  # pilatus file numbers (range() includes lower bound, but not upper bound!)
calib_scan = DIR + 'calib2.0001'

calib_scan_energy_column = 0
calib_scan_I0_column = 6

calib_filter_low  = 10 # ignore pixels with counts below this value
calib_filter_high = 10000  # ignore pixels with counts above this (bad pixels?)
calib_filter_neighbors = 1 # ingore pixels without at least this many neighbors

calib_filename = DIR + 'calibration.dat'  # filename to save calibration matrix as

# spectrum parameters
spec_root = DIR + 'rxes_'  # spectrum pilatus filename base
spec_nums = range(1,168)      # spectrum image numbers
spec_scan = DIR + 'rxes.0001' # spectrum scan file

spec_scan_energy_column = 0
spec_scan_I0_column = 6

spec_filter_low = 0
spec_filter_high = 100000

spec_low_energy = 7605   # minimum emission energy to include in spectrum
spec_high_energy = None  # maximum emission energy to include
spec_energy_step = 0.7   # emission energy bin size

spec_filename = DIR + 'rxes.dat'  # file to save spectrum to


# The following two parameters are used for both calibration and spectrum processing

# a list of bad pixels (note that the top left pixel is 0,0)
# ImageJ uses (1,1) for the top left, so be sure to subtract one if you
# are getting the values from there
bad_pixels = [
    (13, 184)
]

# regions to kill (ignore completely)
kill_regions = [
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
  energies, I0s = minixs.read_scan_info(calib_scan,
      [calib_scan_energy_column, calib_scan_I0_column])

  print "Calibration"
  t1 = time.time()

  c = minixs.Calibrator(energies, calib_files, direction)

  """
  for i in [36,37]:
    c.images[i].pixels[:,:] = 0

  """
  c.filter_images(calib_filter_low, calib_filter_high, calib_filter_neighbors, bad_pixels)

  c.build_calibration_matrix()
  c.kill_regions(kill_regions)
  c.save(calib_filename.replace('.dat','_preinterp.dat'))
  c.interpolate()
  c.save(calib_filename)

  t2 = time.time()
  print "  finished in %.2f s"  % (t2 - t1,)
else:
  print "Skipping calibration."


if do_process and os.path.exists(spec_filename):
  do_process = ask_yn_question("Processed data file exists. Reprocess? (y/n): ")

if do_process:
  energies, I0s = minixs.read_scan_info(spec_scan,
      [spec_scan_energy_column, spec_scan_I0_column])

  print "Process spectra"

  t1 = time.time()

  spectra = minixs.process_all(
      calib_filename,
      spec_scan,
      spec_root,
      spec_nums,
      low_cutoff=spec_filter_low,
      high_cutoff=spec_filter_high,
      low_energy=spec_low_energy,
      high_energy=spec_high_energy,
      energy_step=spec_energy_step,
      zero_pad=zero_pad
      )

  t2 = time.time()
  print"  finished in %.2f s" % (t2 - t1,)

  rixs = minixs.build_rixs(spectra, energies)
  minixs.save_rixs(spec_filename, rixs)


