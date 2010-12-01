import numpy as np
from scipy.optimize import leastsq

def gauss(x,x0,sigma):
  return np.exp(-(x-x0)**2 / (2*sigma**2))

def gauss_model(params, x):
  A,x0,sigma = params
  return A*gauss(x,x0,sigma)

def gauss_error(params, *args):
  x,y = args
  return gauss_model(params,x) - y

def gauss_leastsq(data, guess):
  """
  Fit a single gaussian to data

  Parameters
  ----------
    data: tuple containing (x,y) data point vectors
    guess: tuple containing starting (amplitude, mean, stddev) values
  """
  return leastsq(gauss_error, guess, data)
