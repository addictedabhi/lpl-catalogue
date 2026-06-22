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
