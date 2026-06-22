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
