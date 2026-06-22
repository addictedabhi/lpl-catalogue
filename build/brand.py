from __future__ import annotations
import json
import os
import re
from collections import Counter
import requests

DEFAULT_TOKENS = {
    "ground": "#FFF1F2", "card": "#FFFBF7", "text": "#46283A", "muted": "#8A6B7C",
    "accent": "#E8587A", "accent_soft": "#FBE0E7", "line": "#E9C9D2", "gold": "#C98A4B",
    "serif": 'Georgia,"Times New Roman",serif',
    "sans": '-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,system-ui,sans-serif',
}

_HEX_RE = re.compile(r"#([0-9a-fA-F]{6})\b")
_FONT_RE = re.compile(r"font-family\s*:\s*([^;}{]+)", re.IGNORECASE)
_LOGO_TAG_RE = re.compile(r'<img[^>]*header__heading-logo[^>]*>', re.IGNORECASE)
_SRC_ATTR_RE = re.compile(r'src="([^"]+)"')


def discover_logo(html: str, default: str) -> str:
    """Find the site's header (masthead) logo URL from homepage HTML."""
    tag = _LOGO_TAG_RE.search(html)
    if tag:
        src = _SRC_ATTR_RE.search(tag.group(0))
        if src:
            url = src.group(1).replace("&amp;", "&").strip()
            if url.startswith("//"):
                url = "https:" + url
            return url
    return default


def _rel_luminance(hex_color: str) -> float:
    """WCAG relative luminance of an #rrggbb color."""
    def chan(c: float) -> float:
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * chan(r) + 0.7152 * chan(g) + 0.0722 * chan(b)


def contrast_with_white(hex_color: str) -> float:
    """Contrast ratio of white text on the given background color."""
    lum = _rel_luminance(hex_color)
    return (1.0 + 0.05) / (lum + 0.05)


def pick_pink(palette: list[str]) -> str | None:
    """Return the first hex in palette that reads as a pink, else None.
    Pink = red channel dominant, clearly above green (excludes gold/yellow)."""
    for h in palette:
        r, g, b = int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)
        if r > 150 and (r - g) > 50 and (r - b) > 30 and g < 190:
            return h
    return None


def extract_palette(css_text: str) -> list[str]:
    hexes = ["#" + m.group(1).lower() for m in _HEX_RE.finditer(css_text)]
    counts = Counter(hexes)
    return [h for h, _ in counts.most_common()]


def _fetch(url: str) -> str:
    r = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    return r.text


def build_brand(out_dir: str = "assets/brand", tokens_path: str = "build/brand_tokens.json",
                logo_url: str = "https://littlepinkllama.com/cdn/shop/files/ChatGPT_Image_Feb_21_2026_06_53_33_PM_30d39ff7-a5af-4803-ab17-a5b65983ba53.png?v=1771774533&width=600",
                site_url: str = "https://littlepinkllama.com/") -> dict:
    os.makedirs(out_dir, exist_ok=True)
    tokens = dict(DEFAULT_TOKENS)

    # Discover the real masthead logo from the homepage (fall back to default URL).
    resolved_logo_url = logo_url
    home_html: str | None = None
    try:
        home_html = _fetch(site_url)
        resolved_logo_url = discover_logo(home_html, logo_url)
    except Exception as e:  # noqa: BLE001
        print(f"[brand] logo discovery failed, using default URL: {e}")

    # Logo (best-effort; keep default styling if it fails).
    logo_path = os.path.join(out_dir, "logo.png")
    try:
        resp = requests.get(resolved_logo_url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        with open(logo_path, "wb") as f:
            f.write(resp.content)
        tokens["logo"] = "assets/brand/logo.png"
    except Exception as e:  # noqa: BLE001 - logging only, build continues
        tokens["logo"] = None
        print(f"[brand] logo download failed: {e}")

    # Sample colors/fonts from the live site (best-effort).
    try:
        html = home_html if home_html is not None else _fetch(site_url)
        css_links = re.findall(r'<link[^>]+href="([^"]+\.css[^"]*)"', html)
        css_text = html
        for link in css_links[:3]:
            if link.startswith("//"):
                link = "https:" + link
            elif link.startswith("/"):
                link = site_url.rstrip("/") + link
            try:
                css_text += _fetch(link)
            except Exception:
                pass
        pal = extract_palette(css_text)
        pink = pick_pink(pal)
        # Only adopt a sampled pink if white button text stays legible on it
        # (WCAG-ish >= 3.0); otherwise keep the vibrant default raspberry.
        if pink and contrast_with_white(pink) >= 3.0:
            tokens["accent"] = pink
        fonts = _FONT_RE.findall(css_text)
        if fonts:
            sampled = fonts[0].strip().rstrip(";")
            # Keep the sampled brand font but always retain a fallback stack.
            tokens["sans"] = sampled + ", " + DEFAULT_TOKENS["sans"]
    except Exception as e:  # noqa: BLE001
        print(f"[brand] palette/font sampling failed, using defaults: {e}")

    with open(tokens_path, "w", encoding="utf-8") as f:
        json.dump(tokens, f, indent=2)
    return tokens
