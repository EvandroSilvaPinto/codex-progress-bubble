"""Small delayed tooltip for canvas controls."""
import tkinter as tk


class Tooltip:
    def __init__(self,parent):
        self.parent = parent
        self.window = None
        self.pending = None

    def hide(self):
        if self.pending is not None:
            self.parent.after_cancel(self.pending)
            self.pending = None
        if self.window is not None:
            self.window.destroy()
            self.window = None

    def show(self,text,x,y):
        self.hide()
        def display():
            self.pending = None
            self.window = tk.Toplevel(self.parent)
            self.window.withdraw()
            self.window.overrideredirect(True)
            self.window.attributes('-topmost',True)
            tk.Label(self.window,text=text,bg='#202c46',fg='#f3f5ff',
                font=('Segoe UI',9),padx=10,pady=6,justify='left').pack()
            self.window.update_idletasks()
            left = max(0,min(x+12,self.window.winfo_screenwidth()-self.window.winfo_reqwidth()-8))
            top = max(0,min(y+20,self.window.winfo_screenheight()-self.window.winfo_reqheight()-8))
            self.window.geometry(f'+{left}+{top}')
            self.window.deiconify()
        self.pending = self.parent.after(350,display)
