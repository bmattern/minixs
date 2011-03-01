import os
from glob import glob
from parser import Parser, STRING, INT, FLOAT, LIST
import numpy as np
from numpy.linalg import norm
import geom
from itertools import izip

HBARC = 1973.2696 # eV * angstroms
HC    = 2 * np.pi * HBARC 

DIR= os.path.join(os.path.dirname(__file__), 'data', 'spectrometers')

lattice_constants = {
    'Ge':  5.65735,
    'Si':  5.4309,
    'GaP': 5.4512,
    }

def clamp(v, min, max):
  if v < min:
    return min
  if v > max:
    return max
  else:
    return v

def tag_to_path(tag):
  return os.path.join(DIR, tag)

def list_spectrometers():
  files = glob(name_to_path('*'))
  files.sort()
  return [ os.path.basename(f) for f in files]

class Spectrometer(object):
  def __init__(self, tag=None):
    if tag:
      self.load_by_tag(tag)

    self.camera_shape = (195, 487)

  def load_by_tag(self, tag):
    self.load(tag_to_path(tag))

  def load(self, filename):
    self.load_errors = []

    with open(filename) as f:
      point_list = (LIST, (FLOAT, FLOAT, FLOAT))
      p = Parser({
        'Name': STRING,
        'Element': STRING,
        'Line': STRING,
        'Xtal': (STRING, INT, INT, INT),
        'Energy Range': (FLOAT, FLOAT),
        'Exit Aperture': point_list,
        'Entrance Aperture': point_list,
        'Xtals': point_list,
        'Sample': point_list,
        'Camera': point_list,
        'Beam': point_list
        })
      
      info = p.parse(f.readlines())
      self.load_errors += p.errors
      
      self.name = info.get('Name')
      self.element = info.get('Element')
      self.energy_range = info.get('Energy Range')

      xtal = info.get('Xtal')
      if xtal:
        self.xtal_type = info.get('Xtal')[0]
        self.xtal_cut = info.get('Xtal')[1:4]
      else:
        self.load_errors.append('Missing crystal type information ("Xtal" line).')

      exit_aperture = info.get('Exit Aperture')
      if exit_aperture:
        if len(exit_aperture) == 4:
          self.exit_aperture = [geom.Point(*p) for p in exit_aperture]
        else:
          self.load_errors.append('Aperture contains %d points instead of 4.' % len(self.exit_aperture))
      else:
        self.load_errors.append("Missing Exit Aperture")

      entrance_aperture = info.get('Entrance Aperture')
      if entrance_aperture:
        if len(entrance_aperture) % 4 == 0:
          self.entrance_aperture = [
              [geom.Point(*p) for p in entrance_aperture[4*i:4*(i+1)]]
              for i in range(len(entrance_aperture)/4)
              ]
        else:
          self.load_errors.append('Aperture contains %d points instead of 4.' % len(self.entrance_aperture))
      else:
        self.load_errors.append('Missing Entrance Apertures')

      xtals = info.get('Xtals')
      if len(xtals) % 4 == 0:
        self.xtals = [[geom.Point(*p) for p in xtals[4*i:4*(i+1)]] for i in range(len(xtals)/4)]
        self.xtal_planes = [geom.Plane.FromPoints(*x[0:3]) for x in self.xtals]
      else:
        self.load_errors.append('Xtal list contains %d points, which is not a multiple of 4.' % len(xtals))

      sample = info.get('Sample')
      if len(sample) == 1:
        self.sample = geom.Point(*sample[0])
      else:
        self.load_errors.append('One sample point must be specified, not %d.' % len(sample))

      camera = info.get('Camera')
      if len(camera) == 4:
        self.camera = [geom.Point(*p) for p in camera]
        self.camera_plane = geom.Plane.FromPoints(*self.camera[0:3])
      else:
        self.load_errors.append('Camera contains %d points instead of 4.' % len(self.camera))

      beam = info.get('Beam')
      if len(beam) == 1:
        self.beam = geom.Point(*beam[0])
      else:
        self.load_errors.append('One beam direction must be specified, not %d.' % len(beam))

  def camera_pixel_to_point(self, pixel):
    # returns the coordinates of the top left corner of the request pixel
    px,py = pixel
    h,w = self.camera_shape

    cam_x = self.camera[1] - self.camera[0]
    cam_y = self.camera[3] - self.camera[0]

    return self.camera[0] + px / float(w) * cam_x + py / float(h) * cam_y

  def point_to_camera_pixel(self, point, tolerance=.001):

    d = point - self.camera_plane.p0

    # check that point is within tolerance of plane
    if abs(np.dot(d,self.camera_plane.n)) > tolerance:
      return None # not in plane

    cx = self.camera[1] - self.camera[0]
    cy = self.camera[3] - self.camera[0]

    lx = norm(cx)
    cx /= lx

    ly = norm(cy)
    cy /= ly

    px = np.dot(d, cx) / lx * self.camera_shape[1]
    py = np.dot(d, cy) / ly * self.camera_shape[0]

    return (px,py)

  def camera_pixel_locations(self):
    h,w = self.camera_shape
    coords = np.zeros((w*h,2))
    index = np.arange(w*h)
    coords[:,0] = index % w
    coords[:,1] = index / w

    points = self.camera[0] + \
             (np.outer(coords[:,0]/float(w), self.camera[1] - self.camera[0]) +
              np.outer(coords[:,1]/float(h), self.camera[3] - self.camera[0]))
    return points.reshape((h,w,3))

  def image_points(self):
    images = []
    for xtal_plane in self.xtal_planes:
      image = geom.reflect_through_plane(self.sample, xtal_plane)
      images.append(image)

    return images

  def calculate_active_regions(self):
    if len(self.entrance_aperture) != len(self.xtals):
      raise Exception("Number of entrance apertures and crystals must be same")

    # run through apertures and crystals
    for aperture, xtal_plane in izip(self.entrance_aperture, self.xtal_planes):
      for corner in aperture:
        l = geom.Line.FromPoints(self.sample, corner)
        p = geom.intersect_line_with_plane(l, xtal_plane)

  def project_point_through_rect_onto_camera(self, point, rect):
    h, w = self.camera_shape
    x1 = w
    x2 = 0
    y1 = h
    y2 = 0

    for corner in rect:
      l = geom.Line.FromPoints(point, corner)
      p = geom.intersect_line_with_plane(l, self.camera_plane)

      x,y = self.point_to_camera_pixel(p)
      x = clamp(int(x+1e-5),0,w-1)
      y = clamp(int(y+1e-5),0,h-1)

      if x < x1:
        x1 = x
      if y < y1:
        y1 = y

      if x > x2:
        x2 = x
      if y > y2:
        y2 = y

    return [x1, y1, x2, y2]

  def mockup_calibration_matrix(self):
    h,w = self.camera_shape
    calib = np.zeros((h,w))

    d0 = lattice_constants[self.xtal_type]
    # XXX this assumes the crystal is cubic (all that we currently use are)
    #     it would be good to generalize this though
    d = d0 / norm(self.xtal_cut)

    images = self.image_points()
    bounds = []

    pixels = self.camera_pixel_locations()

    # find image points and xtal projection boundaries
    for xtal_plane, image, entrance_aperture in izip(self.xtal_planes, images, self.entrance_aperture):
      exit_projection = self.project_point_through_rect_onto_camera(image, self.exit_aperture)

      active_region = [
          geom.intersect_line_with_plane(
            geom.Line.FromPoints(self.sample, corner),
            xtal_plane
            )
          for corner in entrance_aperture
          ]

      active_projection = self.project_point_through_rect_onto_camera(image, active_region)

      x1 = max(exit_projection[0], active_projection[0])
      y1 = max(exit_projection[1], active_projection[1])
      x2 = min(exit_projection[2], active_projection[2])
      y2 = min(exit_projection[3], active_projection[3])
        
      bounds.append([x1,y1,x2,y2])
      rw = x2-x1
      rh = y2-y1

      dn = pixels[y1:y2, x1:x2].reshape((rw*rh,3)) - image
      length = np.sqrt((dn**2).sum(1))
      cos_theta = np.abs((dn*xtal_plane.n).sum(1)) / length
      energy = HC / (2 * d) / cos_theta
      energy = energy.reshape((rh,rw))

      calib[y1:y2,x1:x2] = energy

    self.images = images
    self.projection_bounds = bounds
    return calib

  def solid_angle_map(self, bounds):
    """
    Calculate the solid angle subtended by each pixel in sr

    Parameters:
      bounds - list of (x1,y1,x2,y2) bounding rectangles

    Each rectangle in the list of bounds should correspond to the
    projection from a single analyzer crystal through the exit aperture.

    The center of the bounds rect is used to determine which xtal it
    corresponds to. So, this could be incorrect if a small sliver at the
    edge of a crystal projection is provided.
    """
    h,w = self.camera_shape
    domega = np.zeros((h,w))

    # calculate pixel size
    pw = norm(self.camera[1] - self.camera[0]) / w
    ph = norm(self.camera[1] - self.camera[0]) / h

    images = self.image_points()

    pixels = self.camera_pixel_locations()
    num_xtals = len(self.xtal_planes)

    for x1,y1,x2,y2 in bounds:
      xc = (x1+x2)/2.0
      yc = (y1+y2)/2.0

      # determine which crystal this corresponds to
      i = int(xc) * num_xtals / w

      print xc,yc, i, self.xtals[i][0]
      # projection shape size
      sh = y2 - y1
      sw = x2 - x1

      dn = pixels[y1:y2,x1:x2].reshape((sw*sh,3)) - images[i]
      length = np.sqrt((dn**2).sum(1))
      cos_theta = np.abs((dn*self.camera_plane.n).sum(1)) / length
      domega[y1:y2,x1:x2] = (pw*ph*cos_theta / length**2).reshape((sh,sw))

    return domega
