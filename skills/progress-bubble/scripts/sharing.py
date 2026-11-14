"""Nonblocking desktop entry point for optional, reader-only QR sharing."""
import json
import os
from pathlib import Path
import queue
import threading
from tkinter import messagebox
from native_qr import show_qr
from i18n import t
from web_client import load_secret,secret_path,sync_task,WebError


def service_url():
    if os.environ.get('PROGRESS_BUBBLE_WEB_URL'):
        return os.environ['PROGRESS_BUBBLE_WEB_URL']
    try:
        return json.loads((Path(__file__).parent.parent/'web-service.json').read_text(encoding='utf-8')).get('url')
    except (OSError,ValueError,AttributeError):
        return None


def share_task(app):
    if getattr(app,'sharing_in_flight',False):
        return
    try:
        record=load_secret(secret_path(app.state))
    except WebError:
        record=None
    if record and record.get('created') and not record.get('revocation_pending'):
        show_qr(app,record['endpoint']+'/#'+record['id']+'.'+record['read_token'])
        return
    endpoint=service_url()
    if not endpoint:
        messagebox.showinfo(t('Compartilhar acompanhamento'),t('Serviço web ainda não configurado.'),parent=app.root)
        return
    if not messagebox.askyesno(t('Compartilhar acompanhamento'),t('Enviar somente título, mensagem e progresso para gerar um link temporário? Quem tiver o link poderá visualizar esta demanda.'),parent=app.root):
        return
    app.sharing_in_flight=True
    results=queue.Queue()
    snapshot=dict(app.data)
    def execute():
        try:results.put(sync_task(snapshot,app.state,endpoint,True))
        except Exception:results.put(None)
    def check():
        try:
            info=results.get_nowait()
        except queue.Empty:
            app.root.after(100,check)
            return
        app.sharing_in_flight=False
        if info and info.get('url') and not info.get('error'):
            show_qr(app,info['url'])
        else:
            messagebox.showwarning(t('Compartilhar acompanhamento'),t('Não foi possível sincronizar. O acompanhamento local continua disponível.'),parent=app.root)
    threading.Thread(target=execute,daemon=True).start()
    app.root.after(100,check)
