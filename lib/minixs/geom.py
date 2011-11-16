import numpy as np
from numpy.linalg import norm

def Vector(x,y,z):
  return np.array([x,y,z])

Point = Vector

def angle_between(v1, v2):
  return np.arccos(np.dot(v1,v2) / norm(v1) / norm(v2))

class Plane(object):
  def __init__(self, p0, n):
    """
    Parameters:
      p0 - a point in the plane
      n  - unit vector normal to plane
    """
    self.p0 = np.array(p0)
    self.n = np.array(n)

  @classmethod
  def FromPoints(cls, p1, p2, p3):
    n = np.cross(p2-p1, p3-p1)
    n /= norm(n)

    return cls(p1, n)

  def __repr__(self):
    return "Plane(%s, %s)" % (self.p0.__repr__(), self.n.__repr__())

class Rectangle(Plane):
  """
  A bounded, rectilinear region of a plane.
  """
  def __init__(self, p0, p1, p2):
    """
    A rectangular surface.

    Parameters:
      p0: point with local coords (0,0)
      p1: point with local coords (1,0)
      p2: point with local coords (0,1)
    """

    # defining points
    self.p0 = np.asarray(p0, dtype='float')
    self.p1 = np.asarray(p1, dtype='float')
    self.p2 = np.asarray(p2, dtype='float')

    # basis vectors for rectangle
    self.x = (self.p1 - self.p0)
    self.y = (self.p2 - self.p0)

    # reciprocal vectors
    self.kx = self.x / np.dot(self.x, self.x)
    self.ky = self.y / np.dot(self.y, self.y)

    # normal vector
    self.n = np.cross(self.x, self.y)
    self.area = np.linalg.norm(self.n)
    self.n /= self.area

  def closest_point(self, p):
    dp = np.asarray(p) - self.p0
    dp -= np.dot(dp, self.n) * self.n
    return self.p0 + dp

  def global_to_local(self, p):
    dp = np.asarray(p) - self.p0
    return np.array([np.dot(dp, self.kx), np.dot(dp, self.ky)])

  def local_to_global(self, p):
    return self.p0 + p[0] * self.x + p[1] * self.y

  def corners(self):
    return [self.local_to_global(p) for p in [(0,0),(1,0),(1,1),(0,1)]]

  def __repr__(self):
    return "Rectangle(%s, %s, %s)" % (self.p0.__repr__(), self.p1.__repr__(), self.p2.__repr__())

class Line(object):
  def __init__(self, l0, n):
    """
    Parameters:
      l0 - a point on the line
      n  - a unit vector in direction of lin
    """
    self.l0 = l0
    self.n = n

  @classmethod
  def FromPoints(cls, p1, p2):
    n = np.array(p2) - np.array(p1)
    n /= norm(n)

    return cls(p1, n)

  def __repr__(self):
    return "Line(%s, %s)" % (self.l0.__repr__(), self.n.__repr__())

def intersect_line_with_plane(line, plane):
  """
  Find intersection point of a line with a plane.

  Returns:
    The intersection point if it exists and is unique.
    The origin of the plane if the line is contained within the plane.
    None if the line is parallel to, but out of, the plane.
  """

  a = np.dot(plane.p0 - line.l0, plane.n)
  b = np.dot(line.n, plane.n)  

  if (b == 0): # line parallel to plane
    if (a == 0): # in plane
      return plane.p0
    else: # out of plane 
      return None
  else:
    return line.l0 + a/b * line.n


def reflect_through_plane(point, plane):
  tmp = point - plane.p0
  return plane.p0 + tmp - 2 * np.dot(tmp, plane.n) * plane.n

def project_point_through_rect_onto_rect(point, rect1, rect2):

  lines = [Line.FromPoints(point, corner) for corner in rect1.corners()]
  points = np.array([intersect_line_with_plane(l, rect2) for l in lines])
  #if np.any(p is None for p in points): continue

  # convert to xtal coordinates
  lpoints = np.array([rect2.global_to_local(p) for p in points])
  # clamp to xtal
  # FIXME: this is only correct2 if the projection is rect2angular
  #        and has sides parallel to xtal sides...
  lpoints[lpoints<0] = 0
  lpoints[lpoints>1] = 1

  # check if there is any overlap with xtal, and skip if not
  size = lpoints.max(0) - lpoints.min(0)
  if np.any(size < 1e-5):
    return None

  # convert back to global coordinates
  return [rect2.local_to_global(p) for p in lpoints]
