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
from colors import load_colors, update_html, MAIN_COLORS, reset_colors
from tooltip import Tooltip
from i18n import t as tr
from shapes import rounded_png
from sizing import load_sizes, save_size, geometry, show_size_menu
from placement import PositionSlot, initial_position
from progress import displayed_progress
from window_style import configure_window
from transitions import PanelMotion,animations_enabled,enter_view,exit_view
from sharing import share_task
from native_qr import draw_qr,hide_qr,copy_qr

TRANSPARENT = '#010203'


class Bubble:
    def __init__(self, state):
        self.state = state
        self.data = {}
        self.expanded = False
        self.mobile_url = None
        self.down = None
        self.moved = False
        self.theme = load_colors()
        self.colors_open = False
        self.bubble_hover = False
        self.close_hide_job = None
        self.sizes = load_sizes()
        user = ctypes.WinDLL('user32', use_last_error=True)
        try:
            user.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
        except AttributeError:
            user.SetProcessDPIAware()
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.overrideredirect(True)
        self.root.attributes('-toolwindow', True)
        self.scale = max(1.0,user.GetDpiForSystem()/96)
        self.root.tk.call('tk','scaling',self.scale*96/72)
        self.layout = geometry(self.scale,self.sizes)
        self.width,self.height = self.layout['width'],self.layout['height']
        self.root.title(tr('Acompanhamento da demanda'))
        icon = Path(__file__).resolve().parent.parent / 'assets/logo.ico'
        if icon.is_file():
            self.root.iconbitmap(default=str(icon))
        self.root.attributes('-topmost', True)
        self.root.configure(bg=TRANSPARENT)
        self.root.attributes('-transparentcolor', TRANSPARENT)
        self.position_slot = PositionSlot()
        self.root.bind('<Destroy>',lambda e:self.position_slot.close() if e.widget is self.root else None)
        x,y = initial_position(self.root.winfo_screenwidth(),self.root.winfo_screenheight(),
            self.width,self.height,self.scale,self.layout['bubble'],self.position_slot.index)
        self.root.geometry(f'{self.width}x{self.height}+{x}+{y}')
        self.root.update_idletasks()
        self.hwnd = configure_window(self.root)
        self.canvas = tk.Canvas(self.root, bg=TRANSPARENT, highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        self.motion=PanelMotion(self.root,self.canvas,animations_enabled())
        self.tooltip = Tooltip(self.root)
        self.canvas.tag_bind('bubble', '<ButtonPress-1>', self.press)
        self.canvas.bind('<B1-Motion>', self.drag)
        self.canvas.bind('<ButtonRelease-1>', self.release)
        self.canvas.tag_bind('close', '<ButtonRelease-1>', lambda e: self.close_card())
        self.canvas.tag_bind('bubble-close', '<ButtonRelease-1>', lambda e: self.root.destroy())
        self.canvas.bind('<Motion>', self.hover_bubble)
        self.canvas.bind('<Leave>', self.defer_hide_bubble_close)
        self.canvas.bind('<Enter>', self.hover_bubble)
        self.canvas.tag_bind('report', '<ButtonRelease-1>', lambda e: self.open_html())
        self.canvas.tag_bind('colors', '<ButtonRelease-1>', lambda e: self.edit_colors())
        self.canvas.tag_bind('reset-colors', '<ButtonRelease-1>', lambda e: self.reset_theme())
        self.canvas.tag_bind('sizes','<ButtonRelease-1>',lambda e:show_size_menu(self,e))
        self.canvas.tag_bind('mobile','<ButtonRelease-1>',lambda e:share_task(self))
        self.canvas.tag_bind('qr-back','<ButtonRelease-1>',lambda e:hide_qr(self))
        self.canvas.tag_bind('qr-copy','<ButtonRelease-1>',lambda e:copy_qr(self))
        self.canvas.bind('<Button-3>',lambda e:show_size_menu(self,e))
        for tag in ('bubble', 'close', 'report','colors','reset-colors','sizes','mobile','qr-back','qr-copy'):
            self.canvas.tag_bind(tag, '<Enter>', lambda e: self.canvas.configure(cursor='hand2'))
            self.canvas.tag_bind(tag, '<Leave>', lambda e: self.canvas.configure(cursor=''))
        self.root.bind('<Escape>', lambda event: self.root.destroy())
        self.root.deiconify()
        self.refresh()

    def rounded(self, x1, y1, x2, y2, radius, fill, tag, outline=''):
        scale = self.layout['card']
        backing = self.theme['background'] if tag == 'progress' else ''
        photo = tk.PhotoImage(data=rounded_png((x2-x1)*scale,(y2-y1)*scale,
            radius*scale,fill,outline,backing,scale))
        self.shape_images.append(photo)
        return self.canvas.create_image(x1,y1,image=photo,anchor='nw',tags=tag)

    def text(self, x, y, text, size=10, color=None, bold=False, translate=True, **kw):
        if 'width' in kw:
            kw['width'] *= self.layout['card']
        return self.canvas.create_text(x,y,text=tr(text) if translate else text,fill=color or self.theme['foreground'],
                    anchor=kw.pop('anchor','nw'),justify=kw.pop('justify','left'),
                    font=('Segoe UI',-max(1,round(size*self.layout['card']*96/72)),'bold' if bold else 'normal'), **kw)

    def draw(self):
        motion=getattr(self,'motion',None)
        if motion is not None:motion.cancel()
        self.tooltip.hide()
        c = self.canvas
        c.delete('all')
        self.shape_images = []
        p = round(displayed_progress(self.data),1)
        status = self.data.get('status', 'Aguardando atualização')
        t = self.theme
        color = t[{'Concluído':'complete','Falha':'error',
                   'Interrompido':'waiting','Aguardando informação':'waiting'}.get(status,'ongoing')]
        if self.expanded and getattr(self,'mobile_url',None):
            draw_qr(self)
        elif self.expanded:
            self.rounded(5,8,355,270,24,'#080d17','card')
            self.rounded(1,1,351,261,22,t['background'],'card',t['border'])
            self.text(23,20,'ACOMPANHAMENTO',8,t['muted'],True)
            if self.colors_open:
                self.text(252,20,'Redefinir cores',8,t['links'],anchor='ne',tags='reset-colors')
            self.text(300,20,'Cores',8,t['links'],anchor='ne',tags='colors')
            self.text(328,25,'×',14,t['muted'],anchor='center',tags='close')
            title = self.data.get('title',tr('Sua demanda'))
            self.text(23,46,title[:48]+('…' if len(title)>48 else ''),14,bold=True,width=300,translate=False)
            symbol = {'Concluído':'✓','Falha':'!','Interrompido':'‖','Aguardando informação':'?'}.get(status,'▶')
            self.text(23,90,symbol+' '+tr(status),9,color)
            self.text(23,153,f'{int(p)}%',25,bold=True,anchor='sw')
            self.text(132,153,'progresso estimado',9,t['muted'],anchor='sw')
            self.rounded(23,164,329,171,3,t['track'],'progress')
            if p:
                self.rounded(23,164,23+306*p/100,171,3,t['bar'] if status=='Em andamento' else color,'progress')
            self.text(23,185,self.data.get('message','')[:88],9,t['message'],width=302,translate=False)
            self.text(329,90,'Tamanhos',8,t['links'],anchor='ne',tags='sizes')
            self.text(329,112,'Celular',8,t['links'],anchor='ne',tags='mobile')
            self.text(23,234,eta_text(self.data),9,t['links'])
            label = 'Abrir conversa  ↗' if self.data.get('conversation_url') else 'Abrir detalhes  ↗'
            self.text(329,234,label,9,t['links'],anchor='ne',tags='report')
        offset = self.layout['offset']
        if offset:
            c.move('all',0,offset)
            self.rounded(1,1,351,63,18,t['background'],'palette-bg',t['border'])
            for index,(key,label) in enumerate(MAIN_COLORS):
                x = 176+(index-2)*62
                tag = 'palette-'+key
                scale = self.layout['card']
                photo = tk.PhotoImage(data=rounded_png(32*scale,32*scale,16*scale,
                    t[key],t['foreground'],t['background'],scale))
                self.shape_images.append(photo)
                c.create_image(x-16,16,image=photo,anchor='nw',tags=tag)
                c.tag_bind(tag,'<ButtonRelease-1>',lambda event,k=key:self.choose_color(k))
                c.tag_bind(tag,'<Enter>',lambda event,k=key:self.color_tooltip(k,event))
                c.tag_bind(tag,'<Leave>',lambda event:self.hide_tooltip())
        card_scale = self.layout['card']
        c.scale('all',0,0,card_scale,card_scale)
        c.move('all',self.layout['card_x'],0)
        c.addtag_all('panel')
        bs = self.layout['bubble']
        bx, by = self.layout['bubble_x'], self.layout['bubble_y']
        self.ring_image = tk.PhotoImage(data=ring_png(p,t['ring'] if status=='Em andamento' else color,
            bs,t['bubble_background'],t['track'],t['border']))
        c.create_image(bx,by,image=self.ring_image,anchor='nw',tags='bubble')
        c.create_text(bx+42*bs,by+42*bs,text=f'{int(p)}%',fill=t['bubble_text'],
                      font=('Segoe UI',-max(1,round(14*bs*96/72)),'bold'),tags='bubble')
        self.draw_bubble_close()

    def close_card(self):
        self.down = None
        self.expanded = False
        if self.colors_open:
            self.mobile_url=None
            self.set_color_panel(False)
        elif getattr(self,'mobile_url',None):
            self.mobile_url=None
            exit_view(self,self.resize)
        else:
            exit_view(self,self.draw)

    def draw_bubble_close(self):
        c = self.canvas
        c.delete('bubble-close')
        if not self.bubble_hover:
            return
        s = self.layout['bubble']
        x = self.layout['bubble_x']+69*s
        y = self.layout['bubble_y']-8*s
        self.close_image = tk.PhotoImage(data=rounded_png(22*s,22*s,11*s,
            self.theme['background'],self.theme['border'],stroke=s))
        c.create_image(x,y,image=self.close_image,anchor='center',tags='bubble-close')
        c.create_text(x,y,text='×',fill=self.theme['foreground'],
                      font=('Segoe UI',-max(1,round(11*s*96/72)),'bold'),tags='bubble-close')

    def defer_hide_bubble_close(self, event=None):
        if self.close_hide_job is not None:
            self.root.after_cancel(self.close_hide_job)
        self.close_hide_job = self.root.after(250, self.hide_bubble_close)

    def hover_bubble(self, event):
        if self.close_hide_job is not None:
            self.root.after_cancel(self.close_hide_job)
            self.close_hide_job = None
        bs = self.layout['bubble']
        x = (event.x-self.layout['bubble_x'])/bs
        y = (event.y-self.layout['bubble_y'])/bs
        over_close = (x-69)**2+(y+8)**2 <= 16**2
        visible = over_close or (x-42)**2+(y-42)**2 <= 42**2
        if visible != self.bubble_hover:
            self.bubble_hover = visible
            self.draw_bubble_close()
        if visible:
            self.canvas.configure(cursor='hand2')

    def hide_bubble_close(self, event=None):
        self.close_hide_job = None
        self.bubble_hover = False
        self.canvas.delete('bubble-close')

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
            if self.expanded:self.close_card()
            else:
                self.expanded=True
                enter_view(self,self.draw)
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

    def reset_theme(self):
        self.tooltip.hide()
        try:
            theme = reset_colors()
        except OSError as error:
            from tkinter import messagebox
            messagebox.showerror(tr('Redefinir cores'),tr('Não foi possível salvar as cores: {error}',error=error),parent=self.root)
            return
        self.apply_colors(theme)

    def edit_colors(self):
        self.expanded = True
        self.set_color_panel(not self.colors_open)

    def resize(self):
        old_width, old_height = self.width, self.height
        self.layout = geometry(self.scale,self.sizes,self.colors_open and self.expanded)
        self.width,self.height = self.layout['width'],self.layout['height']
        x = max(0,min(self.root.winfo_x()+old_width-self.width,
                      self.root.winfo_screenwidth()-self.width))
        y = max(0,min(self.root.winfo_y()+old_height-self.height,
                      self.root.winfo_screenheight()-self.height))
        self.root.geometry(f'{self.width}x{self.height}+{x}+{y}')
        self.draw()

    def change_size(self,role,size):
        try:
            self.sizes = save_size(role,size)
        except OSError as error:
            from tkinter import messagebox
            messagebox.showerror(tr('Tamanhos'),tr('Não foi possível salvar: {error}',error=error),parent=self.root)
            return
        self.resize()

    def set_color_panel(self,visible):
        self.colors_open = visible
        self.resize()

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
        self.tooltip.show(tr(descriptions[key]),event.x_root,event.y_root)

    def hide_tooltip(self):
        self.canvas.configure(cursor='')
        self.tooltip.hide()

    def refresh(self):
        sizes = load_sizes()
        if sizes != self.sizes:
            self.sizes = sizes
            self.resize()
        theme = load_colors()
        if theme != self.theme:
            self.apply_colors(theme)
        try:
            data = json.loads(self.state.read_text(encoding='utf-8'))
            if data.get('dismissed') and data.get('status') == 'Concluído' and data.get('percent') == 100:
                self.root.destroy()
                return
            current_eta = eta_text(data)
            current_progress = round(displayed_progress(data),1)
            if (data != self.data or current_eta != getattr(self,'last_eta',None)
                    or current_progress != getattr(self,'last_progress',None)):
                self.data = data
                self.last_eta = current_eta
                self.last_progress = current_progress
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
