"""Native-resolution antialiased UI shapes without external dependencies."""
from functools import lru_cache
import math
import struct
import zlib


def rgb(color):
    return tuple(int(color[i:i+2],16) for i in (1,3,5))


@lru_cache(maxsize=96)
def rounded_png(width, height, radius, fill, border='', backing='', stroke=1):
    width, height = max(1,round(width)), max(1,round(height))
    radius = max(0,min(radius,width/2,height/2))
    inside, edge = rgb(fill), rgb(border or fill)
    background = rgb(backing) if backing else (0,0,0)
    pixels = bytearray()
    for y in range(height):
        pixels.append(0)
        for x in range(width):
            dx = abs(x+.5-width/2)-(width/2-radius)
            dy = abs(y+.5-height/2)-(height/2-radius)
            distance = math.hypot(max(dx,0),max(dy,0))+min(max(dx,dy),0)-radius
            coverage = max(0,min(1,.5-distance))
            inner = max(0,min(1,.5-distance-stroke)) if border else 1
            color = tuple(round(a+(b-a)*inner) for a,b in zip(edge,inside))
            if backing:
                color = tuple(round(a+(b-a)*coverage) for a,b in zip(background,color))
                alpha = 255
            else:
                alpha = round(coverage*255)
            pixels.extend((*color,alpha))

    def chunk(kind,data):
        return struct.pack('!I',len(data))+kind+data+struct.pack('!I',zlib.crc32(kind+data)&0xffffffff)
    return (b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!2I5B',width,height,8,6,0,0,0))
            +chunk(b'IDAT',zlib.compress(bytes(pixels)))+chunk(b'IEND',b''))
