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

def test_normalize_filters_images_without_src():
    raw = {"products": [{"title": "X", "handle": "x",
                         "images": [{"src": ""}, {"src": None}, {}],
                         "variants": [{"price": "10.0"}]}]}
    assert normalize_products(raw)[0]["images"] == []
