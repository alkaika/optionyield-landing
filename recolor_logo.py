"""
Recolor the OptionYield logo (black + green on white JPG) to the landing page
theme, preserving the original artwork and wordmark font exactly:
  - white background -> transparent
  - black elements   -> theme text color (white on dark / #1A1D20 on light)
  - green elements   -> theme accent (#00E676 dark / #00A846 light),
                        keeping the original gradient shading via per-pixel
                        brightness remapping
Outputs: logo-dark.png, logo-light.png, favicon.png (mark on a rounded tile).
"""
from PIL import Image, ImageDraw
import colorsys
import os

SRC = r"C:\Users\alana\OneDrive\Desktop\Finance Mobile App\Logos\Gemini_Generated_Image_pojf19pojf19pojf.jpg"
OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# Theme targets (must match ThemeContext tokens mirrored in index.html)
THEMES = {
    "dark": {"text": (255, 255, 255), "hue": 152 / 360, "sat": 1.00, "v_lo": 0.60, "v_hi": 0.95},
    "light": {"text": (26, 29, 32), "hue": 146 / 360, "sat": 0.95, "v_lo": 0.42, "v_hi": 0.80},
}


def load_trimmed():
    img = Image.open(SRC).convert("RGB")
    w, h = img.size
    px = img.load()

    def strong_ink(x, y):
        r, g, b = px[x, y]
        return min(r, g, b) < 190  # ignore faint JPEG noise

    # Trim using rows/columns with real ink, not single stray pixels
    minx, miny, maxx, maxy = w, h, -1, -1
    for y in range(h):
        if sum(strong_ink(x, y) for x in range(0, w, 2)) > 2:
            miny = y
            break
    for y in range(h - 1, -1, -1):
        if sum(strong_ink(x, y) for x in range(0, w, 2)) > 2:
            maxy = y
            break
    for x in range(w):
        if sum(strong_ink(x, y) for y in range(0, h, 2)) > 2:
            minx = x
            break
    for x in range(w - 1, -1, -1):
        if sum(strong_ink(x, y) for y in range(0, h, 2)) > 2:
            maxx = x
            break
    return img.crop((minx, miny, maxx + 1, maxy + 1))


def unblend_from_white(r, g, b):
    """Pixel was composited as C over white with some alpha; recover (C, a)."""
    a = (255 - min(r, g, b)) / 255.0
    if a <= 0.03:
        return None, 0.0
    c = [min(255.0, max(0.0, (ch - (1 - a) * 255) / a)) for ch in (r, g, b)]
    return c, a


def is_green_raw(r, g, b):
    """Green-ness judged on the raw pixel so amplified JPEG noise near
    black/white edges can never be classified as logo green."""
    return g > r + 18 and g > b + 18


def build_logo(theme):
    img = load_trimmed()
    w, h = img.size
    src = img.load()

    # Pass 1: brightness range of green pixels for the gradient remap
    vs = []
    for y in range(h):
        for x in range(w):
            r, g, b = src[x, y]
            if is_green_raw(r, g, b):
                c, a = unblend_from_white(r, g, b)
                if c is None:
                    continue
                vs.append(colorsys.rgb_to_hsv(*[ch / 255 for ch in c])[2])
    vs.sort()
    v5 = vs[int(len(vs) * 0.05)]
    v95 = vs[int(len(vs) * 0.95)]
    span = max(0.05, v95 - v5)

    t = THEMES[theme]
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dst = out.load()
    for y in range(h):
        for x in range(w):
            r, g, b = src[x, y]
            c, a = unblend_from_white(r, g, b)
            if c is None:
                continue
            if is_green_raw(r, g, b):
                vv = colorsys.rgb_to_hsv(*[ch / 255 for ch in c])[2]
                nv = t["v_lo"] + (vv - v5) / span * (t["v_hi"] - t["v_lo"])
                nv = min(1.0, max(0.0, nv))
                r2, g2, b2 = colorsys.hsv_to_rgb(t["hue"], t["sat"], nv)
            else:
                r2, g2, b2 = [ch / 255 for ch in t["text"]]
            dst[x, y] = (round(r2 * 255), round(g2 * 255), round(b2 * 255), round(a * 255))
    return out


def make_favicon(logo_light):
    w, h = logo_light.size
    alpha = logo_light.split()[3].load()
    # First fully-transparent column run in the left half separates mark from wordmark
    split = None
    run = 0
    for x in range(int(w * 0.5)):
        col_empty = all(alpha[x, y] == 0 for y in range(h))
        run = run + 1 if col_empty else 0
        if run >= 8 and x > w * 0.15:
            split = x - run // 2
            break
    if split is None:
        split = h  # fall back to square crop
    mark = logo_light.crop((0, 0, split, h))
    side = max(mark.size)
    sq = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    sq.paste(mark, ((side - mark.size[0]) // 2, (side - mark.size[1]) // 2), mark)

    size = 128
    tile = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(tile)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=28, fill=(255, 255, 255, 255),
                        outline=(224, 226, 231, 255), width=2)
    inner = int(size * 0.78)
    mark_resized = sq.resize((inner, inner), Image.LANCZOS)
    tile.alpha_composite(mark_resized, ((size - inner) // 2, (size - inner) // 2))
    tile.resize((64, 64), Image.LANCZOS).save(os.path.join(OUT_DIR, "favicon.png"))
    tile.resize((32, 32), Image.LANCZOS).save(os.path.join(OUT_DIR, "favicon-32.png"))


for theme in ("dark", "light"):
    logo = build_logo(theme)
    logo.save(os.path.join(OUT_DIR, f"logo-{theme}.png"))
    print(theme, logo.size)

make_favicon(build_logo("light"))
print("favicon written")
