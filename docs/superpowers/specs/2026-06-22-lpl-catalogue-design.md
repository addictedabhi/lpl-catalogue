# Little Pink Llama — Static Catalogue Website Design

**Date:** 2026-06-22
**Status:** Approved (design), pending spec review

## Goal

A single-page, static catalogue website for Little Pink Llama (handcrafted kids'
accessories) that:

- Renders every product grouped by category, with price and details from the
  catalogue document.
- Shows one base image per product; clicking opens a gallery of that product's
  additional images.
- Has sticky category navigation that smooth-scrolls to each category section.
- Offers a downloadable, professionally designed PDF of the full catalogue.
- Matches the look and feel of the live site (littlepinkllama.com) — soft pink,
  warm, whimsical-but-premium.

## Sources of Truth

| Source | Role |
|--------|------|
| `base_data/LittlePinkLlama_Catalogue_v3.docx` | Authoritative for which products exist, prices, badges, color variants, descriptions, category copy, contact info, testimonials. Also the image source for products not on the live site. |
| `https://littlepinkllama.com` (Shopify `/products.json`) | Image galleries (multiple images per product) for products that match a docx entry. |

**Rule:** The docx defines the catalogue. Live-site data is used only to enrich
matched products with image galleries. Where docx and site prices differ, **docx
wins**. Site-only products (e.g. Crochet Toys) are **excluded**.

### Categories (from docx, in display order)
1. Rakhi (~16 products) — docx images only, no gallery
2. Bathrobes (3 products) — docx images only, no gallery
3. Brooches — matched to site for galleries
4. Hair Clips — matched to site for galleries
5. Collars — matched to site for galleries

### Known mismatches (handled, not blocking)
- Rakhi and Bathrobes are **not** on the live site → single docx image, no gallery.
- Crochet Toys (Bunny, Bear, Dog, Dino) are on the site but **not** in the docx →
  excluded.
- Prices differ between sources → docx value is used.

## Architecture

Two clean layers: a build-time **data pipeline** and a runtime **static site**.

```
docx + Shopify products.json
        │
        ▼
   [ Python build pipeline ]
        │
        ├─ catalogue-data.js   (window.CATALOGUE = {...})
        ├─ images/<slug>/*.jpg (downloaded, optimized)
        ├─ catalogue.pdf       (themed, committed)
        └─ build-report.txt    (coverage / unmatched log)
        │
        ▼
   [ Static site: index.html + assets/ ]
        renders from catalogue-data.js
```

### Layer 1 — Data pipeline (`build/`, Python)

Runtimes/libs: `python-docx` (parse + extract docx images), `requests`
(Shopify fetch + image download), `Pillow` (resize/optimize), `playwright`
(render PDF from a themed HTML template).

Steps (each a focused module):

1. **`extract_docx.py`** — Parse the 12 docx tables into product records:
   `name, category, price, badges[], variants[], description`, plus the embedded
   per-product image (extracted from the docx zip, mapped to the product by its
   table cell). Emits intermediate `docx_products` + saves docx images.

2. **`fetch_shopify.py`** — GET `/products.json?limit=250`; normalize each
   product to `{title, handle, type, images[]}`.

3. **`merge.py`** — Match docx products to Shopify products by normalized
   `name + category` (lowercased, punctuation/`- Brooch` suffix stripped, fuzzy
   fallback). Produce the final merged catalogue:
   - Price/details/badges/variants/description: **from docx**.
   - Gallery images: **from Shopify** when matched.
   - **Base image** = first Shopify image if matched, else the docx image.
   - Rakhi/Bathrobes: docx image only.
   - Unmatched docx products: keep with docx image, log a warning.

4. **`download_images.py`** — Download every referenced image into
   `images/<slug>/NN.jpg`, resize to a max dimension and compress (web-friendly
   sizes; keep an adequately large base + gallery size). Skip re-downloading
   existing files.

5. **`build_data.py`** — Emit `catalogue-data.js` defining `window.CATALOGUE`:
   ordered categories, each with products `{ slug, name, price, badges,
   variants, description, baseImage, gallery[] }`, plus brand/contact/testimonial
   metadata. (A JS file, not raw JSON, so the page works when opened as a local
   file as well as on GitHub Pages — no fetch/CORS limitation.)

6. **`build_pdf.py`** — Render `catalogue.pdf` from a themed HTML template
   (`build/pdf_template.html`) via Playwright `page.pdf()`. Layout: branded cover
   → category divider pages → product entries (one representative image + name,
   price, badges, variants, short detail) → contact/bulk-order page. Professional
   color palette matched to the brand pink theme, web fonts embedded.

A single `build/run.py` orchestrates steps 1→6 and writes `build-report.txt`
(counts: parsed, matched, unmatched list, total images downloaded).

### Layer 2 — Static site (repo root)

Plain HTML/CSS/vanilla-JS. No framework, no build step for the site itself.

- **`index.html`** — semantic single page:
  - **Hero**: logo, tagline, "Download Catalogue (PDF)" button.
  - **Sticky category nav**: anchor links → smooth scroll to each section;
    highlights the active section on scroll.
  - **Category sections** (`<section id="rakhi">` etc.): heading + category
    blurb + responsive product grid.
  - **Product card**: base image, name, price, badge pill(s), variant color
    dots, short detail. Cards with a gallery are visibly clickable.
  - **Footer**: bulk-orders CTA, contact (WhatsApp / email / Instagram),
    testimonials.
- **`assets/styles.css`** — design tokens (brand pink palette, spacing,
  radius, typography), mobile-first responsive grid, card + nav + modal styles.
- **`assets/app.js`** — reads `window.CATALOGUE`, renders sections/cards,
  wires sticky-nav active state + smooth scroll, and the **lightbox modal**
  (gallery: prev/next arrows, swipe, keyboard arrows, Esc to close, click
  backdrop to close). Products without a gallery open a single image (or skip
  the modal).
- **`catalogue-data.js`**, **`images/`**, **`catalogue.pdf`** — generated.
- Paths are **relative** so the site works on GitHub Pages project hosting
  (`/lpl-catalogue/`) and when opened locally.

### Brand assets & fidelity (match the live site)

The catalogue must use the **real brand identity**, not approximations:

- **Logo**: download the actual logo (`LPL_Logo_HD.png` from the Shopify CDN) and
  use it in the header, hero, and PDF — not a stand-in mark/emoji.
- **Colors**: sample the live site's actual brand palette (pinks, neutrals,
  button/accent colors) and use those exact values as the design tokens.
- **Typography**: match the fonts the live site uses (self-host the same web
  fonts, or the closest available equivalents) rather than substituting.
- **Other brand details**: tagline, voice, and any recurring brand motifs are
  taken from the live site / docx so the catalogue reads as the same brand.

The build pipeline downloads these brand assets into the repo (e.g.
`assets/brand/`) alongside product images, so the site is self-contained. The
mockup's emoji tiles and approximate palette were illustrative only; the real
build uses real photos, the real logo, and site-matched colors and fonts.

### Theme

Soft pink pastel base, warm neutrals, rounded corners, gentle shadows, generous
whitespace; whimsical but premium — driven by the sampled brand tokens above and
applied consistently to both the site and the PDF template.

## Data Flow

1. Run `python build/run.py`.
2. Pipeline parses docx, fetches Shopify, merges, downloads images, emits
   `catalogue-data.js`, builds `catalogue.pdf`, writes `build-report.txt`.
3. `index.html` loads `catalogue-data.js` + assets and renders the catalogue.
4. User browses categories via sticky nav, opens product galleries, downloads
   the PDF.

## Error Handling

- **Unmatched product**: fall back to docx image, log in build report (does not
  fail the build).
- **Missing/failed image download**: log + use a placeholder; build continues.
- **Shopify fetch failure**: build aborts with a clear message (galleries
  require it); docx-only run can be a documented fallback flag later if needed.
- **Site runtime**: if `window.CATALOGUE` is absent, show a friendly message
  rather than a blank page.

## Testing

- **Pipeline**: `build-report.txt` coverage check — every docx product present,
  matched/unmatched counts sane, image counts > 0 per category. A few unit
  checks on the docx parser (price/badge/variant extraction) and the matcher
  (normalization + a couple of known name pairs).
- **Site**: manual visual pass on desktop + mobile widths; verify smooth-scroll
  nav, lightbox open/close/navigate, PDF download.
- **PDF**: visual review — cover, every product present, one image each, colors
  correct.

Scope is a static catalogue, not application logic; testing stays lightweight
and focused on the pipeline's correctness and a visual pass.

## Out of Scope (YAGNI)

- No cart / checkout / e-commerce (live Shopify site already does that).
- No CMS or admin UI — re-run the pipeline to update.
- No search/filter (single page, modest product count; sticky nav suffices).
- No site-only Crochet Toys, no live price sync.

## Deliverables

- `build/` Python pipeline (modules + `run.py` + `pdf_template.html`).
- `index.html`, `assets/styles.css`, `assets/app.js`.
- Generated: `catalogue-data.js`, `images/`, `catalogue.pdf`, `build-report.txt`.
- Short `README.md`: how to run the pipeline and deploy to GitHub Pages.
