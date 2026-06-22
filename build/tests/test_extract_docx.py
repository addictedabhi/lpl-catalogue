import os
from build.extract_docx import extract_catalogue, CATEGORY_TABLES

DOCX = "base_data/LittlePinkLlama_Catalogue_v3.docx"

def test_categories_order():
    cats = extract_catalogue(DOCX, "build/.cache/docx_images_test")
    assert [c["id"] for c in cats] == [cid for _, cid in CATEGORY_TABLES]

def test_brooches_has_bestseller_llama():
    cats = extract_catalogue(DOCX, "build/.cache/docx_images_test")
    brooches = next(c for c in cats if c["id"] == "brooches")
    llama = next(p for p in brooches["products"] if p["name"] == "Llama")
    assert llama["badge"] == "Bestseller"
    assert llama["price"] == 799

def test_bathrobes_count_and_price():
    cats = extract_catalogue(DOCX, "build/.cache/docx_images_test")
    bath = next(c for c in cats if c["id"] == "bathrobes")
    assert len(bath["products"]) == 3
    assert all(p["price"] == 1499 for p in bath["products"])

def test_docx_images_saved():
    out = "build/.cache/docx_images_test"
    cats = extract_catalogue(DOCX, out)
    bath = next(c for c in cats if c["id"] == "bathrobes")
    imgs = [p["docx_image"] for p in bath["products"] if p["docx_image"]]
    assert len(imgs) >= 1
    assert os.path.exists(imgs[0])
    assert len(imgs) == len(bath["products"])  # every product got an image
    assert len(set(imgs)) == len(imgs)         # each image is distinct
