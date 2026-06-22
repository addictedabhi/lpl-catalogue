# Little Pink Llama Catalogue Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a static single-page catalogue website for Little Pink Llama, fed by a Python build pipeline that merges the catalogue docx (prices/details) with the live Shopify store (image galleries) and produces a professional downloadable PDF.

**Architecture:** A Python pipeline (`build/`) parses the docx, fetches Shopify `products.json`, matches and merges them (docx authoritative for price/details, Shopify for image galleries), downloads all images + real brand assets, and emits `catalogue-data.js`, `catalogue.pdf`, and `build-report.txt`. The site (repo root) is plain HTML/CSS/vanilla-JS that renders from `catalogue-data.js`. No framework, no site build step.

**Tech Stack:** Python 3.10 (`python-docx`, `requests`, `Pillow`, `playwright`, `pytest`), HTML/CSS/vanilla-JS, GitHub Pages.

## Global Constraints

- **Catalogue scope:** docx defines the catalogue — Rakhi, Bathrobes, Brooches, Hair Clips, Collars, in that display order. Site-only products (Crochet Toys) are excluded.
- **Source of truth:** docx wins on price, badges, color variants, descriptions, category copy. Shopify supplies image galleries only.
- **Base image:** first Shopify image when a product is matched; otherwise the docx image. Rakhi & Bathrobes have docx images only (no gallery).
- **Prices:** rupee values exactly as in the docx, formatted `₹X,XXX` (Indian grouping).
- **Brand fidelity:** use the real logo (`https://littlepinkllama.com/cdn/shop/collections/LPL_Logo_HD.png`), site-sampled colors, and site-matched fonts — no stand-in marks/emoji in the real build.
- **Paths:** all site asset references are relative (works on GitHub Pages project hosting `/lpl-catalogue/` and when opened locally).
- **Data delivery:** product data ships as `catalogue-data.js` setting `window.CATALOGUE` (no runtime fetch, so it works from `file://`).
- **Contact (from docx):** WhatsApp/Call `+91 94600 74404`, email `lplkidscouture@gmail.com`, web `www.littlepinkllama.com`, Instagram `@little_pink_llama_`.
- **Idempotency:** re-running the pipeline overwrites generated outputs deterministically; image downloads skip files already present.

---

## File Structure

**Build pipeline (`build/`):**
- `build/parse_text.py` — pure functions: parse a product cell's text lines into a record; normalize names.
- `build/extract_docx.py` — open the docx, walk category tables, extract product records + per-product images.
- `build/fetch_shopify.py` — fetch + normalize `products.json` (with on-disk cache).
- `build/merge.py` — match docx↔Shopify, build the merged catalogue structure.
- `build/brand.py` — download logo, sample brand colors/fonts → `assets/brand/` + `build/brand_tokens.json`.
- `build/download_images.py` — download + resize product/docx images into `images/<slug>/`.
- `build/emit_data.py` — write `catalogue-data.js`.
- `build/pdf_template.py` — render the merged catalogue into a themed HTML string for the PDF.
- `build/build_pdf.py` — render that HTML to `catalogue.pdf` via Playwright.
- `build/run.py` — orchestrate all steps; write `build-report.txt`.
- `build/requirements.txt`, `build/conftest.py`.

**Tests (`build/tests/`):** one `test_<module>.py` per logic module.

**Site (repo root):**
- `index.html`, `assets/styles.css`, `assets/app.js`.
- Generated: `catalogue-data.js`, `images/`, `assets/brand/`, `catalogue.pdf`, `build-report.txt`.

**Repo:** `.gitignore`, `README.md`.

---

### Task 1: Project scaffold

**Files:**
- Create: `build/requirements.txt`, `build/conftest.py`, `build/__init__.py`, `.gitignore`, `pytest.ini`

**Interfaces:**
- Consumes: nothing.
- Produces: a Python package rooted at `build/` importable in tests as `build.<module>`; pytest discoverable.

- [ ] **Step 1: Create `build/requirements.txt`**

```
python-docx==1.1.2
requests==2.32.3
Pillow==10.4.0
playwright==1.47.0
pytest==8.3.2
```

- [ ] **Step 2: Create `.gitignore`**

```
__pycache__/
*.pyc
.pytest_cache/
build/.cache/
```

> Note: generated outputs (`catalogue-data.js`, `images/`, `assets/brand/`, `catalogue.pdf`, `build-report.txt`) ARE committed — they are the deployable site. Only caches and Python cruft are ignored.

- [ ] **Step 3: Create `pytest.ini`**

```ini
[pytest]
testpaths = build/tests
python_files = test_*.py
```

- [ ] **Step 4: Create empty `build/__init__.py` and `build/conftest.py`**

`build/conftest.py`:
```python
# Ensures repo root is importable so `import build.<module>` works in tests.
```

`build/__init__.py`: empty file.

- [ ] **Step 5: Install deps and verify pytest runs**

Run: `pip install -r build/requirements.txt && python -m playwright install chromium && pytest -q`
Expected: pytest exits with "no tests ran" (exit code 5) — confirms discovery works.

- [ ] **Step 6: Commit**

```bash
git add build/requirements.txt build/conftest.py build/__init__.py .gitignore pytest.ini
git commit -m "chore: scaffold catalogue build pipeline"
```

---

### Task 2: Product-text parser (pure functions)

**Files:**
- Create: `build/parse_text.py`
- Test: `build/tests/test_parse_text.py`

**Interfaces:**
- Produces:
  - `parse_product_lines(lines: list[str]) -> dict | None` — returns `{"name": str, "price": int, "badge": str|None, "variants": list[str], "features": list[str]}` or `None` if `lines` has no parseable product.
  - `normalize_name(name: str, category: str | None = None) -> str` — lowercased, suffix/punctuation-stripped key for matching.

- [ ] **Step 1: Write the failing test**

```python
# build/tests/test_parse_text.py
from build.parse_text import parse_product_lines, normalize_name

def test_parse_basic_product():
    lines = ["Llama", "Price", "Rs. 599", "✦ 100% Handmade", "✦ Premium Quality"]
    r = parse_product_lines(lines)
    assert r["name"] == "Llama"
    assert r["price"] == 599
    assert r["badge"] is None
    assert r["variants"] == []
    assert "100% Handmade" in r["features"]

def test_parse_badge_prefix():
    lines = ["★ Bestseller", "Llama", "Price", "Rs. 799", "✦ 100% Handmade"]
    r = parse_product_lines(lines)
    assert r["badge"] == "Bestseller"
    assert r["name"] == "Llama"
    assert r["price"] == 799

def test_parse_color_variants():
    lines = ["Elephant", "Price", "Rs. 799", "✦ 100% Handmade",
             "✦ Color Variants: Red, Green, Pink & Gray"]
    r = parse_product_lines(lines)
    assert r["variants"] == ["Red", "Green", "Pink", "Gray"]

def test_parse_comma_price():
    lines = ["Unicorn Bathrobe", "Price", "Rs. 1,499", "✦ Premium Quality"]
    assert parse_product_lines(lines)["price"] == 1499

def test_parse_empty_returns_none():
    assert parse_product_lines([]) is None
    assert parse_product_lines([""]) is None

def test_normalize_strips_suffix_and_punct():
    assert normalize_name("Amazing Spider man - Brooch", "Brooches") == normalize_name("Amazing Spiderman", "Brooches")
    assert normalize_name("Derpy Tiger Collar", "Collars") == "derpytiger"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest build/tests/test_parse_text.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'build.parse_text'`

- [ ] **Step 3: Write minimal implementation**

```python
# build/parse_text.py
from __future__ import annotations
import re

_PRICE_RE = re.compile(r"Rs\.?\s*([\d,]+)", re.IGNORECASE)
_VARIANT_RE = re.compile(r"Color Variants?\s*:?\s*(.+)", re.IGNORECASE)
_SUFFIX_RE = re.compile(r"\b(brooch|hair\s*clip|clip|collar|bathrobe|rakhi)s?\b", re.IGNORECASE)


def parse_product_lines(lines: list[str]) -> dict | None:
    toks = [l.strip() for l in lines if l and l.strip()]
    if not toks:
        return None

    badge = None
    if toks[0].startswith("★"):
        badge = toks[0].lstrip("★").strip()
        toks = toks[1:]
    if not toks:
        return None

    name = toks[0]
    if name.lower() in ("price",) or _PRICE_RE.search(name):
        return None  # first real token must be a name

    price = None
    variants: list[str] = []
    features: list[str] = []
    for t in toks[1:]:
        m = _PRICE_RE.search(t)
        if m and price is None:
            price = int(m.group(1).replace(",", ""))
            continue
        if t.lower() == "price":
            continue
        v = _VARIANT_RE.search(t.lstrip("✦").strip())
        if v:
            raw = v.group(1)
            variants = [p.strip() for p in re.split(r"[,&]", raw) if p.strip()]
            continue
        feat = t.lstrip("✦").strip()
        if feat:
            features.append(feat)

    if price is None:
        return None
    return {"name": name, "price": price, "badge": badge,
            "variants": variants, "features": features}


def normalize_name(name: str, category: str | None = None) -> str:
    s = name.lower()
    s = _SUFFIX_RE.sub(" ", s)            # drop product-type words
    s = re.sub(r"[^a-z0-9]+", "", s)      # drop spaces/punctuation
    return s
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest build/tests/test_parse_text.py -v`
Expected: PASS (6 passed)

- [ ] **Step 5: Commit**

```bash
git add build/parse_text.py build/tests/test_parse_text.py
git commit -m "feat: add product-text parser and name normalizer"
```

---

### Task 3: docx extraction (records + images)

**Files:**
- Create: `build/extract_docx.py`
- Test: `build/tests/test_extract_docx.py`

**Interfaces:**
- Consumes: `parse_product_lines` (Task 2).
- Produces:
  - `CATEGORY_TABLES: list[tuple[str, str]]` — ordered `(category_name, category_id)`: `[("Rakhi","rakhi"),("Bathrobes","bathrobes"),("Brooches","brooches"),("Hair Clips","hairclips"),("Collars","collars")]`.
  - `extract_catalogue(docx_path: str, image_out_dir: str) -> list[dict]` — list of category dicts: `{"name","id","blurb","products":[{...record, "category","docx_image": <relative path or None>}]}`. Saves docx images to `image_out_dir/<category_id>/<index>.<ext>`.

- [ ] **Step 1: Write the failing test**

```python
# build/tests/test_extract_docx.py
import os
from build.extract_docx import extract_catalogue, CATEGORY_TABLES

DOCX = "base_data/LittlePinkLlama_Catalogue_v3.docx"

def test_categories_order():
    cats = extract_catalogue(DOCX, "build/.cache/docx_images_test")
    assert [c["id"] for c in cats] == [cid for _, cid in CATEGORY_TABLES]

def test_brooches_has_bestseller_llama():
    cats = extract_catalogue(DOCX, "build/.cache/docx_images_test")
    brooches = next(c for c in cats if c["id"] == "brooches")
    llama = next(p for p in brooches["products"] if p["name"] == "Llama")
    assert llama["badge"] == "Bestseller"
    assert llama["price"] == 799

def test_bathrobes_count_and_price():
    cats = extract_catalogue(DOCX, "build/.cache/docx_images_test")
    bath = next(c for c in cats if c["id"] == "bathrobes")
    assert len(bath["products"]) == 3
    assert all(p["price"] == 1499 for p in bath["products"])

def test_docx_images_saved():
    out = "build/.cache/docx_images_test"
    cats = extract_catalogue(DOCX, out)
    bath = next(c for c in cats if c["id"] == "bathrobes")
    imgs = [p["docx_image"] for p in bath["products"] if p["docx_image"]]
    assert len(imgs) >= 1
    assert os.path.exists(imgs[0])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest build/tests/test_extract_docx.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'build.extract_docx'`

- [ ] **Step 3: Write minimal implementation**

```python
# build/extract_docx.py
from __future__ import annotations
import os
import docx
from docx.oxml.ns import qn
from build.parse_text import parse_product_lines

# (category_name, category_id) in display order. Index = position in docx.tables.
CATEGORY_TABLES = [
    ("Rakhi", "rakhi"),
    ("Bathrobes", "bathrobes"),
    ("Brooches", "brooches"),
    ("Hair Clips", "hairclips"),
    ("Collars", "collars"),
]
# docx table indices for the five category tables (verified against v3 docx).
_TABLE_INDEX = {"rakhi": 3, "bathrobes": 4, "brooches": 5, "hairclips": 6, "collars": 7}


def _cell_lines(cell) -> list[str]:
    return [p.text for p in cell.paragraphs]


def _cell_image_blob(cell, part):
    """Return (blob, ext) for the first embedded image in a table cell, or None."""
    for blip in cell._element.findall(".//" + qn("a:blip")):
        rid = blip.get(qn("r:embed"))
        if rid and rid in part.rels:
            img = part.rels[rid].target_part
            ext = os.path.splitext(img.partname)[1] or ".png"
            return img.blob, ext
    return None


def extract_catalogue(docx_path: str, image_out_dir: str) -> list[dict]:
    doc = docx.Document(docx_path)
    part = doc.part
    cats: list[dict] = []

    for name, cid in CATEGORY_TABLES:
        table = doc.tables[_TABLE_INDEX[cid]]
        cat_dir = os.path.join(image_out_dir, cid)
        os.makedirs(cat_dir, exist_ok=True)

        # Row 0: [title, blurb]
        header_cells = table.rows[0].cells
        blurb = header_cells[-1].text.strip() if len(header_cells) > 1 else ""

        products: list[dict] = []
        seen_cells = set()
        idx = 0
        for row in table.rows[1:]:
            for cell in row.cells:
                key = id(cell._element)
                if key in seen_cells:
                    continue
                seen_cells.add(key)
                rec = parse_product_lines(_cell_lines(cell))
                if not rec:
                    continue
                img = _cell_image_blob(cell, part)
                docx_image = None
                if img:
                    blob, ext = img
                    path = os.path.join(cat_dir, f"{idx}{ext}")
                    with open(path, "wb") as f:
                        f.write(blob)
                    docx_image = path.replace("\\", "/")
                rec["category"] = name
                rec["docx_image"] = docx_image
                products.append(rec)
                idx += 1

        cats.append({"name": name, "id": cid, "blurb": blurb, "products": products})
    return cats
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest build/tests/test_extract_docx.py -v`
Expected: PASS (4 passed). If `test_categories_order` reveals a different table index, fix `_TABLE_INDEX` to match (indices verified as 3–7 during design).

- [ ] **Step 5: Commit**

```bash
git add build/extract_docx.py build/tests/test_extract_docx.py
git commit -m "feat: extract products and images from catalogue docx"
```

---

### Task 4: Shopify fetch + normalize

**Files:**
- Create: `build/fetch_shopify.py`
- Test: `build/tests/test_fetch_shopify.py`

**Interfaces:**
- Produces:
  - `normalize_products(raw: dict) -> list[dict]` — from a `products.json` payload returns `[{"title","handle","images":[<src>...],"price": int}]` (price = first variant price floored to int).
  - `load_products(cache_path: str = "base_data/lpl_products.json", url: str = "https://littlepinkllama.com/products.json?limit=250", refresh: bool = False) -> list[dict]` — returns normalized products; downloads to `cache_path` if missing or `refresh`, else reads cache.

- [ ] **Step 1: Write the failing test**

```python
# build/tests/test_fetch_shopify.py
from build.fetch_shopify import normalize_products

def test_normalize_extracts_fields():
    raw = {"products": [{
        "title": "Llama - Brooch", "handle": "llama-brooch",
        "images": [{"src": "//x/a.jpg"}, {"src": "//x/b.png"}],
        "variants": [{"price": "849.00"}],
    }]}
    out = normalize_products(raw)
    assert out[0]["title"] == "Llama - Brooch"
    assert out[0]["handle"] == "llama-brooch"
    assert out[0]["images"] == ["https://x/a.jpg", "https://x/b.png"]
    assert out[0]["price"] == 849

def test_normalize_handles_no_images():
    raw = {"products": [{"title": "X", "handle": "x", "images": [], "variants": [{"price": "10.0"}]}]}
    assert normalize_products(raw)[0]["images"] == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest build/tests/test_fetch_shopify.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# build/fetch_shopify.py
from __future__ import annotations
import json
import os
import requests


def _abs_url(src: str) -> str:
    if src.startswith("//"):
        return "https:" + src
    return src


def normalize_products(raw: dict) -> list[dict]:
    out = []
    for p in raw.get("products", []):
        variants = p.get("variants") or [{}]
        price_raw = variants[0].get("price", "0")
        out.append({
            "title": p.get("title", "").strip(),
            "handle": p.get("handle", ""),
            "images": [_abs_url(i["src"]) for i in p.get("images", []) if i.get("src")],
            "price": int(float(price_raw)),
        })
    return out


def load_products(cache_path: str = "base_data/lpl_products.json",
                  url: str = "https://littlepinkllama.com/products.json?limit=250",
                  refresh: bool = False) -> list[dict]:
    if refresh or not os.path.exists(cache_path):
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        with open(cache_path, "w", encoding="utf-8") as f:
            f.write(resp.text)
    with open(cache_path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return normalize_products(raw)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest build/tests/test_fetch_shopify.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add build/fetch_shopify.py build/tests/test_fetch_shopify.py
git commit -m "feat: fetch and normalize Shopify products"
```

---

### Task 5: Match + merge docx with Shopify

**Files:**
- Create: `build/merge.py`
- Test: `build/tests/test_merge.py`

**Interfaces:**
- Consumes: `normalize_name` (Task 2); category dicts (Task 3); normalized Shopify products (Task 4).
- Produces:
  - `merge_catalogue(cats: list[dict], shopify: list[dict]) -> list[dict]` — returns category dicts where each product gains `"slug","gallery": list[str], "base_image_src": str|None, "matched": bool`. `slug = f"{category_id}-{normalize_name(name)}"`. Gallery = matched Shopify product's images; `base_image_src` = first gallery image if matched else `None` (download step falls back to docx image). `matched=False` when no Shopify match.

- [ ] **Step 1: Write the failing test**

```python
# build/tests/test_merge.py
from build.merge import merge_catalogue

SHOPIFY = [
    {"title": "Llama - Brooch", "handle": "llama-brooch",
     "images": ["https://x/llama1.jpg", "https://x/llama2.jpg"], "price": 849},
    {"title": "Ruby Sparkle", "handle": "ruby-sparkle",
     "images": ["https://x/ruby1.jpg"], "price": 1399},
]

def _cats():
    return [
        {"name": "Brooches", "id": "brooches", "blurb": "b", "products": [
            {"name": "Llama", "price": 799, "badge": "Bestseller", "variants": [],
             "features": ["100% Handmade"], "category": "Brooches", "docx_image": "d/llama.png"}]},
        {"name": "Collars", "id": "collars", "blurb": "c", "products": [
            {"name": "Ruby Sparkle", "price": 1399, "badge": "Premium", "variants": [],
             "features": [], "category": "Collars", "docx_image": "d/ruby.png"}]},
        {"name": "Rakhi", "id": "rakhi", "blurb": "r", "products": [
            {"name": "Umbrella – Black", "price": 699, "badge": None, "variants": [],
             "features": [], "category": "Rakhi", "docx_image": "d/umb.png"}]},
    ]

def test_matched_product_gets_gallery_and_keeps_docx_price():
    out = merge_catalogue(_cats(), SHOPIFY)
    llama = out[0]["products"][0]
    assert llama["matched"] is True
    assert llama["price"] == 799  # docx wins
    assert llama["gallery"] == ["https://x/llama1.jpg", "https://x/llama2.jpg"]
    assert llama["base_image_src"] == "https://x/llama1.jpg"
    assert llama["slug"] == "brooches-llama"

def test_unmatched_product_has_no_gallery():
    out = merge_catalogue(_cats(), SHOPIFY)
    umb = out[2]["products"][0]
    assert umb["matched"] is False
    assert umb["gallery"] == []
    assert umb["base_image_src"] is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest build/tests/test_merge.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# build/merge.py
from __future__ import annotations
from build.parse_text import normalize_name


def _shopify_index(shopify: list[dict]) -> dict[str, dict]:
    idx: dict[str, dict] = {}
    for p in shopify:
        key = normalize_name(p["title"])
        # First occurrence wins; keep the one with the most images on collision.
        if key not in idx or len(p["images"]) > len(idx[key]["images"]):
            idx[key] = p
    return idx


def merge_catalogue(cats: list[dict], shopify: list[dict]) -> list[dict]:
    idx = _shopify_index(shopify)
    for cat in cats:
        for prod in cat["products"]:
            key = normalize_name(prod["name"], cat["name"])
            match = idx.get(key)
            prod["slug"] = f"{cat['id']}-{key}"
            if match and match["images"]:
                prod["matched"] = True
                prod["gallery"] = list(match["images"])
                prod["base_image_src"] = match["images"][0]
            else:
                prod["matched"] = False
                prod["gallery"] = []
                prod["base_image_src"] = None
    return cats
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest build/tests/test_merge.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add build/merge.py build/tests/test_merge.py
git commit -m "feat: match and merge docx catalogue with Shopify galleries"
```

---

### Task 6: Brand assets — logo + sampled tokens

**Files:**
- Create: `build/brand.py`
- Test: `build/tests/test_brand.py`

**Interfaces:**
- Produces:
  - `DEFAULT_TOKENS: dict` — fallback palette/fonts (the design-approved values) used when sampling fails: keys `ground, card, text, muted, accent, accent_soft, line, gold, serif, sans`.
  - `extract_palette(css_text: str) -> list[str]` — return distinct `#rrggbb` hex colors found in CSS, most frequent first.
  - `build_brand(out_dir: str = "assets/brand", tokens_path: str = "build/brand_tokens.json", logo_url: str = "https://littlepinkllama.com/cdn/shop/collections/LPL_Logo_HD.png", site_url: str = "https://littlepinkllama.com/") -> dict` — downloads the logo to `out_dir/logo.png`, fetches the site, samples colors/fonts, merges over `DEFAULT_TOKENS`, writes `tokens_path`, returns the token dict (always includes `logo` relative path).

- [ ] **Step 1: Write the failing test**

```python
# build/tests/test_brand.py
from build.brand import extract_palette, DEFAULT_TOKENS

def test_extract_palette_orders_by_frequency():
    css = "a{color:#E8587A} b{color:#E8587A} c{background:#FFF1F2}"
    pal = extract_palette(css)
    assert pal[0] == "#e8587a"
    assert "#fff1f2" in pal

def test_default_tokens_have_required_keys():
    for k in ["ground","card","text","muted","accent","accent_soft","line","gold","serif","sans"]:
        assert k in DEFAULT_TOKENS
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest build/tests/test_brand.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# build/brand.py
from __future__ import annotations
import json
import os
import re
from collections import Counter
import requests

DEFAULT_TOKENS = {
    "ground": "#FFF1F2", "card": "#FFFBF7", "text": "#46283A", "muted": "#8A6B7C",
    "accent": "#E8587A", "accent_soft": "#FBE0E7", "line": "#E9C9D2", "gold": "#C98A4B",
    "serif": 'Georgia,"Times New Roman",serif',
    "sans": '-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,system-ui,sans-serif',
}

_HEX_RE = re.compile(r"#([0-9a-fA-F]{6})\b")
_FONT_RE = re.compile(r"font-family\s*:\s*([^;}{]+)", re.IGNORECASE)


def extract_palette(css_text: str) -> list[str]:
    hexes = ["#" + m.group(1).lower() for m in _HEX_RE.finditer(css_text)]
    counts = Counter(hexes)
    return [h for h, _ in counts.most_common()]


def _fetch(url: str) -> str:
    r = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    return r.text


def build_brand(out_dir: str = "assets/brand", tokens_path: str = "build/brand_tokens.json",
                logo_url: str = "https://littlepinkllama.com/cdn/shop/collections/LPL_Logo_HD.png",
                site_url: str = "https://littlepinkllama.com/") -> dict:
    os.makedirs(out_dir, exist_ok=True)
    tokens = dict(DEFAULT_TOKENS)

    # Logo (best-effort; keep default styling if it fails).
    logo_path = os.path.join(out_dir, "logo.png")
    try:
        resp = requests.get(logo_url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        with open(logo_path, "wb") as f:
            f.write(resp.content)
        tokens["logo"] = "assets/brand/logo.png"
    except Exception as e:  # noqa: BLE001 - logging only, build continues
        tokens["logo"] = None
        print(f"[brand] logo download failed: {e}")

    # Sample colors/fonts from the live site (best-effort).
    try:
        html = _fetch(site_url)
        css_links = re.findall(r'<link[^>]+href="([^"]+\.css[^"]*)"', html)
        css_text = html
        for link in css_links[:3]:
            if link.startswith("//"):
                link = "https:" + link
            elif link.startswith("/"):
                link = site_url.rstrip("/") + link
            try:
                css_text += _fetch(link)
            except Exception:
                pass
        pal = extract_palette(css_text)
        pinks = [h for h in pal if int(h[1:3],16) > int(h[5:7],16) and int(h[1:3],16) > 150]
        if pinks:
            tokens["accent"] = pinks[0]
        fonts = _FONT_RE.findall(css_text)
        if fonts:
            tokens["sans"] = fonts[0].strip()
    except Exception as e:  # noqa: BLE001
        print(f"[brand] palette/font sampling failed, using defaults: {e}")

    with open(tokens_path, "w", encoding="utf-8") as f:
        json.dump(tokens, f, indent=2)
    return tokens
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest build/tests/test_brand.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Verify live brand fetch works (manual, networked)**

Run: `python -c "from build.brand import build_brand; print(build_brand())"`
Expected: prints token dict incl. `'logo': 'assets/brand/logo.png'`; `assets/brand/logo.png` exists and is a valid PNG (open it). If logo or sampling fails, defaults are used and a message is printed — acceptable.

- [ ] **Step 6: Commit**

```bash
git add build/brand.py build/tests/test_brand.py assets/brand/logo.png build/brand_tokens.json
git commit -m "feat: download real logo and sample brand tokens from live site"
```

---

### Task 7: Image downloader + resizer

**Files:**
- Create: `build/download_images.py`
- Test: `build/tests/test_download_images.py`

**Interfaces:**
- Consumes: merged category dicts (Task 5).
- Produces:
  - `local_gallery_paths(slug: str, n: int) -> list[str]` — relative paths `images/<slug>/0.jpg ... n-1.jpg`.
  - `download_catalogue_images(cats: list[dict], out_root: str = "images") -> dict` — downloads each product's gallery (Shopify) or copies its docx image as `0.jpg`; resizes so max dimension ≤ 1200px, JPEG quality 85; sets on each product `"images": list[str]` (relative paths, base image first) and `"base_image": images[0] | placeholder`. Returns stats `{"downloaded": int, "from_docx": int, "missing": int}`. Skips files already on disk.

- [ ] **Step 1: Write the failing test**

```python
# build/tests/test_download_images.py
from build.download_images import local_gallery_paths

def test_local_gallery_paths():
    assert local_gallery_paths("brooches-llama", 2) == [
        "images/brooches-llama/0.jpg", "images/brooches-llama/1.jpg"]

def test_local_gallery_paths_zero():
    assert local_gallery_paths("x-y", 0) == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest build/tests/test_download_images.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# build/download_images.py
from __future__ import annotations
import io
import os
import shutil
import requests
from PIL import Image

MAX_DIM = 1200
PLACEHOLDER = "assets/placeholder.png"


def local_gallery_paths(slug: str, n: int) -> list[str]:
    return [f"images/{slug}/{i}.jpg" for i in range(n)]


def _save_resized(blob: bytes, dest: str) -> bool:
    try:
        img = Image.open(io.BytesIO(blob)).convert("RGB")
        img.thumbnail((MAX_DIM, MAX_DIM))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        img.save(dest, "JPEG", quality=85)
        return True
    except Exception as e:  # noqa: BLE001
        print(f"[images] failed to save {dest}: {e}")
        return False


def download_catalogue_images(cats: list[dict], out_root: str = "images") -> dict:
    stats = {"downloaded": 0, "from_docx": 0, "missing": 0}
    for cat in cats:
        for prod in cat["products"]:
            slug = prod["slug"]
            srcs = prod.get("gallery", [])
            saved: list[str] = []
            if srcs:
                for i, src in enumerate(srcs):
                    dest = f"{out_root}/{slug}/{i}.jpg"
                    if os.path.exists(dest):
                        saved.append(dest)
                        continue
                    try:
                        r = requests.get(src, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
                        r.raise_for_status()
                        if _save_resized(r.content, dest):
                            saved.append(dest)
                            stats["downloaded"] += 1
                    except Exception as e:  # noqa: BLE001
                        print(f"[images] download failed {src}: {e}")
            elif prod.get("docx_image") and os.path.exists(prod["docx_image"]):
                dest = f"{out_root}/{slug}/0.jpg"
                if os.path.exists(dest):
                    saved.append(dest)
                else:
                    with open(prod["docx_image"], "rb") as f:
                        if _save_resized(f.read(), dest):
                            saved.append(dest)
                            stats["from_docx"] += 1

            prod["images"] = [p.replace("\\", "/") for p in saved]
            if prod["images"]:
                prod["base_image"] = prod["images"][0]
            else:
                prod["base_image"] = PLACEHOLDER
                stats["missing"] += 1
    return stats
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest build/tests/test_download_images.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Create a placeholder image asset**

Run:
```bash
python -c "from PIL import Image; import os; os.makedirs('assets',exist_ok=True); Image.new('RGB',(600,600),'#FBE0E7').save('assets/placeholder.png')"
```
Expected: `assets/placeholder.png` exists.

- [ ] **Step 6: Commit**

```bash
git add build/download_images.py build/tests/test_download_images.py assets/placeholder.png
git commit -m "feat: download and resize product/docx images"
```

---

### Task 8: Emit `catalogue-data.js`

**Files:**
- Create: `build/emit_data.py`
- Test: `build/tests/test_emit_data.py`

**Interfaces:**
- Consumes: fully merged + image-downloaded category dicts (Tasks 5, 7); brand tokens (Task 6).
- Produces:
  - `build_payload(cats: list[dict], tokens: dict) -> dict` — site-ready structure `{"brand": {...}, "categories": [{"id","name","icon","blurb","products":[{"slug","name","price","price_display","badge","variants","detail","base_image","gallery":[...] }]}], "contact": {...}, "testimonials": [...]}`. `price_display = "₹" + Indian-grouped price`. `detail` = first feature or "100% Handmade". `gallery` = product `images`. Category `icon` from `CATEGORY_ICONS`.
  - `write_data_js(payload: dict, path: str = "catalogue-data.js") -> None` — writes `window.CATALOGUE = <json>;`.
  - `format_inr(n: int) -> str`.

- [ ] **Step 1: Write the failing test**

```python
# build/tests/test_emit_data.py
import json, re
from build.emit_data import build_payload, write_data_js, format_inr

def test_format_inr():
    assert format_inr(799) == "799"
    assert format_inr(1499) == "1,499"

def _cats():
    return [{"name":"Brooches","id":"brooches","blurb":"b","products":[
        {"name":"Llama","price":799,"badge":"Bestseller","variants":[],
         "features":["100% Handmade"],"slug":"brooches-llama",
         "images":["images/brooches-llama/0.jpg","images/brooches-llama/1.jpg"],
         "base_image":"images/brooches-llama/0.jpg"}]}]

def test_payload_shape():
    p = build_payload(_cats(), {"accent":"#E8587A","logo":"assets/brand/logo.png"})
    prod = p["categories"][0]["products"][0]
    assert prod["price_display"] == "₹799"
    assert prod["detail"] == "100% Handmade"
    assert prod["gallery"] == ["images/brooches-llama/0.jpg","images/brooches-llama/1.jpg"]
    assert p["brand"]["accent"] == "#E8587A"
    assert p["contact"]["whatsapp"] == "+91 94600 74404"

def test_write_data_js(tmp_path):
    p = build_payload(_cats(), {"accent":"#E8587A"})
    out = tmp_path/"catalogue-data.js"
    write_data_js(p, str(out))
    text = out.read_text(encoding="utf-8")
    assert text.startswith("window.CATALOGUE =")
    json.loads(re.sub(r"^window\.CATALOGUE\s*=\s*|;\s*$", "", text.strip()))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest build/tests/test_emit_data.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# build/emit_data.py
from __future__ import annotations
import json

CATEGORY_ICONS = {"rakhi": "✸", "bathrobes": "✤", "brooches": "✦",
                  "hairclips": "✿", "collars": "❤"}

CONTACT = {"whatsapp": "+91 94600 74404", "email": "lplkidscouture@gmail.com",
           "website": "www.littlepinkllama.com", "instagram": "@little_pink_llama_"}

TESTIMONIALS = [
    {"quote": "The detailing is exquisite — felt very premium!", "author": "Anisha"},
    {"quote": "Everyone at the party asked where it was from!", "author": "Shilpa L.B."},
    {"quote": "Love the quality. Do you do baby shower hampers?", "author": "Divya S."},
]


def format_inr(n: int) -> str:
    s = str(n)
    if len(s) <= 3:
        return s
    head, tail = s[:-3], s[-3:]
    parts = []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    parts.insert(0, head)
    return ",".join(parts) + "," + tail


def build_payload(cats: list[dict], tokens: dict) -> dict:
    out_cats = []
    for cat in cats:
        prods = []
        for p in cat["products"]:
            detail = (p.get("features") or ["100% Handmade"])[0]
            prods.append({
                "slug": p["slug"], "name": p["name"], "price": p["price"],
                "price_display": "₹" + format_inr(p["price"]),
                "badge": p.get("badge"), "variants": p.get("variants", []),
                "detail": detail, "base_image": p["base_image"],
                "gallery": p.get("images", []),
            })
        out_cats.append({"id": cat["id"], "name": cat["name"],
                         "icon": CATEGORY_ICONS.get(cat["id"], "✦"),
                         "blurb": cat["blurb"], "products": prods})
    return {"brand": tokens, "categories": out_cats,
            "contact": CONTACT, "testimonials": TESTIMONIALS}


def write_data_js(payload: dict, path: str = "catalogue-data.js") -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write("window.CATALOGUE = ")
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write(";\n")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest build/tests/test_emit_data.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add build/emit_data.py build/tests/test_emit_data.py
git commit -m "feat: emit catalogue-data.js payload"
```

---

### Task 9: Pipeline orchestrator + report

**Files:**
- Create: `build/run.py`
- Test: `build/tests/test_run_smoke.py`

**Interfaces:**
- Consumes: every build module above.
- Produces:
  - `run(refresh: bool = False) -> dict` — runs extract → fetch → merge → brand → images → emit; writes `build-report.txt`; returns a summary dict `{"products","matched","unmatched":[slug...],"images":{...}}`. Does NOT build the PDF (Task 11 adds that call).
  - CLI: `python build/run.py [--refresh]`.

- [ ] **Step 1: Write the failing smoke test**

```python
# build/tests/test_run_smoke.py
import os
from build.run import run

def test_run_produces_data_and_report():
    summary = run(refresh=False)
    assert summary["products"] > 40       # all docx products across 5 categories
    assert os.path.exists("catalogue-data.js")
    assert os.path.exists("build-report.txt")
    # Rakhi/Bathrobes are docx-only → some unmatched is expected and fine.
    assert isinstance(summary["unmatched"], list)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest build/tests/test_run_smoke.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'build.run'`

- [ ] **Step 3: Write minimal implementation**

```python
# build/run.py
from __future__ import annotations
import argparse

from build.extract_docx import extract_catalogue
from build.fetch_shopify import load_products
from build.merge import merge_catalogue
from build.brand import build_brand
from build.download_images import download_catalogue_images
from build.emit_data import build_payload, write_data_js

DOCX = "base_data/LittlePinkLlama_Catalogue_v3.docx"


def run(refresh: bool = False) -> dict:
    cats = extract_catalogue(DOCX, "build/.cache/docx_images")
    shopify = load_products(refresh=refresh)
    cats = merge_catalogue(cats, shopify)
    tokens = build_brand()
    img_stats = download_catalogue_images(cats)

    payload = build_payload(cats, tokens)
    write_data_js(payload)

    products = [p for c in cats for p in c["products"]]
    unmatched = [p["slug"] for p in products if not p["matched"]]
    summary = {"products": len(products), "matched": len(products) - len(unmatched),
               "unmatched": unmatched, "images": img_stats}

    with open("build-report.txt", "w", encoding="utf-8") as f:
        f.write("Little Pink Llama — build report\n")
        f.write(f"Products parsed: {summary['products']}\n")
        f.write(f"Matched to Shopify: {summary['matched']}\n")
        f.write(f"Images downloaded: {img_stats['downloaded']}, "
                f"from docx: {img_stats['from_docx']}, missing: {img_stats['missing']}\n")
        f.write("Unmatched (docx-only, expected for Rakhi/Bathrobes):\n")
        for s in unmatched:
            f.write(f"  - {s}\n")
    return summary


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true", help="re-fetch Shopify products")
    args = ap.parse_args()
    s = run(refresh=args.refresh)
    print(f"Done. {s['matched']}/{s['products']} matched. "
          f"Images: {s['images']}. See build-report.txt")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest build/tests/test_run_smoke.py -v`
Expected: PASS. This performs real network calls; ensure connectivity. Inspect `build-report.txt` and confirm matched count is sensible (Brooches/Hair Clips/Collars mostly matched; Rakhi/Bathrobes unmatched).

- [ ] **Step 5: Run the full pipeline and commit generated outputs**

Run: `python build/run.py --refresh`
Then:
```bash
git add build/run.py build/tests/test_run_smoke.py catalogue-data.js build-report.txt images base_data/lpl_products.json
git commit -m "feat: add pipeline orchestrator and generate catalogue data"
```

---

### Task 10: Static site (index.html + styles.css + app.js)

**Files:**
- Create: `index.html`, `assets/styles.css`, `assets/app.js`
- Test: `build/tests/test_site_assets.py`

**Interfaces:**
- Consumes: `catalogue-data.js` (`window.CATALOGUE`), `assets/brand/logo.png`.
- Produces: the rendered single-page site. `app.js` reads `window.CATALOGUE`, renders nav + category sections + cards, wires scrollspy + smooth scroll + lightbox.

- [ ] **Step 1: Write the failing test (asset presence + token wiring)**

```python
# build/tests/test_site_assets.py
import os, re

def test_site_files_exist():
    for f in ["index.html", "assets/styles.css", "assets/app.js"]:
        assert os.path.exists(f), f

def test_index_references_data_and_assets():
    html = open("index.html", encoding="utf-8").read()
    assert "catalogue-data.js" in html
    assert "assets/app.js" in html
    assert "assets/styles.css" in html

def test_styles_use_css_variables():
    css = open("assets/styles.css", encoding="utf-8").read()
    assert "--accent" in css and "--ground" in css

def test_app_reads_catalogue_global():
    js = open("assets/app.js", encoding="utf-8").read()
    assert "window.CATALOGUE" in js
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest build/tests/test_site_assets.py -v`
Expected: FAIL (files do not exist yet)

- [ ] **Step 3: Create `index.html`**

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Little Pink Llama — Catalogue 2026</title>
  <link rel="stylesheet" href="assets/styles.css" />
</head>
<body>
  <header class="bar">
    <div class="wrap bar-in">
      <a class="brand" href="#top"><img id="logo" alt="Little Pink Llama" /></a>
      <nav class="cats" id="nav" aria-label="Categories"></nav>
    </div>
  </header>

  <section class="hero wrap" id="top">
    <div class="eyebrow">Product Catalogue · 2026</div>
    <h1>Handcrafted for <em>little dreamers</em></h1>
    <p>Elegant, comfortable, and made with love — premium, sustainable accessories stitched by hand.</p>
    <div class="hero-actions">
      <a class="btn btn-primary" href="catalogue.pdf" download>⬇ Download Catalogue (PDF)</a>
      <a class="btn btn-ghost" href="#brooches">Browse the collection</a>
    </div>
  </section>

  <main class="wrap" id="cats"></main>

  <footer id="footer"></footer>

  <div class="lb" id="lb" aria-hidden="true">
    <div class="lb-card" role="dialog" aria-modal="true" aria-label="Product gallery">
      <div class="lb-stage" id="lbStage">
        <button class="lb-close" id="lbClose" aria-label="Close">✕</button>
        <button class="lb-nav prev" id="lbPrev" aria-label="Previous image">‹</button>
        <button class="lb-nav next" id="lbNext" aria-label="Next image">›</button>
        <img id="lbImg" alt="" />
      </div>
      <div class="lb-strip" id="lbStrip"></div>
      <div class="lb-info"><h4 id="lbName"></h4><div class="price" id="lbPrice"></div></div>
    </div>
  </div>

  <script src="catalogue-data.js"></script>
  <script src="assets/app.js"></script>
</body>
</html>
```

- [ ] **Step 4: Create `assets/styles.css`**

Use the design-approved tokens. (These mirror `DEFAULT_TOKENS`; `app.js` overrides `--accent` and logo from `window.CATALOGUE.brand` at runtime so site-sampled values win.)

```css
:root{
  --ground:#FFF1F2; --card:#FFFBF7; --text:#46283A; --muted:#8A6B7C;
  --accent:#E8587A; --accent-soft:#FBE0E7; --line:#E9C9D2; --gold:#C98A4B;
  --shadow:24px 32px 60px -36px rgba(70,40,58,.45);
  --serif:Georgia,"Times New Roman",serif;
  --sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,system-ui,sans-serif;
}
*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth;scroll-padding-top:84px}
@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}*{transition:none!important;animation:none!important}}
body{background:var(--ground);color:var(--text);font-family:var(--sans);line-height:1.5;
  -webkit-font-smoothing:antialiased;
  background-image:radial-gradient(circle at 12% 8%,#FFE3EA 0,transparent 42%),radial-gradient(circle at 88% 4%,#FDEFD9 0,transparent 38%);}
.wrap{max-width:1120px;margin:0 auto;padding:0 24px}
header.bar{position:sticky;top:0;z-index:40;background:rgba(255,241,242,.86);backdrop-filter:blur(10px);border-bottom:1px solid var(--line)}
.bar-in{display:flex;align-items:center;gap:18px;height:68px}
.brand{display:flex;align-items:center}
.brand img{height:42px;width:auto;display:block}
nav.cats{display:flex;gap:6px;margin-left:auto;flex-wrap:wrap;justify-content:flex-end}
nav.cats a{font-size:13.5px;color:var(--muted);text-decoration:none;padding:8px 14px;border-radius:999px;border:1.5px dashed transparent;transition:.18s;font-weight:600}
nav.cats a:hover{color:var(--text);background:var(--accent-soft)}
nav.cats a.active{color:var(--accent);border-color:var(--accent);background:#fff}
nav.cats a:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.hero{padding:74px 0 56px;text-align:center}
.eyebrow{font-size:12px;letter-spacing:.32em;text-transform:uppercase;color:var(--accent);font-weight:700;margin-bottom:18px}
.hero h1{font-family:var(--serif);font-weight:700;font-size:clamp(40px,7vw,76px);line-height:1.02;letter-spacing:-.5px}
.hero h1 em{font-style:italic;color:var(--accent)}
.hero p{max-width:540px;margin:22px auto 0;color:var(--muted);font-size:18px}
.hero-actions{display:flex;gap:14px;justify-content:center;margin-top:34px;flex-wrap:wrap}
.btn{font-size:15px;font-weight:700;border:none;cursor:pointer;border-radius:999px;padding:15px 28px;text-decoration:none;display:inline-flex;align-items:center;gap:9px;transition:.18s}
.btn-primary{background:var(--accent);color:#fff;box-shadow:0 12px 26px -12px var(--accent)}
.btn-primary:hover{transform:translateY(-2px)}
.btn-ghost{background:#fff;color:var(--text);border:1.5px solid var(--line)}
.btn-ghost:hover{border-color:var(--accent);color:var(--accent)}
.btn:focus-visible{outline:2px solid var(--accent);outline-offset:3px}
section.cat{padding:46px 0 14px;scroll-margin-top:84px}
.cat-head{display:flex;align-items:flex-end;gap:16px;margin-bottom:6px}
.cat-head h2{font-family:var(--serif);font-size:clamp(28px,4vw,40px);font-weight:700;letter-spacing:-.3px}
.cat-head .count{color:var(--muted);font-size:14px;font-weight:600;padding-bottom:8px}
.cat-blurb{color:var(--muted);max-width:620px;font-size:15.5px}
.stitch{height:2px;border:none;border-top:2.5px dashed var(--line);margin:18px 0 28px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:22px}
.card{background:var(--card);border-radius:20px;border:1px solid #F0DCE2;box-shadow:var(--shadow);overflow:hidden;cursor:pointer;transition:transform .2s,box-shadow .2s;position:relative;text-align:left}
.card:hover{transform:translateY(-5px)}
.card:focus-visible{outline:2px solid var(--accent);outline-offset:3px}
.thumb{aspect-ratio:1/1;position:relative;background:var(--accent-soft)}
.thumb img{width:100%;height:100%;object-fit:cover;display:block}
.thumb .more{position:absolute;right:10px;bottom:10px;background:rgba(70,40,58,.78);color:#fff;font-size:11px;font-weight:700;padding:5px 10px;border-radius:999px}
.badge{position:absolute;left:12px;top:12px;font-size:11px;font-weight:800;letter-spacing:.04em;text-transform:uppercase;padding:6px 11px;border-radius:999px;background:#fff;color:var(--accent);box-shadow:0 4px 10px -4px rgba(70,40,58,.4)}
.badge.gold{color:var(--gold)}
.meta{padding:16px 18px 20px}
.meta .name{font-family:var(--serif);font-size:18px;font-weight:700;margin-bottom:4px}
.row{display:flex;align-items:center;justify-content:space-between;margin-top:8px}
.price{font-weight:800;font-size:16px}
.dots{display:flex;gap:5px}
.dots i{width:13px;height:13px;border-radius:50%;border:1.5px solid #fff;box-shadow:0 0 0 1px var(--line);display:inline-block}
.tag{font-size:11px;color:var(--muted);background:var(--accent-soft);padding:4px 9px;border-radius:6px;font-weight:700}
footer{margin-top:60px;background:var(--text);color:#FCE9EF}
.foot-cta{text-align:center;padding:54px 24px 36px}
.foot-cta h3{font-family:var(--serif);font-size:30px;margin-bottom:10px}
.foot-cta p{color:#D9B8C6;max-width:440px;margin:0 auto 22px}
.quotes{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:18px;max-width:1000px;margin:0 auto;padding:0 24px 30px}
.quote{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.12);border-radius:16px;padding:20px}
.quote p{font-family:var(--serif);font-style:italic;font-size:15.5px;margin-bottom:10px}
.quote span{font-size:13px;color:#E8A6BE;font-weight:700}
.foot-bottom{border-top:1px solid rgba(255,255,255,.12);padding:22px 24px;display:flex;gap:18px;justify-content:center;flex-wrap:wrap;font-size:14px}
.foot-bottom a{color:#FCE9EF;text-decoration:none;font-weight:600}
.lb{position:fixed;inset:0;z-index:90;background:rgba(46,24,38,.72);backdrop-filter:blur(6px);display:none;place-items:center;padding:24px}
.lb.open{display:grid}
.lb-card{background:var(--card);border-radius:22px;max-width:600px;width:100%;overflow:hidden;box-shadow:0 40px 90px -40px #000}
.lb-stage{aspect-ratio:1/1;position:relative;background:var(--accent-soft)}
.lb-stage img{width:100%;height:100%;object-fit:contain;display:block}
.lb-nav{position:absolute;top:50%;transform:translateY(-50%);width:44px;height:44px;border-radius:50%;border:none;background:#fff;color:var(--text);font-size:20px;cursor:pointer;box-shadow:0 6px 16px -6px rgba(0,0,0,.4)}
.lb-nav.prev{left:14px}.lb-nav.next{right:14px}
.lb-close{position:absolute;right:14px;top:14px;width:40px;height:40px;border-radius:50%;border:none;background:#fff;cursor:pointer;font-size:18px;z-index:2}
.lb-strip{display:flex;gap:8px;padding:14px;justify-content:center;background:#fff;flex-wrap:wrap}
.lb-strip img{width:54px;height:54px;border-radius:10px;object-fit:cover;cursor:pointer;border:2px solid transparent}
.lb-strip img.on{border-color:var(--accent)}
.lb-info{padding:6px 20px 22px;text-align:center}
.lb-info h4{font-family:var(--serif);font-size:22px}
.lb-info .price{font-size:18px;margin-top:6px}
.btn:focus-visible,.lb-nav:focus-visible,.lb-close:focus-visible,.lb-strip img:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
```

- [ ] **Step 5: Create `assets/app.js`**

```javascript
(function () {
  "use strict";
  var C = window.CATALOGUE;
  if (!C) {
    document.getElementById("cats").innerHTML =
      '<p style="text-align:center;padding:60px;color:#8A6B7C">Catalogue data not loaded. Run the build pipeline.</p>';
    return;
  }

  // Brand overrides (site-sampled accent + real logo).
  if (C.brand && C.brand.accent) document.documentElement.style.setProperty("--accent", C.brand.accent);
  var logo = document.getElementById("logo");
  logo.src = (C.brand && C.brand.logo) ? C.brand.logo : "assets/brand/logo.png";

  function el(tag, cls, html) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html != null) e.innerHTML = html;
    return e;
  }
  function isGold(badge) { return badge && /premium/i.test(badge); }

  // Nav
  var nav = document.getElementById("nav");
  C.categories.forEach(function (cat) {
    var a = el("a", null, cat.icon + " " + cat.name);
    a.href = "#" + cat.id;
    a.dataset.id = cat.id;
    nav.appendChild(a);
  });

  // Sections
  var root = document.getElementById("cats");
  C.categories.forEach(function (cat) {
    var sec = el("section", "cat");
    sec.id = cat.id;
    sec.appendChild(el("div", "cat-head",
      '<h2>' + cat.icon + " " + cat.name + '</h2><span class="count">' +
      cat.products.length + ' designs</span>'));
    sec.appendChild(el("p", "cat-blurb", cat.blurb));
    sec.appendChild(el("hr", "stitch"));
    var grid = el("div", "grid");
    cat.products.forEach(function (p) {
      var card = el("div", "card");
      card.tabIndex = 0;
      var hasGallery = p.gallery && p.gallery.length > 1;
      var dots = (p.variants && p.variants.length)
        ? '<span class="dots">' + p.variants.map(function () {
            return '<i style="background:' + "#E8587A" + '"></i>'; }).join("") + "</span>"
        : '<span class="tag">' + (p.detail || "100% handmade") + "</span>";
      card.innerHTML =
        '<div class="thumb"><img loading="lazy" src="' + p.base_image + '" alt="' + p.name + '" />' +
        (p.badge ? '<span class="badge ' + (isGold(p.badge) ? "gold" : "") + '">★ ' + p.badge + "</span>" : "") +
        (hasGallery ? '<span class="more">📷 ' + p.gallery.length + "</span>" : "") +
        '</div><div class="meta"><div class="name">' + p.name + '</div>' +
        '<div class="row"><span class="price">' + p.price_display + "</span>" + dots + "</div></div>";
      card.addEventListener("click", function () { openLB(p); });
      card.addEventListener("keydown", function (e) { if (e.key === "Enter") openLB(p); });
      grid.appendChild(card);
    });
    sec.appendChild(grid);
    root.appendChild(sec);
  });

  // Footer
  var ct = C.contact;
  document.getElementById("footer").innerHTML =
    '<div class="foot-cta"><h3>We accept bulk orders</h3>' +
    '<p>Gifting hampers, baby showers, return gifts — reach out for bulk pricing.</p>' +
    '<a class="btn btn-primary" href="https://wa.me/919460074404">💬 WhatsApp ' + ct.whatsapp + "</a></div>" +
    '<div class="quotes">' + C.testimonials.map(function (t) {
      return '<div class="quote"><p>“' + t.quote + '”</p><span>— ' + t.author + "</span></div>"; }).join("") +
    "</div>" +
    '<div class="foot-bottom"><a href="https://littlepinkllama.com">' + ct.website + "</a>" +
    '<a href="mailto:' + ct.email + '">' + ct.email + "</a>" +
    '<a href="https://instagram.com/little_pink_llama_">' + ct.instagram + "</a></div>";

  // Scrollspy
  var links = Array.prototype.slice.call(document.querySelectorAll("nav.cats a"));
  var spy = new IntersectionObserver(function (es) {
    es.forEach(function (e) {
      if (e.isIntersecting) links.forEach(function (l) {
        l.classList.toggle("active", l.dataset.id === e.target.id); });
    });
  }, { rootMargin: "-45% 0px -50% 0px" });
  C.categories.forEach(function (cat) { spy.observe(document.getElementById(cat.id)); });

  // Lightbox
  var lb = document.getElementById("lb"), img = document.getElementById("lbImg"),
      strip = document.getElementById("lbStrip");
  var frames = [], cur = 0;
  function openLB(p) {
    frames = (p.gallery && p.gallery.length) ? p.gallery : [p.base_image];
    cur = 0;
    document.getElementById("lbName").textContent = p.name;
    document.getElementById("lbPrice").textContent = p.price_display;
    var multi = frames.length > 1;
    document.getElementById("lbPrev").style.display = multi ? "block" : "none";
    document.getElementById("lbNext").style.display = multi ? "block" : "none";
    strip.style.display = multi ? "flex" : "none";
    strip.innerHTML = frames.map(function (f, i) {
      return '<img data-i="' + i + '" class="' + (i === 0 ? "on" : "") + '" src="' + f + '" alt="" />'; }).join("");
    Array.prototype.forEach.call(strip.children, function (t) {
      t.onclick = function () { cur = +t.dataset.i; render(); }; });
    render();
    lb.classList.add("open"); lb.setAttribute("aria-hidden", "false");
  }
  function render() {
    img.src = frames[cur];
    Array.prototype.forEach.call(strip.children, function (t, i) {
      t.classList.toggle("on", i === cur); });
  }
  function close() { lb.classList.remove("open"); lb.setAttribute("aria-hidden", "true"); }
  document.getElementById("lbClose").onclick = close;
  document.getElementById("lbPrev").onclick = function () { cur = (cur - 1 + frames.length) % frames.length; render(); };
  document.getElementById("lbNext").onclick = function () { cur = (cur + 1) % frames.length; render(); };
  lb.addEventListener("click", function (e) { if (e.target === lb) close(); });
  document.addEventListener("keydown", function (e) {
    if (!lb.classList.contains("open")) return;
    if (e.key === "Escape") close();
    if (e.key === "ArrowRight") document.getElementById("lbNext").click();
    if (e.key === "ArrowLeft") document.getElementById("lbPrev").click();
  });
})();
```

- [ ] **Step 6: Run asset test to verify it passes**

Run: `pytest build/tests/test_site_assets.py -v`
Expected: PASS (4 passed)

- [ ] **Step 7: Visual verification in a browser**

Run: `python -m http.server 8000` then open `http://localhost:8000/`.
Verify: real logo in header; real photos on cards; sticky nav scrolls + active pill highlights; clicking a Brooch/Hair Clip/Collar opens a multi-image gallery; Rakhi/Bathrobes open single image; Esc/arrows/click-outside work; mobile width (DevTools) reflows to 1–2 columns; PDF button present (file added next task).

- [ ] **Step 8: Commit**

```bash
git add index.html assets/styles.css assets/app.js build/tests/test_site_assets.py
git commit -m "feat: render static catalogue site from catalogue-data.js"
```

---

### Task 11: Professional PDF

**Files:**
- Create: `build/pdf_template.py`, `build/build_pdf.py`
- Modify: `build/run.py` (call PDF build at end of `run`)
- Test: `build/tests/test_pdf_template.py`

**Interfaces:**
- Consumes: the payload from `build_payload` (Task 8); brand tokens (Task 6).
- Produces:
  - `render_pdf_html(payload: dict) -> str` — full standalone HTML document for the PDF (cover with logo + title, per-category sections with one image + name/price/badge/variants/detail per product, contact/bulk page). Uses absolute `file://`-friendly relative paths to local images.
  - `build_pdf(payload: dict, out_path: str = "catalogue.pdf") -> None` — renders the HTML with Playwright Chromium `page.pdf()` (A4, print background on).
  - `run()` (Task 9) updated to call `build_pdf(payload)`.

- [ ] **Step 1: Write the failing test**

```python
# build/tests/test_pdf_template.py
from build.pdf_template import render_pdf_html

PAYLOAD = {
  "brand": {"accent": "#E8587A", "logo": "assets/brand/logo.png"},
  "categories": [{"id":"brooches","name":"Brooches","icon":"✦","blurb":"b","products":[
     {"slug":"brooches-llama","name":"Llama","price":799,"price_display":"₹799",
      "badge":"Bestseller","variants":["Red","Green"],"detail":"100% Handmade",
      "base_image":"images/brooches-llama/0.jpg","gallery":["images/brooches-llama/0.jpg"]}]}],
  "contact": {"whatsapp":"+91 94600 74404","email":"e@x.com","website":"w","instagram":"@i"},
  "testimonials": [{"quote":"q","author":"a"}],
}

def test_html_contains_product_and_cover():
    html = render_pdf_html(PAYLOAD)
    assert "<!doctype html>" in html.lower()
    assert "Llama" in html
    assert "₹799" in html
    assert "Brooches" in html
    assert "assets/brand/logo.png" in html

def test_html_lists_variants_and_badge():
    html = render_pdf_html(PAYLOAD)
    assert "Bestseller" in html
    assert "Red" in html and "Green" in html
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest build/tests/test_pdf_template.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write `build/pdf_template.py`**

```python
# build/pdf_template.py
from __future__ import annotations
import html as _html


def _esc(s) -> str:
    return _html.escape(str(s if s is not None else ""))


def _product_card(p: dict) -> str:
    variants = ""
    if p.get("variants"):
        variants = '<div class="pv">Variants: ' + _esc(", ".join(p["variants"])) + "</div>"
    badge = '<span class="pb">★ ' + _esc(p["badge"]) + "</span>" if p.get("badge") else ""
    return (
        '<div class="pcard">'
        '<div class="pimg"><img src="' + _esc(p["base_image"]) + '" /></div>'
        '<div class="pname">' + _esc(p["name"]) + badge + "</div>"
        '<div class="pprice">' + _esc(p["price_display"]) + "</div>"
        '<div class="pdetail">' + _esc(p.get("detail", "")) + "</div>" + variants +
        "</div>"
    )


def _category(cat: dict) -> str:
    cards = "".join(_product_card(p) for p in cat["products"])
    return (
        '<section class="cat">'
        '<h2>' + _esc(cat["icon"]) + " " + _esc(cat["name"]) + "</h2>"
        '<p class="blurb">' + _esc(cat["blurb"]) + "</p>"
        '<div class="pgrid">' + cards + "</div>"
        "</section>"
    )


def render_pdf_html(payload: dict) -> str:
    accent = payload["brand"].get("accent", "#E8587A")
    logo = payload["brand"].get("logo") or ""
    ct = payload["contact"]
    cats = "".join(_category(c) for c in payload["categories"])
    logo_tag = ('<img class="cover-logo" src="' + _esc(logo) + '" />') if logo else ""
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><style>
  @page {{ size: A4; margin: 14mm; }}
  * {{ box-sizing: border-box; }}
  body {{ font-family: Georgia, serif; color: #46283A; margin: 0; }}
  .cover {{ height: 250mm; display:flex; flex-direction:column; align-items:center; justify-content:center;
            text-align:center; page-break-after: always; background:#FFF1F2; }}
  .cover-logo {{ width: 120px; margin-bottom: 24px; }}
  .cover h1 {{ font-size: 42px; margin: 0; }}
  .cover h1 em {{ color: {accent}; font-style: italic; }}
  .cover p {{ color:#8A6B7C; font-size:15px; margin-top:14px; }}
  .cat {{ page-break-before: always; }}
  .cat h2 {{ font-size: 26px; border-bottom: 2.5px dashed #E9C9D2; padding-bottom: 8px; }}
  .blurb {{ color:#8A6B7C; font-size:12px; font-family: Arial, sans-serif; margin: 6px 0 14px; }}
  .pgrid {{ display:grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }}
  .pcard {{ border:1px solid #F0DCE2; border-radius:12px; overflow:hidden; page-break-inside: avoid; }}
  .pimg {{ aspect-ratio:1/1; background:#FBE0E7; }}
  .pimg img {{ width:100%; height:100%; object-fit:cover; display:block; }}
  .pname {{ font-weight:bold; font-size:13px; padding:8px 10px 2px; }}
  .pb {{ color:{accent}; font-size:9px; font-family:Arial,sans-serif; margin-left:6px; }}
  .pprice {{ font-weight:bold; padding:0 10px; color:{accent}; }}
  .pdetail, .pv {{ font-family:Arial,sans-serif; font-size:10px; color:#8A6B7C; padding:2px 10px; }}
  .pv {{ padding-bottom:10px; }}
  .contact {{ page-break-before: always; text-align:center; padding-top:60px; }}
  .contact h2 {{ font-size:24px; }}
  .contact p {{ font-family:Arial,sans-serif; color:#46283A; font-size:14px; }}
</style></head><body>
  <div class="cover">{logo_tag}
    <h1>Handcrafted for <em>little dreamers</em></h1>
    <p>Product Catalogue · 2026 — premium, sustainable, handmade accessories</p>
  </div>
  {cats}
  <section class="contact">
    <h2>We accept bulk orders</h2>
    <p>WhatsApp / Call: {_esc(ct['whatsapp'])}</p>
    <p>Email: {_esc(ct['email'])}</p>
    <p>{_esc(ct['website'])} · {_esc(ct['instagram'])}</p>
  </section>
</body></html>"""
```

- [ ] **Step 4: Write `build/build_pdf.py`**

```python
# build/build_pdf.py
from __future__ import annotations
import os
from playwright.sync_api import sync_playwright
from build.pdf_template import render_pdf_html


def build_pdf(payload: dict, out_path: str = "catalogue.pdf") -> None:
    html = render_pdf_html(payload)
    tmp_html = os.path.abspath("build/.cache/catalogue_pdf.html")
    os.makedirs(os.path.dirname(tmp_html), exist_ok=True)
    with open(tmp_html, "w", encoding="utf-8") as f:
        f.write(html)
    # Serve relative image paths from repo root by loading the HTML via file:// at root.
    root_html = os.path.abspath("catalogue_pdf_render.html")
    with open(root_html, "w", encoding="utf-8") as f:
        f.write(html)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page()
            page.goto("file://" + root_html.replace("\\", "/"))
            page.pdf(path=out_path, format="A4", print_background=True)
            browser.close()
    finally:
        if os.path.exists(root_html):
            os.remove(root_html)
```

- [ ] **Step 5: Wire PDF build into `run()`**

In `build/run.py`, add import and call. Modify the section after `write_data_js(payload)`:

```python
from build.build_pdf import build_pdf   # add near other build imports
```
and immediately after `write_data_js(payload)` add:
```python
    build_pdf(payload)
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `pytest build/tests/test_pdf_template.py -v`
Expected: PASS (2 passed)

- [ ] **Step 7: Generate the PDF and verify visually**

Run: `python build/run.py`
Expected: `catalogue.pdf` created. Open it: branded cover with real logo; one image + name/price/badge/variants per product; every category present; contact page; colors correct; no broken images.

- [ ] **Step 8: Commit**

```bash
git add build/pdf_template.py build/build_pdf.py build/run.py build/tests/test_pdf_template.py catalogue.pdf
git commit -m "feat: generate professional branded catalogue PDF"
```

---

### Task 12: README + GitHub Pages deploy

**Files:**
- Create: `README.md`
- Test: `build/tests/test_readme.py`

**Interfaces:**
- Consumes: nothing at runtime.
- Produces: docs for running the pipeline and deploying.

- [ ] **Step 1: Write the failing test**

```python
# build/tests/test_readme.py
import os
def test_readme_has_run_and_deploy():
    assert os.path.exists("README.md")
    t = open("README.md", encoding="utf-8").read().lower()
    assert "python build/run.py" in t
    assert "github pages" in t
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest build/tests/test_readme.py -v`
Expected: FAIL (no README.md)

- [ ] **Step 3: Write `README.md`**

```markdown
# Little Pink Llama — Catalogue Website

A static single-page catalogue for Little Pink Llama. Product prices and details
come from `base_data/LittlePinkLlama_Catalogue_v3.docx`; image galleries and the
brand logo come from the live Shopify store.

## Build

```bash
pip install -r build/requirements.txt
python -m playwright install chromium
python build/run.py --refresh    # re-fetch Shopify; omit --refresh to use the cache
```

This regenerates `catalogue-data.js`, `images/`, `assets/brand/logo.png`,
`catalogue.pdf`, and `build-report.txt`.

## Run locally

```bash
python -m http.server 8000
# open http://localhost:8000/
```

## Tests

```bash
pytest -q
```

## Deploy (GitHub Pages)

1. Commit all generated files (`catalogue-data.js`, `images/`, `assets/`, `catalogue.pdf`).
2. Push to GitHub.
3. Repo → Settings → Pages → Source: `main` branch, root folder.
4. The site serves at `https://<user>.github.io/lpl-catalogue/`. All paths are
   relative, so it works there and when opened locally.

## Updating the catalogue

Edit the docx (or the live store), then re-run `python build/run.py --refresh`
and commit the changed generated files.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest build/tests/test_readme.py -v`
Expected: PASS

- [ ] **Step 5: Run the full test suite**

Run: `pytest -q`
Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add README.md build/tests/test_readme.py
git commit -m "docs: add build and GitHub Pages deploy instructions"
```

---

## Self-Review

**Spec coverage:**
- Single-page site, 5 categories, docx order → Tasks 3, 8, 10. ✓
- Prices/details/badges/variants from docx → Tasks 2, 3, 8. ✓
- Shopify galleries, base image rules, Rakhi/Bathrobes docx-only → Tasks 4, 5, 7. ✓
- Real logo + sampled brand colors/fonts → Task 6, applied in Tasks 10, 11. ✓
- Sticky category nav + smooth scroll + scrollspy → Task 10. ✓
- Lightbox gallery → Task 10. ✓
- Professional downloadable PDF → Task 11. ✓
- `catalogue-data.js` (no fetch), relative paths, GitHub Pages → Tasks 8, 10, 12. ✓
- Error handling (unmatched→docx image, missing→placeholder, build report) → Tasks 6, 7, 9. ✓
- Exclude site-only Crochet Toys → Task 5 (only docx products are iterated). ✓
- Contact + testimonials → Task 8. ✓

**Placeholder scan:** No TBD/TODO; every code step contains full code; commands have expected output. ✓

**Type consistency:** `parse_product_lines`/`normalize_name` (Task 2) used consistently in Tasks 3, 5. Product dict grows predictably: parse fields → `category,docx_image` (T3) → `slug,gallery,base_image_src,matched` (T5) → `images,base_image` (T7) → payload fields (T8). `build_payload`/`render_pdf_html` consume the same payload shape (Tasks 8, 11). `build_brand` returns tokens incl. `logo`, consumed in Tasks 8/10/11. ✓

**Note for implementer:** Task 9 Step 4 and Task 11 Step 7 make real network calls and require connectivity + `playwright install chromium` (Task 1). The docx table indices (3–7) were verified during design; if Task 3's `test_categories_order` fails, adjust `_TABLE_INDEX`.
