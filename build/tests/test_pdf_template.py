# build/tests/test_pdf_template.py
from build.pdf_template import render_pdf_html

PAYLOAD = {
  "brand": {"accent": "#E8587A", "logo": "assets/brand/logo.png"},
  "categories": [{"id":"brooches","name":"Brooches","icon":"✦","blurb":"b","products":[
     {"slug":"brooches-llama","name":"Llama","price":8.88,"price_display":"$8.88",
      "badge":"Bestseller","variants":["Red","Green"],"detail":"100% Handmade",
      "base_image":"images/brooches-llama/0.jpg","gallery":["images/brooches-llama/0.jpg"]}]}],
  "contact": {"whatsapp":"+91 94600 74404","email":"e@x.com","website":"w","instagram":"@i"},
  "testimonials": [{"quote":"q","author":"a"}],
}

def test_html_contains_product_and_cover():
    html = render_pdf_html(PAYLOAD)
    assert "<!doctype html>" in html.lower()
    assert "Llama" in html
    assert "$8.88" in html
    assert "Brooches" in html
    assert "assets/brand/logo.png" in html

def test_html_lists_variants_and_badge():
    html = render_pdf_html(PAYLOAD)
    assert "Bestseller" in html
    assert "Red" in html and "Green" in html
