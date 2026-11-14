"""Render the illustrative README animation. Requires Pillow for asset generation only."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SCALE = 2
W, H = 960, 540
BG, CARD, FG = '#0a101d', '#101827', '#f3f5ff'
MUTED, TRACK, ACCENT, GREEN = '#8897ae', '#263149', '#8b9dff', '#58d9b0'
FONT = Path('C:/Windows/Fonts/segoeui.ttf')
BOLD = Path('C:/Windows/Fonts/segoeuib.ttf')


def frame(percent, expanded=True, palette=False, complete=False):
    im = Image.new('RGB', (W*SCALE, H*SCALE), BG)
    d = ImageDraw.Draw(im)

    def text(x, y, value, size=16, color=FG, bold=False, anchor=None):
        font = ImageFont.truetype(str(BOLD if bold else FONT), size*SCALE)
        d.text((x*SCALE, y*SCALE), value, font=font, fill=color, anchor=anchor)

    def box(bounds, radius, fill, outline=None):
        d.rounded_rectangle(tuple(v*SCALE for v in bounds), radius*SCALE,
                            fill=fill, outline=outline, width=SCALE)

    color = GREEN if complete else ACCENT
    text(58, 76, 'PROGRESS BUBBLE', 13, GREEN, True)
    text(58, 116, 'Seu agente trabalha.', 30, bold=True)
    text(58, 159, 'Você acompanha.', 30, bold=True)
    text(58, 223, 'Codex · Claude Code · Antigravity', 15, MUTED)
    text(58, 254, 'Progresso e tempo restante à vista.', 16, MUTED)
    caption = ('Entrega concluída. Até o próximo pedido.' if complete else
               'Cinco cores. A sua combinação.' if palette else
               'Clique para abrir o acompanhamento.' if not expanded else
               'Status claro, sem perder o foco.')
    text(58, 354, caption, 16, GREEN if complete else FG)
    text(58, 489, 'Demonstração ilustrativa · duração e progresso estimados', 12, MUTED)
    y = 122
    if expanded:
        box((518, y, 902, y+282), 22, CARD, '#2b374d')
        text(542, y+18, 'ACOMPANHAMENTO', 11, MUTED)
        text(819, y+18, 'Cores', 12, MUTED)
        text(875, y+15, '×', 18, MUTED)
        text(542, y+53, 'Preparando relatório', 21, bold=True)
        text(542, y+95, 'Concluído' if complete else 'Em andamento', 13, color)
        text(542, y+126, f'{percent}%', 36, bold=True)
        text(650, y+147, 'progresso estimado', 12, MUTED)
        box((542, y+182, 877, y+190), 4, TRACK)
        box((542, y+182, 542+335*percent/100, y+190), 4, color)
        message = ('Relatório entregue e verificado.' if complete else
                   'Revisando o conteúdo.' if percent > 60 else 'Organizando as informações.')
        text(542, y+209, message, 13, '#c5cfdf')
        if not complete:
            text(542, y+250, 'Menos de 1 min' if percent > 60 else 'Faltam cerca de 3 min', 11, ACCENT)
        text(768, y+250, 'Abrir conversa ↗', 12, ACCENT)
    if palette and expanded:
        box((518, 48, 902, 111), 20, CARD, '#2b374d')
        for x, c in zip(range(586, 835, 62), (CARD, FG, ACCENT, '#f0a8d0', GREEN)):
            d.ellipse(((x-16)*SCALE, 64*SCALE, (x+16)*SCALE, 96*SCALE),
                      fill=c, outline=FG, width=SCALE)
    cx, cy, r = 857, 457, 40
    d.ellipse(((cx-r)*SCALE, (cy-r)*SCALE, (cx+r)*SCALE, (cy+r)*SCALE), fill=CARD)
    bounds = ((cx-r+6)*SCALE, (cy-r+6)*SCALE, (cx+r-6)*SCALE, (cy+r-6)*SCALE)
    d.arc(bounds, 0, 360, fill=TRACK, width=5*SCALE)
    d.arc(bounds, -90, -90+3.6*percent, fill=color, width=5*SCALE)
    text(cx, cy, f'{percent}%', 20, anchor='mm', bold=True)
    return im.resize((W, H), Image.Resampling.LANCZOS)


scenes = [(15, False, False, False, 1400), (15, True, False, False, 1300)]
scenes += [(p, True, False, False, 160) for p in range(20, 66, 5)]
scenes += [(65, True, True, False, 1800)]
scenes += [(p, True, False, False, 200) for p in range(70, 100, 5)]
scenes += [(100, True, False, True, 2400), (100, False, False, True, 1300)]
frames = [frame(*scene[:4]) for scene in scenes]
palette = frames[12].quantize(colors=128)
frames = [f.quantize(palette=palette, dither=Image.Dither.NONE) for f in frames]
target = ROOT/'assets/demo.gif'
frames[0].save(target, save_all=True, append_images=frames[1:],
               duration=[s[4] for s in scenes], loop=0, optimize=True, disposal=2)
print(f'{target}: {target.stat().st_size:,} bytes, {len(frames)} frames')
