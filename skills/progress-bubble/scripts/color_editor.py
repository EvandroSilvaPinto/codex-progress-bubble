"""One native palette opened from one of the five main color bubbles."""
from tkinter import colorchooser, messagebox
from colors import MAIN_COLORS, contrast, save_colors, set_main_color


def choose_color(parent,theme,key,on_saved):
    label = dict(MAIN_COLORS)[key]
    selected = colorchooser.askcolor(theme[key],parent=parent,title=f'Cor: {label}')[1]
    if not selected:
        return
    try:
        result = set_main_color(theme,key,selected)
        save_colors(result)
        on_saved(result)
        text_ratio = min(contrast(result[k],result['background'])
                         for k in ('foreground','muted','message','links'))
        if text_ratio < 4.5 or contrast(result['ring'],result['track']) < 3:
            messagebox.showwarning('Contraste baixo',
                'Cor aplicada. Algumas combinações podem ficar difíceis de ler.\n'
                'Você pode ajustar Fundo, Texto, Progresso ou Detalhes.',parent=parent)
    except (ValueError,OSError) as error:
        messagebox.showerror('Não foi possível salvar a cor',str(error),parent=parent)
