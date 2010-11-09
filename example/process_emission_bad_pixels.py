"""
An example processing script that includes filtering of bad pixels

Note that the only bad pixel present in the provided example data is outside of the crystal regions, so this isn't required. But this script can be modified for data that does require it.
"""

import minixs as mx
from minixs.misc import gen_file_list
from minixs.exposure import Exposure
from minixs.calibrate import Calibration
from minixs.filter import BadPixelFilter

calibration_file = 'example.calib' # file to load calibration from
incident_energy = 7615.01 # in eV
I0 = 1 # this is used for normalization (I = counts / pixel / I0)
exposures = [ 'calib_00010.tif' ] # this can be multiple exposures taken at the same incident beam energy

bad_pixels = [(14,185)] # pixels whose values should be ignored
xes_file = 'example.xes' # file to save spectrum to

if __name__ == "__main__":
  from minixs.emission  import EmissionSpectrum

  xes = EmissionSpectrum()
  xes.calibration_file = calibration_file
  xes.incident_energy = incident_energy
  xes.I0 = I0
  xes.exposure_files = exposures

  # set up bad pixel filter if needed
  if bad_pixels:
    fltr = BadPixelFilter()
    calib = Calibration()
    calib.load(calibration_file)
    if calib.dispersive_direction in [mx.UP, mx.DOWN]:
      mode = fltr.MODE_INTERP_V
    else:
      mode = fltr.MODE_INTERP_H
    fltr.set_val((mode, bad_pixels))
    xes.filters.append(fltr)

  # process
  print "Processing..."
  xes.process()

  print "Finished\n"

  print "Saving as '%s'" % xes_file
  xes.save(xes_file)
