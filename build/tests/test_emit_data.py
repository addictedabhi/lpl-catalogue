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
