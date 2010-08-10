from numpy import loadtxt, savetxt

COLUMN_WIDTH = 21
class ScanFile:
  def __init__(self, filename=None):
    if filename:
      self.load(filename)

  def load(self, filename):
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
    self.columns = [column_names[i:i+COLUMN_WIDTH].strip() for i in xrange(1,len(column_names)-2, COLUMN_WIDTH)]

    # load in data
    self.data = loadtxt(filename)

  def save(self, filename=None, fmt=None):
    if not filename:
      filename = self.filename

    assert filename, "A filename must be provided in order to save"

    if fmt is None:
      fmt = '%%%d.8f' % COLUMN_WIDTH

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

