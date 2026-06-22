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
