# build/merge.py
from __future__ import annotations
from build.parse_text import normalize_name

# docx category id -> Shopify product-type token
_CATEGORY_TYPE = {"brooches": "brooch", "hairclips": "hairclip", "collars": "collar"}


def _title_type(title: str) -> str:
    t = title.lower()
    if "brooch" in t:
        return "brooch"
    if "hair" in t and "clip" in t:
        return "hairclip"
    if "collar" in t:
        return "collar"
    return "other"


def _build_indexes(shopify: list[dict]):
    by_key: dict[tuple[str, str], dict] = {}   # (name, type) -> product
    by_name: dict[str, list[dict]] = {}        # name -> products
    for p in shopify:
        name = normalize_name(p["title"])
        key = (name, _title_type(p["title"]))
        if key not in by_key or len(p["images"]) > len(by_key[key]["images"]):
            by_key[key] = p
        by_name.setdefault(name, []).append(p)
    return by_key, by_name


def _find_match(name: str, cat_id: str, by_key: dict, by_name: dict) -> dict | None:
    typ = _CATEGORY_TYPE.get(cat_id)
    if not typ:                       # rakhi/bathrobes are docx-only: never match
        return None
    m = by_key.get((name, typ))
    if m:
        return m
    candidates = by_name.get(name, [])
    if len(candidates) == 1:          # unambiguous name-only fallback
        return candidates[0]
    return None


def merge_catalogue(cats: list[dict], shopify: list[dict]) -> list[dict]:
    by_key, by_name = _build_indexes(shopify)
    for cat in cats:
        for prod in cat["products"]:
            key = normalize_name(prod["name"], cat["name"])
            match = _find_match(key, cat["id"], by_key, by_name)
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
