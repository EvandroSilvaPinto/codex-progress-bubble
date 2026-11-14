"""Per-user, independently editable colors shared by bubbles and HTML reports."""
import json
import os
from pathlib import Path
import re

DEFAULTS = dict(background='#101827',foreground='#f3f5ff',muted='#8897ae',
    message='#c5cfdf',border='#2b374d',track='#263149',bar='#8b9dff',
    ring='#8b9dff',bubble_background='#101827',bubble_text='#f3f5ff',
    links='#8b9dff',ongoing='#8b9dff',complete='#58d9b0',error='#ff8b9d',waiting='#f3c57d')
LABELS = ('Fundo do cartão','Texto principal','Texto secundário','Mensagem','Bordas',
    'Trilha sem progresso','Barra em andamento','Anel em andamento','Fundo da bolinha',
    'Percentual da bolinha','Links e tempo restante','Estado: em andamento',
    'Estado: concluído','Estado: falha','Estado: espera/interrompido')
MAIN_COLORS = (('background','Fundo'),('foreground','Texto'),('ring','Progresso'),
               ('links','Detalhes'),('complete','Estados'))


def set_main_color(theme,key,value):
    if key not in dict(MAIN_COLORS):
        raise ValueError('Cor principal desconhecida')
    result = normalize(dict(theme,**{key:value}))
    value = result[key]
    def mix(a,b,weight):
        return '#'+''.join(f'{round(int(a[i:i+2],16)*(1-weight)+int(b[i:i+2],16)*weight):02x}'
                           for i in (1,3,5))
    if key == 'background':
        result['bubble_background'] = value
    if key == 'foreground':
        result['bubble_text'] = value
    if key in ('background','foreground'):
        for role,weight in (('muted',.65),('message',.85),('border',.22),('track',.16)):
            result[role] = mix(result['background'],result['foreground'],weight)
    if key == 'ring':
        result.update(bar=value,ongoing=value)
    if key == 'complete':
        result.update(error=value,waiting=value)
    return normalize(result)


def config_path():
    base = os.environ.get('APPDATA') or os.environ.get('XDG_CONFIG_HOME')
    return (Path(base) if base else Path.home()/'.config')/'ProgressBubble/colors.json'


def normalize(values):
    result = dict(DEFAULTS)
    for key in DEFAULTS:
        value = values.get(key,DEFAULTS[key])
        if not isinstance(value,str) or not re.fullmatch(r'#[0-9a-fA-F]{6}',value):
            raise ValueError(f'{key}: use uma cor hexadecimal como #F3A9CE')
        if value.lower() == '#010203':
            raise ValueError('#010203 é reservado para a transparência da janela')
        result[key] = value.lower()
    return result


def load_colors(path=None):
    try:
        return normalize(json.loads((path or config_path()).read_text(encoding='utf-8')))
    except (OSError,ValueError,AttributeError):
        return dict(DEFAULTS)


def save_colors(values,path=None):
    result = normalize(values)
    target = path or config_path()
    target.parent.mkdir(parents=True,exist_ok=True)
    temp = target.with_suffix('.tmp')
    temp.write_text(json.dumps(result,indent=2),encoding='utf-8')
    os.replace(temp,target)


def reset_colors(path=None):
    """Restore every role, including colors derived from the five main groups."""
    theme = dict(DEFAULTS)
    save_colors(theme, path)
    return theme


def css(theme,status='Em andamento'):
    state = theme[{'Concluído':'complete','Falha':'error','Interrompido':'waiting',
                   'Aguardando informação':'waiting'}.get(status,'ongoing')]
    bar = theme['bar'] if status=='Em andamento' else state
    return (f"body,main{{background:{theme['background']}!important;color:{theme['foreground']}!important}}"
        f"main{{border-color:{theme['border']}!important}}.eyebrow,.value span{{color:{theme['muted']}!important}}"
        f".message{{color:{theme['message']}!important}}#eta,a{{color:{theme['links']}!important}}"
        f"progress,progress::-webkit-progress-bar{{background:{theme['track']}!important}}"
        f"progress::-webkit-progress-value{{background:{bar}!important}}"
        f"progress::-moz-progress-bar{{background:{bar}!important}}"
        f".status{{color:{state}!important;background:transparent!important}}")


def update_html(path,theme):
    if not path.is_file():
        return
    page = path.read_text(encoding='utf-8')
    page = re.sub(r'<style id="custom-colors">.*?</style>','',page,flags=re.S)
    try:
        state = json.loads(path.with_suffix('.json').read_text(encoding='utf-8')).get('status')
    except (OSError,ValueError,AttributeError):
        state = 'Em andamento'
    page = page.replace('</head>',f'<style id="custom-colors">{css(theme,state)}</style></head>')
    temp = path.with_suffix('.colors.tmp')
    temp.write_text(page,encoding='utf-8')
    os.replace(temp,path)


def contrast(a,b):
    def luminance(color):
        rgb = [int(color[i:i+2],16)/255 for i in (1,3,5)]
        return sum((v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4)*w
                   for v,w in zip(rgb,(.2126,.7152,.0722)))
    low,high = sorted((luminance(a),luminance(b)))
    return (high+.05)/(low+.05)
