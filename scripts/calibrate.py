from minixs.misc import gen_file_list

calib_filename = 'example.calib' # file to save out to
scan_file  = 'calib.0001'      # file containing energies
energy_col = 0                   # column containing energies

# list of exposure filenames (example_00001.tif ... example_00018.tif)
exposures = [ 'calib_%05d.tif' % i for i in range(1,19) ]

# Direction in which energy increases.
# Can be "Up", "Down", "Left" or "Right"
dispersive_direction = "Left"

# Filters to apply to images
filters = [
    ('Low Cutoff', 10),
    #('High Cutoff', 10000),
    ('Neighbors', 2)
    ]

# Boundaries of regions containing individual spectra
# In miniXS these each correspond to reflections from individual crystals
xtal_boundaries = [
    #(x1, y1, x2, y2),
    (17, 7, 119, 190),
    (135, 6, 229, 190),
    (249, 7, 343, 187),
    (357, 9, 457, 189)
    ] 

if __name__ == "__main__":
  from minixs.calibrate import Calibration
  from minixs.misc import read_scan_info
  import minixs.filter as filter
  from minixs.constants import *

  c = Calibration()

  c.exposure_files = exposures
  c.energies = read_scan_info(scan_file, [energy_col])[0]
  c.dispersive_direction = DIRECTION_NAMES.index(dispersive_direction)

  # load up filters
  for name, val in filters:
    f = filter.get_filter_by_name(name)
    if f is None:
      print "Unknown filter: %s" % name
      exit(1)

    f.set_val(val)
    c.filters.append(f)

  # convert xtal format to that used by rest of code
  c.xtals = [ ((x1,y1),(x2,y2)) for x1,y1,x2,y2 in xtal_boundaries ]

  # calibrate
  print "Calibrating..."
  c.calibrate()

  print "Finished\n"

  print "Residues\n--------\n"
  for i in range(len(xtal_boundaries)):
    print "Xtal #%d" % i
    print "  Linear: %.3e" % c.lin_res[i]
    print "  RMS: %.3e" % c.rms_res[i]
    print "\n"

  print "Saving as '%s'" % calib_filename
  c.save(calib_filename)
