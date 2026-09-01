# OptionYield — Landing Page

Marketing landing page for **OptionYield**, the mobile-first options income app
(covered calls & cash-secured puts). Single-page static site — no build step,
no dependencies, no framework.

## Files

| File | Purpose |
| --- | --- |
| `index.html` | The entire page: markup, styles, and scripts |
| `logo-dark.png` / `logo-light.png` | Logo recolored for the site's dark/light themes |
| `favicon.png` / `favicon-32.png` | Browser tab icons (logo mark on a dark tile) |
| `app-screenshot.jpg` | App screenshot shown in the hero |
| `recolor_logo.py` | Regenerates the logo assets from the source artwork |

## Preview locally

Open `index.html` directly in a browser, or serve the folder:

```bash
python -m http.server 8741
# then visit http://localhost:8741
```

## Editing

All content and styles live in `index.html`. Design tokens are CSS custom
properties in `:root` (dark, the default) and `html[data-theme="light"]`,
mirroring the mobile app's `ThemeContext`.

To re-theme the logo after changing brand colors, update the color targets in
`recolor_logo.py` and re-run:

```bash
python recolor_logo.py
```

It maps the logo's black → theme text color and green → theme accent, and
regenerates `logo-dark.png`, `logo-light.png`, and both favicons.

## Deploying (Cloudflare Pages)

The DNS for the site's domain is managed by Cloudflare, so Cloudflare Pages is
the host — free tier, unlimited bandwidth, automatic SSL.

1. Cloudflare dashboard → **Workers & Pages → Create → Pages → Connect to Git**.
2. Pick this repo (`optionyield-landing`), branch `main`.
3. Build settings: framework preset **None**, build command **(empty)**,
   output directory **/** (the repo root is the site).
4. Deploy, then add the custom domain under the project's
   **Custom domains** tab — records and SSL are provisioned automatically.

Every push to `main` redeploys the site automatically.
