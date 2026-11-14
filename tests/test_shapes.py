from pathlib import Path
import struct
import sys
import unittest
import zlib

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'skills/progress-bubble/scripts'))
from shapes import rounded_png


def pixels(png):
    width,height = struct.unpack('!II',png[16:24])
    offset,data = 8,b''
    while offset<len(png):
        length = struct.unpack('!I',png[offset:offset+4])[0]
        if png[offset+4:offset+8]==b'IDAT':
            data += png[offset+8:offset+8+length]
        offset += length+12
    raw = zlib.decompress(data)
    rows = [raw[y*(width*4+1)+1:(y+1)*(width*4+1)] for y in range(height)]
    return width,height,[tuple(row[x:x+4]) for row in rows for x in range(0,len(row),4)]


class ShapeTests(unittest.TestCase):
    def test_circle_has_smooth_edges_and_preserves_selected_color(self):
        width,height,rgba = pixels(rounded_png(32,32,16,'#ff77aa','#ffffff','#101827'))
        self.assertEqual((width,height),(32,32))
        self.assertEqual(rgba[16*32+16],(255,119,170,255))
        self.assertEqual(rgba[0],(16,24,39,255))
        self.assertGreater(len(set(rgba)),10)

    def test_panels_have_transparent_corners_and_native_dimensions(self):
        for scale in (.85,1,1.2,1.5,2):
            width,height,rgba = pixels(rounded_png(40*scale,30*scale,8*scale,'#101827'))
            self.assertEqual((width,height),(round(40*scale),round(30*scale)))
            self.assertEqual(rgba[0][3],0)
            self.assertTrue(any(0<p[3]<255 for p in rgba))
