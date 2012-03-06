import numpy as np

SCAN_COLUMN_WIDTH = 21

class ScanFile(object):
  """
  A PNC (Advanced Photon Source Sector 20) scan file.

  Example:
    >>> import minixs as mx
    >>> s = mx.scanfile.ScanFile(filename)
    >>> s.headers[0]
    '# 1-D Scan File created by LabVIEW Control Panel  2/18/2012  5:21:44 PM; Scan time 1 hrs 2 min 42 sec. \r\n'
    >>> s.columns
    ['Mono Energy (alt) *', 'Scaler preset time *', 'ID Gap *', 'PreSlit', 'preKB', 'I0', 'IT', 'Iref (Cal)', 'cyberstar', 'S20-PILATUS1:Stats1:T']
    >>> s.data.shape
    (121,10)
    >>> energies = s.data[:,0]
    >>> I0 = s.data[:,5]
    >>> total_intensity = s.data[:,9]
    >>> plot(energies, total_intensity / I0)
    >>> len(s.headers)
    59

  """
  def __init__(self, filename=None):
    if filename:
      self.load(filename)

  def load(self, filename, headers_only=False):
    self.filename = filename

    #read in headers
    with open(filename) as f:
      self.headers = []
      for line in f:
        if line[0] != '#':
          # rewind to beginning of this line
          f.seek(-len(line), 1)
          break

        # strip off '#' and newline
        self.headers.append(line)

    column_names = self.headers[-1]
    self.columns = [column_names[i:i+SCAN_COLUMN_WIDTH].strip() for i in xrange(1,len(column_names)-2, SCAN_COLUMN_WIDTH)]

    # load in data
    if not headers_only:
      self.data = np.loadtxt(filename)

      # reshape single column
      if len(self.data.shape) == 1:
        self.data.shape = (self.data.shape[0], 1)

  def save(self, filename=None, fmt=None):
    if not filename:
      filename = self.filename

    assert filename, "A filename must be provided in order to save"

    if fmt is None:
      fmt = '%%%d.8f' % SCAN_COLUMN_WIDTH

    with open(filename, 'w') as f:
      for line in self.headers:
        f.write(line)

      # numpy cannot save with dos newlines...
      #savetxt(f, self.data, fmt=fmt, delimiter=' ')

      # so, save by hand
      for row in self.data:
        for val in row:
          f.write(fmt % val)
          f.write(' ')
        f.write('\r\n')

  def find_column(self, key):
    for i,col in enumerate(self.columns):
      if key in col.lower():
        return i
    return None
