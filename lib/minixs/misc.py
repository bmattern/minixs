import numpy as np
from itertools import izip, product as iproduct
from scanfile import ScanFile

def gen_rects(horizontal_bounds=None, vertical_bounds=None):
  """Convert lists of horizontal and vertical boundary locations into rectangles"""
  return [
      ((l,t),(r,b))
      for (l,r) in izip(horizontal_bounds[0:-1], horizontal_bounds[1:])
      for (t,b) in izip(vertical_bounds[0:-1], vertical_bounds[1:])
      ]

def gen_file_list(prefix, vals, zero_pad=3, suffix='.tif'):
  """Generate a list of numerically sequenced file names"""
  fmt = '%s%%0%dd%s' % (prefix, zero_pad, suffix)
  return [fmt % val for val in vals]

def read_scan_info(scanfile, columns):
  """Read a subset of columns from a scan file

  The default columns correspond to the typical Mono Energy an I0 columns.
  The returned list is transposed so that the following works:

  c0, c6 = read_scan_info("scanfile.0001", [0,6])
  """

  s = ScanFile(scanfile)
  return s.data[:,columns].transpose()

def determine_dispersive_direction(e1, e2, threshold=.75, sep=20):
  """Given two exposures with increasing energy, determine
  the dispersive direction on the camera"""

  p1 = e1.pixels.copy()
  p2 = e2.pixels.copy()

  p1[np.where(p1 > 10000)] = 0
  p2[np.where(p2 > 10000)] = 0

  tests = [
      (0, (1,sep)), # DOWN
      (1, (-sep,-1)), # LEFT
      (0, (-sep,-1)),   # UP
      (1, (1,sep))    # RIGHT
      ]

  diffs = [
      np.min([ np.sum(np.abs(p2 - np.roll(p1,i,axis)))
            for i in np.arange(i1,i2) ])
      for axis, (i1,i2) in tests ]

  if np.min(diffs) / np.average(diffs) < threshold:
    return np.argmin(diffs)

  return -1


def build_rixs(spectra, energies):
  total_length = np.sum([len(s) for s in spectra])
  full_spectrum = np.zeros((total_length, 6))

  i = 0
  for s,E in izip(spectra, energies):
    full_spectrum[i:i+len(s),0] = E
    full_spectrum[i:i+len(s),1:] = s
    i += len(s)

  return full_spectrum

def save_rixs(filename, rixs):
  with open(filename, 'w') as f:
    f.write("#    E_incident      E_emission       Intensity           Sigma          Counts      Num_pixels\n")

    fmt = ('% 15.2f', '% 15.2f', '% 15.8e','% 15.8e','% 15d', '% 15d')
    savetxt(f, rixs, fmt=fmt)


def rixs_xes_cut(rixs, energy):
  energies = np.unique(rixs[:,0])
 
  i = argmin(np.abs(energies - energy))

  return rixs[np.where(rixs[:,0] == energies[i])]

def rixs_pfy_cut(rixs, energy):
  energies = np.unique(rixs[:,1])
 
  i = np.argmin(np.abs(energies - energy))

  return rixs[np.where(rixs[:,1] == energies[i])]


def rixs2d(rixs):
  inc_energies = np.unique(rixs[:,0])
  emit_energies = np.unique(rixs[:,1])

  rixs2d = np.zeros((len(emit_energies), len(inc_energies)))

  i = len(inc_energies)
  return rixs[:,2].reshape((i,len(rixs)/i)).T

def plot_rixs_contour(rixs, plot_log=False, aspect=1):
  incE = np.unique(rixs[:,0])
  emitE = np.unique(rixs[:,1])
  r2d = rixs2d(rixs)
  if plot_log:
    r2d = log10(r2d)

  from matplotlib.pyplot import contourf, figure, colorbar
  figure()
  contourf(incE, emitE, r2d, 50, aspect=aspect)
  colorbar()

def plot_rixs(rixs, start=0, end=-1, plot_log=False, aspect=1):
  incE = np.unique(rixs[:,0])
  emitE = np.unique(rixs[:,1])
  r2d = rixs2d(rixs)
  if plot_log:
    r2d = log(r2d)

  from matplotlib.pyplot import imshow, figure
  figure()
  imshow(
      r2d[:,start:end],
      extent=(incE[start],incE[end],emitE[-1],emitE[0]),
      aspect=aspect)

def plot_spectrum(s, **kwargs):
  plot_errorbars = True
  if kwargs.has_key('errorbar'):
    plot_errorbars = kwargs['errorbar']
    del(kwargs['errorbar'])

  new_plot = True
  if kwargs.has_key('new_plot'):
    new_plot = kwargs['new_plot']
    del(kwargs['new_plot'])

  normalize = False
  if kwargs.has_key('normalize'):
    normalize = kwargs['normalize']
    del(kwargs['normalize'])


  from matplotlib.pyplot import plot, errorbar, figure

  if new_plot:
    figure()

 
  n = 1
  if normalize:
    n = np.sum(s[:,1]) / len(s[:,1])

  if plot_errorbars:
    errorbar(s[:,0], s[:,1]/n, s[:,2]/n, **kwargs)
  else:
    plot(s[:,0], s[:,1]/n, **kwargs)
    
