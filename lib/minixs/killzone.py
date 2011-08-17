import os
import numpy as np

class KillzoneList(object):
  def __init__(self):
    # ordered list of filenames
    self.exposure_files = []

    # map of killzones
    #    filename => { rects: [], circles: [] }
    self.killzones = {}

  def validate(self):
    self.validation_errors = []
    if len(self.exposure_files) < 1:
      self.validation_errors.append("No exposure files have been selected.")
    if not self.calibration_file:
      self.validation_errors.append("No calibration matrix has been specified.")

    return len(self.validation_errors) == 0

  def save(self, filename):
    f = open(filename, "w")

    for ef in self.exposure_files:
      rects = '|'.join("%d,%d,%d,%d" % (x1,y1,x2,y2) for (x1,y1),(x2,y2) in self.killzones[ef]['rects'])
      print self.killzones[ef]['circles']
      circles = '|'.join("%d,%d,%d" % (xc,yc,r) for xc,yc,r in self.killzones[ef]['circles'])

      f.write("%s:%s:%s\n" % (ef, rects, circles))

    f.close()

  def load(self, filename):
    f = open(filename)

    exposure_files = []
    killzones = {}
    for line in f:
      ef, rects, circles = line.strip().split(':')
      if rects:
        rects = [[int(s) for s in rect.split(',')] for rect in rects.split('|')]
        rects = [[[x1,y1], [x2,y2]] for x1,y1,x2,y2 in rects]
      else:
        rects = []

      if circles:
        circles = [[int(s) for s in c.split(',')] for c in circles.split('|')]
      else:
        circles = []
      exposure_files.append(ef)
      killzones[ef] = {'rects': rects, 'circles': circles}
    f.close()

    self.exposure_files = exposure_files
    self.killzones = killzones

  def mask(self, filename, shape=(197,485)):
    kz = self.killzones.get(os.path.abspath(filename))
    if not kz:
      return None

    m = np.zeros(shape)
    rows,cols = shape
    y,x = mgrid[:rows, :cols]

    for x0,y0,r0 in kz['circles']:
      dr = np.hypot(x-x0, y-y0)
      m[dr <= r0] = 1

    for x1,y1,x2,y2 in kz['rects']:
      m[y1:y2,x1:x2] = 1

    return m
