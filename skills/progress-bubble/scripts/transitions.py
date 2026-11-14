"""Short card-only translations; preserve QR pixels and the bubble position."""
import ctypes
import os
import time
import tkinter as tk


def animations_enabled():
    if os.name=='nt':
        try:
            enabled=ctypes.c_int(1)
            if ctypes.WinDLL('user32').SystemParametersInfoW(0x1042,0,ctypes.byref(enabled),0):
                return bool(enabled.value)
        except (AttributeError,OSError):
            pass
    return True


class PanelMotion:
    def __init__(self,root,canvas,enabled=True,clock=time.perf_counter):
        self.root,self.canvas,self.enabled,self.clock=root,canvas,enabled,clock
        self.job=None;self.items=();self.offset=(0,0);self.done=None

    def cancel(self):
        if self.job is not None:
            try:self.root.after_cancel(self.job)
            except tk.TclError:pass
        self.job=None
        try:
            for item in self.items:self.canvas.move(item,-self.offset[0],-self.offset[1])
        except tk.TclError:pass
        self.items=();self.offset=(0,0);self.done=None

    def enter(self,draw):
        self.cancel();draw();self._start(False,None)

    def exit(self,draw):
        self.cancel();self._start(True,draw)

    def _start(self,closing,done):
        self.items=tuple(self.canvas.find_withtag('panel'))
        if not self.enabled or not self.items:
            if done:done()
            return
        self.closing=closing;self.done=done;self.started=self.clock();self._step()

    def _step(self):
        self.job=None
        progress=min(1,max(0,(self.clock()-self.started)/.16))
        eased=1-(1-progress)**3
        target=(0,round(8*eased)) if self.closing else (round(8*(1-eased)),0)
        try:
            for item in self.items:self.canvas.move(item,target[0]-self.offset[0],target[1]-self.offset[1])
        except tk.TclError:
            self.cancel();return
        self.offset=target
        if progress<1:self.job=self.root.after(16,self._step)
        else:
            done=self.done;self.cancel()
            if done:done()


def enter_view(app,draw):
    motion=getattr(app,'motion',None)
    if motion is None:draw()
    else:motion.enter(draw)


def exit_view(app,draw):
    motion=getattr(app,'motion',None)
    if motion is None:draw()
    else:motion.exit(draw)
