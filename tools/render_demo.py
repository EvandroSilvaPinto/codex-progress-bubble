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
    text(58, 116, 'Your agent works.', 30, bold=True)
    text(58, 159, 'You stay in the loop.', 30, bold=True)
    text(58, 223, 'Codex · Claude Code · Antigravity', 15, MUTED)
    text(58, 254, 'Smooth estimates. Progress in view.', 16, MUTED)
    caption = ('Parallel tasks, bubbles side by side.' if complete and not expanded else
               'Delivered. Ready for your next request.' if complete else
               'Five colors. Your combination.' if palette else
               'Click to open the progress card.' if not expanded else
               'Clear status. Keep your focus.')
    text(58, 354, caption, 16, GREEN if complete else FG)
    text(58, 489, 'Illustrative demo · time-based estimated progress', 12, MUTED)
    y = 122
    if expanded:
        box((518, y, 902, y+282), 22, CARD, '#2b374d')
        text(542, y+18, 'PROGRESS', 11, MUTED)
        if palette:
            text(704, y+18, 'Reset colors', 11, ACCENT)
        text(819, y+18, 'Colors', 12, MUTED)
        text(875, y+15, '×', 18, MUTED)
        text(542, y+53, 'Preparing report', 21, bold=True)
        text(542, y+95, 'Completed' if complete else 'In progress', 13, color)
        text(542, y+126, f'{percent}%', 36, bold=True)
        text(650, y+147, 'estimated progress', 12, MUTED)
        box((542, y+182, 877, y+190), 4, TRACK)
        box((542, y+182, 542+335*percent/100, y+190), 4, color)
        message = ('Report delivered and verified.' if complete else
                   'Reviewing the content.' if percent > 60 else 'Organizing the information.')
        text(542, y+209, message, 13, '#c5cfdf')
        text(818, y+95, 'Sizes', 10, ACCENT)
        if not complete:
            text(542, y+250, 'Less than 1 min' if percent > 60 else 'About 3 min left', 11, ACCENT)
        text(768, y+250, 'Open chat ↗', 12, ACCENT)
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
    if complete and not expanded:
        second = (710*SCALE,417*SCALE,790*SCALE,497*SCALE)
        d.ellipse(second,fill=CARD)
        arc = (716*SCALE,423*SCALE,784*SCALE,491*SCALE)
        d.arc(arc,0,360,fill=TRACK,width=5*SCALE)
        d.arc(arc,-90,36,fill=ACCENT,width=5*SCALE)
        text(750,457,'35%',20,anchor='mm',bold=True)
        d.ellipse((873*SCALE,396*SCALE,895*SCALE,418*SCALE),
                  fill=CARD,outline=MUTED,width=SCALE)
        text(884,407,'×',14,anchor='mm')
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
