"""Build every static SVG used by the profile README.

    python scripts/build_assets.py

Inputs live in assets/src (fonts, icons, path-traced viewport frames).
Standard library only; the viewport frames come from render_viewport.py.
"""

import base64
import math
import re

from archive_feed import build_feed
from kit import (
    BG, CYAN, DISPLAY, FG, FG_2, FG_3, GREEN, HAZARD, LABEL, LINE, LINE_2, MONO, MONO_B,
    ORANGE, PANEL, PANEL_2, RED, SANS, SRC, barcode, chamfer, clip_text, corner_ticks, crosshair, dot_grid,
    esc, hazard_pattern, svg, text, text_width, write,
)

BLINK = "@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}.blink{animation:blink 1.1s steps(1) infinite}"
FADE_UP = (
    "@keyframes up{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}"
    ".up{animation:up .6s cubic-bezier(.2,.7,.2,1) both}"
)


# ---------------------------------------------------------------------------
# HERO
# ---------------------------------------------------------------------------
def hero():
    W, H = 1280, 600
    T = 16.0  # viewport cycle (s)
    spps = (1, 4, 16, 64, 256)
    starts = [0.5 + i * 1.7 for i in range(len(spps))]
    reveal = 1.25
    vx, vy, vw, vh = 772, 120, 400, 360  # image rect

    def kt(*ts):
        return ";".join(f"{min(max(t / T, 0), 1):.4f}" for t in ts)

    frames, scans, counters = [], [], []
    for i, (spp, s) in enumerate(zip(spps, starts)):
        data = base64.b64encode((SRC / f"viewport-{spp}.jpg").read_bytes()).decode()
        frames.append(
            f'<clipPath id="rv{i}"><rect x="{vx}" y="{vy}" width="{vw}" height="0">'
            f'<animate attributeName="height" values="0;0;{vh};{vh}" keyTimes="{kt(0, s, s + reveal, T)}" '
            f'dur="{T}s" repeatCount="indefinite"/></rect></clipPath>'
            f'<image x="{vx}" y="{vy}" width="{vw}" height="{vh}" clip-path="url(#rv{i})" '
            f'href="data:image/jpeg;base64,{data}"/>'
        )
        scans.append(
            f'<g opacity="0"><rect x="{vx}" y="-24" width="{vw}" height="24" fill="url(#scan)"/>'
            f'<rect x="{vx}" y="-1" width="{vw}" height="2" fill="{CYAN}"/>'
            f'<animateTransform attributeName="transform" type="translate" '
            f'values="0 {vy};0 {vy};0 {vy + vh};0 {vy + vh}" keyTimes="{kt(0, s, s + reveal, T)}" '
            f'dur="{T}s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="0;1;1;0;0" '
            f'keyTimes="{kt(0, s, s + reveal, s + reveal + 0.05, T)}" dur="{T}s" repeatCount="indefinite"/></g>'
        )
        end = starts[i + 1] if i + 1 < len(spps) else T
        counters.append(
            f'<g opacity="0">{text(vx + vw, 102, f"SPP {spp:04d}", 15, HAZARD, MONO_B, anchor="end")}'
            f'<animate attributeName="opacity" values="0;1;0" keyTimes="{kt(0, s, end)}" calcMode="discrete" '
            f'dur="{T}s" repeatCount="indefinite"/></g>'
        )
    done_at = starts[-1] + reveal
    status = (
        f'<g opacity="1">{text(vx + vw, 512, "● RENDERING", 12, ORANGE, MONO, anchor="end")}'
        f'<animate attributeName="opacity" values="1;0" keyTimes="{kt(0, done_at)}" calcMode="discrete" '
        f'dur="{T}s" repeatCount="indefinite"/></g>'
        f'<g opacity="0">{text(vx + vw, 512, "● CONVERGED", 12, GREEN, MONO, anchor="end")}'
        f'<animate attributeName="opacity" values="0;1" keyTimes="{kt(0, done_at)}" calcMode="discrete" '
        f'dur="{T}s" repeatCount="indefinite"/></g>'
    )

    # typed terminal line
    cmd = "render(); build_tools(); automate(); repeat();"
    tx, ty, tsize = 92, 522, 19
    cw = 0.6 * tsize
    TT, t0, step = 12.0, 0.8, 0.065
    times = [0.0] + [t0 + i * step for i in range(len(cmd) + 1)] + [TT]
    widths = [0.0] + [i * cw for i in range(len(cmd) + 1)] + [len(cmd) * cw]
    ktt = ";".join(f"{t / TT:.4f}" for t in times)
    typed_text = text(tx, ty, cmd, tsize, FG, MONO, extra=f'textLength="{len(cmd) * cw:.1f}"')
    typed = (
        f'<clipPath id="type"><rect x="{tx}" y="{ty - 22}" width="0" height="30">'
        f'<animate attributeName="width" values="{";".join(f"{w:.1f}" for w in widths)}" keyTimes="{ktt}" '
        f'calcMode="discrete" dur="{TT}s" repeatCount="indefinite"/></rect></clipPath>'
        + text(64, ty, "&gt;", tsize, CYAN, MONO_B)
        + f'<g clip-path="url(#type)">{typed_text}</g>'
        + f'<rect class="blink" x="{tx}" y="{ty - 17}" width="{cw:.1f}" height="21" fill="{HAZARD}">'
        f'<animate attributeName="x" values="{";".join(f"{tx + w:.1f}" for w in widths)}" keyTimes="{ktt}" '
        f'calcMode="discrete" dur="{TT}s" repeatCount="indefinite"/></rect>'
    )

    name = "TIM-1E"
    name_w = text_width(name, 210, DISPLAY)
    # Python 3.10 (on 9950) forbids reusing the f-string's quote inside {}, so build these first.
    ghost_c = text(60, 290, name, 210, CYAN, DISPLAY, extra='fill-opacity=".55"')
    ghost_o = text(60, 290, name, 210, ORANGE, DISPLAY, extra='fill-opacity=".45"')
    title = (
        f'<g class="glitch-c">{ghost_c}</g>'
        f'<g class="glitch-o">{ghost_o}</g>'
        f'<g clip-path="url(#wipe)">{text(60, 290, name, 210, FG, DISPLAY)}</g>'
        f'<clipPath id="wipe"><rect x="40" y="100" width="0" height="220">'
        f'<animate attributeName="width" from="0" to="{name_w + 40:.0f}" dur=".9s" begin=".15s" fill="freeze" '
        f'calcMode="spline" keySplines=".2 .7 .2 1" keyTimes="0;1"/></rect></clipPath>'
    )

    body = f"""
<defs>
  {hazard_pattern()}
  {dot_grid()}
  <clipPath id="panel"><path d="{chamfer(8, 8, W - 16, H - 16, 30, 'tr bl')}"/></clipPath>
  <linearGradient id="scan" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="{CYAN}" stop-opacity="0"/><stop offset="1" stop-color="{CYAN}" stop-opacity=".35"/>
  </linearGradient>
  <radialGradient id="halo" cx="0.5" cy="0.5" r="0.5">
    <stop offset="0" stop-color="{HAZARD}" stop-opacity=".10"/><stop offset="1" stop-color="{HAZARD}" stop-opacity="0"/>
  </radialGradient>
</defs>
<g clip-path="url(#panel)">
  <rect width="{W}" height="{H}" fill="{BG}"/>
  <rect width="{W}" height="{H}" fill="url(#dots)" opacity=".7"/>
  <ellipse cx="{vx + vw / 2}" cy="{vy + vh / 2}" rx="420" ry="300" fill="url(#halo)"/>

  <rect x="8" y="8" width="{W}" height="46" fill="{PANEL}"/>
  <path d="M8 54H{W}" stroke="{LINE}"/>
  <rect x="34" y="25" width="12" height="12" fill="{HAZARD}"/>
  {text(56, 36, "TIM-1E // FIELD FILE", 13, FG_2, MONO_B, ls=1)}
  {text(W / 2, 36, "PUBLIC · READ ONLY", 13, FG_3, MONO, anchor="middle", ls=2)}
  <circle class="blink" cx="1078" cy="31" r="4" fill="{GREEN}"/>
  {text(1240, 36, "LINK ESTABLISHED", 13, FG_2, MONO, anchor="end", ls=1)}

  <rect x="64" y="86" width="112" height="28" fill="{HAZARD}"/>
  {text(76, 107, "OPERATOR", 19, BG, LABEL, ls=2.5)}
  {text(192, 106, "ID 0x1E · GITHUB PROFILE TERMINAL", 13, FG_3, MONO, ls=1)}
  {title}
  {text(66, 340, "GRAPHICS RESEARCHER", 30, FG, LABEL, ls=4)}
  {text(66, 378, "杂食型图形研究员养成中，今天也在给技能树加点。", 19, FG_2, SANS)}

  <rect x="66" y="414" width="10" height="10" fill="{HAZARD}"/>
  {text(88, 424, "MAIN TRACK", 13, FG_3, MONO, ls=1)}
  {text(210, 425, "3D 生成与渲染 · 几何 · 光照", 19, FG, SANS)}
  <rect x="66" y="450" width="10" height="10" fill="{CYAN}"/>
  {text(88, 460, "SIDE QUESTS", 13, FG_3, MONO, ls=1)}
  {text(210, 461, "工具开发 · 逆向增强 · 硬件 · 自动化", 19, FG, SANS)}
  <path d="M64 488H690" stroke="{LINE}" stroke-dasharray="2 6"/>
  {typed}

  <path d="{chamfer(vx - 28, 72, vw + 56, 456, 18, 'tl br')}" fill="{PANEL}" stroke="{LINE_2}"/>
  {text(vx, 102, "VIEWPORT_01 · PATH TRACER", 13, FG_2, MONO_B, ls=1)}
  {''.join(counters)}
  <rect x="{vx}" y="{vy}" width="{vw}" height="{vh}" fill="#050506"/>
  {''.join(frames)}
  {''.join(scans)}
  {corner_ticks(vx - 8, vy - 8, vw + 16, vh + 16, 12, HAZARD, 2)}
  {text(vx, 512, "cornell_box · 6 BOUNCES · NEE", 12, FG_3, MONO)}
  {status}

  <path d="M8 552H{W}" stroke="{LINE}"/>
  <rect x="0" y="552" width="300" height="48" fill="url(#hz)"/>
  {text(326, 581, "RENDERER: HAND-WRITTEN SVG + NUMPY PATH TRACER · NO JS WAS HARMED", 12, FG_3, MONO, ls=1)}
  {barcode(1040, 566, 120, 22, "tim-1e-hero", FG_3)}
  {text(1240, 583, "№ 0x1E", 14, FG_2, MONO_B, anchor="end")}
</g>
<path d="{chamfer(8, 8, W - 16, H - 16, 30, 'tr bl')}" stroke="{LINE_2}" stroke-width="1.5"/>
"""
    css = (
        BLINK
        + "@keyframes gc{0%,88%,100%{transform:translate(0,0)}89%{transform:translate(7px,-2px)}"
        "91%{transform:translate(-4px,1px)}93%{transform:translate(3px,0)}}"
        "@keyframes go{0%,88%,100%{transform:translate(0,0)}89%{transform:translate(-6px,2px)}"
        "91%{transform:translate(5px,-1px)}93%{transform:translate(-2px,0)}}"
        ".glitch-c{animation:gc 7s steps(1) infinite}.glitch-o{animation:go 7s steps(1) infinite}"
    )
    return svg(W, H, body, css, "Tim-1e field file: graphics researcher. Animated path-traced viewport.")


# ---------------------------------------------------------------------------
# NAV TABS
# ---------------------------------------------------------------------------
NAV = [
    ("01", "PROFILE", "档案"),
    ("02", "LOADOUT", "装备"),
    ("03", "MISSIONS", "任务"),
    ("04", "SIGNAL", "信号"),
    ("05", "ARCHIVE", "博客"),
]


def nav_tab(num, label, cn, external=False):
    W, H = 300, 100
    fill, ink, sub = (HAZARD, BG, "#3d3300") if external else (PANEL, FG, FG_3)
    arrow = "↗" if external else "↓"
    body = f"""
<path d="{chamfer(1, 1, W - 2, H - 2, 16, 'tr bl')}" fill="{fill}" stroke="{HAZARD if external else LINE_2}" stroke-width="1.5"/>
<rect x="1" y="16" width="6" height="40" fill="{BG if external else HAZARD}"/>
{text(24, 38, num, 22, sub if external else HAZARD, MONO_B)}
{text(W - 22, 38, cn, 22, sub if external else FG_2, SANS, anchor="end")}
{text(22, 84, label, 46, ink, DISPLAY, ls=1)}
{text(W - 22, 84, arrow, 26, ink if external else HAZARD, MONO_B, anchor="end")}
"""
    return svg(W, H, body, title=f"{num} {label} {cn}")


# ---------------------------------------------------------------------------
# SECTION HEADERS
# ---------------------------------------------------------------------------
SECTIONS = [
    ("01", "OPERATOR PROFILE", "档案"),
    ("02", "LOADOUT", "装备栏"),
    ("03", "MISSION FILES", "任务档案"),
    ("04", "SIGNAL", "活动信号"),
    ("05", "ARCHIVE LINK", "博客终端"),
]


def section_header(num, title, cn):
    W, H = 1280, 132
    tw = text_width(title, 66, DISPLAY)
    ticks = "".join(f"M{x} 112V{118 if x % 80 else 106}" for x in range(200, W - 40, 20))
    body = f"""
<defs><clipPath id="p"><path d="{chamfer(1, 1, W - 2, H - 2, 18, 'tr bl')}"/></clipPath></defs>
<g clip-path="url(#p)">
  <rect width="{W}" height="{H}" fill="{BG}"/>
  {text(30, 38, f"§{num}", 18, HAZARD, MONO_B)}
  <path d="M76 32H124" stroke="{HAZARD}" stroke-width="2"/>
  {text(136, 38, f"SECTION {num} / 05", 13, FG_3, MONO, ls=2)}
  {text(28, 98, title, 66, FG, DISPLAY, ls=1)}
  {text(28 + tw + 18, 96, f"/ {cn}", 28, FG_2, SANS)}
  {barcode(1080, 56, 150, 34, "sec" + num, FG_3)}
  {text(W - 30, 38, f"0x{int(num):02X}", 13, FG_3, MONO, anchor="end")}
  <path d="M0 112H{W}" stroke="{LINE_2}"/>
  <rect x="0" y="109" width="170" height="6" fill="{HAZARD}"/>
  <path d="{ticks}" stroke="{LINE_2}"/>
</g>
<path d="{chamfer(1, 1, W - 2, H - 2, 18, 'tr bl')}" stroke="{LINE_2}" stroke-width="1.5"/>
"""
    return svg(W, H, body, title=f"{num} {title} {cn}")


# ---------------------------------------------------------------------------
# PROFILE
# ---------------------------------------------------------------------------
def icosahedron():
    p = (1 + 5**0.5) / 2
    v = [(-1, p, 0), (1, p, 0), (-1, -p, 0), (1, -p, 0), (0, -1, p), (0, 1, p),
         (0, -1, -p), (0, 1, -p), (p, 0, -1), (p, 0, 1), (-p, 0, -1), (-p, 0, 1)]
    n = math.sqrt(1 + p * p)
    v = [(a / n, b / n, c / n) for a, b, c in v]
    edges = [(i, j) for i in range(12) for j in range(i + 1, 12)
             if abs(sum((v[i][k] - v[j][k]) ** 2 for k in range(3)) - (2 / n) ** 2) < 1e-6]
    return v, edges


def wire_portrait(cx, cy, R):
    verts, edges = icosahedron()
    N, dur = 36, 18
    tilt_x, tilt_z = math.radians(-18), math.radians(12)

    def project(v, a):
        x, y, z = v
        x, z = x * math.cos(a) + z * math.sin(a), -x * math.sin(a) + z * math.cos(a)
        y, z = y * math.cos(tilt_x) - z * math.sin(tilt_x), y * math.sin(tilt_x) + z * math.cos(tilt_x)
        x, y = x * math.cos(tilt_z) - y * math.sin(tilt_z), x * math.sin(tilt_z) + y * math.cos(tilt_z)
        s = 3.6 / (3.6 - z)
        return cx + x * R * s, cy - y * R * s, z

    frames = [[project(v, 2 * math.pi * f / N) for v in verts] for f in range(N + 1)]
    out = []
    for i, j in edges:
        ds, ops = [], []
        for fr in frames:
            (x1, y1, z1), (x2, y2, z2) = fr[i], fr[j]
            ds.append(f"M{x1:.1f} {y1:.1f}L{x2:.1f} {y2:.1f}")
            ops.append(f"{0.18 + 0.82 * ((z1 + z2) / 2 + 1) / 2:.2f}")
        out.append(
            f'<path stroke="{FG}" stroke-width="1.6" stroke-linecap="round">'
            f'<animate attributeName="d" values="{";".join(ds)}" dur="{dur}s" repeatCount="indefinite"/>'
            f'<animate attributeName="stroke-opacity" values="{";".join(ops)}" dur="{dur}s" repeatCount="indefinite"/></path>'
        )
    for k in range(len(verts)):
        xs = ";".join(f"{fr[k][0]:.1f}" for fr in frames)
        ys = ";".join(f"{fr[k][1]:.1f}" for fr in frames)
        out.append(
            f'<circle r="3.2" fill="{HAZARD}"><animate attributeName="cx" values="{xs}" dur="{dur}s" repeatCount="indefinite"/>'
            f'<animate attributeName="cy" values="{ys}" dur="{dur}s" repeatCount="indefinite"/></circle>'
        )
    return "".join(out)


def radar(cx, cy, R):
    axes = [("RENDER", "A+", 0.9), ("GEOMETRY", "A", 0.8), ("TOOLING", "S", 1.0),
            ("REVERSE", "B+", 0.7), ("HARDWARE", "B", 0.6), ("AUTOMATION", "A", 0.8)]
    n = len(axes)

    def pt(i, r):
        a = -math.pi / 2 + 2 * math.pi * i / n
        return math.cos(a) * r, math.sin(a) * r

    rings = "".join(
        f'<path d="M{"L".join(f"{x:.1f} {y:.1f}" for x, y in (pt(i, R * k / 4) for i in range(n)))}Z" '
        f'stroke="{LINE_2}" stroke-dasharray="{"0" if k == 4 else "2 4"}"/>'
        for k in range(1, 5)
    )
    spokes = "".join(f'<path d="M0 0L{pt(i, R)[0]:.1f} {pt(i, R)[1]:.1f}" stroke="{LINE}"/>' for i in range(n))
    poly = "L".join(f"{pt(i, R * v)[0]:.1f} {pt(i, R * v)[1]:.1f}" for i, (_, _, v) in enumerate(axes))
    dots = "".join(
        f'<circle cx="{pt(i, R * v)[0]:.1f}" cy="{pt(i, R * v)[1]:.1f}" r="3.5" fill="{HAZARD}"/>'
        for i, (_, _, v) in enumerate(axes)
    )
    labels = ""
    for i, (name, grade, _) in enumerate(axes):
        x, y = pt(i, R + 30)
        anchor = "middle" if abs(x) < 5 else ("start" if x > 0 else "end")
        labels += text(f"{cx + x:.1f}", f"{cy + y - 2:.1f}", name, 13, FG_2, MONO, anchor=anchor, ls=1)
        labels += text(f"{cx + x:.1f}", f"{cy + y + 20:.1f}", grade, 22, HAZARD, DISPLAY, anchor=anchor)
    return f"""
<g transform="translate({cx} {cy})">
  {rings}{spokes}
  <g>
    <path d="M0 0L0 {-R}" stroke="{CYAN}" stroke-width="1.5" stroke-opacity=".8"/>
    <path d="M0 0L0 {-R}A{R} {R} 0 0 0 {-R * math.sin(math.radians(40)):.1f} {-R * math.cos(math.radians(40)):.1f}Z" fill="{CYAN}" fill-opacity=".10"/>
    <animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="6s" repeatCount="indefinite"/>
  </g>
  <g>
    <path d="M{poly}Z" fill="{HAZARD}" fill-opacity=".16" stroke="{HAZARD}" stroke-width="2" stroke-linejoin="round"/>
    {dots}
    <animateTransform attributeName="transform" type="scale" values="0;1.06;1" keyTimes="0;.75;1" dur="1.1s" begin=".2s" fill="freeze"/>
  </g>
</g>
{labels}
"""


def profile():
    W, H = 1280, 560
    rows = [
        ("CODENAME", f'<tspan font-family="{DISPLAY}" font-size="34" fill="{FG}">Tim_e</tspan>'
                     f'<tspan font-family="{MONO}" font-size="15" fill="{FG_3}" dx="12">aka Tim-1e</tspan>'),
        ("CLASS", "图形研究员 · 杂食型"),
        ("MAIN TRACK", "3D 生成与渲染 · 几何 / 光照 / 工程细节"),
        ("SIDE QUESTS", "工具开发 / 逆向增强 / 硬件开发 / 自动化"),
        ("OBJECTIVE", "论文能啃，管线能写，服务能搭，硬件能修"),
        ("STATUS", f'<tspan fill="{GREEN}">ONLINE</tspan> — 向全栈能力最强的图形研究员进化中'),
    ]
    fx, fy, step = 432, 70, 76
    fields = ""
    for k, (label, value) in enumerate(rows):
        y = fy + k * step
        fields += f'<g class="up" style="animation-delay:{0.15 + k * 0.09:.2f}s">'
        fields += text(fx, y, label, 13, FG_3, MONO, ls=2)
        if label == "STATUS":
            fields += f'<circle class="blink" cx="{fx + 74}" cy="{y - 4}" r="4" fill="{GREEN}"/>'
        fields += text(fx, y + 32, value, 20, FG, SANS)
        fields += f'<path d="M{fx} {y + 48}H{fx + 420}" stroke="{LINE}" stroke-dasharray="2 5"/></g>'

    body = f"""
<defs>{dot_grid("pd", 20)}{hazard_pattern("hz2", size=10)}</defs>
<path d="{chamfer(8, 8, W - 16, H - 16, 24, 'tr bl')}" fill="{BG}" stroke="{LINE_2}" stroke-width="1.5"/>

<path d="{chamfer(32, 32, 360, H - 64, 14, 'tl br')}" fill="{PANEL}" stroke="{LINE}"/>
<rect x="33" y="33" width="358" height="{H - 66}" fill="url(#pd)" opacity=".6"/>
{text(52, 62, "FIG.01 — PORTRAIT", 12, FG_2, MONO_B, ls=1)}
{text(372, 62, "REC", 12, ORANGE, MONO_B, anchor="end")}
<circle class="blink" cx="336" cy="58" r="4" fill="{ORANGE}"/>
<ellipse cx="212" cy="430" rx="110" ry="14" fill="#000" opacity=".55"/>
<ellipse cx="212" cy="272" rx="168" ry="44" stroke="{CYAN}" stroke-opacity=".35" stroke-dasharray="3 5" transform="rotate(-14 212 272)"/>
<circle r="5" fill="{CYAN}"><animateMotion dur="7s" repeatCount="indefinite" path="M380 272A168 44 0 1 1 44 272A168 44 0 1 1 380 272" rotate="0"/></circle>
{wire_portrait(212, 262, 128)}
{corner_ticks(64, 98, 296, 352, 12, FG_3)}
{crosshair(212, 262, 6, FG_3)}
<path d="M56 470h24M56 470v-24" stroke="{RED}" stroke-width="2"/>
{text(52, 498, "MESH icosahedron · 12v 30e · wire", 12, FG_3, MONO)}
{text(52, 520, "* 真人照片已归档，此处以网格代替", 13, FG_3, SANS)}

{fields}

<path d="{chamfer(884, 32, 364, H - 64, 14, 'tr bl')}" fill="{PANEL}" stroke="{LINE}"/>
{text(904, 62, "ATTRIBUTE MATRIX", 12, FG_2, MONO_B, ls=1)}
{text(1228, 62, "SELF-EVAL", 12, FG_3, MONO, anchor="end")}
{radar(1066, 290, 104)}
<rect x="885" y="{H - 66}" width="362" height="33" fill="url(#hz2)" opacity=".85"/>
<rect x="904" y="{H - 61}" width="198" height="23" fill="{PANEL}"/>
{text(912, H - 44, "* 自评，仅供参考 (｀・ω・´)", 13, FG_2, SANS)}
"""
    return svg(W, H, body, BLINK + FADE_UP, "Operator profile: Tim_e, graphics researcher")



# ---------------------------------------------------------------------------
# LOADOUT
# ---------------------------------------------------------------------------
POWERSHELL = (  # custom glyph, 24x24
    '<path d="M4.6 3h18.2c.8 0 1.3.7 1.1 1.4l-3.6 15.4c-.2.7-.8 1.2-1.5 1.2H.6c-.8 0-1.3-.7-1.1-1.4'
    'L3.1 4.2C3.3 3.5 3.9 3 4.6 3Z" fill="currentColor"/>'
    f'<path d="M6.5 7.2l5.2 4.6-6.6 4.6M11.4 16.6h5.2" stroke="{PANEL}" stroke-width="2.1" '
    'stroke-linecap="round" stroke-linejoin="round" fill="none"/>'
)

LOADOUT = [
    ("A", "PRIMARY", "语言", [
        ("python", "PYTHON", "#5aa0e0"), ("cplusplus", "C++", "#659ad2"), ("rust", "RUST", ORANGE),
        ("typescript", "TYPESCRIPT", "#4a9ae8"), ("javascript", "JAVASCRIPT", "#f7df1e"),
        ("html5", "HTML", "#f06529"), ("powershell", "POWERSHELL", "#5391fe"), ("lua", "LUA", "#7c8cff"),
        ("gnubash", "SHELL", "#5ccc3a"),
    ]),
    ("B", "SECONDARY", "渲染 · 工具链", [
        ("nvidia", "OPTIX · CUDA", "#76b900"), ("blender", "BLENDER", "#e87d0d"), ("git", "GIT", "#f05032"),
        ("githubactions", "ACTIONS", "#2088ff"), ("nodedotjs", "NODE.JS", "#5fa04e"),
        ("vercel", "VERCEL", FG), ("linux", "LINUX", "#fcc624"), (None, "NEXT UNLOCK", FG_3),
    ]),
]


def icon_paths(slug):
    if slug == "powershell":
        return POWERSHELL
    raw = (SRC / "icons" / f"{slug}.svg").read_text(encoding="utf-8")
    return "".join(f'<path d="{d}" fill="currentColor"/>' for d in re.findall(r' d="([^"]+)"', raw))


def loadout():
    W = 1280
    sx, sw, sh, gap = 232, 104, 132, 10
    row_h = sh + 34
    H = 48 + row_h * len(LOADOUT) + 4
    parts, n = [], 0
    for r, (slot, name, cn, items) in enumerate(LOADOUT):
        y = 40 + r * row_h
        parts.append(text(36, y + 22, f"SLOT {slot}", 13, HAZARD, MONO_B, ls=2))
        parts.append(text(34, y + 64, name, 38, FG, DISPLAY, ls=1))
        parts.append(text(36, y + 94, cn, 17, FG_2, SANS))
        parts.append(text(36, y + 122, f"{len([i for i in items if i[0]])} EQUIPPED", 12, FG_3, MONO, ls=1))
        for c, (slug, label, color) in enumerate(items):
            x = sx + c * (sw + gap)
            delay = f"{0.1 + n * 0.045:.2f}s"
            n += 1
            if slug is None:
                parts.append(
                    f'<g class="up" style="animation-delay:{delay}">'
                    f'<path d="{chamfer(x, y, sw, sh, 12, "tr bl")}" stroke="{FG_3}" stroke-dasharray="4 4"/>'
                    + text(x + sw / 2, y + 76, "?", 44, FG_3, DISPLAY, anchor="middle")
                    + text(x + sw / 2, y + 114, label, 12, FG_3, MONO, anchor="middle")
                    + "</g>"
                )
                continue
            parts.append(
                f'<g class="up" style="animation-delay:{delay}">'
                f'<path d="{chamfer(x, y, sw, sh, 12, "tr bl")}" fill="{PANEL}" stroke="{LINE_2}"/>'
                + text(x + 9, y + 18, f"{slot}-{c + 1:02d}", 10, FG_3, MONO)
                + f'<g transform="translate({x + sw / 2 - 21} {y + 34}) scale(1.75)" color="{FG}">{icon_paths(slug)}</g>'
                + text(x + sw / 2, y + 108, label, 15 if len(label) < 10 else 13, FG_2, LABEL, anchor="middle", ls=1)
                + f'<rect x="{x + sw / 2 - 16}" y="{y + sh - 12}" width="32" height="3" fill="{color}"/>'
                + "</g>"
            )
    body = f"""
<path d="{chamfer(8, 8, W - 16, H - 16, 24, 'tr bl')}" fill="{BG}" stroke="{LINE_2}" stroke-width="1.5"/>
<path d="M210 40V{H - 40}" stroke="{LINE}" stroke-dasharray="2 5"/>
{''.join(parts)}
"""
    return svg(W, H, body, FADE_UP, "Loadout: languages and tools")


# ---------------------------------------------------------------------------
# MISSION CARDS
# ---------------------------------------------------------------------------
MISSIONS = [
    ("Blender-SPCBPT", "RND-01", "RENDER", HAZARD, "C++", "#f34b7d",
     "SPCBPT-OptiX7 渲染器的 Blender 5.2 前端。", "#optix #blender"),
    ("optix7_advance_PKUcourse", "RND-02", "RENDER", HAZARD, "C++", "#f34b7d",
     "基于 optix7course 框架的 Sponza 场景渲染。", "#optix7 #sponza"),
    ("ProxyTracing", "RND-03", "RESEARCH", HAZARD, "HTML", "#e34c26",
     "ProxyTracing 论文的项目主页。", "#paper #project-page"),
    ("holocubic-cli", "HW-01", "HARDWARE", ORANGE, "Python", "#3572A5",
     "HoloCubic DevTools API 的跨语言 CLI。", "#holocubic #cli"),
    ("cxcc", "TL-01", "TOOLING", CYAN, "PowerShell", "#012456",
     "Codex 与 Claude Code 的统一控制平面。", "#codex #claude-code"),
    ("CelestialCardArt", "MOD-01", "MOD", GREEN, "Mod", GREEN,
     "天体卡面：《杀戮尖塔 2》卡面美化模组。", "#sts2 #card-art"),
]


def mission_glyph(kind, x, y, color):
    """64px line-art glyph per category, lightly animated."""
    g = f'<g transform="translate({x} {y})" stroke="{color}" stroke-width="2" fill="none" stroke-linecap="round">'
    if kind in ("RENDER", "RESEARCH"):
        g += (
            '<circle cx="40" cy="44" r="18"/>'
            '<path d="M0 8L26 30M54 32L76 10M76 10L68 10M76 10L76 18" stroke-dasharray="4 4">'
            '<animate attributeName="stroke-dashoffset" from="16" to="0" dur="1s" repeatCount="indefinite"/></path>'
            '<path d="M-4 70H84" stroke-opacity=".5"/>'
        )
    elif kind == "HARDWARE":
        g += (
            '<path d="M40 6L72 22V58L40 74L8 58V22Z"/><path d="M8 22L40 38L72 22M40 38V74" stroke-opacity=".6"/>'
            f'<path d="M16 32L34 41V60L16 51Z" fill="{color}" fill-opacity=".25">'
            '<animate attributeName="fill-opacity" values=".1;.5;.1" dur="2.4s" repeatCount="indefinite"/></path>'
        )
    elif kind == "TOOLING":
        g += (
            '<rect x="4" y="10" width="72" height="56" rx="2"/><path d="M4 22H76" stroke-opacity=".6"/>'
            '<path d="M16 36L26 44L16 52"/>'
            f'<rect x="32" y="50" width="14" height="3" fill="{color}" stroke="none" class="blink"/>'
        )
    else:
        g += (
            '<rect x="14" y="4" width="52" height="72" rx="4"/>'
            f'<path d="M40 22L45 35L58 36L48 45L51 58L40 51L29 58L32 45L22 36L35 35Z" fill="{color}" fill-opacity=".3">'
            '<animate attributeName="fill-opacity" values=".1;.6;.1" dur="2.8s" repeatCount="indefinite"/></path>'
        )
    return g + "</g>"


def mission_card(repo, code, kind, color, lang, lang_color, desc, tags):
    W, H = 640, 220
    size = 46
    while text_width(repo, size, DISPLAY) > 450 and size > 30:
        size -= 2
    body = f"""
<defs><clipPath id="c"><path d="{chamfer(1, 1, W - 2, H - 2, 18, 'tr bl')}"/></clipPath></defs>
<g clip-path="url(#c)">
  <rect width="{W}" height="{H}" fill="{PANEL}"/>
  <rect width="10" height="{H}" fill="{color}"/>
  <path d="M{W - 140} 0H{W}V{H}H{W - 140}Z" fill="{PANEL_2}"/>
  {mission_glyph(kind, W - 110, 64, color)}
</g>
<path d="{chamfer(1, 1, W - 2, H - 2, 18, 'tr bl')}" stroke="{LINE_2}" stroke-width="1.5"/>
{text(34, 44, code, 18, color, MONO_B, ls=1)}
{text(34 + text_width(code, 18, MONO_B) + 14, 44, f"· {kind}", 15, FG_3, MONO, ls=1)}
{text(W - 24, 44, "↗", 24, HAZARD, MONO_B, anchor="end")}
{text(32, 100, esc(repo), size, FG, DISPLAY)}
{text(34, 142, esc(clip_text(desc, 20, 450)), 20, FG_2, SANS)}
<circle cx="42" cy="186" r="7" fill="{lang_color}" stroke="{FG_3}"/>
{text(58, 192, lang, 16, FG_2, MONO)}
{text(58 + text_width(lang, 16, MONO) + 22, 192, esc(tags), 15, FG_3, MONO)}
"""
    return svg(W, H, body, BLINK, f"{repo}: {desc}")


# ---------------------------------------------------------------------------
# FOOTER
# ---------------------------------------------------------------------------
def footer():
    W, H = 1280, 168
    body = f"""
<defs>{hazard_pattern(size=16)}<clipPath id="p"><path d="{chamfer(1, 1, W - 2, H - 2, 18, 'tr bl')}"/></clipPath></defs>
<g clip-path="url(#p)">
  <rect width="{W}" height="{H}" fill="{BG}"/>
  <rect width="{W}" height="18" fill="url(#hz)"/>
  {text(30, 104, "END OF FILE", 62, FG, DISPLAY, ls=2)}
  {text(30 + text_width("END OF FILE", 62, DISPLAY) + 34, 102, "感谢翻阅，档案终端随时在线。", 22, FG_2, SANS)}
  {text(W - 30, 66, "TIM-1E // 2026 · PUBLIC READ ONLY", 13, FG_3, MONO, anchor="end", ls=1)}
  {text(W - 52, 104, "visitor@tim-1e:~$ exit", 16, FG_2, MONO, anchor="end")}
  <rect class="blink" x="{W - 42}" y="89" width="10" height="18" fill="{HAZARD}"/>
  <path d="M0 132H{W}" stroke="{LINE}"/>
  {barcode(30, 142, 220, 14, "eof", FG_3)}
  {text(W - 30, 154, "SESSION CLOSED", 12, FG_3, MONO, anchor="end", ls=3)}
</g>
<path d="{chamfer(1, 1, W - 2, H - 2, 18, 'tr bl')}" stroke="{LINE_2}" stroke-width="1.5"/>
"""
    return svg(W, H, body, BLINK, "End of file")


# ---------------------------------------------------------------------------
# VIEW SWITCH BARS (used as <summary> of two exclusive <details name="view">)
# Each bar previews the style it switches to.
# ---------------------------------------------------------------------------
CLASSIC_FONT = "Inter, Segoe UI, Microsoft YaHei, Arial, sans-serif"


def view_bar_field():
    W, H = 1280, 96
    body = f"""
<defs>{hazard_pattern(size=12)}<clipPath id="p"><path d="{chamfer(1, 1, W - 2, H - 2, 18, 'tr bl')}"/></clipPath></defs>
<g clip-path="url(#p)">
  <rect width="{W}" height="{H}" fill="{BG}"/>
  <rect width="22" height="{H}" fill="url(#hz)"/>
  {text(50, 36, "VIEW A · DEFAULT", 13, HAZARD, MONO_B, ls=2)}
  {text(48, 78, "FIELD FILE", 42, FG, DISPLAY, ls=1)}
  {text(48 + text_width("FIELD FILE", 42, DISPLAY) + 20, 76, "档案终端版 · 动画 / 路径追踪 / 实时博客", 20, FG_2, SANS)}
  <circle class="blink" cx="{W - 216}" cy="57" r="4" fill="{GREEN}"/>
  {text(W - 34, 62, "CLICK TO SWITCH ▸", 15, FG_2, MONO, anchor="end", ls=1)}
</g>
<path d="{chamfer(1, 1, W - 2, H - 2, 18, 'tr bl')}" stroke="{HAZARD}" stroke-width="1.5"/>
"""
    return svg(W, H, body, BLINK, "Switch view: Field File")


def view_bar_classic():
    W, H = 1280, 96
    body = f"""
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="{W}" y2="{H}" gradientUnits="userSpaceOnUse">
    <stop stop-color="#111E33"/><stop offset="0.55" stop-color="#0F172A"/><stop offset="1" stop-color="#10261F"/>
  </linearGradient>
  <linearGradient id="line" x1="40" y1="0" x2="{W - 40}" y2="0" gradientUnits="userSpaceOnUse">
    <stop stop-color="#60A5FA"/><stop offset="0.48" stop-color="#22D3EE"/><stop offset="1" stop-color="#22C55E"/>
  </linearGradient>
</defs>
<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="20" fill="url(#bg)" stroke="#334155" stroke-width="1.5"/>
<text x="40" y="38" fill="#22D3EE" font-family="{CLASSIC_FONT}" font-size="14" font-weight="800" letter-spacing="1.8">VIEW B · CLASSIC</text>
<text x="40" y="74" fill="#F8FAFC" font-family="{CLASSIC_FONT}" font-size="30" font-weight="860">经典卡片版</text>
<text x="210" y="73" fill="#A7F3D0" font-family="{CLASSIC_FONT}" font-size="19" font-weight="700">原始风格 · 卡片 / 徽章 / 统计</text>
<text x="{W - 40}" y="62" text-anchor="end" fill="#CBD5E1" font-family="{CLASSIC_FONT}" font-size="17" font-weight="760">点击切换 ▸</text>
<path d="M40 86H{W - 40}" stroke="url(#line)" stroke-width="2" stroke-linecap="round" opacity=".7"/>
"""
    return svg(W, H, body, title="Switch view: Classic")


def main():
    print("building assets/")
    write("hero.svg", hero())
    for num, label, cn in NAV:
        write(f"nav/{num}-{label.lower()}.svg", nav_tab(num, label, cn, external=label == "ARCHIVE"))
    for num, title, cn in SECTIONS:
        write(f"sections/{num}.svg", section_header(num, title, cn))
    write("profile.svg", profile())
    write("loadout.svg", loadout())
    for m in MISSIONS:
        write(f"missions/{m[0]}.svg", mission_card(*m))
    write("footer.svg", footer())
    write("view/field.svg", view_bar_field())
    write("view/classic.svg", view_bar_classic())
    build_feed()


if __name__ == "__main__":
    main()
