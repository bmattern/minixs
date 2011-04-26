"""
Raw detector exposures
"""
from PIL import Image
import numpy as np
from itertools import izip
import os

class Exposure:
  """
  Raw detector exposures

  This handles loading and saving exposure files, which are currently assumed
  to be tif files from a Dectris Pilatus detector. Any image file that
  is supported by the Python Imaging Library should load correctly, however,
  unless the image has a single channel, it will most likely not work with
  any of the rest of the minixs code.
  """
  def __init__(self, filename = None):
    self.loaded = False
    if filename is not None:
      self.load(filename)

  def load(self, filename):
    """
    Load a single image file
    """
    self.filename = filename

    ext = filename.split(os.path.extsep)[-1]
    if ext == 'raw':
      with open(filename) as f:
        d = f.read()

      # XXX this assumes pilatus 100K...
      self.image = None
      self.raw = np.fromstring(d, '>f').astype('int32').reshape((195,-1))
      pass

    else:
      self.image = Image.open(filename)
      self.raw = np.asarray(self.image)

    self.pixels = self.raw.copy()
    try:
      self.info = self.parse_description(self.image.tag.get(270))
    except:
      pass
    self.loaded = True

  def load_multi(self, filenames):
    """
    Load several image files summing together their pixel values
    """
    self.filenames = filenames
    self.pixels = None
    if filenames:
      self.loaded = True

    for f in filenames:
      ext = f.split(os.path.extsep)[-1]
      if ext == 'raw':
        with open(f) as fh:
          d = fh.read()

        # XXX this assumes pilatus 100K...
        p = np.fromstring(d, '>f').astype('int32').reshape((195,-1))
      else:
        im = Image.open(f)
        p = np.asarray(im)

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
    """
    Apply a set of filters to an exposure

    Each filter in the list `filters` has its `filter` method called
    on this exposure's pixel array.
    """
    for f in filters:
      f.filter(self.pixels, energy)
  
  def filter_low_high(self, low, high):
    """
    DEPRECATED
    """
    if low == None: low = self.pixels.min()
    if high == None: high = self.pixels.max()

    mask = logical_and(self.pixels >= low, self.pixels <= high)
    self.pixels *= mask

  def filter_neighbors(self, cutoff):
    """
    DEPRECATED
    """
    from itertools import product
    nbors = (-1,0,1)
    mask = sum([
      roll(roll(self.pixels>0,i,0),j,1)
      for i,j in product(nbors,nbors)
      if i != 0 or j != 0
      ], 0) >= cutoff
    self.pixels *= mask

  def filter_bad_pixels(self, bad_pixels):
    """
    DEPRECATED
    """
    for x,y in bad_pixels:
      self.pixels[y,x] = 0


  def detect_bad_pixels(self, num_bins=20, bin_sep=3):
    raise Exception("Not yet implemented")
    # if we find bins separated from the rest by more than bin_sep zero bins, assume they contain bad pixels

    h = np.histogram(self.pixels.flat, num_bins)
    counts = h[0]
    bounds = h[1]

    print counts
    # start at high count end of histogram.
    high_start = -1
    zero_start = -1
    for i in range(len(counts))[::-1]:
      if counts[i] == 0 and high_start == -1:
        high_start = i+1
      elif counts[i] != 0 and high_start != -1:
        zero_start = i+1
        break

    num_zeros = high_start - zero_start
    print high_start, zero_start, num_zeros
    if num_zeros > bin_sep:
      max_good_counts = bounds[high_start]
      y,x = np.where(self.pixels > max_good_counts)
      bad_pixels = [(xi,yi) for xi,yi in zip(x,y)]
    else:
      bad_pixels = []

    return bad_pixels

  def detect_bad_pixels2(self):
    p = self.pixels.copy()
    n = np.product(p.shape)
    bad_pixels = []
    while True:
      a,b = np.histogram(p.flat)

      if sum(a==0) < 2:
        break

      i = np.where(p > b[-2])
      bad_pixels += [(x,y) for y,x in izip(*i)]
      p[i] = 0

    print a
    print b
    return bad_pixels, p

