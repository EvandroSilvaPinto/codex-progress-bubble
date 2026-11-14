"""Save HTML + JSON status and optionally open the Windows floating bubble."""
import argparse
import html
import json
import os
import math
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timedelta
from timing import eta_text
from navigation import conversation_url
from colors import load_colors, css
from i18n import t, system_language


def save(path, content):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(content, encoding='utf-8')
    os.replace(temporary, path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--title')
    parser.add_argument('--percent', type=int)
    parser.add_argument('--status', default='Em andamento', choices=[
        'Em andamento', 'Aguardando informação', 'Concluído', 'Interrompido', 'Falha'])
    parser.add_argument('--message')
    parser.add_argument('--conversation-url', help='Known origin chat URL; Codex can use CODEX_THREAD_ID')
    parser.add_argument('--conversation-app', type=Path, help='Installed Codex/ChatGPT executable if Windows has no URL handler')
    parser.add_argument('--eta-minutes', type=float, help='Estimated remaining minutes, supplied by the agent')
    parser.add_argument('--dismiss-completed', action='store_true')
    parser.add_argument('--open', action='store_true')
    parser.add_argument('--edit-colors', action='store_true', help='Open the native color editor with the bubble')
    args = parser.parse_args()
    if args.dismiss_completed:
        state = args.output.resolve().with_suffix('.json')
        if state.exists():
            data = json.loads(state.read_text(encoding='utf-8'))
            if data.get('status') == 'Concluído' and data.get('percent') == 100:
                data['dismissed'] = True
                save(state, json.dumps(data, ensure_ascii=False))
        return
    if any(value is None for value in (args.title,args.percent,args.message)):
        parser.error('--title, --percent and --message are required for updates')
    if not 0 <= args.percent <= 100:
        parser.error('Percentual deve estar entre 0 e 100')
    if args.percent == 100 and args.status != 'Concluído':
        parser.error('100% é reservado para Concluído')
    if args.status == 'Concluído' and args.percent != 100:
        parser.error('Concluído requer 100%')
    if args.eta_minutes is not None and (not math.isfinite(args.eta_minutes) or not 0 < args.eta_minutes <= 525600):
        parser.error('--eta-minutes must be finite, positive and no greater than one year')
    target = args.output.resolve()
    previous = {}
    if target.with_suffix('.json').is_file():
        try:
            previous = json.loads(target.with_suffix('.json').read_text(encoding='utf-8'))
        except (OSError,ValueError):
            pass
    try:
        origin_url = conversation_url(args.conversation_url,previous)
    except ValueError as error:
        parser.error(str(error))
    app = args.conversation_app
    if app and (not app.is_file() or app.name.lower() not in ('chatgpt.exe','codex.exe')):
        parser.error('--conversation-app must point to the installed ChatGPT.exe or Codex.exe')
    target.parent.mkdir(parents=True, exist_ok=True)
    moment = datetime.now().astimezone()
    now = moment.strftime('%d/%m/%Y %H:%M:%S %z')
    eta_at = None
    if args.status == 'Em andamento':
        if args.eta_minutes is not None:
            eta_at = (moment+timedelta(minutes=args.eta_minutes)).isoformat()
        elif target.with_suffix('.json').is_file():
            try:
                eta_at = json.loads(target.with_suffix('.json').read_text(encoding='utf-8')).get('eta_at')
            except (OSError,ValueError):
                pass
    language = system_language()
    data = dict(title=args.title, percent=args.percent, status=args.status,language=language,
                message=args.message, updated=now, html=str(target), eta_at=eta_at,
                conversation_url=origin_url,conversation_app=str(app.resolve()) if app else previous.get('conversation_app'))
    eta = html.escape(eta_text(data))
    escaped = {key: html.escape(str(value)) for key, value in data.items()}
    escaped['status'] = html.escape(t(args.status,language))
    labels = {key:html.escape(t(value,language)) for key,value in dict(
        tracking='ACOMPANHAMENTO',progress='Progresso estimado',
        estimated='progresso estimado',chat='Abrir conversa ↗').items()}
    eta_labels = json.dumps({key:t(value,language) for key,value in dict(
        overdue='Recalculando previsão',short='Menos de 1 min',
        remaining='Faltam cerca de {minutes} min').items()},ensure_ascii=False)
    refresh = '' if args.status in ('Concluído', 'Interrompido', 'Falha') else '<meta http-equiv="refresh" content="1">'
    page = f'''<!doctype html><html lang="{'pt-BR' if language=='pt' else 'en'}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">{refresh}
<title>{escaped['title']}</title><style>
*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(ellipse at 20% 0%,#202c51,transparent 55%),#080e19;color:#f1f4ff;font:16px/1.6 'Segoe UI',system-ui;display:grid;min-height:100vh;place-items:center;padding:24px}}
main{{width:min(100%,580px);padding:clamp(24px,6vw,48px);background:linear-gradient(145deg,#172237,#101827);border:1px solid #2b374d;border-radius:28px;box-shadow:0 32px 100px #0006}}
.eyebrow{{font-size:11px;letter-spacing:.2em;color:#8897ae;font-weight:600}}h1{{font-size:clamp(23px,5vw,32px);line-height:1.25;margin:16px 0 24px}}.status{{display:inline-block;border:1px solid #6379c855;background:#8b9dff12;color:#b9c3ff;padding:5px 12px;border-radius:20px;font-size:13px;margin-bottom:30px}}
progress{{display:block;appearance:none;width:100%;height:10px;border:0;border-radius:20px;overflow:hidden;background:#27334a;accent-color:#8b9dff}}progress::-webkit-progress-bar{{background:#27334a}}progress::-webkit-progress-value{{background:linear-gradient(90deg,#7c83ff,#9db9ff);border-radius:20px}}progress::-moz-progress-bar{{background:#8b9dff}}.value{{font-size:38px;font-weight:650;margin:14px 0 24px}}.value span{{font-size:13px;font-weight:400;color:#8897ae;margin-left:10px}}.message{{color:#c5cfdf}}footer{{margin-top:30px;padding-top:18px;border-top:1px solid #29354a;color:#8897ae;font-size:12px}}
</style><style id="custom-colors">{css(load_colors(),args.status)}</style></head><body><main><div class="eyebrow">{labels['tracking']}</div><h1>{escaped['title']}</h1><div class="status">● {escaped['status']}</div>
<progress aria-label="{labels['progress']}" max="100" value="{args.percent}"></progress>
<p class="value">{args.percent}%<span>{labels['estimated']}</span></p><p class="message">{escaped['message']}</p>
<p id="eta" data-finish="{escaped['eta_at'] if eta_at else ''}" style="color:#9aadff;font-size:13px;font-weight:400">{eta}</p>
{('<a href="'+escaped['conversation_url']+'" style="color:#9aadff;font-size:13px">'+labels['chat']+'</a>') if origin_url else ''}
<script>
const el=document.getElementById('eta'), words={eta_labels};
function refreshEta(){{
  if(!el.dataset.finish)return;
  const finish=new Date(el.dataset.finish), left=finish-Date.now();
  el.textContent=left<=0?words.overdue:left<60000?words.short:words.remaining.replace('{{minutes}}',Math.ceil(left/60000));
}}
refreshEta();setInterval(refreshEta,1000);
</script>
</main></body></html>'''
    save(target, page)
    state = target.with_suffix('.json')
    save(state, json.dumps(data, ensure_ascii=False))
    if (args.open or args.edit_colors) and os.name == 'nt':
        script = Path(__file__).with_name('bubble.py')
        pythonw = Path(sys.executable).with_name('pythonw.exe')
        subprocess.Popen([str(pythonw), str(script), str(state)]+(['--edit-colors'] if args.edit_colors else []),
                         creationflags=subprocess.CREATE_NO_WINDOW,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(target)


if __name__ == '__main__':
    main()
