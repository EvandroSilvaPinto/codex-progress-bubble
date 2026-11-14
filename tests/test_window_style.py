import ctypes
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'skills/progress-bubble/scripts'))
from window_style import configure_window


class WindowStyleTests(unittest.TestCase):
    def test_frame_policy_applies_only_to_the_bubble_without_global_settings(self):
        user,dwm = Mock(),Mock()
        user.GetParent.return_value=123
        user.GetWindowLongW.side_effect=[0x00CF0000,0x00040000]
        root=Mock()
        with patch.object(ctypes,'WinDLL',side_effect=[user,dwm],create=True):
            self.assertEqual(configure_window(root),123)
        self.assertEqual(user.SetWindowLongW.call_args_list[0].args,(123,-16,0x00080000))
        self.assertEqual(user.SetWindowLongW.call_args_list[1].args,(123,-20,0x80))
        args=dwm.DwmSetWindowAttribute.call_args.args
        self.assertEqual(args[:2],(123,2))
        self.assertEqual(ctypes.cast(args[2],ctypes.POINTER(ctypes.c_int)).contents.value,1)
        user.SetWindowPos.assert_called_once_with(123,None,0,0,0,0,0x0037)

    def test_frame_style_still_applies_if_dwm_api_is_unavailable(self):
        user=Mock()
        user.GetParent.return_value=123
        user.GetWindowLongW.return_value=0
        with patch.object(ctypes,'WinDLL',side_effect=[user,OSError('unavailable')],create=True):
            configure_window(Mock())
        user.SetWindowPos.assert_called_once()
