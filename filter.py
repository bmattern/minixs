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
  def __init__(self):
    self.enabled = True

  def filter(self, pixels, energy):
    raise ValueError("Unimplemented Filter: %s" % self.name)

  def set_str(self, valstr):
    return None

  def get_str(self):
    return None

  def set_val(self, val):
    self.val = val

  def get_val(self):
    return self.val

class IntFilter(Filter):
  view_name = "IntFilterView"

  def set_str(self, valstr):
    if valstr == "None":
      self.val = None
    else:
      self.val = int(valstr)

  def get_str(self):
    if self.val is None:
      return "None"
    else:
      return str(self.val)

class FloatFilter(Filter):
  view_name = "FloatFilterView"

  def set_str(self, valstr):
    if self.val is None:
      return "None"
    else:
      self.val = float(valstr)

  def get_str(self):
    return "%.2f" % self.val

class ChoiceFilter(Filter):
  view_name = "ChoiceFilterView"

  CHOICES = [
      ]

  def set_str(self, valstr):
    try:
      self.val = self.CHOICES.index(valstr)
    except ValueError:
      raise ValueError("Unknown %s Type: %s" % (self.name, valstr))

  def get_str(self):
    return self.CHOICES[self.val]

##################
#                #
# Actual Filters #
#                #
##################

class MinFilter(IntFilter):
  name = "Min Visible"
  view_name = "IntFilterView"

  def filter(self, pixels, energy):
    pass

class MaxFilter(IntFilter):
  name = "Max Visible"
  view_name = "IntFilterView"

  def filter(self, pixels, energy):
    pass

class LowFilter(IntFilter):
  name = "Low Cutoff"
  def filter(self, pixels, energy):
    if self.val is None:
      return
    pixels[np.where(pixels < self.val)] = 0

class HighFilter(IntFilter):
  name = "High Cutoff"
  def filter(self, pixels, energy):
    if self.val is None:
      return
    pixels[np.where(pixels > self.val)] = 0

class NeighborFilter(IntFilter):
  name = "Neighbors"
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
  name = "Bad Pixels"

  MODE_ZERO_OUT = 0
  MODE_INTERP_H = 1
  MODE_INTERP_V = 2

  def set_str(self, valstr):
    tmp = valstr.split('|')
    if len(tmp) == 2:
      self.mode = tmp[0]
      pts = tmp[1].split(';')
      self.bad_pixels = [[c.strip() for c in pt.split(',')] for pt in pts]
    else:
      raise Exception("Invalid filter value: %s" % valstr)

  def get_str(self):
    pts = ';'.join(['%d,%d' % p for p in self.points])
    return '%d|%s' % (self.mode, pts)

  def filter(self, pixels, energy):
    for x,y in self.bad_pixels:
      if self.mode == MODE_ZERO_OUT:
        pixels[y,x] = 0
      elif self.mode == MODE_INTERP_H:
        pixels[y,x] = (pixels[y,x-1] + pixels[y,x+1])/2.
      elif self.mode == MODE_INTERP_V:
        pixels[y,x] = (pixels[y-1,x] + pixels[y+1,x])/2.

class EmissionFilter(ChoiceFilter):
  name = "Emission Filter"

  TYPE_FE_KBETA = 0
  CHOICES = [
      "Fe Kbeta"
      ]
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
