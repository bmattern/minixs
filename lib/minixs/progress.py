class ProgressIndicator(object):
  def __init__(self, name="Main"):
    self.steps = [(0.0, 1.0, name)]
    self.progress = 0.0

  def push_step(self, name, scale):
    prev_start, prev_stop, prev_name = self.steps[-1]
    start = self.progress 
    stop = start + (prev_stop - prev_start) * scale
    self.msg = name
    self.steps.append((start, stop, name))
    self.do_update()

  def pop_step(self):
    start, stop, name = self.steps.pop()
    self.progress = stop
    self.msg = self.steps[-1][-1]
    self.do_update()

  def update(self, msg, progress):
    # translate step progress to full progress
    start, stop, name = self.steps[-1]
    if msg is not None:
      self.msg = msg
    self.progress = start + (progress * (stop - start))
    self.do_update()

  def do_update(self):
    """
    Override this to display progress in a more useful fashion
    """
    pass

class PrintProgressIndicator(ProgressIndicator):
  def do_update(self):
    print("Progress (%d%%): %s" % (self.progress*100, self.msg))

