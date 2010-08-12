import minixs 
import time
import os, sys

######################################
# Configurable parameters
######################################

# dispersive direction in image
direction = minixs.VERTICAL

# calibration parameters
calib_root = 'rotated/rotated-elastic4_'
calib_nums = range(1,17)
calib_scan = 'rotated/cerh3elastic.0004'

calib_scan_energy_column = 0
calib_scan_I0_column = 6

calib_filter_low  = 3.5
calib_filter_high = 75
calib_filter_neighbors = 1

calib_filename = 'rotated/rotated_calibration.dat'

# spectrum parameters
spec_root = 'rotated/rotated-rxes4_'
spec_nums = range(1,79)
spec_scan = 'rotated/cerh3rexs4.0002'

spec_scan_energy_column = 0
spec_scan_I0_column = 6

spec_filter_low = 0
spec_filter_high = 200

spec_low_energy = 4800
spec_high_energy = None
spec_energy_step = 0.5 # bin size

spec_filename = 'rotated/rotated_rixs.dat'


kill_regions = [
    ((0,0),(800,10)),
    ((0,105),(800,120)),
    ((389,0),(800,120)),
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
  calib_files = minixs.gen_file_list(calib_root, calib_nums)
  energies, I0s = minixs.read_scan_info(calib_scan,
      [calib_scan_energy_column, calib_scan_I0_column])

  print "Calibration"
  t1 = time.time()

  c = minixs.Calibrator(energies, I0s, calib_files, direction)
  c.filter_images(calib_filter_low, calib_filter_high, calib_filter_neighbors)
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
      energy_step=spec_energy_step
      )

  t2 = time.time()
  print"  finished in %.2f s" % (t2 - t1,)

  rixs = minixs.build_rixs(spectra, energies)
  minixs.save_rixs(spec_filename, rixs)

