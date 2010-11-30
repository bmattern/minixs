import numpy as np

SCAN_COLUMN_WIDTH = 21

class ScanFile:
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

