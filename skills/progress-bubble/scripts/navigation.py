"""Resolve a known conversation origin without inventing agent-specific links."""
import os
from pathlib import Path
import subprocess
from urllib.parse import urlsplit
from uuid import UUID
import webbrowser


def validate_url(url):
    if any(c.isspace() for c in url):
        raise ValueError('Conversation URL must not contain whitespace')
    parts=urlsplit(url)
    if parts.scheme in ('https','http') and parts.hostname and not parts.username and not parts.password:
        return url
    if parts.scheme=='codex' and parts.netloc=='threads' and not parts.query and not parts.fragment:
        UUID(parts.path.lstrip('/'))
        return url
    raise ValueError('Use a known HTTP(S) conversation URL or codex://threads/<UUID>')


def conversation_url(explicit, previous):
    if explicit == 'none':
        return None
    url=explicit or previous.get('conversation_url')
    if url:
        return validate_url(url)
    thread=os.environ.get('CODEX_THREAD_ID')
    if thread:
        try:
            return 'codex://threads/'+str(UUID(thread))
        except ValueError:
            pass
    return None


def open_conversation(data):
    try:
        url=validate_url(data['conversation_url'])
        app=Path(data.get('conversation_app') or '')
        if url.startswith('codex:') and app.is_file() and app.name.lower() in ('chatgpt.exe','codex.exe'):
            subprocess.Popen([str(app),url],creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),
                             stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            return True
        if os.name=='nt':
            os.startfile(url)
            return True
        return webbrowser.open(url)
    except (OSError,ValueError,KeyError):
        return False
