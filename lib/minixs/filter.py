"""
Exposure filters

A set of filters that act on exposure pixel arrays.

See the `Filter` class documentation for details on how to implement new
filters.
"""

import numpy as np

#########################
#                       #
# Abstract Base Classes #
#                       #
#########################
class Filter(object):
  """
  Abstract filter base class

  Filters take an array of pixels and process them in some fashion

  To implement a new filter type, create a subclass of Filter.

  Set the name, default_val and default_enabled class variables.

  Implement class methods `str_to_val` and `val_to_str` that convert the
  filter's parameters between a string representation (to be saved in an
  output file) and the internal representation (of any type).

  Finally, implement the object method `filter`, which applies this filter to
  an array of pixels (in place).

  To create a filter that has only one parameter of a basic type, subclass
  one of IntFilter, FloatFilter, or StringFilter. These already have
  implementations of `str_to_val` and `val_to_str`.
  """
  name = ""
  default_val = None
  default_enabled = False

  def __init__(self):
    self.enabled = True
    self.val = self.default_val

  def filter(self, pixels, energy):
    """
    Apply this filter to an array of pixels

    This must be overridden by subclasses.

    Parameters
    ----------
      pixels: an array of counts received at each pixel
      energy: the incident beam energy
    """
    raise ValueError("Unimplemented Filter: %s" % self.name)

  def set_str(self, valstr):
    """
    Set filter's value from a string
    """
    self.val = self.str_to_val(valstr)

  def get_str(self):
    """
    Get filter's value as a string
    """
    return self.val_to_str(self.val)

  def set_val(self, val):
    """
    Set filter's value
    """
    self.val = val

  def get_val(self):
    """
    Get filter's value
    """
    return self.val

  @classmethod
  def str_to_val(cls,valstr):
    """
    Convert value from string to whichever representation is used internally

    This is used to load a filter from a file
    """
    return None

  @classmethod
  def val_to_str(cls,val):
    """
    Convert value from internal representation to string

    This is used to save a filter to a file
    """
    return str(val)

class IntFilter(Filter):
  """
  An abstract class for a filter that takes a single integer parameter
  """
  view_name = "IntFilterView"

  @classmethod
  def str_to_val(cls,valstr):
    if valstr == '':
      return 0
    else:
      return int(valstr)

class FloatFilter(Filter):
  """
  An abstract class for a filter that takes a single float parameter
  """
  view_name = "FloatFilterView"

  @classmethod
  def val_to_str(cls,val):
    return "%.2f" % val

  @classmethod
  def str_to_val(cls,valstr):
    if valstr == '':
      return 0
    else:
      return float(valstr)

class StringFilter(Filter):
  """
  An abstract class for a filter that takes a single string parameter
  """
  view_name = "StringFilterView"

  @classmethod
  def val_to_str(cls,val):
    return val

class ChoiceFilter(Filter):
  """
  An abstract class for a filter that has a single parameter chosen from a set

  Subclasses should override the `CHOICES` class variable with a list of
  strings values of possible choices.

  The `val` object variable will be set to the index of the selected choice.
  """
  view_name = "ChoiceFilterView"
  default_value = 0

  CHOICES = [
      ]

  @classmethod
  def val_to_str(cls,val):
    if val == -1:
      return ''

    try:
      return cls.CHOICES[val]
    except IndexError:
      return ''

  @classmethod
  def str_to_val(cls,valstr):
    if valstr == '':
      return -1

    return cls.CHOICES.index(valstr)

##################
#                #
# Actual Filters #
#                #
##################

class MinFilter(IntFilter):
  """
  A dummy filter used by the Calibrator GUI to set the lower contrast level to show
  """
  name = "Min Visible"
  view_name = "IntFilterView"
  default_val = 0
  default_enabled = True

  def filter(self, pixels, energy):
    pass

class MaxFilter(IntFilter):
  """
  A dummy filter used by the Calibrator GUI to set the upper contrast level to show
  """
  name = "Max Visible"
  view_name = "IntFilterView"
  default_val = 1000
  default_enabled = False

  def filter(self, pixels, energy):
    pass

class LowFilter(IntFilter):
  """
  Zero out all pixels below a given threshold
  """
  name = "Low Cutoff"
  default_val = 5
  default_enabled = True

  def filter(self, pixels, energy):
    if self.val is None:
      return
    pixels[np.where(pixels < self.val)] = 0

class HighFilter(IntFilter):
  """
  Zero out all pixels above a given threshold
  """
  name = "High Cutoff"
  default_val = 1000
  default_enabled = False

  def filter(self, pixels, energy):
    if self.val is None:
      return
    pixels[np.where(pixels > self.val)] = 0

class NeighborFilter(IntFilter):
  """
  Zero out all pixels with fewer than the given number of nonzero neighbors

  A neighbor is defined as a pixel whose row and column are within one of the
  pixel under consideration, not including the pixel itself. Each pixel has 8
  neighbors.
  """
  name = "Neighbors"
  default_val = 2
  default_enabled = True

  def filter(self, pixels, energy):
    from itertools import product
    nbors = (-1,0,1)
    mask = np.sum([
      np.roll(np.roll(pixels > 0,i,0),j,1)
      for i,j in product(nbors,nbors)
      if i != 0 or j != 0
      ], 0) >= self.val 
    pixels *= mask

class BadPixelFilter(Filter):
  """
  Filter out a set of specified pixels

  Each pixel in the provided list is processed in manner which depends on the
  mode:

    0: Zero out pixels
    1: Linearly interpolate value from pixels to left and right
    2: Linearly interpolate value from pixels above and below
  """

  name = "Bad Pixels"

  default_val = (0,[])
  default_enabled = False

  MODE_ZERO_OUT = 0
  MODE_INTERP_H = 1
  MODE_INTERP_V = 2

  @classmethod
  def str_to_val(cls, valstr):
    tmp = valstr.split('|')
    if len(tmp) == 2:
      mode = int(tmp[0])
      pts = tmp[1].split(';')
      bad_pixels = [[int(c.strip()) for c in pt.split(',')] for pt in pts]
      return (mode, bad_pixels)
    else:
      raise Exception("Invalid filter value: %s" % valstr)

  @classmethod
  def val_to_str(cls, val):
    mode, points = val
    points = ';'.join(['%d,%d' % tuple(p) for p in points])
    return '%d|%s' % (mode, points)

  def filter(self, pixels, energy):
    mode, bad_pixels = self.val
    for x,y in bad_pixels:
      if mode == self.MODE_ZERO_OUT:
        pixels[y,x] = 0
      elif mode == self.MODE_INTERP_H:
        pixels[y,x] = (pixels[y,x-1] + pixels[y,x+1])/2.
      elif mode == self.MODE_INTERP_V:
        pixels[y,x] = (pixels[y-1,x] + pixels[y+1,x])/2.

class EmissionFilter(ChoiceFilter):
  """
  A filter to remove fluorescence from elastic exposures

  This is hard coded to only handle the Fe Kbeta von Hamos
  spectrometer. At some point, this should be replaced
  by something more flexible.
  """
  name = "Emission Filter"

  TYPE_FE_KBETA = 0
  TYPE_FE_KBETA_TIGHT = 1
  CHOICES = [
      "Fe Kbeta",
      "Fe Kbeta v2"
      ]

  default_val = TYPE_FE_KBETA
  default_enabled = False

  def filter(self, pixels, energy):
    if self.val == self.TYPE_FE_KBETA:
      if energy >= 7090:
        z = 1.3214 * energy - 9235.82 - 12
        pixels[0:z,:] = 0
    elif self.val == self.TYPE_FE_KBETA_TIGHT:
      m = [ 1.267343, 1.265995, 1.267343, 1.275763, 1.258217, 1.254672, 1.254672, 1.267664, 1.304953, 1.289443 ]
      b = [ -8847.35, -8846.56, -8849.35, -8913.20, -8790.86, -8762.06, -8761.06, -8847.43, -9109.12, -9006.66 ]
      w = pixels.shape[1]

      if energy >= 7090:
        for i in range(10):
          x1 = np.floor(w / 10.0 * i)
          x2 = np.ceil(w / 10.0 * (i+1))
          z = m[i] * energy + b[i] - 1
          pixels[0:z,x1:x2] = 0
    else:
      raise ValueError("Unimplemented Emission Filter")


###################
#                 #
# Filter Registry #
#                 #
###################

REGISTRY = []
FILTER_MAP = {}


def get_filter_by_name(name):
  """
  Lookup filter by name

  Parameters
  ----------
    name: the name of the filter

  Returns
  -------
    an instantiated filter object of the given type or None if name is unknown
  """

  global FILTER_MAP
  fltr = FILTER_MAP.get(name, None)
  if fltr is None:
    return None
  else:
    return fltr()

def register(f):
  """
  Register a filter

  Parameters
  ----------
    f: a class derived from Filter
  """
  FILTER_MAP[f.name] = f
  REGISTRY.append(f)
  

# register standard filters
FILTERS = [
  MinFilter,
  MaxFilter,
  LowFilter,
  HighFilter,
  NeighborFilter,
  BadPixelFilter,
  EmissionFilter
  ]
for f in FILTERS:
  register(f)
