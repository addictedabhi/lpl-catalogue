# build/tests/test_site_assets.py
import os, re

def test_site_files_exist():
    for f in ["index.html", "assets/styles.css", "assets/app.js"]:
        assert os.path.exists(f), f

def test_index_references_data_and_assets():
    html = open("index.html", encoding="utf-8").read()
    assert "catalogue-data.js" in html
    assert "assets/app.js" in html
    assert "assets/styles.css" in html

def test_styles_use_css_variables():
    css = open("assets/styles.css", encoding="utf-8").read()
    assert "--accent" in css and "--ground" in css

def test_app_reads_catalogue_global():
    js = open("assets/app.js", encoding="utf-8").read()
    assert "window.CATALOGUE" in js
