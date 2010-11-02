from info import CalibrationInfo
from exposure import Exposure
from itertools import izip
from constants import *

import numpy as np


def find_maxima(pixels, direction, energy, window_size = 3):
  """
  Find locations of local maxima of `pixels` array in `direction`.

  The location is calculated as the first moment in a window of half width
  `window_size` centered at a local maximum.

  Parameters
  ----------
  p : pixel array from an elastic exposure
  direction: minixs.DIRECTION_* indicating dispersive direction
  window_size : size in pixels around max for windowed average

  Returns
  -------
  xy : array of x, y and energy coordinates
  """

  # convert direction to axis (XXX make this a function call somewhere)
  rolldir = direction % 2

  # shorten expressions below by aliasing pixels array
  p = pixels

  # build mask of local maxima locations
  local_max = np.logical_and(p >= np.roll(p,-1,rolldir), p > np.roll(p, 1, rolldir))

  # perform windowed averaging to find average col value in local peak
  colMoment = np.zeros(p.shape)
  norm = np.zeros(p.shape)

  # build vector of indices along column (row) 
  cols = np.arange(0,p.shape[rolldir])
  if direction == VERTICAL:
    cols.shape = (len(cols),1)

  # find first moments about local maxima
  for i in range(-window_size,window_size+1):
    colMoment += local_max * np.roll(cols * p, i, rolldir)
    norm += local_max * np.roll(p, i, rolldir)

  # calculate average
  windowedAvg = colMoment / norm
  windowedAvg[np.isnan(windowedAvg)] = 0

  # we only want the locations of actual maxima
  index = np.where(windowedAvg > 0)
 
  # pull out the pixel locations of the peak centers
  if direction == VERTICAL:
    y = windowedAvg[index]
    x = index[1]
  else:
    x = windowedAvg[index]
    y = index[0]

  z = energy * np.ones(x.shape)

  # return N x 2 array of peak locations
  return np.vstack([x,y,z]).T

FIT_QUADRATIC = 1
FIT_CUBIC   = 2
FIT_ELLIPSOID = 3

def fit_xtal(xtal, points, dest, fit_type = FIT_CUBIC):
  # boundary coordinates
  (x1,y1),(x2,y2) = xtal

  # extract points inside this xtal region
  index = np.where(np.logical_and(
      np.logical_and(
        points[:,0] >= x1,
        points[:,0] < x2),
      np.logical_and(
        points[:,1] >= y1,
        points[:,1] < y2
        )
      ))
  x,y,z = points[index].T

  # if we have no points in this region, we can't fit anything
  # XXX this should pass the warning up to higher level code instead
  #     of printing it out to stdout
  if len(x) == 0:
    print "Warning: No points in xtal ", xtal
    return

  # build points to evaluate fit at
  xx, yy = np.meshgrid(np.arange(x1,x2), np.arange(y1,y2))
  xx = np.ravel(xx)
  yy = np.ravel(yy)

  if fit_type == FIT_QUADRATIC:
    # fit to quadratic: z = Ax^2 + By^2 + Cxy + Dx + Ey + F
    A = np.vstack([x**2, y**2, x*y, x, y, np.ones(x.shape)]).T
    fit, r = np.linalg.lstsq(A,z)[0:2]

    # calculate residues
    rms_res = np.sqrt(r / len(z))[0]
    lin_res = sum(z - np.dot(A, fit)) / len(z)

    # evaluate at all points
    zz = np.dot(
           np.vstack([xx**2,yy**2,xx*yy,xx,yy,np.ones(xx.shape)]).T,
           fit
         ).T

  elif fit_type == FIT_CUBIC:
    # fit to quartic:
    #   Ax^3 + By^3 + Cx^2y + Dxy^2 + Ex^2 + Fy^2 + Gxy + Hx + Iy + J = z
    A = np.vstack([x**3,y**3,x**2*y,x*y**2,x**2, y**2, x*y, x, y, np.ones(x.shape)]).T
    fit, r = np.linalg.lstsq(A,z)[0:2]

    # calculate residues
    rms_res = np.sqrt(r / len(z))[0]
    lin_res = sum(z - np.dot(A, fit)) / len(z)

    # evaluate at all points
    zz = np.dot(
           np.vstack([
             xx**3, yy**3, xx**2*yy, xx*yy**2,
             xx**2, yy**2, xx*yy,
             xx, yy,
             np.ones(xx.shape)
           ]).T,
           fit
         ).T

  elif fit_type == FIT_ELLIPSOID:
    raise Exception("Fit method not yet implemented.")
    # XXX this doesn't seem to work...
    # Fit to ellipsoid:
    # Ax^2 + By^2 + Cz^2 + Dxy + Eyz + Fzx + Gx + Hy + Iz = 1
    data = np.vstack([
      x*x,
      y*y,
      z*z,
      x*y,
      y*z,
      z*x,
      x,
      y,
      z
      ]).T

    w = np.ones(x.shape)
    fit, r = np.linalg.lstsq(data,w)[0:2]

    #rms_res = np.sqrt(r / len(w))[0]
    lin_res = (w - np.dot(data, fit)).sum() / len(w)
    rms_res = np.sqrt(((w - np.dot(data, fit))**2).sum() / len(w))

    # now solve for z in terms of x and y to evaluate
    A,B,C,D,E,F,G,H,I = fit
    a = C
    b = E*yy + F*xx + I
    c = A*xx**2 + B*yy**2 + D*xx*yy + G*xx + H*yy - 1
    zz = (-b + np.sqrt(b**2 - 4*a*c)) / (2*a)

  # fill the calibration matrix with values from fit
  dest[yy,xx] = zz

  return lin_res, rms_res

def calibrate(info, fit_type=FIT_CUBIC):
  # load exposure files
  exposures = [Exposure(f) for f in info.exposure_files]

  points = []
  lin_res = []
  rms_res = []

  for exposure, energy in izip(exposures, info.energies):
    # apply filters
    for f in info.filters:
      f.filter(exposure.pixels, energy)

    # extract locations of peaks
    points.append(find_maxima(exposure.pixels,
                              info.dispersive_direction,
                              energy))

  points = np.vstack(points)

  # create empty calibration matrix
  calib = np.zeros(exposures[0].pixels.shape)

  # fit smooth shape for each crystal and fill in calib with fit
  for xtal in info.xtals:
    lr, rr = fit_xtal(xtal, points, calib, fit_type)
    lin_res.append(lr)
    rms_res.append(rr)

  info.calibration_matrix = calib
  # return list of points used for fit and residues for diagnostics
  return points, lin_res, rms_res
