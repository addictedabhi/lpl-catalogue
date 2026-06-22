from build.merge import merge_catalogue

SHOPIFY = [
    {"title": "Llama - Brooch", "handle": "llama-brooch",
     "images": ["https://x/llama1.jpg", "https://x/llama2.jpg"], "price": 849},
    {"title": "Ruby Sparkle", "handle": "ruby-sparkle",
     "images": ["https://x/ruby1.jpg"], "price": 1399},
]

def _cats():
    return [
        {"name": "Brooches", "id": "brooches", "blurb": "b", "products": [
            {"name": "Llama", "price": 799, "badge": "Bestseller", "variants": [],
             "features": ["100% Handmade"], "category": "Brooches", "docx_image": "d/llama.png"}]},
        {"name": "Collars", "id": "collars", "blurb": "c", "products": [
            {"name": "Ruby Sparkle", "price": 1399, "badge": "Premium", "variants": [],
             "features": [], "category": "Collars", "docx_image": "d/ruby.png"}]},
        {"name": "Rakhi", "id": "rakhi", "blurb": "r", "products": [
            {"name": "Umbrella – Black", "price": 699, "badge": None, "variants": [],
             "features": [], "category": "Rakhi", "docx_image": "d/umb.png"}]},
    ]

def test_matched_product_gets_gallery_and_keeps_docx_price():
    out = merge_catalogue(_cats(), SHOPIFY)
    llama = out[0]["products"][0]
    assert llama["matched"] is True
    assert llama["price"] == 799  # docx wins
    assert llama["gallery"] == ["https://x/llama1.jpg", "https://x/llama2.jpg"]
    assert llama["base_image_src"] == "https://x/llama1.jpg"
    assert llama["slug"] == "brooches-llama"

def test_unmatched_product_has_no_gallery():
    out = merge_catalogue(_cats(), SHOPIFY)
    umb = out[2]["products"][0]
    assert umb["matched"] is False
    assert umb["gallery"] == []
    assert umb["base_image_src"] is None

def test_same_name_different_categories_get_correct_galleries():
    shopify = [
        {"title": "Derpy Tiger - Brooch", "handle": "d-b",
         "images": ["https://x/b1.jpg", "https://x/b2.jpg"], "price": 849},
        {"title": "Derpy Tiger - Hair Clips", "handle": "d-h",
         "images": ["https://x/h1.jpg"], "price": 849},
        {"title": "Derpy Tiger Collar", "handle": "d-c",
         "images": ["https://x/c1.jpg", "https://x/c2.jpg", "https://x/c3.jpg"], "price": 1399},
    ]
    cats = [
        {"name": "Brooches", "id": "brooches", "blurb": "", "products": [
            {"name": "Derpy Tiger", "price": 799, "badge": None, "variants": [],
             "features": [], "category": "Brooches", "docx_image": "d/x.png"}]},
        {"name": "Hair Clips", "id": "hairclips", "blurb": "", "products": [
            {"name": "Derpy Tiger", "price": 799, "badge": None, "variants": [],
             "features": [], "category": "Hair Clips", "docx_image": "d/y.png"}]},
        {"name": "Collars", "id": "collars", "blurb": "", "products": [
            {"name": "Derpy Tiger", "price": 1399, "badge": None, "variants": [],
             "features": [], "category": "Collars", "docx_image": "d/z.png"}]},
    ]
    out = merge_catalogue(cats, shopify)
    assert out[0]["products"][0]["base_image_src"] == "https://x/b1.jpg"
    assert out[1]["products"][0]["base_image_src"] == "https://x/h1.jpg"
    assert out[2]["products"][0]["base_image_src"] == "https://x/c1.jpg"
    slugs = [out[i]["products"][0]["slug"] for i in range(3)]
    assert len(set(slugs)) == 3

def test_rakhi_never_matches_shopify():
    shopify = [{"title": "Captain America - Brooch", "handle": "ca-b",
                "images": ["https://x/ca.jpg"], "price": 749}]
    cats = [{"name": "Rakhi", "id": "rakhi", "blurb": "", "products": [
        {"name": "Captain America", "price": 699, "badge": None, "variants": [],
         "features": [], "category": "Rakhi", "docx_image": "d/ca.png"}]}]
    out = merge_catalogue(cats, shopify)
    p = out[0]["products"][0]
    assert p["matched"] is False
    assert p["gallery"] == []
    assert p["base_image_src"] is None
