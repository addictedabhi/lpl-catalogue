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
