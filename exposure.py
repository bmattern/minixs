from PIL import Image
from numpy import asarray, logical_and, roll
import itertools

class Exposure:
  def __init__(self, filename):
    self.load(filename)

  def load(self, filename):
    self.filename = filename

    self.image = Image.open(filename)
    self.pixels = asarray(self.image).copy()
    self.info = self.parse_description(self.image.tag.get(270))

  def parse_description(self, desc):
    try:
      # split into lines and strip off '#'
      info = [line[2:] for line in desc.split('\r\n')][:-1]
    except:
      info = []
    return info

  def filter_low_high(self, low, high):
    mask = logical_and(self.pixels >= low, self.pixels <= high)
    self.pixels *= mask

  def filter_neighbors(self, cutoff):
    nbors = (-1,0,1)
    mask = sum([
      roll(roll(self.pixels>0,i,0),j,1)
      for i,j in itertools.product(nbors,nbors)
      if i != 0 or j != 0
      ], 0) >= cutoff
    self.pixels *= mask

