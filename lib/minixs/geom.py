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
    return "Plane(%s, %s)" % (self.p0.__repr__(), self.n.__repr__())

def intersect_line_with_plane(line, plane):
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
