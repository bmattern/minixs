import minixs 
import time
import os, sys
from itertools import izip

######################################
# Configurable parameters
######################################

DIR = "/home/bmattern/research/Fe_K_Beta/data/fe_wire_2/"

# dispersive direction in image
direction = minixs.VERTICAL

zero_pad = 5

# calibration parameters
calib_root = DIR + 'elastic_'
calib_nums = range(1,50)
calib_scan = DIR + 'elastic.0001'

calib_scan_energy_column = 0
calib_scan_I0_column = 6

calib_filter_low  = 10
calib_filter_high = 200
calib_filter_neighbors = 1

calib_filename = DIR + 'calibration.dat'

# spectrum parameters
spec_root = DIR + 'xanes_'
spec_nums = range(1,161)
spec_scan = DIR + 'xanes.0001'

spec_scan_energy_column = 0
spec_scan_I0_column = 6

spec_filter_low = 0
spec_filter_high = 100000

spec_low_energy = 7000
spec_high_energy = None
spec_energy_step = 0.7 # bin size

spec_filename = DIR + 'xanes.dat'


kill_regions = [
    ]


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


do_calibration = True

if os.path.exists(calib_filename):
  do_calibration = ask_yn_question("Calibration matrix exists. Recalibrate? (y/n): ")
      
if do_calibration: 
  calib_files = minixs.gen_file_list(calib_root, calib_nums, zero_pad)
  energies, I0s = minixs.read_scan_info(calib_scan,
      [calib_scan_energy_column, calib_scan_I0_column])

  print "Calibration"
  t1 = time.time()

  c = minixs.Calibrator(energies, I0s, calib_files, direction)

  for i in [36,37]:
    c.images[i].pixels[:,:] = 0

  c.filter_images(calib_filter_low, calib_filter_high, calib_filter_neighbors)

  for energy, exposure in izip(c.energies, c.images):
    # mask out emission from calibration scan
    if energy >= 7090:
      z = 1.3214 * energy - 9235.82 - 12
      exposure.pixels[0:z,:] = 0

      

  c.build_calibration_matrix()
  c.kill_regions([])
  c.interpolate()
  c.save(calib_filename)

  t2 = time.time()
  print "  finished in %.2f s"  % (t2 - t1,)
else:
  print "Skipping calibration."

do_process = True

if os.path.exists(spec_filename):
  do_process = ask_yn_question("Processed data file exists. Reprocess? (y/n): ")

energies, I0s = minixs.read_scan_info(spec_scan,
    [spec_scan_energy_column, spec_scan_I0_column])

if do_process:
  print "Processing %d spectra" % len(spec_nums)

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

