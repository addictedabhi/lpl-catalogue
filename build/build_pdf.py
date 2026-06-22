# build/build_pdf.py
from __future__ import annotations
import os
from playwright.sync_api import sync_playwright
from build.pdf_template import render_pdf_html


def build_pdf(payload: dict, out_path: str = "catalogue.pdf") -> None:
    html = render_pdf_html(payload)
    # Serve relative image paths from repo root by loading the HTML via file:// at root.
    root_html = os.path.abspath("catalogue_pdf_render.html")
    with open(root_html, "w", encoding="utf-8") as f:
        f.write(html)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page()
            page.goto("file://" + root_html.replace("\\", "/"))
            page.pdf(path=out_path, format="A4", print_background=True)
            browser.close()
    finally:
        if os.path.exists(root_html):
            os.remove(root_html)
