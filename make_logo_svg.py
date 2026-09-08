"""
Vectorize the OptionYield mark into SVG.

Source: logo-mark-800.png (800px transparent mark PNG).
Outputs:
  logo-mark.svg  — natural proportions (viewBox 0 0 800 732)
  favicon.svg    — square viewBox 0 0 512 512 per Google's favicon spec
"""
import math
import numpy as np
from PIL import Image, ImageFilter
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

CHARCOAL = "#1A1D20"

img = Image.open("logo-mark-800.png").convert("RGBA")
mark = img.crop(img.getbbox())
W, H = mark.size
S = H / 206.0          # scale factor: legacy constants were tuned at H=206
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
        for rr in range(int(60 * S), int(118 * S)):
            x = int(round(cx + rr * math.cos(a))); y = int(round(cy + rr * math.sin(a)))
            if not (0 <= x < W and 0 <= y < H): break
            dk = dark[y, x]
            if dk and not in_run: rs = rr; in_run = True
            elif not dk and in_run:
                if rr - rs >= 8 * S: pts.append((cx + (rs + rr) / 2 * math.cos(a), cy + (rs + rr) / 2 * math.sin(a)))
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
    for rr in range(int(r - 20 * S), int(r + 20 * S)):
        x = int(round(cx + rr * math.cos(a))); y = int(round(cy + rr * math.sin(a)))
        if not (0 <= x < W and 0 <= y < H): break
        dk = dark[y, x]
        if dk and not in_run: in_run = True; run = 1
        elif dk and in_run: run += 1
        elif in_run: break
    if in_run: th.append(run)
ring_t = float(np.median(th))
print(f"ring: center=({cx:.1f},{cy:.1f}) r={r:.1f} thickness={ring_t:.1f}")

# ─── Bars: dark columns inside the ring, excluding arrow corridor ─────────
r_in = r - ring_t / 2 - 4 * S
gy, gx = np.nonzero(green)
green_img = Image.fromarray((green * 255).astype(np.uint8))
K = int(7 * S) // 2 * 2 + 1          # odd dilation kernel
green_dil = np.array(green_img.filter(ImageFilter.MaxFilter(K))) > 100
cand = dark & (np.hypot(np.arange(W)[None,:] - cx, np.arange(H)[:,None] - cy) < r_in) & (~green_dil)

bars = []
x0 = max(2, int(cx - 68 * S))
x1 = min(W - 2, int(cx + 66 * S))
col_hits = {}
MIN_RUN = int(24 * S)
for x in range(x0, x1):
    col = np.nonzero(cand[:, x])[0]
    if len(col) == 0: continue
    runs = []; s = col[0]; p = col[0]
    for y in col[1:]:
        if y - p > 2 * S: runs.append((s, p)); s = y
        p = y
    runs.append((s, p))
    top, bot = max(runs, key=lambda t: t[1] - t[0])
    if (bot - top) >= MIN_RUN:
        col_hits[x] = (top, bot)
xs_b = sorted(col_hits)
clusters = []; cur = [xs_b[0]]
for a, b in zip(xs_b, xs_b[1:]):
    if b - a <= 4 * S: cur.append(b)
    else: clusters.append(cur); cur = [b]
clusters.append(cur)
for c in clusters:
    if len(c) < 10 * S: continue
    tops = sorted(col_hits[x][0] for x in c)
    bars.append((c[0], c[-1], tops[len(tops)//2], int(170 * S)))
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

arrow = dp(verts, 0.25 * S)
print(f"arrow contour: {len(verts)} pts -> {len(arrow)} after simplification")
arrow_d = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in arrow) + " Z"

# gradient endpoints + sampled colors along the arrow
tail_sel = gx < np.percentile(gx, 12)
head_sel = gy < np.percentile(gy, 12)
def hexmean(sx, sy):
    return "#%02X%02X%02X" % tuple(int(np.median(arr[sy, sx, c])) for c in range(3))
tcol, hcol = hexmean(gx[tail_sel], gy[tail_sel]), hexmean(gx[head_sel], gy[head_sel])
print("tail color:", tcol, "head color:", hcol)

# ─── Assemble SVG ─────────────────────────────────────────────────────────
bars_svg = "\n".join(
    f'  <rect x="{bx}" y="{ty}" width="{bx2-bx+1}" height="{bb-ty+1}"/>'
    for bx, bx2, ty, bb in bars)

mark_body = f'''<defs>
  <linearGradient id="oyG" gradientUnits="userSpaceOnUse" x1="{15*S:.0f}" y1="{155*S:.0f}" x2="{210*S:.0f}" y2="{15*S:.0f}">
    <stop offset="0" stop-color="{tcol}"/>
    <stop offset="0.5" stop-color="{hcol}"/>
    <stop offset="1" stop-color="{hcol}"/>
  </linearGradient>
  <mask id="cut">
    <rect width="{W}" height="{H}" fill="#fff"/>
    <path d="{arrow_d}" fill="#000" stroke="#000" stroke-width="{9*S:.1f}"/>
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

S2 = 512 / max(W, H)
TX = (512 - W * S2) / 2
TY = (512 - H * S2) / 2
open("favicon.svg", "w", encoding="utf-8").write(
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">'
    f'<g transform="translate({TX:.1f},{TY:.1f}) scale({S2:.4f})">{mark_body}</g></svg>'
)
print("written: logo-mark.svg, favicon.svg")
