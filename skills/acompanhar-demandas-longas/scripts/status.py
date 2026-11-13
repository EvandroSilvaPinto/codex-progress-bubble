"""Save HTML + JSON status and optionally open the Windows floating bubble."""
import argparse
import html
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime


def save(path, content):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(content, encoding='utf-8')
    os.replace(temporary, path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--title', required=True)
    parser.add_argument('--percent', type=int, required=True)
    parser.add_argument('--status', default='Em andamento', choices=[
        'Em andamento', 'Aguardando informação', 'Concluído', 'Interrompido', 'Falha'])
    parser.add_argument('--message', required=True)
    parser.add_argument('--open', action='store_true')
    args = parser.parse_args()
    if not 0 <= args.percent <= 100:
        parser.error('Percentual deve estar entre 0 e 100')
    if args.percent == 100 and args.status != 'Concluído':
        parser.error('100% é reservado para Concluído')
    if args.status == 'Concluído' and args.percent != 100:
        parser.error('Concluído requer 100%')
    target = args.output.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now().astimezone().strftime('%d/%m/%Y %H:%M:%S %z')
    data = dict(title=args.title, percent=args.percent, status=args.status,
                message=args.message, updated=now, html=str(target))
    escaped = {key: html.escape(str(value)) for key, value in data.items()}
    refresh = '' if args.status in ('Concluído', 'Interrompido', 'Falha') else '<meta http-equiv="refresh" content="20">'
    page = f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">{refresh}
<title>{escaped['title']}</title><style>
*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(ellipse at 20% 0%,#202c51,transparent 55%),#080e19;color:#f1f4ff;font:16px/1.6 'Segoe UI',system-ui;display:grid;min-height:100vh;place-items:center;padding:24px}}
main{{width:min(100%,580px);padding:clamp(24px,6vw,48px);background:linear-gradient(145deg,#172237,#101827);border:1px solid #2b374d;border-radius:28px;box-shadow:0 32px 100px #0006}}
.eyebrow{{font-size:11px;letter-spacing:.2em;color:#8897ae;font-weight:600}}h1{{font-size:clamp(23px,5vw,32px);line-height:1.25;margin:16px 0 24px}}.status{{display:inline-block;border:1px solid #6379c855;background:#8b9dff12;color:#b9c3ff;padding:5px 12px;border-radius:20px;font-size:13px;margin-bottom:30px}}
progress{{display:block;appearance:none;width:100%;height:10px;border:0;border-radius:20px;overflow:hidden;background:#27334a;accent-color:#8b9dff}}progress::-webkit-progress-bar{{background:#27334a}}progress::-webkit-progress-value{{background:linear-gradient(90deg,#7c83ff,#9db9ff);border-radius:20px}}progress::-moz-progress-bar{{background:#8b9dff}}.value{{font-size:38px;font-weight:650;margin:14px 0 24px}}.value span{{font-size:13px;font-weight:400;color:#8897ae;margin-left:10px}}.message{{color:#c5cfdf}}footer{{margin-top:30px;padding-top:18px;border-top:1px solid #29354a;color:#8897ae;font-size:12px}}
</style></head><body><main><div class="eyebrow">ACOMPANHAMENTO</div><h1>{escaped['title']}</h1><div class="status">● {escaped['status']}</div>
<progress aria-label="Progresso estimado" max="100" value="{args.percent}"></progress>
<p class="value">{args.percent}%<span>progresso estimado</span></p><p class="message">{escaped['message']}</p>
<footer>Última atualização · {escaped['updated']}</footer></main></body></html>'''
    save(target, page)
    state = target.with_suffix('.json')
    save(state, json.dumps(data, ensure_ascii=False))
    if args.open and os.name == 'nt':
        script = Path(__file__).with_name('bubble.py')
        pythonw = Path(sys.executable).with_name('pythonw.exe')
        subprocess.Popen([str(pythonw), str(script), str(state)],
                         creationflags=subprocess.CREATE_NO_WINDOW,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(target)


if __name__ == '__main__':
    main()
