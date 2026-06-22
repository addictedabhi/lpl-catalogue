# build/run.py
from __future__ import annotations
import argparse
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from build.extract_docx import extract_catalogue
from build.fetch_shopify import load_products
from build.merge import merge_catalogue
from build.brand import build_brand
from build.download_images import download_catalogue_images
from build.emit_data import build_payload, write_data_js
from build.build_pdf import build_pdf

DOCX = "base_data/LittlePinkLlama_Catalogue_v3.docx"


def run(refresh: bool = False) -> dict:
    cats = extract_catalogue(DOCX, "build/.cache/docx_images")
    shopify = load_products(refresh=refresh)
    cats = merge_catalogue(cats, shopify)
    tokens = build_brand()
    img_stats = download_catalogue_images(cats)

    payload = build_payload(cats, tokens)
    write_data_js(payload)
    build_pdf(payload)

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
