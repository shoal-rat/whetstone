#!/usr/bin/env python3
"""Look at captures the way an art director does, and put numbers on it.

For each image: a contact-sheet row (colour, value/greyscale, three-tone squint,
thumbnail) plus statistics: luminance spread, contrast, clipping, value
structure, saturation, colourfulness, dominant hues and edge density. Compare
against a reference or a before shot, and measure light ratios between patches.

  python3 look.py shot.png -o sheet.png
  python3 look.py after.png --before before.png -o sheet.png
  python3 look.py shot.png --ref target.jpg --patch lit=820,300,60,60 --patch shadow=900,420,60,60

Patches are x,y,w,h in the image's own pixels. Ratios use linear light, which is
what "a 3:1 key-to-fill ratio" means; stops = log2(ratio).

Needs Pillow:  python3 -m pip install pillow
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps
except ImportError:
    sys.exit("look.py needs Pillow:  python3 -m pip install pillow")

PANEL_W = 480
HUE_NAMES = ["red", "orange", "yellow", "yellow-green", "green", "green-cyan", "cyan", "azure",
             "blue", "violet", "magenta", "rose"]


def percentile(hist: list[int], q: float) -> int:
    total = sum(hist)
    if not total:
        return 0
    target, acc = total * q, 0
    for v, n in enumerate(hist):
        acc += n
        if acc >= target:
            return v
    return len(hist) - 1


def srgb_to_linear(v: float) -> float:
    c = v / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


LIN = [srgb_to_linear(v) for v in range(256)]


def pixels(img: Image.Image):
    """Pixel values; uses the newer Pillow API when present."""
    fn = getattr(img, "get_flattened_data", None)
    return fn() if fn else img.getdata()


def luma(img: Image.Image) -> Image.Image:
    """Rec. 709 luma from sRGB as an L image."""
    return img.convert("RGB").convert("L", (0.2126, 0.7152, 0.0722, 0))


def stats(img: Image.Image) -> dict:
    rgb = img.convert("RGB")
    small = rgb.copy()
    small.thumbnail((360, 360))
    L = luma(rgb)
    h = L.histogram()
    n = sum(h)
    mean = sum(v * c for v, c in enumerate(h)) / n
    var = sum(((v - mean) ** 2) * c for v, c in enumerate(h)) / n
    hsv = small.convert("HSV")
    hh, ss, vv = hsv.split()
    sh = ss.histogram()
    sn = sum(sh)
    # Hasler & Süsstrunk colourfulness on the thumbnail.
    rg, yb = [], []
    for r, g, b in pixels(small):
        rg.append(r - g)
        yb.append(0.5 * (r + g) - b)
    def ms(xs):
        m = sum(xs) / len(xs)
        return m, math.sqrt(sum((x - m) ** 2 for x in xs) / len(xs))
    (mrg, srg), (myb, syb) = ms(rg), ms(yb)
    colourful = math.sqrt(srg ** 2 + syb ** 2) + 0.3 * math.sqrt(mrg ** 2 + myb ** 2)
    # Dominant hues, weighted by saturation, ignoring near-greys and near-blacks.
    buckets = [0.0] * 12
    for hue, sat, val in zip(pixels(hh), pixels(ss), pixels(vv)):
        if sat > 40 and val > 30:
            buckets[int(hue / 256 * 12) % 12] += sat
    tot = sum(buckets) or 1
    hues = sorted(((b / tot, HUE_NAMES[i]) for i, b in enumerate(buckets)), reverse=True)[:3]
    edges = luma(small).filter(ImageFilter.FIND_EDGES).histogram()
    en = sum(edges)
    return {
        "size": f"{img.width}x{img.height}",
        "luma_p2": percentile(h, 0.02), "luma_p50": percentile(h, 0.5), "luma_p98": percentile(h, 0.98),
        "luma_mean": round(mean, 1),
        "rms_contrast": round(math.sqrt(var) / 255, 3),
        "clip_dark_pct": round(100 * sum(h[:6]) / n, 2),
        "clip_bright_pct": round(100 * sum(h[250:]) / n, 2),
        "shadows_pct": round(100 * sum(h[:85]) / n, 1),
        "midtones_pct": round(100 * sum(h[85:170]) / n, 1),
        "highlights_pct": round(100 * sum(h[170:]) / n, 1),
        "sat_mean": round(sum(v * c for v, c in enumerate(sh)) / sn / 255, 3),
        "sat_p90": round(percentile(sh, 0.9) / 255, 3),
        "colourfulness": round(colourful, 1),
        "dominant_hues": [f"{name} {share:.0%}" for share, name in hues if share > 0.05] or ["(near-grey)"],
        "edge_density_pct": round(100 * sum(edges[32:]) / en, 1),
    }


def patch_lum(img: Image.Image, box: tuple[int, int, int, int]) -> float:
    x, y, w, h = box
    crop = img.convert("RGB").crop((x, y, x + w, y + h))
    vals = [0.2126 * LIN[r] + 0.7152 * LIN[g] + 0.0722 * LIN[b] for r, g, b in pixels(crop)]
    return sum(vals) / max(len(vals), 1)


def font(size: int):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def fit(img: Image.Image, w: int) -> Image.Image:
    return img.resize((w, max(1, round(img.height * w / img.width))), Image.LANCZOS)


def row(img: Image.Image, label: str, patches: dict) -> Image.Image:
    rgb = img.convert("RGB")
    if patches:
        rgb = rgb.copy()
        d = ImageDraw.Draw(rgb)
        lw = max(2, rgb.width // 400)
        for name, (x, y, w, h) in patches.items():
            d.rectangle((x, y, x + w, y + h), outline=(255, 0, 180), width=lw)
            d.text((x + lw * 2, y + lw * 2), name, fill=(255, 0, 180), font=font(max(14, rgb.width // 60)))
    col = fit(rgb, PANEL_W)
    val = fit(luma(rgb), PANEL_W).convert("RGB")
    squint = ImageOps.posterize(fit(luma(rgb), PANEL_W).filter(ImageFilter.GaussianBlur(PANEL_W / 120)), 2)
    squint = squint.point(lambda v: 30 if v < 64 else (128 if v < 160 else 225)).convert("RGB")
    thumb = fit(rgb, 64).resize((PANEL_W, round(col.height)), Image.NEAREST)
    ph = col.height
    head = 26
    out = Image.new("RGB", (PANEL_W * 4 + 5 * 8, ph + head + 8), (24, 24, 28))
    d = ImageDraw.Draw(out)
    titles = [label, "value (luma)", "squint: 3 values", "thumbnail read"]
    for i, (im, t) in enumerate(zip((col, val, squint, thumb), titles)):
        x = 8 + i * (PANEL_W + 8)
        out.paste(im.resize((PANEL_W, ph)), (x, head))
        d.text((x, 6), t, fill=(235, 235, 235), font=font(15))
    return out


def parse_patch(s: str) -> tuple[str, tuple[int, int, int, int]]:
    try:
        name, nums = s.split("=", 1)
        x, y, w, h = (int(v) for v in nums.split(","))
        return name, (x, y, w, h)
    except ValueError:
        raise argparse.ArgumentTypeError(f"bad --patch {s!r}; use name=x,y,w,h")


def print_stats(rows: list[tuple[str, dict]]) -> None:
    keys = list(rows[0][1].keys())
    w = max(len(k) for k in keys) + 2
    print("".ljust(w) + "".join(lbl[:22].ljust(24) for lbl, _ in rows))
    for k in keys:
        vals = []
        for _, s in rows:
            v = s[k]
            vals.append((", ".join(v) if isinstance(v, list) else str(v))[:22].ljust(24))
        print(k.ljust(w) + "".join(vals))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("images", nargs="+", help="captures to review")
    ap.add_argument("--before", help="the same shot before the change")
    ap.add_argument("--ref", help="a reference image that shows the target look")
    ap.add_argument("--patch", action="append", type=parse_patch, default=[], help="name=x,y,w,h (repeatable)")
    ap.add_argument("-o", "--out", help="write the contact sheet here (png/jpg)")
    ap.add_argument("--json", action="store_true", help="print statistics as JSON")
    a = ap.parse_args()

    items = []
    if a.before:
        items.append(("before: " + Path(a.before).name, Image.open(a.before)))
    for p in a.images:
        items.append((Path(p).name, Image.open(p)))
    if a.ref:
        items.append(("ref: " + Path(a.ref).name, Image.open(a.ref)))

    patches = dict(a.patch)
    results = [(label, stats(img)) for label, img in items]
    patch_out = {}
    if patches:
        for label, img in items:
            if label.startswith("ref: "):
                continue
            lums = {name: patch_lum(img, box) for name, box in patches.items()}
            names = list(lums)
            ratios = {}
            for other in names[1:]:
                r = lums[names[0]] / max(lums[other], 1e-6)
                ratios[f"{names[0]}:{other}"] = {"ratio": round(r, 2), "stops": round(math.log2(max(r, 1e-6)), 2)}
            patch_out[label] = {"linear_luminance": {k: round(v, 4) for k, v in lums.items()}, "ratios": ratios}

    if a.json:
        print(json.dumps({"stats": dict(results), "patches": patch_out}, indent=2))
    else:
        print_stats(results)
        for label, p in patch_out.items():
            parts = [f"{k} {v['ratio']}:1 ({v['stops']:+.2f} stops)" for k, v in p["ratios"].items()]
            print(f"patches [{label}]: " + "; ".join(parts))
        print("\nReading guide: luma p2–p98 spread under ~120 or rms_contrast under ~0.12 usually reads flat;"
              "\nclip_* over ~2% loses detail; a scene with no clear shadow or highlight mass has weak value"
              "\nstructure; sat_mean over ~0.55 with colourfulness over ~90 often reads garish. These are"
              "\nprompts for your eye, not rules: judge against the reference and the intended style.")

    if a.out:
        rows = [row(img, label, patches if not label.startswith("ref: ") else {}) for label, img in items]
        sheet = Image.new("RGB", (rows[0].width, sum(r.height for r in rows)), (24, 24, 28))
        y = 0
        for r in rows:
            sheet.paste(r, (0, y))
            y += r.height
        sheet.save(a.out, quality=90)
        print(f"\ncontact sheet: {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
