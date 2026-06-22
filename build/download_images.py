from __future__ import annotations
import io
import os
import requests
from PIL import Image

MAX_DIM = 1200
PLACEHOLDER = "assets/placeholder.png"


def local_gallery_paths(slug: str, n: int) -> list[str]:
    return [f"images/{slug}/{i}.jpg" for i in range(n)]


def _save_resized(blob: bytes, dest: str) -> bool:
    try:
        img = Image.open(io.BytesIO(blob)).convert("RGB")
        img.thumbnail((MAX_DIM, MAX_DIM))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        img.save(dest, "JPEG", quality=85)
        return True
    except Exception as e:  # noqa: BLE001
        print(f"[images] failed to save {dest}: {e}")
        return False


def download_catalogue_images(cats: list[dict], out_root: str = "images") -> dict:
    stats = {"downloaded": 0, "from_docx": 0, "missing": 0}
    for cat in cats:
        for prod in cat["products"]:
            slug = prod["slug"]
            srcs = prod.get("gallery", [])
            saved: list[str] = []
            if srcs:
                for i, src in enumerate(srcs):
                    dest = f"{out_root}/{slug}/{i}.jpg"
                    if os.path.exists(dest):
                        saved.append(dest)
                        continue
                    try:
                        r = requests.get(src, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
                        r.raise_for_status()
                        if _save_resized(r.content, dest):
                            saved.append(dest)
                            stats["downloaded"] += 1
                    except Exception as e:  # noqa: BLE001
                        print(f"[images] download failed {src}: {e}")
            elif prod.get("docx_image") and os.path.exists(prod["docx_image"]):
                dest = f"{out_root}/{slug}/0.jpg"
                if os.path.exists(dest):
                    saved.append(dest)
                else:
                    with open(prod["docx_image"], "rb") as f:
                        if _save_resized(f.read(), dest):
                            saved.append(dest)
                            stats["from_docx"] += 1

            prod["images"] = [p.replace("\\", "/") for p in saved]
            if prod["images"]:
                prod["base_image"] = prod["images"][0]
            else:
                prod["base_image"] = PLACEHOLDER
                stats["missing"] += 1
    return stats
