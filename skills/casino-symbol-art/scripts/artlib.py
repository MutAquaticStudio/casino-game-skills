"""Shared helpers for the art scripts: magenta key-out, crop, fonts, art folder loading.

Not run directly. Imported by slice_symbols.py, compose_screen.py and fx_sprites.py.
"""
import json, os
import numpy as np
from PIL import Image, ImageFilter, ImageFont
from scipy import ndimage as ndi

FONT_BOLD = ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/Library/Fonts/Arial Bold.ttf", "C:/Windows/Fonts/arialbd.ttf"]


def key_out(im):
    """Remove the magenta (#FF00FF) key: strict match plus a 2 px halo into pinkish pixels, then a 1 px defringe."""
    a = np.asarray(im.convert("RGB")).astype(np.int32)
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    mask = (R > 175) & (B > 175) & (G < 115) & (np.abs(R - B) < 60)
    halo = ndi.binary_dilation(mask, iterations=2) & (R > 150) & (B > 120) & (G < 150) & (R - G > 70) & (B - G > 50)
    mask = mask | halo
    alpha = np.where(mask, 0, 255).astype(np.uint8)
    out = Image.fromarray(np.dstack([a.astype(np.uint8), alpha]), "RGBA")
    al = Image.fromarray(alpha).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.8))
    out.putalpha(al)
    return out


def crop_alpha(im, thr=10):
    bb = im.getchannel("A").point(lambda v: 255 if v > thr else 0).getbbox()
    return im.crop(bb) if bb else im


def font(size):
    for p in FONT_BOLD:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def fit(im, box_w, box_h=None):
    box_h = box_h or box_w
    s = min(box_w / im.width, box_h / im.height)
    return im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)


def load_art(art_dir):
    """Return (style, plan_by_asset). Exits with a clear message when the harness has not been run."""
    sp, pp = os.path.join(art_dir, "style.json"), os.path.join(art_dir, "plan.json")
    if not (os.path.exists(sp) and os.path.exists(pp)):
        raise SystemExit(f"{art_dir}/style.json or plan.json missing: run art_harness.py first")
    style = json.load(open(sp))
    plan = {p["asset"]: p for p in json.load(open(pp))["plan"]}
    return style, plan


def layer(art_dir, name, required=True):
    p = os.path.join(art_dir, "layers", name + ".png")
    if not os.path.exists(p):
        if required:
            raise SystemExit(f"missing {p}: generate it from art/prompts/{name}.txt (see plan.json)")
        return None
    return Image.open(p)


def components(alpha_img, closing=6, min_frac=0.02):
    """Bounding slices of the blobs in an RGBA image, ignoring blobs smaller than min_frac of the largest."""
    a = np.asarray(alpha_img.getchannel("A")) > 10
    if closing:
        a = ndi.binary_closing(a, iterations=closing)
    lab, n = ndi.label(a)
    objs = ndi.find_objects(lab)
    if not n:
        return []
    areas = ndi.sum(a, lab, range(1, n + 1))
    keep = [(float(areas[i]), objs[i]) for i in range(n) if areas[i] >= min_frac * areas.max()]
    return keep  # (area, (slice_y, slice_x))
