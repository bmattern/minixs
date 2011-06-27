MOD_NONE  = 0x0
MOD_SHIFT = 0x1
MOD_CTRL  = 0x2
MOD_ALT   = 0x4
MOD_CMD   = 0x8

def mouse_event_modifier_mask(evt):
  mask = 0
  mask |= evt.ShiftDown() * MOD_SHIFT
  mask |= evt.ControlDown() * MOD_CTRL
  mask |= evt.AltDown() * MOD_ALT
  mask |= evt.CmdDown() * MOD_CMD
  return mask

