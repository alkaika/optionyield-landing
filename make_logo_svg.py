"""
Vectorize the OptionYield mark from logo-light.png into SVG.

Outputs:
  logo-mark.svg  — natural proportions (viewBox 0 0 W H)
  favicon.svg    — square viewBox 0 0 512 512 per Google's favicon spec
"""
import math
import numpy as np
from PIL import Image, ImageFilter
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

CHARCOAL = "#1A1D20"

img = Image.open("logo-light.png").convert("RGBA")
mark = img.crop((0, 0, 228, 206))
mark = mark.crop(mark.getbbox())
W, H = mark.size
arr = np.array(mark).astype(int)
R, G, B, A = arr[:,:,0], arr[:,:,1], arr[:,:,2], arr[:,:,3]

green = (G > R + 25) & (G > B + 25) & (A > 100)
dark = (R < 90) & (G < 90) & (B < 90) & (A > 100)

# ─── Ring: iteratively fit a circle to the outermost dark band ───────────
# Scan clean sectors only (bottom-right + left), avoiding the arrow corridor
ys, xs = np.nonzero(dark)
cx, cy = xs.mean(), ys.mean()
r = np.percentile(np.hypot(xs - cx, ys - cy), 97)
angles = [math.radians(a) for a in list(range(15, 76, 2)) + list(range(185, 266, 2))]
for _ in range(5):
    pts = []
    for a in angles:
        runs = []; in_run = False
        for rr in range(60, 118):
            x = int(round(cx + rr * math.cos(a))); y = int(round(cy + rr * math.sin(a)))
            if not (0 <= x < W and 0 <= y < H): break
            dk = dark[y, x]
            if dk and not in_run: rs = rr; in_run = True
            elif not dk and in_run:
                if rr - rs >= 8: pts.append((cx + (rs + rr) / 2 * math.cos(a), cy + (rs + rr) / 2 * math.sin(a)))
                in_run = False
    X = np.array([p[0] for p in pts]); Y = np.array([p[1] for p in pts])
    A2 = np.column_stack([X, Y, np.ones(len(X))])
    b = X**2 + Y**2
    sol, *_ = np.linalg.lstsq(A2, b, rcond=None)
    cx, cy = sol[0] / 2, sol[1] / 2
    r = math.sqrt(sol[2] + cx*cx + cy*cy)
# thickness: median dark run containing the fitted centerline radius
th = []
for a in angles:
    run = 0; in_run = False
    for rr in range(int(r - 20), int(r + 20)):
        x = int(round(cx + rr * math.cos(a))); y = int(round(cy + rr * math.sin(a)))
        if not (0 <= x < W and 0 <= y < H): break
        dk = dark[y, x]
        if dk and not in_run: in_run = True; run = 1
        elif dk and in_run: run += 1
        elif in_run: break
    if in_run: th.append(run)
ring_t = float(np.median(th))
print(f"ring: center=({cx:.1f},{cy:.1f}) r={r:.1f} thickness={ring_t}")

# ─── Bars: dark columns inside the ring, excluding arrow corridor ─────────
r_in = r - ring_t / 2 - 4
gy, gx = np.nonzero(green)
green_dil = np.zeros_like(green)
K = 7
for dy in range(-K, K + 1):
    for dx in range(-K, K + 1):
        if dx*dx + dy*dy <= K*K:
            ys2 = np.clip(gy + dy, 0, H - 1); xs2 = np.clip(gx + dx, 0, W - 1)
            green_dil[ys2, xs2] = True
cand = dark & (np.hypot(np.arange(W)[None,:] - cx, np.arange(H)[:,None] - cy) < r_in) & (~green_dil)

bars = []
x0 = max(2, int(cx - 68))
x1 = min(W - 2, int(cx + 66))
col_hits = {}
for x in range(x0, x1):
    col = np.nonzero(cand[:, x])[0]
    if len(col) == 0: continue
    runs = []; s = col[0]; p = col[0]
    for y in col[1:]:
        if y - p > 2: runs.append((s, p)); s = y
        p = y
    runs.append((s, p))
    top, bot = max(runs, key=lambda t: t[1] - t[0])
    if (bot - top) >= 40:
        col_hits[x] = (top, bot)
xs_b = sorted(col_hits)
clusters = []; cur = [xs_b[0]]
for a, b in zip(xs_b, xs_b[1:]):
    if b - a <= 5: cur.append(b)
    else: clusters.append(cur); cur = [b]
clusters.append(cur)
for c in clusters:
    if len(c) < 12: continue
    tops = sorted(col_hits[x][0] for x in c)
    bars.append((c[0], c[-1], tops[len(tops)//2], 170))
print("bars:", bars)

# ─── Arrow: trace the green outline with matplotlib contour ───────────────
fig = plt.figure()
cs = plt.contour(green[::-1].astype(float), levels=[0.5])
verts_all = []
for path in cs.get_paths():
    v = path.vertices
    if len(v) > 20: verts_all.append(v)
plt.close(fig)
verts = max(verts_all, key=len)
verts = [(x, H - y) for x, y in verts]   # flip back to image coords

# Douglas-Peucker simplification
def dp(pts, eps):
    if len(pts) < 3: return pts
    (x1, y1), (x2, y2) = pts[0], pts[-1]
    dmax, idx = 0.0, 0
    for i in range(1, len(pts) - 1):
        x0, y0 = pts[i]
        num = abs((y2 - y1) * x0 - (x2 - x1) * y0 + x2 * y1 - y2 * x1)
        den = math.hypot(y2 - y1, x2 - x1) or 1e-9
        dd = num / den
        if dd > dmax: dmax, idx = dd, i
    if dmax > eps:
        a = dp(pts[:idx+1], eps); b = dp(pts[idx:], eps)
        return a[:-1] + b
    return [pts[0], pts[-1]]

arrow = dp(verts, 1.1)
print(f"arrow contour: {len(verts)} pts -> {len(arrow)} after simplification")
arrow_d = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in arrow) + " Z"

# gradient endpoints: tail = green pixels left quarter, head = top quarter
gys, gxs = np.nonzero(green)
tail_sel = gxs < np.percentile(gxs, 12)
head_sel = gys < np.percentile(gys, 12)
tcol = [int(np.median(G[gy2, gx2])) for gy2, gx2 in ((gys[tail_sel], gxs[tail_sel]),) for G in (arr[:,:,1],)][0]
tcol = (int(np.median(arr[:,:,0][gys[tail_sel], gxs[tail_sel]])),
        int(np.median(arr[:,:,1][gys[tail_sel], gxs[tail_sel]])),
        int(np.median(arr[:,:,2][gys[tail_sel], gxs[tail_sel]])))
hcol = (int(np.median(arr[:,:,0][gys[head_sel], gxs[head_sel]])),
        int(np.median(arr[:,:,1][gys[head_sel], gxs[head_sel]])),
        int(np.median(arr[:,:,2][gys[head_sel], gxs[head_sel]])))
def hx(c): return "#%02X%02X%02X" % c
print("tail color:", hx(tcol), "head color:", hx(hcol))

# ─── Assemble SVG ─────────────────────────────────────────────────────────
bars_svg = "\n".join(
    f'  <rect x="{bx}" y="{ty}" width="{bx2-bx+1}" height="{bb-ty+1}"/>'
    for bx, bx2, ty, bb in bars)

mark_body = f'''<defs>
  <linearGradient id="oyG" gradientUnits="userSpaceOnUse" x1="15" y1="155" x2="210" y2="15">
    <stop offset="0" stop-color="{hx(tcol)}"/>
    <stop offset="0.5" stop-color="{hx(hcol)}"/>
    <stop offset="1" stop-color="{hx(hcol)}"/>
  </linearGradient>
  <mask id="cut">
    <rect width="{W}" height="{H}" fill="#fff"/>
    <path d="{arrow_d}" fill="#000" stroke="#000" stroke-width="9"/>
  </mask>
</defs>
<g fill="{CHARCOAL}" mask="url(#cut)">
  <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r - ring_t/2:.1f}" fill="none" stroke="{CHARCOAL}" stroke-width="{ring_t:.1f}"/>
{bars_svg}
</g>
<path d="{arrow_d}" fill="url(#oyG)"/>'''

open("logo-mark.svg", "w", encoding="utf-8").write(
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}">{mark_body}</svg>'
)

S = 512 / max(W, H)
TX = (512 - W * S) / 2
TY = (512 - H * S) / 2
open("favicon.svg", "w", encoding="utf-8").write(
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">'
    f'<g transform="translate({TX:.1f},{TY:.1f}) scale({S:.4f})">{mark_body}</g></svg>'
)
print("written: logo-mark.svg, favicon.svg")
