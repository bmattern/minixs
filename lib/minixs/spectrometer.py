import os
from glob import glob
from parser import Parser, STRING, INT, FLOAT, LIST
import numpy as np
from numpy.linalg import norm
import geom
from itertools import izip
from constants import *

HBARC = 1973.2696 # eV * angstroms
HC    = 2 * np.pi * HBARC

SPECTROMETER_DATADIR = os.path.join(os.path.dirname(__file__), 'data', 'spectrometers')

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
  return os.path.join(SPECTROMETER_DATADIR, tag)

def list_spectrometers(include_names=False):
  files = glob(tag_to_path('*'))
  files.sort()
  if include_names:
    s = Spectrometer()
    tags = []
    names = []
    for f in files:
      try:
        s.load(f)
      except:
        print ("Invalid spectrometer file: %s" % f)
        continue
      tags.append(os.path.basename(f))

      name = s.name
      if not s.name:
        name = '%s %s' % (s.element, s.line)
      names.append(name)

    return tags, names

  else:
    return [ os.path.basename(f) for f in files]

class Spectrometer(object):
  """
  Properties of a spectrometer.

  This contains geometric properties (camera, xtals, apertures, etc), and
  the xtal material and orientation.

  Additionally, includes methods to perform raytracing and generate
  mockup calibration.
  """
  def __init__(self, tag=None):
    self.tag = None
    self.filename = None

    self.camera_shape = (195, 487)
    if tag:
      if os.path.exists(tag):
        self.load(tag)
      else:
        self.load_by_tag(tag)

  def load_by_tag(self, tag):
    path = tag_to_path(tag)
    if os.path.exists(path):
      self.tag = tag
      self.load(path)
    else:
      raise Exception("Unknown Spectrometer tag: %s" % tag)

  def load(self, filename):
    self.load_errors = []

    with open(filename) as f:
      point_list = (LIST, (FLOAT, FLOAT, FLOAT))
      p = Parser({
        'Name': STRING,
        'Element': STRING,
        'Line': STRING,
        'Xtal': (STRING, INT, INT, INT),
        'Num Xtals': INT,
        'Dispersive Direction': STRING,
        'Energy Range': (FLOAT, FLOAT),
        'Exit Aperture': point_list,
        'Entrance Aperture': point_list,
        'Xtals': point_list,
        'Sample': point_list,
        'Camera': point_list,
        'Beam': point_list
        })

      self.filename = filename

      info = p.parse(f.readlines())
      self.load_errors += p.errors

      self.name = info.get('Name')
      self.element = info.get('Element')
      self.line = info.get('Line')
      self.energy_range = info.get('Energy Range')

      xtal = info.get('Xtal')
      if xtal:
        self.xtal_type = info.get('Xtal')[0]
        self.xtal_cut = info.get('Xtal')[1:4]

        if self.xtal_type in lattice_constants:
          d0 = lattice_constants[self.xtal_type]
          self.E0 = HC * norm(self.xtal_cut) / (2 * d0)
        else:
          self.E0 = None

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


      self.num_xtals = 0
      xtals = info.get('Xtals')
      if xtals:
        if len(xtals) % 4 == 0:
          self.xtals = [[geom.Point(*p) for p in xtals[4*i:4*(i+1)]] for i in range(len(xtals)/4)]
          self.xtal_rects = [geom.Rectangle(x[0], x[1], x[3]) for x in self.xtals]
          self.num_xtals = len(self.xtals)
        else:
          self.load_errors.append('Xtal list contains %d points, which is not a multiple of 4.' % len(xtals))
      else:
        self.load_errors.append('Missing analyzer crystal geometry.')

      num_xtals = info.get('Num Xtals')
      if num_xtals:
        if self.num_xtals > 0 and num_xtals != self.num_xtals:
          self.load_errors.append('Geometry specified for %d xtals, but \'Num Xtals\' key also included with value: %d.' % (self.num_xtals, num_xtals))
        else:
          self.num_xtals = num_xtals

      dirname = info.get('Dispersive Direction')
      if dirname:
        if dirname in DIRECTION_NAMES:
          self.dispersive_direction = DIRECTION_NAMES.index(dirname)
        else:
          self.load_errors.append("Unknown dispersive direction: %s. Should be one of 'Up', 'Down', 'Left' or 'Right'")

      sample = info.get('Sample')
      if sample:
        if len(sample) == 1:
          self.sample = geom.Point(*sample[0])
        else:
          self.load_errors.append('One sample point must be specified, not %d.' % len(sample))
      else:
        self.load_errors.append('Missing sample point.')

      camera = info.get('Camera')
      if camera:
        if len(camera) == 4:
          self.camera = [geom.Point(*p) for p in camera]
          self.camera_rect = geom.Rectangle(
              self.camera[0],
              self.camera[1],
              self.camera[3])
        else:
          self.load_errors.append('Camera contains %d points instead of 4.' % len(self.camera))
      else:
        self.load_errors.append('Missing camera geometry')

      beam = info.get('Beam')
      if beam:
        if len(beam) == 1:
          self.beam = geom.Point(*beam[0])
        else:
          self.load_errors.append('One beam direction must be specified, not %d.' % len(beam))
      else:
        self.load_errors.append('Beam direction not specified')

  def camera_pixel_to_point(self, pixel):
    # returns the coordinates of the top left corner of the request pixel
    px,py = pixel
    h,w = self.camera_shape

    cam_x = self.camera[1] - self.camera[0]
    cam_y = self.camera[3] - self.camera[0]

    return self.camera[0] + px / float(w) * cam_x + py / float(h) * cam_y

  def point_to_camera_pixel(self, point, tolerance=.001):

    d = point - self.camera_rect.p0

    # check that point is within tolerance of plane
    if abs(np.dot(d,self.camera_rect.n)) > tolerance:
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

  def camera_pixel_locations(self, dx=0.5, dy=0.5):
    """
    Calculate the coordinates of all pixels of the detector

    Parameters:
      dx - horizontal location within pixel (0 = left, .5 = center, 1=right)
      dy - vertical location within pixel (0 = top, .5 = center, 1=bottom)
    """
    h,w = self.camera_shape
    coords = np.zeros((w*h,2))
    index = np.arange(w*h)
    coords[:,0] = index % w
    coords[:,1] = index / w

    points = self.camera[0] + \
             (np.outer((coords[:,0]+dx)/float(w), self.camera[1] - self.camera[0]) +
              np.outer((coords[:,1]+dy)/float(h), self.camera[3] - self.camera[0]))
    return points.reshape((h,w,3))

  def image_points(self):
    """
    Calculate reflections of sample location about analyzer crystal faces
    """
    return [geom.reflect_through_plane(self.sample, xp) for xp in self.xtal_rects]

  def project_point_through_rect_onto_camera(self, point, rect):
    """
    Find pixels covered by projection of a point through a rectangle
    """
    h, w = self.camera_shape
    x1 = w
    x2 = 0
    y1 = h
    y2 = 0

    for corner in rect:
      l = geom.Line.FromPoints(point, corner)
      p = geom.intersect_line_with_plane(l, self.camera_rect)

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

  def calculate_projection_bounds(self):
    """
    Determine exposed region on camera from each xtal.

    Finds projection of specular radiation from source point
    through entrance aperture, off xtal, through exit aperture
    and onto camera.

    For now, this finds top left and bottom right corners (in camera coords)
    and assumes region to be rectangular.

    TODO: should be easy to extend this to calculate full trapezoidal region
          or, could add option to give largest rect inside, or smallest rect
          outside...
    """

    bounds = []
    images = self.image_points()

    for xtal_plane, image, entrance_aperture in izip(self.xtal_rects, images, self.entrance_aperture):
      # project image points through exit aperture onto camera
      exit_projection = self.project_point_through_rect_onto_camera(image, self.exit_aperture)

      # find region of crystals exposed by source
      active_region = [
          geom.intersect_line_with_plane(
            geom.Line.FromPoints(self.sample, corner),
            xtal_plane
            )
          for corner in entrance_aperture
          ]

      # project images through active region on to camera
      active_projection = self.project_point_through_rect_onto_camera(image, active_region)

      # "intersect" (not complete intersection... see TODO above)
      x1 = max(exit_projection[0], active_projection[0])
      y1 = max(exit_projection[1], active_projection[1])
      x2 = min(exit_projection[2], active_projection[2])
      y2 = min(exit_projection[3], active_projection[3])

      # add it to the list
      bounds.append([x1,y1,x2,y2])

    return bounds

  def mockup_calibration_matrix(self, dx=0.5, dy=0.5):
    """
    Create a theoretical calibration matrix for the designed spectrometer
    geometry.
    """
    h,w = self.camera_shape
    calib = np.zeros((h,w))

    d0 = lattice_constants[self.xtal_type]
    # XXX this assumes the crystal is cubic (all that we currently use are)
    #     it would be good to generalize this though
    d = d0 / norm(self.xtal_cut)

    images = self.image_points()
    bounds = []

    pixels = self.camera_pixel_locations(dx,dy)

    # find image points and xtal projection boundaries
    for xtal_plane, image, entrance_aperture in izip(self.xtal_rects, images, self.entrance_aperture):
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

  def solid_angle_map(self, bounds=None):
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

    xtals_reversed = False

    h,w = self.camera_shape
    domega = np.zeros((h,w))
    distance = np.zeros((h,w))

    # calculate pixel size
    pw = norm(self.camera[1] - self.camera[0]) / w
    ph = norm(self.camera[3] - self.camera[0]) / h
    #print pw, ph

    images = self.image_points()

    design_bounds = self.calculate_projection_bounds()
    if bounds is None:
      bounds = design_bounds

    # determine if xtals in design file are left to right on camera
    # or right to left
    # TODO: this will need to be updated to support spectrometers with
    #       multiple rows of crystals...
    if design_bounds[0][0] > design_bounds[-1][0]:
      xtals_reversed = True

    pixels = self.camera_pixel_locations()
    num_xtals = len(self.xtal_rects)

    for x1,y1,x2,y2 in bounds:
      xc = (x1+x2)/2.0
      yc = (y1+y2)/2.0

      # determine which crystal this corresponds to
      i = int(xc) * num_xtals / w
      if xtals_reversed:
        i = num_xtals - i - 1

      #print xc,yc, i, self.xtals[i][0]
      # projection shape size
      sh = y2 - y1
      sw = x2 - x1

      dn = pixels[y1:y2,x1:x2].reshape((sw*sh,3)) - images[i]
      length = np.sqrt((dn**2).sum(1))
      cos_theta = np.abs((dn*self.camera_rect.n).sum(1)) / length
      distance[y1:y2,x1:x2] = length.reshape((sh,sw))
      domega[y1:y2,x1:x2] = (pw*ph*cos_theta / length**2).reshape((sh,sw))

    self.distance = distance
    return domega

  def calculate_active_regions(self):
    """
    Find projection of sample through entrance apertures onto xtals.

    FIXME: This currently assumes rectangular projections onto crytals.

    Returns:
      List of active regions for each crystal.
      Each entry in list is also a list (since multiple apertures may
        illuminate same xtal).
      Finally, each subentry is a list of 4 points.
    """
    if len(self.entrance_aperture) != len(self.xtals):
      raise Exception("Number of entrance apertures and crystals must be same")

    # run through apertures and crystals

    active_regions = []
    for i, xtal_rect in enumerate(self.xtal_rects):
      active_regions.append([])
      for aperture in self.entrance_aperture:
        ap_rect = geom.Rectangle(aperture[0], aperture[1], aperture[3])
        projection = geom.project_point_through_rect_onto_rect(self.sample, ap_rect, xtal_rect)
        if projection is not None:
          active_regions[i].append(projection)

    return active_regions

  def calculate_projection_bounds2(self):
    """
    Determine exposed region on camera from each xtal.

    Finds projection of specular radiation from source point
    through entrance aperture, off xtal, through exit aperture
    and onto camera.

    For now, this finds top left and bottom right corners (in camera coords)
    and assumes region to be rectangular.

    TODO: should be easy to extend this to calculate full trapezoidal region
          or, could add option to give largest rect inside, or smallest rect
          outside...
    """

    bounds = []
    images = self.image_points()
    active_regions_by_xtal = self.calculate_active_regions()

    for rect, image, active_regions in izip(self.xtal_rects, images, active_regions_by_xtal):
      xtal_bounds = []
      bounds.append(xtal_bounds)
      # project image points through exit aperture onto camera
      exit_projection = self.project_point_through_rect_onto_camera(image, self.exit_aperture)

      for active_region in active_regions:
        # project images through active region on to camera
        active_projection = self.project_point_through_rect_onto_camera(image, active_region)

        # "intersect" (not complete intersection... see TODO above)
        x1 = max(exit_projection[0], active_projection[0])
        y1 = max(exit_projection[1], active_projection[1])
        x2 = min(exit_projection[2], active_projection[2])
        y2 = min(exit_projection[3], active_projection[3])

        if x2 <= x1 or y2 <= y1:
          # no overlap between exit aperture and entrance aperture 
          xtal_bounds.append(None)
        else:
          # add it to the list
          xtal_bounds.append([x1,y1,x2,y2])

    return bounds


  def mockup_calibration_matrix2(self, dx=0.5, dy=0.5):
    """
    Create a theoretical calibration matrix for the designed spectrometer
    geometry.
    """
    h,w = self.camera_shape
    calib = np.zeros((h,w))

    d0 = lattice_constants[self.xtal_type]
    # XXX this assumes the crystal is cubic (all that we currently use are)
    #     it would be good to generalize this though
    d = d0 / norm(self.xtal_cut)

    images = self.image_points()

    bounds_by_xtal = self.calculate_projection_bounds2()

    pixels = self.camera_pixel_locations(dx,dy)

    # find image points and xtal projection boundaries
    for xtal_plane, image, bounds in izip(self.xtal_rects, images, bounds_by_xtal):
      for b in bounds:
        if b is None: continue
        x1,y1,x2,y2 = b
        rw = x2-x1
        rh = y2-y1

        #print rw, rh
        dn = pixels[y1:y2, x1:x2].reshape((rw*rh,3)) - image
        length = np.sqrt((dn**2).sum(1))
        cos_theta = np.abs((dn*xtal_plane.n).sum(1)) / length
        energy = HC / (2 * d) / cos_theta
        energy = energy.reshape((rh,rw))

        calib[y1:y2,x1:x2] = energy

    return calib

  def scattering_angles(self, degrees=False):
    """
    Calculate scattering angles for all analyzer crystals

    Parameters:
      degrees: return values in degrees if True, radians otherwise

    Returns:
      array of scattering angles for all analyzers
    """
    # vectors from sample to virtual images
    dvs = [im - self.sample for im in self.image_points()]

    # angles in radians
    thetas = np.array([np.arccos(np.dot(self.beam, dv)/np.sqrt(np.dot(dv,dv))) for dv in dvs])

    if degrees:
      thetas *= 180 / np.pi
    return thetas
