"""Topmost Windows status bubble with a progress ring and expandable card."""
import ctypes
import hashlib
import json
from pathlib import Path
import sys
import tkinter as tk
import webbrowser
from ring import ring_png
from timing import eta_text
from navigation import open_conversation
from colors import load_colors, update_html, MAIN_COLORS
from tooltip import Tooltip

TRANSPARENT = '#010203'


class Bubble:
    def __init__(self, state):
        self.state = state
        self.data = {}
        self.expanded = False
        self.down = None
        self.moved = False
        self.theme = load_colors()
        self.colors_open = False
        user = ctypes.WinDLL('user32', use_last_error=True)
        try:
            user.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
        except AttributeError:
            user.SetProcessDPIAware()
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.attributes('-toolwindow', True)
        self.scale = max(1.0,user.GetDpiForSystem()/96)
        self.root.tk.call('tk','scaling',self.scale*96/72)
        self.width,self.height = round(360*self.scale),round(350*self.scale)
        self.root.title('Acompanhamento da demanda')
        icon = Path(__file__).resolve().parent.parent / 'assets/logo.ico'
        if icon.is_file():
            self.root.iconbitmap(default=str(icon))
        self.root.attributes('-topmost', True)
        self.root.configure(bg=TRANSPARENT)
        self.root.attributes('-transparentcolor', TRANSPARENT)
        x = max(0, self.root.winfo_screenwidth()-self.width-50)
        y = max(0, self.root.winfo_screenheight()-self.height-160)
        self.root.geometry(f'{self.width}x{self.height}+{x}+{y}')
        self.root.update_idletasks()
        user = ctypes.WinDLL('user32', use_last_error=True)
        user.GetParent.argtypes = [ctypes.c_void_p]
        user.GetParent.restype = ctypes.c_void_p
        hwnd = user.GetParent(self.root.winfo_id())
        user.GetWindowLongW.argtypes = [ctypes.c_void_p, ctypes.c_int]
        user.SetWindowLongW.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_long]
        user.SetWindowLongW(hwnd, -16, user.GetWindowLongW(hwnd, -16) & ~0x00C40000)
        # Floating tool window: visible on the desktop, absent from taskbar/Alt+Tab.
        extended = user.GetWindowLongW(hwnd, -20)
        user.SetWindowLongW(hwnd, -20, (extended & ~0x00040000) | 0x00000080)
        self.canvas = tk.Canvas(self.root, bg=TRANSPARENT, highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        self.tooltip = Tooltip(self.root)
        self.canvas.tag_bind('bubble', '<ButtonPress-1>', self.press)
        self.canvas.bind('<B1-Motion>', self.drag)
        self.canvas.bind('<ButtonRelease-1>', self.release)
        self.canvas.tag_bind('close', '<ButtonRelease-1>', lambda e: self.root.destroy())
        self.canvas.tag_bind('report', '<ButtonRelease-1>', lambda e: self.open_html())
        self.canvas.tag_bind('colors', '<ButtonRelease-1>', lambda e: self.edit_colors())
        self.canvas.bind('<Button-3>',lambda e:self.edit_colors())
        for tag in ('bubble', 'close', 'report','colors'):
            self.canvas.tag_bind(tag, '<Enter>', lambda e: self.canvas.configure(cursor='hand2'))
            self.canvas.tag_bind(tag, '<Leave>', lambda e: self.canvas.configure(cursor=''))
        self.root.bind('<Escape>', lambda event: self.root.destroy())
        self.root.deiconify()
        self.refresh()

    def rounded(self, x1, y1, x2, y2, radius, fill, tag, outline=''):
        points = [x1+radius,y1,x2-radius,y1,x2,y1,x2,y1+radius,
                  x2,y2-radius,x2,y2,x2-radius,y2,x1+radius,y2,
                  x1,y2,x1,y2-radius,x1,y1+radius,x1,y1]
        return self.canvas.create_polygon(points, smooth=True, splinesteps=24,
                                          fill=fill, outline=outline, tags=tag)

    def text(self, x, y, text, size=10, color=None, bold=False, **kw):
        if 'width' in kw:
            kw['width'] *= self.scale
        return self.canvas.create_text(x,y,text=text,fill=color or self.theme['foreground'],
                    anchor=kw.pop('anchor','nw'),justify=kw.pop('justify','left'),
                    font=('Segoe UI',size,'bold' if bold else 'normal'), **kw)

    def draw(self):
        self.tooltip.hide()
        c = self.canvas
        c.delete('all')
        p = max(0, min(100, int(self.data.get('percent', 0))))
        status = self.data.get('status', 'Aguardando atualização')
        t = self.theme
        color = t[{'Concluído':'complete','Falha':'error',
                   'Interrompido':'waiting','Aguardando informação':'waiting'}.get(status,'ongoing')]
        if self.expanded:
            self.rounded(5,8,355,270,24,'#080d17','card')
            self.rounded(1,1,351,261,22,t['background'],'card',t['border'])
            self.text(23,20,'ACOMPANHAMENTO',8,t['muted'],True)
            self.text(300,20,'Cores',8,t['links'],anchor='ne',tags='colors')
            self.text(328,25,'×',14,t['muted'],anchor='center',tags='close')
            title = self.data.get('title','Sua demanda')
            self.text(23,46,title[:48]+('…' if len(title)>48 else ''),14,bold=True,width=300)
            symbol = {'Concluído':'✓','Falha':'!','Interrompido':'‖','Aguardando informação':'?'}.get(status,'▶')
            self.text(23,90,symbol+' '+status,9,color)
            self.text(23,153,f'{p}%',25,bold=True,anchor='sw')
            self.text(132,153,'progresso estimado',9,t['muted'],anchor='sw')
            self.rounded(23,164,329,171,3,t['track'],'card')
            if p:
                self.rounded(23,164,23+306*p/100,171,3,t['bar'] if status=='Em andamento' else color,'card')
            self.text(23,185,self.data.get('message','')[:88],9,t['message'],width=302)
            self.text(23,234,eta_text(self.data),9,t['links'])
            label = 'Abrir conversa  ↗' if self.data.get('conversation_url') else 'Abrir detalhes  ↗'
            self.text(329,234,label,9,t['links'],anchor='ne',tags='report')
        offset = 70 if self.colors_open and self.expanded else 0
        if offset:
            c.move('all',0,offset)
            self.rounded(1,1,351,63,18,t['background'],'palette-bg',t['border'])
            for index,(key,label) in enumerate(MAIN_COLORS):
                x = 176+(index-2)*62
                tag = 'palette-'+key
                c.create_oval(x-16,16,x+16,48,fill=t[key],outline=t['foreground'],width=1,tags=tag)
                c.tag_bind(tag,'<ButtonRelease-1>',lambda event,k=key:self.choose_color(k))
                c.tag_bind(tag,'<Enter>',lambda event,k=key:self.color_tooltip(k,event))
                c.tag_bind(tag,'<Leave>',lambda event:self.hide_tooltip())
        self.ring_image = tk.PhotoImage(data=ring_png(p,t['ring'] if status=='Em andamento' else color,
            self.scale,t['bubble_background'],t['track'],t['border']))
        c.create_image(275,268+offset,image=self.ring_image,anchor='nw',tags='bubble')
        c.create_text(317,310+offset,text=f'{p}%',fill=t['bubble_text'],
                      font=('Segoe UI',14,'bold'),tags='bubble')
        c.scale('all',0,0,self.scale,self.scale)

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
            x = max(0, min(wx+dx, self.root.winfo_screenwidth()-self.width))
            y = max(0, min(wy+dy, self.root.winfo_screenheight()-self.height-60))
            self.root.geometry(f'+{x}+{y}')

    def release(self, event):
        if self.down and not self.moved:
            self.expanded = not self.expanded
            if not self.expanded and self.colors_open:
                self.set_color_panel(False)
            self.draw()
        self.down = None

    def open_html(self):
        if self.data.get('conversation_url') and open_conversation(self.data):
            return
        target = Path(self.data.get('html',''))
        if target.is_file():
            webbrowser.open(target.as_uri())

    def apply_colors(self,theme):
        self.theme = theme
        try:
            update_html(self.state.with_suffix('.html'),theme)
        except OSError:
            pass
        self.draw()

    def edit_colors(self):
        self.expanded = True
        self.set_color_panel(not self.colors_open)

    def set_color_panel(self,visible):
        old_height = self.height
        self.colors_open = visible
        self.height = round((420 if visible else 350)*self.scale)
        y = max(0,self.root.winfo_y()-(self.height-old_height))
        self.root.geometry(f'{self.width}x{self.height}+{self.root.winfo_x()}+{y}')
        self.draw()

    def choose_color(self,key):
        self.tooltip.hide()
        from color_editor import choose_color
        choose_color(self.root,self.theme,key,self.apply_colors)

    def color_tooltip(self,key,event):
        descriptions = {'background':'Fundo — cartão e bolinha',
            'foreground':'Texto — títulos, mensagens e percentual',
            'ring':'Progresso — barra e anel',
            'links':'Detalhes — links e tempo restante',
            'complete':'Estados — conclusão, falha e espera'}
        self.canvas.configure(cursor='hand2')
        self.tooltip.show(descriptions[key],event.x_root,event.y_root)

    def hide_tooltip(self):
        self.canvas.configure(cursor='')
        self.tooltip.hide()

    def refresh(self):
        theme = load_colors()
        if theme != self.theme:
            self.apply_colors(theme)
        try:
            data = json.loads(self.state.read_text(encoding='utf-8'))
            if data.get('dismissed') and data.get('status') == 'Concluído' and data.get('percent') == 100:
                self.root.destroy()
                return
            current_eta = eta_text(data)
            if data != self.data or current_eta != getattr(self,'last_eta',None):
                self.data = data
                self.last_eta = current_eta
                self.draw()
        except (OSError, ValueError, KeyError):
            if not self.data:
                self.draw()
        self.root.after(500, self.refresh)


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
        app = Bubble(state)
        if '--edit-colors' in sys.argv[2:]:
            app.root.after(200,app.edit_colors)
        app.root.mainloop()
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel.CloseHandle(handle)
