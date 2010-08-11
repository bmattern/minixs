import calibrate, process, exposure
import time
import os

######################################

# dispersive direction in image
direction = calibrate.HORIZONTAL

calib_root = 'cerh3/cerh3-elastic4_'
calib_nums = range(1,17)
calib_scan = 'cerh3/cerh3elastic.0004'

calib_filename = 'cerh3/cerh3_calibration.dat'

calib_filter_low  = 3.5
calib_filter_high = 75
calib_filter_neighbors = 1

spec_root = 'cerh3/cerh3-rxes4_'
spec_nums = range(1,79)
spec_scan = 'cerh3/cerh3rexs4.0002'

spec_filter_low = 0
spec_filter_high = 200

spec_low_energy = 4800
spec_high_energy = None
spec_energy_step = 0.5 # bin size

spec_filename = 'cerh3/cerh3_rixs.dat'


#####################################

if not os.path.exists(calib_filename):
  calib_files = calibrate.gen_image_names(calib_root, calib_nums)
  energies, I0s = calibrate.read_scan_info(calib_scan)

  print "Calibration"
  t1 = time.time()

  c = calibrate.Calibrate(energies, I0s, calib_files, direction)
  c.filter_images(calib_filter_low, calib_filter_high, calib_filter_neighbors)
  c.build_calibration_matrix()
  c.kill_regions([])
  c.interpolate()
  c.save(calib_filename)

  t2 = time.time()
  print "  finished in %.2f s"  % (t2 - t1,)
else:
  print "Already calibrated, skipping."

energies, I0s = calibrate.read_scan_info(spec_scan)

print "Process spectra"
t1 = time.time()

spectra = process.process_all(
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

rixs = process.build_rixs(spectra, energies)
process.save_rixs(spec_filename, rixs)


