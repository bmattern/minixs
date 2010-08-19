import minixs 
import time
import os, sys
from itertools import izip

######################################
# Configurable parameters
######################################

do_calibration = True
do_process = False


DIR = "/home/bmattern/research/Fe_K_Beta/data/FeO/"

# dispersive direction in image
direction = minixs.VERTICAL

zero_pad = 5

# calibration parameters
calib_root = DIR + 'sequence_'
calib_nums = range(30,47)
calib_scan = DIR + 'calib.0004'

calib_scan_energy_column = 0
calib_scan_I0_column = 6

calib_filter_low  = 6
calib_filter_high = 10000
calib_filter_neighbors = 1

calib_filename = DIR + 'calibration.dat'

# spectrum parameters
spec_root = DIR + 'sequence_'
spec_nums = range(46,213)
spec_scan = DIR + 'xanes.0001'

spec_scan_energy_column = 0
spec_scan_I0_column = 6

spec_filter_low = 0
spec_filter_high = 100000

spec_low_energy = 7000
spec_high_energy = None
spec_energy_step = 0.7 # bin size

spec_filename = DIR + 'xanes.dat'



bad_pixels = [
    (13, 184)
]

kill_regions = [
    ((391,0),(393,196)),
    ((291,0),(294,196))
    ]



do_multi = True

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

  for energy, exposure in izip(c.energies, c.images):
    # mask out emission from calibration scan
    if energy >= 7090:
      z = 1.3214 * energy - 9235.82 - 12
      exposure.pixels[0:z,:] = 0

      

  c.build_calibration_matrix()
  c.kill_regions(kill_regions)
  c.interpolate(single_xtal=True)
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

