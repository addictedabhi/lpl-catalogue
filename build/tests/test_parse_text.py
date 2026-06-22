from build.parse_text import parse_product_lines, normalize_name

def test_parse_basic_product():
    lines = ["Llama", "Price", "Rs. 599", "✦ 100% Handmade", "✦ Premium Quality"]
    r = parse_product_lines(lines)
    assert r["name"] == "Llama"
    assert r["price"] == 599
    assert r["badge"] is None
    assert r["variants"] == []
    assert "100% Handmade" in r["features"]

def test_parse_badge_prefix():
    lines = ["★ Bestseller", "Llama", "Price", "Rs. 799", "✦ 100% Handmade"]
    r = parse_product_lines(lines)
    assert r["badge"] == "Bestseller"
    assert r["name"] == "Llama"
    assert r["price"] == 799

def test_parse_color_variants():
    lines = ["Elephant", "Price", "Rs. 799", "✦ 100% Handmade",
             "✦ Color Variants: Red, Green, Pink & Gray"]
    r = parse_product_lines(lines)
    assert r["variants"] == ["Red", "Green", "Pink", "Gray"]

def test_parse_comma_price():
    lines = ["Unicorn Bathrobe", "Price", "Rs. 1,499", "✦ Premium Quality"]
    assert parse_product_lines(lines)["price"] == 1499

def test_parse_empty_returns_none():
    assert parse_product_lines([]) is None
    assert parse_product_lines([""]) is None

def test_normalize_strips_suffix_and_punct():
    assert normalize_name("Amazing Spider man - Brooch", "Brooches") == normalize_name("Amazing Spiderman", "Brooches")
    assert normalize_name("Derpy Tiger Collar", "Collars") == "derpytiger"
