import minixs
import time, sys
from numpy import loadtxt, savetxt


DIR = '/home/bmattern/research/Fe_K_Beta/data/FeS2/'

calib_filename = DIR + 'calibration.dat'
spec_root = DIR + 'sequence_'
spec_nums = range(213,285)
spec_count = 6
spec_scan = DIR + 'rxes.0001'

spec_scan_energy_column = 0
spec_scan_I0_column = 6

spec_filter_low = 0
spec_filter_high = 100000

spec_low_energy = 7000
spec_high_energy = 7150
spec_energy_step = 0.7 # bin size

spec_out_form = DIR + 'rxes_%d.dat'

energies, I0s = minixs.read_scan_info(spec_scan,
    [spec_scan_energy_column, spec_scan_I0_column])

calib = loadtxt(calib_filename)
t1 = time.time()
print "Process spectra"

for i in range(spec_count):
  sys.stdout.write(".")
  sys.stdout.flush()


  e = minixs.Exposure()

  nums = spec_nums[i::6]
  file_names = minixs.gen_file_list(spec_root, nums, 5)
  e.load_multi(file_names)

  s = minixs.emission_spectrum(calib,
      e,
      spec_low_energy,
      spec_high_energy,
      spec_energy_step,
      I0s[i])

  savetxt(spec_out_form % energies[i], s)

t2 = time.time()
print"  finished in %.2f s" % (t2 - t1,)

