"""Topmost Windows status bubble with a progress ring and expandable card."""
import ctypes
import hashlib
import json
from pathlib import Path
import sys
import tkinter as tk
import webbrowser

BG = '#101827'
MUTED = '#8897ae'
ACCENT = '#8b9dff'
TRANSPARENT = '#010203'


class Bubble:
    def __init__(self, state):
        self.state = state
        self.data = {}
        self.expanded = False
        self.down = None
        self.moved = False
        self.root = tk.Tk()
        self.root.title('Acompanhamento da demanda')
        self.root.attributes('-topmost', True)
        self.root.configure(bg=TRANSPARENT)
        self.root.attributes('-transparentcolor', TRANSPARENT)
        x = max(0, self.root.winfo_screenwidth()-410)
        y = max(0, self.root.winfo_screenheight()-510)
        self.root.geometry(f'360x350+{x}+{y}')
        self.root.update_idletasks()
        user = ctypes.WinDLL('user32', use_last_error=True)
        user.GetParent.argtypes = [ctypes.c_void_p]
        user.GetParent.restype = ctypes.c_void_p
        hwnd = user.GetParent(self.root.winfo_id())
        user.GetWindowLongW.argtypes = [ctypes.c_void_p, ctypes.c_int]
        user.SetWindowLongW.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_long]
        user.SetWindowLongW(hwnd, -16, user.GetWindowLongW(hwnd, -16) & ~0x00C40000)
        self.canvas = tk.Canvas(self.root, bg=TRANSPARENT, highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        self.canvas.tag_bind('bubble', '<ButtonPress-1>', self.press)
        self.canvas.bind('<B1-Motion>', self.drag)
        self.canvas.bind('<ButtonRelease-1>', self.release)
        self.canvas.tag_bind('close', '<ButtonRelease-1>', lambda e: self.root.destroy())
        self.canvas.tag_bind('report', '<ButtonRelease-1>', lambda e: self.open_html())
        for tag in ('bubble', 'close', 'report'):
            self.canvas.tag_bind(tag, '<Enter>', lambda e: self.canvas.configure(cursor='hand2'))
            self.canvas.tag_bind(tag, '<Leave>', lambda e: self.canvas.configure(cursor=''))
        self.root.bind('<Escape>', lambda event: self.root.destroy())
        self.refresh()

    def rounded(self, x1, y1, x2, y2, radius, fill, tag, outline=''):
        points = [x1+radius,y1,x2-radius,y1,x2,y1,x2,y1+radius,
                  x2,y2-radius,x2,y2,x2-radius,y2,x1+radius,y2,
                  x1,y2,x1,y2-radius,x1,y1+radius,x1,y1]
        return self.canvas.create_polygon(points, smooth=True, splinesteps=24,
                                          fill=fill, outline=outline, tags=tag)

    def text(self, x, y, text, size=10, color='white', bold=False, **kw):
        return self.canvas.create_text(x,y,text=text,fill=color,anchor='nw',
                    font=('Segoe UI',size,'bold' if bold else 'normal'), **kw)

    def draw(self):
        c = self.canvas
        c.delete('all')
        p = max(0, min(100, int(self.data.get('percent', 0))))
        status = self.data.get('status', 'Aguardando atualização')
        color = {'Concluído':'#58d9b0', 'Falha':'#ff8b9d',
                 'Interrompido':'#f3c57d', 'Aguardando informação':'#f3c57d'}.get(status, ACCENT)
        if self.expanded:
            self.rounded(5,8,355,270,24,'#080d17','card')
            self.rounded(1,1,351,261,22,BG,'card', '#2b374d')
            self.text(23,20,'ACOMPANHAMENTO',8,MUTED,True)
            self.text(320,16,'×',16,MUTED,tags='close')
            title = self.data.get('title','Sua demanda')
            self.text(23,46,title[:48]+('…' if len(title)>48 else ''),14,bold=True,width=300)
            self.rounded(23,95,30,102,3,color,'card')
            self.text(38,90,status,9,color)
            self.text(23,116,f'{p}%',25,bold=True)
            self.text(132,137,'progresso estimado',9,MUTED)
            self.rounded(23,164,329,171,3,'#263149','card')
            if p:
                self.rounded(23,164,23+306*p/100,171,3,color,'card')
            self.text(23,185,self.data.get('message','')[:108],9,'#c5cfdf',width=302)
            self.text(23,236,self.data.get('updated','')[11:19],8,MUTED)
            self.text(210,234,'Abrir detalhes  ↗',9,color,tags='report')
        # Separate track and arc make the ring represent actual saved progress.
        c.create_oval(280,278,358,350, fill='#080d17',outline='',tags='bubble')
        c.create_oval(280,273,354,347, fill=BG,outline='#29364c',width=1,tags='bubble')
        c.create_oval(285,278,349,342, outline='#27334a',width=4,tags='bubble')
        if p:
            c.create_arc(285,278,349,342,start=90,extent=-359.9*p/100,
                         style='arc',outline=color,width=4,tags='bubble')
        c.create_text(317,310,text=f'{p}%',fill='#f3f5ff',
                      font=('Segoe UI',14,'bold'),tags='bubble')

    def press(self, event):
        self.down = (event.x_root, event.y_root, self.root.winfo_x(), self.root.winfo_y())
        self.moved = False

    def drag(self, event):
        if not self.down:
            return
        sx, sy, wx, wy = self.down
        dx, dy = event.x_root-sx, event.y_root-sy
        if abs(dx)+abs(dy) > 6:
            self.moved = True
        if self.moved:
            x = max(0, min(wx+dx, self.root.winfo_screenwidth()-360))
            y = max(0, min(wy+dy, self.root.winfo_screenheight()-410))
            self.root.geometry(f'+{x}+{y}')

    def release(self, event):
        if self.down and not self.moved:
            self.expanded = not self.expanded
            self.draw()
        self.down = None

    def open_html(self):
        target = Path(self.data.get('html',''))
        if target.is_file():
            webbrowser.open(target.as_uri())

    def refresh(self):
        try:
            data = json.loads(self.state.read_text(encoding='utf-8'))
            if data != self.data:
                self.data = data
                self.draw()
        except (OSError, ValueError, KeyError):
            if not self.data:
                self.draw()
        self.root.after(2000, self.refresh)


if __name__ == '__main__':
    state = Path(sys.argv[1]).resolve()
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p]
    kernel.CreateMutexW.restype = ctypes.c_void_p
    key = hashlib.sha256(str(state).lower().encode()).hexdigest()
    handle = kernel.CreateMutexW(None, False, 'Local\\CodexStatus'+key)
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    if ctypes.get_last_error() != 183:
        Bubble(state).root.mainloop()
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel.CloseHandle(handle)
