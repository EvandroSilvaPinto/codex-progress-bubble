"""Independent persistent sizes for the card/palette and the progress bubble."""
import json
import os
from colors import config_path
from i18n import t

FACTORS = {'Pequeno': .85, 'Médio': 1.0, 'Grande': 1.2}
DEFAULTS = {'card': 'Médio', 'bubble': 'Médio'}


def load_sizes(path=None):
    try:
        values = json.loads((path or config_path().with_name('sizes.json')).read_text(encoding='utf-8'))
        return {key: values.get(key) if values.get(key) in FACTORS else value
                for key, value in DEFAULTS.items()}
    except (OSError, ValueError, AttributeError):
        return dict(DEFAULTS)


def save_size(role, size, path=None):
    if role not in DEFAULTS or size not in FACTORS:
        raise ValueError('Tamanho desconhecido')
    target = path or config_path().with_name('sizes.json')
    values = load_sizes(target)
    values[role] = size
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix('.tmp')
    temporary.write_text(json.dumps(values, ensure_ascii=False), encoding='utf-8')
    os.replace(temporary, target)
    return values


def geometry(dpi, sizes, palette=False):
    card = dpi*FACTORS[sizes['card']]
    bubble = dpi*FACTORS[sizes['bubble']]
    offset = 70 if palette else 0
    width = round(max(360*card, 100*bubble))
    height = round((270+offset)*card+90*bubble)
    return dict(card=card, bubble=bubble, offset=offset, width=width, height=height,
                card_x=width-360*card, bubble_x=width-85*bubble,
                bubble_y=height-85*bubble)


def show_size_menu(app, event):
    import tkinter as tk
    previous = getattr(app, 'size_menu', None)
    if previous is not None:
        previous.destroy()
    menu = tk.Menu(app.root, tearoff=False)
    app.size_menu = menu
    for role, label in (('card','Acompanhamento e cores'), ('bubble','Bolinha')):
        submenu = tk.Menu(menu, tearoff=False)
        variable = tk.StringVar(value=app.sizes[role])
        for size in FACTORS:
            submenu.add_radiobutton(label=t(size), value=size, variable=variable,
                                    command=lambda r=role,s=size: app.change_size(r,s))
        menu.add_cascade(label=t(label), menu=submenu)
        # Keep Tk variables alive until the popup closes.
        submenu.size_variable = variable
    try:
        menu.tk_popup(event.x_root, event.y_root)
    finally:
        menu.grab_release()
        # Windows can dispatch the selected command after tk_popup returns.
        # Keep the menu and its Tcl callbacks alive until the next opening.
