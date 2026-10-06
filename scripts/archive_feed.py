"""Render assets/archive-feed.svg from the blog's RSS feed (latest 3 entries).

    python scripts/archive_feed.py

Runs daily in .github/workflows/archive-feed.yml. Standard library only.
"""

import urllib.request
import xml.etree.ElementTree as ET
from datetime import timedelta, timezone
from email.utils import parsedate_to_datetime

from kit import (
    BG, CYAN, DISPLAY, FG, FG_2, FG_3, GREEN, HAZARD, LINE, LINE_2, MONO, MONO_B, ORANGE,
    PANEL, PANEL_2, SANS, chamfer, clip_text, esc, hazard_pattern, svg, text, text_width, write,
)

FEED = "https://blog.princival.com/rss.xml"
CST = timezone(timedelta(hours=8))
KINDS = {"logs": ("LOG", ORANGE), "notes": ("NTE", CYAN), "research": ("RES", HAZARD)}


def fetch(url=FEED):
    req = urllib.request.Request(url, headers={"User-Agent": "tim-1e-profile-feed"})
    with urllib.request.urlopen(req, timeout=20) as r:
        root = ET.fromstring(r.read())
    items = []
    for it in root.iter("item"):
        link = it.findtext("link", "")
        kind = next((v for k, v in KINDS.items() if f"/archive/{k}/" in link), ("ARC", FG_2))
        date = parsedate_to_datetime(it.findtext("pubDate")).astimezone(CST)
        items.append({
            "title": it.findtext("title", "").strip(),
            "desc": it.findtext("description", "").strip(),
            "tags": [c.text for c in it.findall("category") if c.text],
            "kind": kind,
            "date": date,
        })
    return items


PROMPT = "visitor@tim-1e:~/archive$ "


def prompt(cmd, y, size=17):
    """Shell prompt line; textLength pins mono advances so the caret lines up everywhere."""
    spans = (
        f'<tspan fill="{CYAN}">visitor@tim-1e</tspan><tspan fill="{FG_3}">:</tspan>'
        f'<tspan fill="{HAZARD}">~/archive</tspan><tspan fill="{FG_3}">$</tspan> {esc(cmd)}'
    )
    length = (len(PROMPT) + len(cmd)) * 0.6 * size
    return text(44, y, spans, size, FG, MONO, extra=f'textLength="{length:.1f}" xml:space="preserve"')


def render(items):
    W, H = 1280, 480
    latest = items[:3]
    latest_date = max(it["date"] for it in items).strftime("%Y-%m-%d") if items else "—"
    tx, max_w = 300, 680
    rows = ""
    for i, it in enumerate(latest):
        y = 156 + i * 88
        code, color = it["kind"]
        tags = " ".join(f"#{t}" for t in it["tags"][:3])
        rows += f'<g class="up" style="animation-delay:{0.5 + i * 0.35:.2f}s">'
        rows += f'<rect x="44" y="{y - 21}" width="62" height="28" fill="none" stroke="{color}" stroke-width="1.5"/>'
        rows += text(75, y - 1, code, 15, color, MONO_B, anchor="middle", ls=1)
        rows += text(124, y - 1, it["date"].strftime("%Y.%m.%d"), 15, FG_3, MONO)
        rows += text(tx, y, esc(clip_text(it["title"], 23, max_w)), 23, FG, SANS)
        rows += text(tx, y + 32, esc(clip_text(it["desc"], 17, max_w)), 17, FG_3, SANS)
        rows += text(124, y + 32, esc(clip_text(tags, 13, 160, MONO)), 13, FG_3, MONO)
        rows += f'<path d="M44 {y + 52}H{tx + max_w}" stroke="{LINE}" stroke-dasharray="2 5"/></g>'

    count = f"{len(items):02d}"
    last_cmd = "open blog.princival.com"
    caret_x = 44 + (len(PROMPT) + len(last_cmd) + 1) * 0.6 * 17
    body = f"""
<defs>{hazard_pattern(size=10)}</defs>
<path d="{chamfer(8, 8, W - 16, H - 16, 24, 'tr bl')}" fill="{BG}" stroke="{LINE_2}" stroke-width="1.5"/>
<path d="M8 8H{W - 32}L{W - 8} 32V54H8Z" fill="{PANEL_2}"/>
<path d="M8 54H{W - 8}" stroke="{LINE}"/>
<rect x="30" y="26" width="10" height="10" fill="{HAZARD}"/>
<rect x="46" y="26" width="10" height="10" fill="{FG_3}"/>
<rect x="62" y="26" width="10" height="10" fill="{FG_3}"/>
{text(W / 2, 36, "ARCHIVE TERMINAL — blog.princival.com", 14, FG_2, MONO_B, anchor="middle", ls=1)}
{text(W - 44, 36, f"RSS · LATEST {latest_date}", 12, FG_3, MONO, anchor="end", ls=1)}

{prompt("tail -n 3 --latest", 98)}
{rows}
{prompt(last_cmd, 446)}
<rect class="blink" x="{caret_x:.1f}" y="431" width="10" height="19" fill="{HAZARD}"/>

<path d="{chamfer(1020, 78, 228, 372, 14, 'tl br')}" fill="{PANEL}" stroke="{LINE}"/>
<g transform="rotate(-8 1134 140)" class="stamp">
  <rect x="1046" y="108" width="176" height="64" fill="none" stroke="{HAZARD}" stroke-width="3"/>
  <rect x="1052" y="114" width="164" height="52" fill="none" stroke="{HAZARD}" stroke-width="1"/>
  {text(1134, 150, "ACCESS GRANTED", 26, HAZARD, DISPLAY, anchor="middle", ls=1.5)}
  {text(1134, 164, "CLEARANCE · PUBLIC", 9, HAZARD, MONO, anchor="middle", ls=2)}
</g>
{text(1040, 226, "FILES INDEXED", 12, FG_3, MONO, ls=2)}
{text(1036, 300, count, 84, FG, DISPLAY)}
{text(1040 + text_width(count, 84, DISPLAY) + 6, 300, "/ RSS", 16, FG_3, MONO)}
<path d="M1040 326H1228" stroke="{LINE}"/>
{text(1040, 352, "CHANNELS", 12, FG_3, MONO, ls=2)}
<rect x="1040" y="366" width="10" height="10" fill="{ORANGE}"/>{text(1058, 376, "LOG 开发日志", 14, FG_2, SANS)}
<rect x="1040" y="390" width="10" height="10" fill="{CYAN}"/>{text(1058, 400, "NTE 经验笔记", 14, FG_2, SANS)}
<rect x="1040" y="414" width="10" height="10" fill="{HAZARD}"/>{text(1058, 424, "RES 研究档案", 14, FG_2, SANS)}
<rect x="1021" y="436" width="226" height="13" fill="url(#hz)" opacity=".8"/>
<circle class="blink" cx="1228" cy="226" r="4" fill="{GREEN}"/>
"""
    css = (
        "@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}.blink{animation:blink 1.1s steps(1) infinite}"
        "@keyframes up{from{opacity:0}to{opacity:1}}.up{animation:up .25s steps(3) both}"
        "@keyframes stamp{0%{opacity:0;transform:scale(1.6)}100%{opacity:1;transform:scale(1)}}"
        ".stamp>*{animation:stamp .35s cubic-bezier(.3,1.4,.5,1) 1.7s both;transform-box:fill-box;transform-origin:center}"
    )
    return svg(W, H, body, css, "Latest entries from blog.princival.com")


def build_feed():
    write("archive-feed.svg", render(fetch()))


if __name__ == "__main__":
    build_feed()
