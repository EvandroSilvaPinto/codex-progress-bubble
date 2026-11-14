"""Coordinate initial positions across independent Windows bubble processes."""
import ctypes


class PositionSlot:
    """A named handle reserves one position; Windows releases it after a crash."""
    def __init__(self):
        self.kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        self.kernel.CreateMutexW.argtypes = [ctypes.c_void_p,ctypes.c_bool,ctypes.c_wchar_p]
        self.kernel.CreateMutexW.restype = ctypes.c_void_p
        self.kernel.CloseHandle.argtypes = [ctypes.c_void_p]
        self.handle = None
        for index in range(256):
            handle = self.kernel.CreateMutexW(None,False,f'Local\\ProgressBubblePosition-{index}')
            error = ctypes.get_last_error()
            if not handle:
                raise ctypes.WinError(error)
            if error != 183:
                self.handle, self.index = handle, index
                return
            self.kernel.CloseHandle(handle)
        raise RuntimeError('Too many progress bubbles open')

    def close(self):
        if self.handle is not None:
            self.kernel.CloseHandle(self.handle)
            self.handle = None


def initial_position(screen_width, screen_height, width, height, dpi, bubble_scale, slot):
    """Move left by one bubble plus a gap; continue upwards when a row is full."""
    right = max(0,screen_width-width-round(50*dpi))
    bottom = max(0,screen_height-height-round(160*dpi))
    step = max(1,round(84*bubble_scale+18*dpi))
    columns = max(1,right//step+1)
    column,row = slot%columns,slot//columns
    x = max(0,min(right-column*step,max(0,screen_width-width)))
    y = max(0,min(bottom-row*step,max(0,screen_height-height)))
    return x,y
