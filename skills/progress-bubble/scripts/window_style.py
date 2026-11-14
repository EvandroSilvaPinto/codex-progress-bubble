"""Per-window frameless styling; never change Windows-wide visual settings."""
import ctypes


def configure_window(root):
    user = ctypes.WinDLL('user32', use_last_error=True)
    user.GetParent.argtypes = [ctypes.c_void_p]
    user.GetParent.restype = ctypes.c_void_p
    hwnd = user.GetParent(root.winfo_id())
    user.GetWindowLongW.argtypes = [ctypes.c_void_p, ctypes.c_int]
    user.SetWindowLongW.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_long]
    # Remove native caption, resize border and minimize/maximize frame controls.
    user.SetWindowLongW(hwnd,-16,user.GetWindowLongW(hwnd,-16)&~0x00C70000)
    extended = user.GetWindowLongW(hwnd,-20)
    user.SetWindowLongW(hwnd,-20,(extended&~0x00040000)|0x00000080)
    try:
        dwm = ctypes.WinDLL('dwmapi')
        dwm.DwmSetWindowAttribute.argtypes = [ctypes.c_void_p,ctypes.c_uint,
                                            ctypes.c_void_p,ctypes.c_uint]
        # DWMWA_NCRENDERING_POLICY = 2; DWMNCRP_DISABLED = 1.
        policy = ctypes.c_int(1)
        dwm.DwmSetWindowAttribute(hwnd,2,ctypes.byref(policy),ctypes.sizeof(policy))
    except (OSError,AttributeError):
        pass
    user.SetWindowPos.argtypes = [ctypes.c_void_p,ctypes.c_void_p,ctypes.c_int,
                                  ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_uint]
    # Apply the new frame without moving, resizing, activating or reordering it.
    user.SetWindowPos(hwnd,None,0,0,0,0,0x0037)
    return hwnd
