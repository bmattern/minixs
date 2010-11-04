"""
views for various filter types
"""

import wx


EventFilterChanged, EVT_FILTER_CHANGED = wx.lib.newevent.NewCommandEvent()

class FilterView(wx.Panel):
  def __init__(self, *args, **kwargs):
    if 'filter' in kwargs.keys():
      self.filter = kwargs['filter']
      del(kwargs['filter'])

    wx.Panel.__init__(self, *args, **kwargs)

  def SetValue(self, val):
    pass

  def GetValue(self):
    pass

  def Enable(self, enable=True):
    wx.Panel.Enable(self, enable)
    self.ctrl.Enable(enable)

  def post_event_filter_changed(self):
    """
    Send event indicating that filter has changed
    """
    evt = EventFilterChanged(self.Id, filter=self.filter)
    wx.PostEvent(self, evt)

class IntFilterView(FilterView):
  def __init__(self, *args, **kwargs):
    FilterView.__init__(self, *args, **kwargs)

    id = args[1]
    spin = wx.SpinCtrl(self, id, '', max=100000)
    self.ctrl = spin

    self.ctrl.Bind(wx.EVT_SPINCTRL, self.OnSpinBox, id=id)

  def SetValue(self, val):
    self.ctrl.SetValue(int(val))

  def GetValue(self):
    return self.ctrl.GetValue()

  def OnSpinBox(self, evt):
    self.post_event_filter_changed()

class ChoiceFilterView(FilterView):
  def __init__(self, *args, **kwargs):
    FilterView.__init__(self, *args, **kwargs)

    id = args[1]
    choice = wx.Choice(self, id, choices=self.filter.CHOICES)
    self.ctrl = choice 

    self.ctrl.Bind(wx.EVT_CHOICE, self.on_choice, id=id)

  def SetValue(self, val):
    self.ctrl.SetSelection(int(val))

  def GetValue(self):
    return self.ctrl.GetSelection()

  def on_choice(self):
    self.post_event_filter_changed()

REGISTRY = []

def register(fltr, view):
  global REGISTRY
  REGISTRY.append((fltr, view, wx.NewId()))

def filter_ids():
  global REGISTRY
  return [id for flter, view, id in REGISTRY]
