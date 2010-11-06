
calibration_file = 'output/example.calib' # file to load calibration from
incident_energy = 7615.01 # in eV
I0 = 1 # this is used for normalization (I = counts / pixel / I0)
exposures = [ 'data/calib_00010.tif' ] # this can be multiple exposures taken at the same incident beam energy

xes_file = 'output/example.xes' # file to save spectrum to

if __name__ == "__main__":
  from minixs.emission  import EmissionSpectrum
  import os

  # make paths absolute
  calibration_file = os.path.abspath(calibration_file)
  exposures = [ os.path.abspath(e) for e in exposures ]

  # fill out emission specgtrum object
  xes = EmissionSpectrum()
  xes.calibration_file = calibration_file
  xes.incident_energy = incident_energy
  xes.I0 = I0
  xes.exposure_files = exposures

  # process
  print "Processing..."
  xes.process()

  print "Finished\n"

  print "Saving as '%s'" % xes_file
  xes.save(xes_file)
