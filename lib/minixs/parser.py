STRING = 1
INT = 2
FLOAT = 3
LIST = 4

STATE_NONE = 0
STATE_LIST = 1

class Parser(object):
  def __init__(self, parser_info={}):
    self.parser_info = parser_info
    self.state = STATE_NONE

  def add_key_type(self, key, valtype):
    self.parser_info[key] = valtype

  def parse(self, lines):
    self.raw = []
    self.parsed = {}
    self.unknown_keys = []
    self.errors = []

    for line in lines:
      self.raw.append(line)
      stripped = line.strip()
      if stripped == '' or stripped[0] == '#':
        continue
      if self.state == STATE_LIST:
        # if indented, then part of list, otherwise 
        if line and line[0] in " \t":
          try:
            self.parsed[self.list_key].append(self.parse_val(self.list_type, line.strip()))
          except Exception as e:
            self.errors.append("Error parsing line '%s': %s"% (line.strip(), e))
          continue
        else:
          self.state = STATE_NONE

      bits = line.split(':', 1)
      key = bits[0].strip()
      if len(bits) > 1:
        val = bits[1].strip()
      else:
        val = ''

      if key in self.parser_info:
        val_type = self.parser_info[key]
        if type(val_type) == tuple and val_type[0] == LIST:
          self.parsed[key] = []
          self.state = STATE_LIST
          self.list_key = key 
          self.list_type = val_type[1]
          continue

        try:
          self.parsed[key] = self.parse_val(val_type, val)
        except Exception as e:
          self.errors.append("Error parsing line '%s': %s"% (line.strip(), e))
      else:
        self.unknown_keys.append(key)

    return self.parsed

  def parse_val(self, val_type, val):
    if callable(val_type):
      return val_type(val)
    elif val_type == STRING:
      return val
    elif val_type == INT:
      return int(val)
    elif val_type == FLOAT:
      return float(val)
    elif type(val_type) == tuple:
      bits = val.split(None,len(val_type)-1)
      return tuple([self.parse_val(bit_type, bit) for bit, bit_type in zip(bits, val_type)])

if __name__ == "__main__":
  # create a dictionary of keys and value types
  parser_info = {
      'name': STRING,
      'xtals': INT,
      'energy_range': (FLOAT, FLOAT),
      'filenames': (LIST, STRING),
      'exposure_files': (LIST, (FLOAT, STRING)),
      }
  p = Parser(parser_info)

  # some example data 
  raw = "name: foobar\nenergy_range: 7000.0 7140.0\nfilenames:\n  file1\n  file2\n  file3\nxtals: 10\nexposure_files:\n  7120.0 foo/what the/file1\n  7140.0 foo/what the/file2\nflub: hmm"

  # parse it
  p.parse(raw.split('\n'))

  # print it
  from pprint import pprint
  pprint(p.parsed)

