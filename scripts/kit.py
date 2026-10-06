"""Shared design kit for the profile SVGs: palette, embedded fonts, shapes.

Standard library only, so the GitHub Actions feed job can import it without installs.
"""

import base64
import hashlib
import html
import io
import json
import re
from functools import lru_cache
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
SRC = ASSETS / "src"

# --- palette (borrowed from the blog's archive-terminal theme) ---------------
BG = "#0c0d0f"
PANEL = "#131519"
PANEL_2 = "#191c21"
LINE = "#2a2d33"
LINE_2 = "#3a3e46"
FG = "#e8e6e1"
FG_2 = "#a4a6ac"
FG_3 = "#6c6f76"
HAZARD = "#ffd400"
CYAN = "#3fd2e6"
ORANGE = "#ff7a2e"
GREEN = "#00d294"
RED = "#ff6568"

# --- type ---------------------------------------------------------------------
CJK = "'Source Han Sans SC','Noto Sans SC','Noto Sans CJK SC','PingFang SC','Microsoft YaHei',sans-serif"
DISPLAY = f"'FF Display',{CJK}"  # Barlow Condensed ExtraBold
LABEL = f"'FF Label',{CJK}"  # Barlow Condensed SemiBold
MONO = f"'FF Mono','JetBrains Mono',Consolas,{CJK}"
MONO_B = f"'FF MonoB','JetBrains Mono',Consolas,{CJK}"
SANS = CJK

FONT_FILES = {
    "FF Display": "BarlowCondensed-ExtraBold.woff2",
    "FF Label": "BarlowCondensed-SemiBold.woff2",
    "FF Mono": "JetBrainsMono-Regular.woff2",
    "FF MonoB": "JetBrainsMono-Bold.woff2",
}


@lru_cache(None)
def _font_b64(name, chars):
    """Base64 woff2; trimmed to `chars` when fontTools is installed (local builds).

    Without fontTools (e.g. the Actions feed job) the full Latin subset is embedded.
    """
    data = (SRC / "fonts" / FONT_FILES[name]).read_bytes()
    try:
        from fontTools import subset
        from fontTools.ttLib import TTFont
    except ImportError:
        return base64.b64encode(data).decode()
    font = TTFont(io.BytesIO(data))
    options = subset.Options()
    options.flavor = "woff2"
    options.layout_features = ["kern"]
    subsetter = subset.Subsetter(options)
    subsetter.populate(text=chars + " ")
    subsetter.subset(font)
    buf = io.BytesIO()
    font.save(buf)
    return base64.b64encode(buf.getvalue()).decode()


def font_css(body):
    """@font-face rules for only the families the SVG body actually uses."""
    chars = set()
    for chunk in re.findall(r">([^<>]+)<", body):
        chars.update(html.unescape(chunk))
    chars = "".join(sorted(chars))
    rules = []
    for family in FONT_FILES:
        if f"'{family}'" in body:
            rules.append(
                f"@font-face{{font-family:'{family}';"
                f"src:url(data:font/woff2;base64,{_font_b64(family, chars)}) format('woff2');}}"
            )
    return "".join(rules)


def esc(s):
    return escape(str(s), {'"': "&quot;"})


def svg(width, height, body, css="", title=None):
    head = f"<title>{esc(title)}</title>" if title else ""
    style = font_css(body) + css
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" fill="none">{head}'
        f"<style>{style}</style>{body}</svg>\n"
    )


def text(x, y, s, size, fill=FG, family=MONO, weight=None, anchor=None, ls=None, extra=""):
    attrs = [f'x="{x}"', f'y="{y}"', f'font-family="{family}"', f'font-size="{size}"', f'fill="{fill}"']
    if weight:
        attrs.append(f'font-weight="{weight}"')
    if anchor:
        attrs.append(f'text-anchor="{anchor}"')
    if ls is not None:
        attrs.append(f'letter-spacing="{ls}"')
    if extra:
        attrs.append(extra)
    return f"<text {' '.join(attrs)}>{s}</text>"


def chamfer(x, y, w, h, c=16, corners="tr bl"):
    """Rect path with 45-degree cut corners (any of tl tr br bl)."""
    k = {name: (c if name in corners.split() else 0) for name in ("tl", "tr", "br", "bl")}
    pts = [
        (x + k["tl"], y),
        (x + w - k["tr"], y),
        (x + w, y + k["tr"]),
        (x + w, y + h - k["br"]),
        (x + w - k["br"], y + h),
        (x + k["bl"], y + h),
        (x, y + h - k["bl"]),
        (x, y + k["tl"]),
    ]
    return "M" + "L".join(f"{px:g} {py:g}" for px, py in pts) + "Z"


def hazard_pattern(pid="hz", color=HAZARD, back=BG, size=14):
    return (
        f'<pattern id="{pid}" width="{size}" height="{size}" patternUnits="userSpaceOnUse" '
        f'patternTransform="rotate(45)"><rect width="{size}" height="{size}" fill="{back}"/>'
        f'<rect width="{size / 2}" height="{size}" fill="{color}"/></pattern>'
    )


def dot_grid(pid="dots", gap=24, color=LINE, r=1):
    return (
        f'<pattern id="{pid}" width="{gap}" height="{gap}" patternUnits="userSpaceOnUse">'
        f'<circle cx="{gap / 2}" cy="{gap / 2}" r="{r}" fill="{color}"/></pattern>'
    )


def barcode(x, y, w, h, seed, color=FG_2):
    """Deterministic decorative barcode."""
    digest = hashlib.sha256(seed.encode()).digest() * 4
    out, cx, i = [], x, 0
    while cx < x + w:
        bar = 1 + digest[i] % 3
        gap = 1 + digest[i + 1] % 3
        if cx + bar > x + w:
            break
        out.append(f'<rect x="{cx}" y="{y}" width="{bar}" height="{h}" fill="{color}"/>')
        cx += bar + gap
        i += 2
    return "".join(out)


def corner_ticks(x, y, w, h, size=10, color=FG_3, sw=1.5):
    s = size
    d = (
        f"M{x} {y + s}V{y}H{x + s}"
        f"M{x + w - s} {y}H{x + w}V{y + s}"
        f"M{x + w} {y + h - s}V{y + h}H{x + w - s}"
        f"M{x + s} {y + h}H{x}V{y + h - s}"
    )
    return f'<path d="{d}" stroke="{color}" stroke-width="{sw}"/>'


def crosshair(cx, cy, r=7, color=FG_3):
    return (
        f'<g stroke="{color}" stroke-width="1"><circle cx="{cx}" cy="{cy}" r="{r}"/>'
        f'<path d="M{cx - r - 4} {cy}H{cx + r + 4}M{cx} {cy - r - 4}V{cy + r + 4}"/></g>'
    )


@lru_cache(None)
def _metrics():
    return json.loads((SRC / "fonts" / "metrics.json").read_text(encoding="utf-8"))


def text_width(s, size, family=SANS):
    """Advance width from the embedded fonts' metrics; CJK falls back to 1em."""
    key = next((k for k in FONT_FILES if f"'{k}'" in family), None)
    table = _metrics()[key] if key else {}
    w = 0.0
    for ch in s:
        if ch in table:
            w += table[ch]
        elif ord(ch) > 0x2E80:
            w += 1.0
        else:
            w += 0.55
    return w * size


def clip_text(s, size, max_w, family=SANS):
    if text_width(s, size, family) <= max_w:
        return s
    while s and text_width(s + "…", size, family) > max_w:
        s = s[:-1]
    return s.rstrip() + "…"


def write(name, content):
    path = ASSETS / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"  {name:<34} {len(content.encode()) // 1024:>4} KB")
