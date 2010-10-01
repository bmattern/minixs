from PIL import Image
import numpy as np
from numpy import *

FILTERS = [ MinFilter, MaxFilter, LowFilter, HighFilter, NeighborFilter, BadPixelFilter, EmissionFilter ]

filter_map = {}
for f in FILTERS:
  filter_map[f.name] = f

def get_filter_by_name(name):
  return filter_map.get(name, None)

class Filter(object):
  name = ""
  def filter(pixels, energy):
    pass

  def set_str(self, valstr):
    return None

  def get_str(self, val):
    return None


class DummyFilter(Filter):
  pass

class IntFilter(Filter):
  def set_str(self, valstr):
    if valstr == "None":
      self.val = None
    else:
      self.val = int(valstr)

  def get_str(self, val):
    if self.val is None:
      return "None"
    else:
      return str(self.val)

class FloatFilter(Filter):
  def set_str(self, valstr):
    if self.val is None:
      return "None"
    else:
      self.val = float(valstr)

  def get_str(self):
    return "%.2f" % self.val

class MinFilter(DummyFilter):
  name = "Min Visible"

class MaxFilter(DummyFilter):
  name = "Max Visible"

class LowFilter(IntFilter):
  name = "Low Cutoff"
  def filter(pixels, energy):
    if self.val is None:
      return
    pixels[np.where(pixels < self.val)] = 0

class HighFilter(IntFilter):
  name = "High Cutoff"
  def filter(pixels, energy):
    if self.val is None:
      return
    pixels[np.where(pixels > self.val)] = 0

class NeighborFilter(IntFilter):
  name = "Neighbors"
  def filter(pixels, energy):
    from itertools import product
    nbors = (-1,0,1)
    mask = np.sum([
      np.roll(np.roll(self.pixels>0,i,0),j,1)
      for i,j in product(nbors,nbors)
      if i != 0 or j != 0
      ], 0) >= cutoff
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

  def get_str(self, val):
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

class EmissionFilter(Filter):
  TYPE_FE_KBETA = 0
  TYPE_NAMES = [
      "Fe Kbeta"
      ]
  def filter(self, pixels, energy):
    if self.type == self.TYPE_FE_KBETA:
      #XXX encode these values in file valstr?
      if energy >= 7090:
        z = 1.3214 * energy - 9235.82 - 12
        pixels[0:z,:] = 0
    else:
      raise ValueError("Unimplemented Emission Filter")

  def set_str(self, valstr):
    try:
      self.type = self.TYPE_NAMES.index(valstr)
    except ValueError:
      raise ValueError("Unknown Emission Filter Type: %s" % valstr)

  def get_str(self):
    return self.TYPE_NAMES[self.type]

class Exposure:
  def __init__(self, filename = None):
    self.loaded = False
    if filename is not None:
      self.load(filename)

  def load(self, filename):
    self.filename = filename

    self.image = Image.open(filename)
    self.raw = asarray(self.image)
    self.pixels = self.raw.copy()
    self.info = self.parse_description(self.image.tag.get(270))
    self.loaded = True

  def load_multi(self, filenames):
    self.filenames = filenames
    self.pixels = None
    for f in filenames:
      im = Image.open(f)
      p = asarray(im)
      if self.pixels is None:
        self.pixels = p.copy()
      else:
        self.pixels += p

  def parse_description(self, desc):
    try:
      # split into lines and strip off '#'
      info = [line[2:] for line in desc.split('\r\n')][:-1]
    except:
      info = []
    return info

  def filter_low_high(self, low, high):
    if low == None: low = self.pixels.min()
    if high == None: high = self.pixels.max()

    mask = logical_and(self.pixels >= low, self.pixels <= high)
    self.pixels *= mask

  def filter_neighbors(self, cutoff):
    from itertools import product
    nbors = (-1,0,1)
    mask = sum([
      roll(roll(self.pixels>0,i,0),j,1)
      for i,j in product(nbors,nbors)
      if i != 0 or j != 0
      ], 0) >= cutoff
    self.pixels *= mask

  def filter_bad_pixels(self, bad_pixels):
    for x,y in bad_pixels:
      self.pixels[y,x] = 0
