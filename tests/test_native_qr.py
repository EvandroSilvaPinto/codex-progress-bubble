import sys
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'skills/progress-bubble/scripts'))

class NativeQRTests(unittest.TestCase):
    def test_shared_card_displays_reader_qr_without_opening_browser(self):
        import sharing
        record=dict(endpoint='https://progress.example',id='a'*32,read_token='b'*43,write_token='c'*43,created=True)
        app=SimpleNamespace(state=Path('test.json'),root=Mock(),data={})
        with patch.object(sharing,'load_secret',return_value=record),patch('webbrowser.open') as browser,patch.object(sharing,'show_qr') as display:
            sharing.share_task(app)
        browser.assert_not_called()
        display.assert_called_once_with(app,record['endpoint']+'/#'+record['id']+'.'+record['read_token'])
        self.assertNotIn(record['write_token'],display.call_args.args[1])

    def test_qr_view_and_back_preserve_the_task_and_hide_colors(self):
        from native_qr import show_qr,hide_qr
        app=SimpleNamespace(colors_open=True,expanded=False,data={'percent':35},resize=Mock())
        show_qr(app,'https://progress.example/#reader')
        self.assertTrue(app.expanded);self.assertFalse(app.colors_open);self.assertTrue(app.mobile_url)
        hide_qr(app)
        self.assertIsNone(app.mobile_url);self.assertEqual(app.data,{'percent':35})
        self.assertEqual(app.resize.call_count,2)

    def test_qr_view_preserves_the_existing_window_dimensions(self):
        from bubble import Bubble
        from native_qr import show_qr
        from sizing import geometry,DEFAULTS
        for scale in (.85,1,1.5,2):
            app=Bubble.__new__(Bubble)
            app.scale=scale;app.sizes=dict(DEFAULTS);app.layout=geometry(scale,DEFAULTS)
            app.width,app.height=app.layout['width'],app.layout['height']
            before=(app.width,app.height)
            app.root=Mock();app.root.winfo_x.return_value=100;app.root.winfo_y.return_value=100
            app.root.winfo_screenwidth.return_value=3840;app.root.winfo_screenheight.return_value=2160
            app.draw=Mock()
            show_qr(app,'https://progress.example/#reader')
            self.assertEqual((app.width,app.height),before)

    def test_native_qr_png_is_crisp_at_each_card_size(self):
        from native_qr import qr_png
        import struct
        url='https://progress.example/#'+'a'*32+'.'+'b'*43
        for scale in (.85,1,1.2,1.5,2):
            data=qr_png(url,round(240*scale))
            self.assertEqual(data[:8],b'\x89PNG\r\n\x1a\n')
            width,height=struct.unpack('!II',data[16:24]);self.assertEqual(width,height)
            self.assertLessEqual(width,round(240*scale))

    def test_copy_action_copies_only_the_reader_link(self):
        from native_qr import copy_qr
        app=SimpleNamespace(root=Mock(),mobile_url='https://progress.example/#reader')
        copy_qr(app)
        app.root.clipboard_clear.assert_called_once()
        app.root.clipboard_append.assert_called_once_with(app.mobile_url)
