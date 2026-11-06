"""Usage: python Frontend/scripts/themeify.py Frontend/src

Replace hard-coded colours in the app CSS with variables and generate a dark palette.

Dark values keep each colour's hue and flip its lightness, so text/background contrast is preserved.
"""
import colorsys, re, sys, os
SRC = sys.argv[1]
FILES = ['index.css', 'auth.css', 'features.css', 'pages/model-insights.css']
HEX = re.compile(r'#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b')
RGBA = re.compile(r'rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*([\d.]+)\s*)?\)')

def to_rgb(h):
    h = h.lower()
    if len(h) == 3: h = ''.join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

def dark(rgb):
    r, g, b = (c / 255 for c in rgb)
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    if l >= 0.80:            # light surfaces and tints -> deep teal-navy surfaces
        nl = 0.075 + (1 - l) * 0.85
        ns = min(s, 0.45) * (0.55 if l > 0.95 else 0.8)
        if s < 0.08: h, ns = 0.53, 0.30   # pure greys/white pick up the brand hue
    elif l <= 0.35:          # dark ink -> light ink
        nl = 0.93 - l * 0.45
        ns = min(s, 0.35)
    else:                    # mid tones (brand, status colours): lift a little for dark backgrounds
        nl = min(0.78, l + 0.10)
        ns = s
    r2, g2, b2 = colorsys.hls_to_rgb(h, nl, ns)
    return tuple(round(c * 255) for c in (r2, g2, b2))

hexname = lambda rgb: '%02x%02x%02x' % rgb
tokens = {}   # var name -> (light, dark)

def hex_sub(m):
    rgb = to_rgb(m.group(1))
    name = f'--c-{hexname(rgb)}'
    tokens[name] = ('#' + hexname(rgb), '#' + hexname(dark(rgb)))
    return f'var({name})'

def rgba_sub(m):
    rgb = tuple(int(m.group(i)) for i in (1, 2, 3))
    a = m.group(4)
    # Shadows (dark rgba) stay as they are; only light overlays need a dark counterpart.
    if sum(rgb) < 300: return m.group(0)
    d = dark(rgb)
    alpha = a if a is not None else '1'
    name = f'--c-{hexname(rgb)}-a{alpha.replace(".", "")}'
    tokens[name] = (f'rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, {alpha})', f'rgba({d[0]}, {d[1]}, {d[2]}, {alpha})')
    return f'var({name})'

for f in FILES:
    path = os.path.join(SRC, f)
    css = open(path).read()
    # Leave url(...) and the font @import alone.
    parts = re.split(r'(url\([^)]*\)|@import[^;]*;)', css)
    out = []
    for i, part in enumerate(parts):
        if i % 2 == 1: out.append(part); continue
        part = RGBA.sub(rgba_sub, part)
        part = HEX.sub(hex_sub, part)
        out.append(part)
    open(path, 'w').write(''.join(out))

lines = ['/* Generated colour tokens: light values are the original design, dark values are derived',
         '   (same hue, flipped lightness). Hand-tuned overrides live in theme.css. */',
         ':root {']
lines += [f'  {k}: {v[0]};' for k, v in sorted(tokens.items())]
lines += ['}', '', ':root[data-theme="dark"] {']
lines += [f'  {k}: {v[1]};' for k, v in sorted(tokens.items())]
lines += ['}', '']
open(os.path.join(SRC, 'theme-colors.css'), 'w').write('\n'.join(lines))
print(len(tokens), 'tokens')
