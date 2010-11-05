import numpy as np

"""
Exposure filters
"""

#########################
#                       #
# Abstract Base Classes #
#                       #
#########################
class Filter(object):
  """
  Abstract filter base class

  Filters take an array of pixels and process them in some fashion
  """
  name = ""
  view_name = "UnimplementedView"
  default_val = None
  default_enabled = False

  def __init__(self):
    self.enabled = True
    self.val = self.default_val

  def filter(self, pixels, energy):
    raise ValueError("Unimplemented Filter: %s" % self.name)

  def set_str(self, valstr):
    self.val = self.str_to_val(valstr)

  def get_str(self):
    return self.val_to_str(self.val)

  def set_val(self, val):
    self.val = val

  def get_val(self):
    return self.val

  @classmethod
  def str_to_val(cls,valstr):
    return None

  @classmethod
  def val_to_str(cls,val):
    return str(val)

class IntFilter(Filter):
  view_name = "IntFilterView"

  @classmethod
  def str_to_val(cls,valstr):
    if valstr == '':
      return 0
    else:
      return int(valstr)

class FloatFilter(Filter):
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
  view_name = "StringFilterView"

  @classmethod
  def val_to_str(cls,val):
    return val

class ChoiceFilter(Filter):
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
  name = "Min Visible"
  view_name = "IntFilterView"
  default_val = 0
  default_enabled = True

  def filter(self, pixels, energy):
    pass

class MaxFilter(IntFilter):
  name = "Max Visible"
  view_name = "IntFilterView"
  default_val = 1000
  default_enabled = False

  def filter(self, pixels, energy):
    pass

class LowFilter(IntFilter):
  name = "Low Cutoff"
  default_val = 5
  default_enabled = True

  def filter(self, pixels, energy):
    if self.val is None:
      return
    pixels[np.where(pixels < self.val)] = 0

class HighFilter(IntFilter):
  name = "High Cutoff"
  default_val = 1000
  default_enabled = False

  def filter(self, pixels, energy):
    if self.val is None:
      return
    pixels[np.where(pixels > self.val)] = 0

class NeighborFilter(IntFilter):
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

"""
class BadPixelFilter(Filter):
  name = "Bad Pixels"

  default_val = []
  default_enabled = False

  MODE_ZERO_OUT = 0
  MODE_INTERP_H = 1
  MODE_INTERP_V = 2

  @classmethod
  def str_to_val(valstr):
    tmp = valstr.split('|')
    if len(tmp) == 2:
      mode = tmp[0]
      pts = tmp[1].split(';')
      bad_pixels = [[c.strip() for c in pt.split(',')] for pt in pts]
      return (mode, bad_pixels)
    else:
      raise Exception("Invalid filter value: %s" % valstr)

  @classmethod
  def val_to_str(val):
    mode, points = val
    points = ';'.join(['%d,%d' % p for p in points])
    return '%d|%s' % (mode, points)

  def filter(self, pixels, energy):
    for x,y in self.bad_pixels:
      if self.mode == MODE_ZERO_OUT:
        pixels[y,x] = 0
      elif self.mode == MODE_INTERP_H:
        pixels[y,x] = (pixels[y,x-1] + pixels[y,x+1])/2.
      elif self.mode == MODE_INTERP_V:
        pixels[y,x] = (pixels[y-1,x] + pixels[y+1,x])/2.
"""

class EmissionFilter(ChoiceFilter):
  name = "Emission Filter"

  TYPE_FE_KBETA = 0
  CHOICES = [
      "Fe Kbeta"
      ]

  default_val = TYPE_FE_KBETA
  default_enabled = False

  def filter(self, pixels, energy):
    if self.val == self.TYPE_FE_KBETA:
      if energy >= 7090:
        z = 1.3214 * energy - 9235.82 - 12
        pixels[0:z,:] = 0
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
  #BadPixelFilter,
  EmissionFilter
  ]
for f in FILTERS:
  register(f)
