"""Antialiased RGBA progress ring, rendered at the display's native resolution."""
from functools import lru_cache
import math
import struct
import zlib


@lru_cache(maxsize=12)
def ring_png(percent, color, scale=1.0, background='#101827', track='#27334a', border='#29364c'):
    size = max(32, round(84*scale))
    factor = size/84
    accent = tuple(int(color[i:i+2],16) for i in (1,3,5))
    base,empty,edge = [tuple(int(c[i:i+2],16) for i in (1,3,5)) for c in (background,track,border)]
    pixels = bytearray()
    sweep = math.tau*max(0,min(100,percent))/100
    for y in range(size):
        pixels.append(0)
        for x in range(size):
            dx,dy = (x+.5)/factor-42,(y+.5)/factor-42
            distance = math.hypot(dx,dy)
            alpha = max(0,min(1,(37-distance)*factor+.5))
            rgb = base
            if distance > 36:
                rgb = edge
            coverage = max(0,min(1,(2-abs(distance-32))*factor+.5))
            angle = math.atan2(dx,-dy)%math.tau
            stroke = accent if percent > 0 and angle <= sweep else empty
            if 0 < percent < 100:
                cap = min(math.hypot(dx,dy+32),
                          math.hypot(dx-32*math.sin(sweep),dy+32*math.cos(sweep)))
                cap_coverage = max(0,min(1,(2-cap)*factor+.5))
                if cap_coverage > coverage:
                    coverage,stroke = cap_coverage,accent
            rgb = tuple(round(a+(b-a)*coverage) for a,b in zip(rgb,stroke))
            pixels.extend((*rgb,round(255*alpha)))
    def chunk(kind,data):
        return struct.pack('!I',len(data))+kind+data+struct.pack('!I',zlib.crc32(kind+data)&0xffffffff)
    return (b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!2I5B',size,size,8,6,0,0,0))
            +chunk(b'IDAT',zlib.compress(bytes(pixels)))+chunk(b'IEND',b''))
