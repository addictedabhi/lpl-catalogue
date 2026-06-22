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
