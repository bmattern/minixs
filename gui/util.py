def read_scan_column_names(scanfile):
  with open(scanfile) as f:
    last = None

    for line in f:
      if line[0] != "#":
        num = len(line.split())

        if last is None:
          num = len(line.split())
          return [ str(i) for i in range(1,num+1) ]

        else:
          last = last[1:]
          cols = last.split()

          # if whitespace separated headers aren't correct, try fixed width
          if len(cols) != num:
            w = 21
            cols = [ last[w*i:w*(i+1)].strip() for i in range(0,len(last)/20) ]
          if len(cols) != num:
            return [ str(i) for i in range(1,num+1) ]

          return [ "%d: %s" % (i,s) for i,s in zip(range(1,num+1), cols) ]

      last = line

def xtals_intersect(xtal1, xtal2):
  (ax1, ay1), (ax2, ay2)  = xtal1
  (bx1, by1), (bx2, by2)  = xtal2

  return (ax1 < bx2 and bx1 < ax2 and 
      ay1 < by2 and by1 < ay2)
  
