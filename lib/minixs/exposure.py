from PIL import Image
from numpy import *

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

  def apply_filters(self, energy, filters):
    for f in filters:
      f.filter(self.pixels, energy)
  
  def filter_low_high(self, low, high):
    # DEPRECATED
    if low == None: low = self.pixels.min()
    if high == None: high = self.pixels.max()

    mask = logical_and(self.pixels >= low, self.pixels <= high)
    self.pixels *= mask

  def filter_neighbors(self, cutoff):
    # DEPRECATED
    from itertools import product
    nbors = (-1,0,1)
    mask = sum([
      roll(roll(self.pixels>0,i,0),j,1)
      for i,j in product(nbors,nbors)
      if i != 0 or j != 0
      ], 0) >= cutoff
    self.pixels *= mask

  def filter_bad_pixels(self, bad_pixels):
    # DEPRECATED
    for x,y in bad_pixels:
      self.pixels[y,x] = 0


