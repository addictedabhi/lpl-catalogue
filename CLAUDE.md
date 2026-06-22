# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A static, single-page product catalogue website for **Little Pink Llama** (handcrafted kids' accessories). The site itself is plain HTML/CSS/vanilla-JS with **no build step**; a separate **Python pipeline (`build/`)** generates the data, images, and PDF the site consumes. Deployed via GitHub Pages.

## Commands

```bash
# One-time setup
pip install -r build/requirements.txt
python -m playwright install chromium      # required for PDF generation

# Regenerate all artifacts (catalogue-data.js, images/, assets/brand/logo.png, catalogue.pdf, build-report.txt)
python build/run.py --refresh              # --refresh re-fetches Shopify; omit to use base_data/lpl_products.json cache

# Serve the site locally (relative paths require a server OR open index.html directly)
python -m http.server 8000                 # http://localhost:8000/

# Tests
pytest -q                                  # full suite
pytest build/tests/test_merge.py -v        # one file
pytest build/tests/test_merge.py::test_same_name_different_categories_get_correct_galleries -v   # one test
```

Tests run from the **repo root** (paths in `pytest.ini` and the site-asset tests are root-relative).

## Architecture

Two layers, one data flow:

```
base_data/*.docx  +  littlepinkllama.com (Shopify /products.json)
        │  (prices/details, SOURCE OF TRUTH)   │  (image galleries + masthead logo)
        ▼                                       ▼
                  build/ pipeline (run.py)
        ▼
  catalogue-data.js  +  images/<slug>/*.jpg  +  catalogue.pdf  +  build-report.txt
        ▼
  index.html + assets/app.js  →  renders from window.CATALOGUE
```

**Pipeline modules** (`build/run.py` orchestrates in this order; each is independently unit-tested):
1. `extract_docx.py` — parses the 5 category tables (indices 3–7) of the docx into product records + extracts the per-product embedded image. Uses `parse_text.py` for the cell text.
2. `fetch_shopify.py` — fetches/caches Shopify `products.json`, normalizes titles/handles/images/price.
3. `merge.py` — **category-aware** matching of docx products to Shopify products; attaches galleries.
4. `brand.py` — downloads the real masthead logo and samples brand colors/fonts from the live site.
5. `download_images.py` — downloads + resizes (≤1200px, JPEG q85) galleries; copies docx images for unmatched products.
6. `emit_data.py` — builds the site payload and writes `catalogue-data.js`.
7. `pdf_template.py` + `build_pdf.py` — renders a themed HTML and prints it to `catalogue.pdf` via Playwright.

**The product dict grows as it flows through the pipeline.** A product starts as `{name, price, badge, variants, features}` (parse) → gains `category, docx_image` (extract) → `slug, gallery, base_image_src, matched` (merge) → `images, base_image` (download) → final payload fields (emit). When changing one stage, check the downstream consumers expect the same keys.

## Critical invariants (don't break these)

- **Docx wins on price and details.** Shopify supplies images only. Where the live price differs, the docx value is used. The catalogue's contents/order are defined by the docx, not the live store.
- **Matching is category-aware** (`merge.py`): the same product name appears across categories (e.g. "Derpy Tiger" is a Brooch, Hair Clip, and Collar). The Shopify index is keyed by `(normalized_name, product_type)` with a single-candidate name-only fallback. Reverting to name-only matching causes cross-category gallery mixups.
- **Rakhi and Bathrobes are docx-only** — they have no live-store match, so they use their docx image (single image, no gallery). Don't let the name-only fallback match them to Shopify products.
- **Site-only "Crochet Toys" are excluded** (not in the docx).
- **Generated artifacts are committed** (`catalogue-data.js`, `images/`, `assets/brand/logo.png`, `catalogue.pdf`, `build-report.txt`) — they are the deployable site. Only caches (`build/.cache/`) and Python cruft are gitignored.
- **All site asset paths are relative** so the site works on GitHub Pages project hosting (`/lpl-catalogue/`) and when opened locally.
- **Data ships as a JS global, not JSON.** `catalogue-data.js` sets `window.CATALOGUE`; `app.js` reads it directly (no `fetch`), so the page works from `file://`.
- **`app.js` escapes all rendered data** via its `esc()` helper, mirroring `pdf_template.py`'s `_esc`. Keep both renderers escaping when adding fields.

## Gotchas

- **Builds are non-deterministic** because `brand.py` re-samples the live site each run: accent color, the `sans` font (Jost prefix), and the logo can change with site availability. `build_brand` falls back to `DEFAULT_TOKENS` on network failure (503/offline), so committed brand tokens may flip between sampled and default values run-to-run. The accent is gated on a WCAG contrast check — a too-pale sampled pink is rejected in favor of the default raspberry `#E8587A`.
- `python build/run.py` works as a script via a `sys.path` bootstrap at the top of `run.py`; `python -m build.run` also works.
- The docx table indices (3–7) are hardcoded in `extract_docx._TABLE_INDEX`. If the source docx structure changes, `test_extract_docx.py::test_categories_order` will catch it — adjust the indices there.
- PDF image paths resolve because `build_pdf.py` writes a temp `catalogue_pdf_render.html` at the **repo root** (gitignored) and loads it via `file://` so relative `images/`/`assets/` paths work; it's deleted in `finally`.
