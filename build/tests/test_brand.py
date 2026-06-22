from build.brand import extract_palette, DEFAULT_TOKENS

def test_extract_palette_orders_by_frequency():
    css = "a{color:#E8587A} b{color:#E8587A} c{background:#FFF1F2}"
    pal = extract_palette(css)
    assert pal[0] == "#e8587a"
    assert "#fff1f2" in pal

def test_default_tokens_have_required_keys():
    for k in ["ground","card","text","muted","accent","accent_soft","line","gold","serif","sans"]:
        assert k in DEFAULT_TOKENS

from build.brand import pick_pink, contrast_with_white

def test_pick_pink_excludes_gold():
    assert pick_pink(["#f5cc51"]) is None          # gold/yellow rejected
    assert pick_pink(["#e8587a"]) == "#e8587a"     # raspberry pink accepted

def test_pick_pink_returns_none_when_no_pink():
    assert pick_pink(["#222222", "#ffffff"]) is None

def test_pale_pink_fails_contrast_gate():
    assert contrast_with_white("#ee9599") < 3.0    # pale -> rejected
    assert contrast_with_white("#e8587a") >= 3.0   # raspberry -> ok

from build.brand import discover_logo

def test_discover_logo_from_header_class():
    html = '<a href="/"><img src="//x/cdn/shop/files/realLogo.png?v=1&amp;width=600" alt="Little Pink Llama" class="header__heading-logo motion-reduce"></a>'
    assert discover_logo(html, "DEFAULT") == "https://x/cdn/shop/files/realLogo.png?v=1&width=600"

def test_discover_logo_falls_back():
    assert discover_logo("<div>no logo here</div>", "DEFAULT") == "DEFAULT"
