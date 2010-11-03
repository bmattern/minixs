from numpy import *
from scipy import polyfit, polyval
from itertools import izip, product as iproduct
import sys, os
import time

from scanfile import ScanFile
from exposure import Exposure
from misc import *

from constants import *

def build_rixs(spectra, energies):
  total_length = sum([len(s) for s in spectra])
  full_spectrum = zeros((total_length, 6))

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
  energies = unique(rixs[:,0])
 
  i = argmin(abs(energies - energy))

  return rixs[where(rixs[:,0] == energies[i])]

def rixs_pfy_cut(rixs, energy):
  energies = unique(rixs[:,1])
 
  i = argmin(abs(energies - energy))

  return rixs[where(rixs[:,1] == energies[i])]


def rixs2d(rixs):
  inc_energies = unique(rixs[:,0])
  emit_energies = unique(rixs[:,1])

  rixs2d = zeros((len(emit_energies), len(inc_energies)))

  i = len(inc_energies)
  return rixs[:,2].reshape((i,len(rixs)/i)).T

def plot_rixs_contour(rixs, plot_log=False, aspect=1):
  incE = unique(rixs[:,0])
  emitE = unique(rixs[:,1])
  r2d = rixs2d(rixs)
  if plot_log:
    r2d = log10(r2d)

  from matplotlib.pyplot import contourf, figure, colorbar
  figure()
  contourf(incE, emitE, r2d, 50, aspect=aspect)
  colorbar()

def plot_rixs(rixs, start=0, end=-1, plot_log=False, aspect=1):
  incE = unique(rixs[:,0])
  emitE = unique(rixs[:,1])
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
    n = sum(s[:,1]) / len(s[:,1])

  if plot_errorbars:
    errorbar(s[:,0], s[:,1]/n, s[:,2]/n, **kwargs)
  else:
    plot(s[:,0], s[:,1]/n, **kwargs)
    
