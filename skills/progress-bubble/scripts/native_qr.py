"""Locally encoded, integer-pixel QR sharing inside the existing progress card."""
from functools import lru_cache
import struct
import zlib
import tkinter as tk
from qrcode import QRCode,ERROR_CORRECT_M
from transitions import enter_view


@lru_cache(maxsize=8)
def qr_matrix(url):
    qr=QRCode(error_correction=ERROR_CORRECT_M,border=4)
    qr.add_data(url);qr.make(fit=True)
    return tuple(tuple(row) for row in qr.get_matrix())


@lru_cache(maxsize=12)
def qr_png(url,available):
    matrix=qr_matrix(url)
    pixel=max(1,available//len(matrix));size=pixel*len(matrix)
    rows=[]
    for row in matrix:
        line=b'\0'+b''.join((b'\0' if dark else b'\xff')*pixel for dark in row)
        rows.extend([line]*pixel)
    def chunk(kind,data):
        return struct.pack('!I',len(data))+kind+data+struct.pack('!I',zlib.crc32(kind+data)&0xffffffff)
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!2I5B',size,size,8,0,0,0,0))+chunk(b'IDAT',zlib.compress(b''.join(rows)))+chunk(b'IEND',b'')


def show_qr(app,url):
    app.mobile_url=url;app.colors_open=False;app.expanded=True;enter_view(app,app.resize)


def hide_qr(app):
    app.mobile_url=None;enter_view(app,app.resize)


def copy_qr(app):
    if getattr(app,'mobile_url',None):
        app.root.clipboard_clear();app.root.clipboard_append(app.mobile_url)


def draw_qr(app):
    theme=app.theme;scale=app.layout['card']
    app.rounded(5,8,355,270,24,'#080d17','card')
    app.rounded(1,1,351,261,22,theme['background'],'card',theme['border'])
    app.text(23,20,'ACOMPANHAMENTO',8,theme['muted'],True)
    app.text(300,20,'Voltar',8,theme['links'],anchor='ne',tags='qr-back')
    app.text(328,25,'×',14,theme['muted'],anchor='center',tags='close')
    image=tk.PhotoImage(data=qr_png(app.mobile_url,round(180*scale)))
    app.shape_images.append(image)
    app.canvas.create_image(176-image.width()/scale/2,45,image=image,anchor='nw',tags='qr-image')
    app.text(176,234,'Copiar link',9,theme['links'],anchor='n',tags='qr-copy')
