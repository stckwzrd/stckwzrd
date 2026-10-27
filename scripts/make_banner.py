#!/usr/bin/env python3
"""Generate assets/banner.svg: ASCII wordmark with a slow highlight sweep and a
disassembly listing that appears line by line. Pure SVG + CSS/SMIL, no scripts,
no external services (GitHub renders this animation when used through <img>).

    python3 scripts/make_banner.py
"""
from html import escape
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "assets" / "banner.svg"

# figlet "slant", pre-rendered so this script has no dependencies
WORDMARK = [
    r"         __       __                           __",
    r"   _____/ /______/ /___      ______  _________/ /",
    r"  / ___/ __/ ___/ //_/ | /| / /_  / / ___/ __  /",
    r" (__  ) /_/ /__/ ,<  | |/ |/ / / /_/ /  / /_/ /",
    r"/____/\__/\___/_/|_| |__/|__/ /___/_/   \__,_/",
]

# (address, bytes, mnemonic, operands, comment)
LISTING = [
    ("0x00401000", "55",             "push", "rbp",          ""),
    ("0x00401001", "48 89 e5",       "mov",  "rbp, rsp",     ""),
    ("0x00401004", "48 83 ec 20",    "sub",  "rsp, 0x20",    ""),
    ("0x00401008", "e8 f3 02 00 00", "call", "sub_401300",   "; stage 1"),
    ("0x0040100d", "85 c0",          "test", "eax, eax",     ""),
    ("0x0040100f", "75 0a",          "jne",  "loc_40101b",   "; verdict"),
]

TAGLINES = ["reverse engineering", "low-level development", "windows internals"]

W, H = 900, 385
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'DejaVu Sans Mono', 'Liberation Mono', monospace"
CYCLE = 16          # seconds for one pass of the listing
STEP = 0.9          # seconds between listing lines
START = 1.0
FADE = 0.5


def keyframes(i):
    t0 = (START + i * STEP) / CYCLE * 100
    t1 = t0 + FADE / CYCLE * 100
    return (f"@keyframes l{i}{{0%,{t0:.2f}%{{opacity:0}}{t1:.2f}%,92%{{opacity:1}}"
            f"97%,100%{{opacity:0}}}}")


def pad(s, n):
    return s + " " * (n - len(s))


def build():
    css = [
        f"text{{font-family:{MONO};white-space:pre}}",
        ".addr{fill:#6e7681}.bytes{fill:#545d68}.mn{fill:#7aa2f7}.op{fill:#c9d1d9}.cm{fill:#6e7681}",
        ".tag{fill:#8b949e;font-size:13px}.dim{fill:#545d68;font-size:13px}",
        ".cur{animation:blink 1.1s steps(1) infinite}",
        "@keyframes blink{0%{fill-opacity:1}50%{fill-opacity:0}}",
    ]
    for i in range(len(LISTING) + 1):
        css.append(keyframes(i))
        css.append(f".l{i}{{opacity:0;animation:l{i} {CYCLE}s linear infinite}}")

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'role="img" aria-label="stckwzrd">',
        "<title>stckwzrd</title>",
        f"<style>{''.join(css)}</style>",
        "<defs>"
        '<linearGradient id="sweep" gradientUnits="userSpaceOnUse" x1="-260" y1="0" x2="0" y2="0">'
        '<stop offset="0" stop-color="#98a4b5"/><stop offset="0.5" stop-color="#ffffff"/>'
        '<stop offset="1" stop-color="#98a4b5"/>'
        '<animate attributeName="x1" values="-260;820;820" keyTimes="0;0.65;1" dur="9s" repeatCount="indefinite"/>'
        '<animate attributeName="x2" values="0;1080;1080" keyTimes="0;0.65;1" dur="9s" repeatCount="indefinite"/>'
        "</linearGradient>"
        '<linearGradient id="rule" x1="0" x2="1" y1="0" y2="0">'
        '<stop offset="0" stop-color="#7aa2f7" stop-opacity="0.9"/>'
        '<stop offset="1" stop-color="#7aa2f7" stop-opacity="0"/></linearGradient>'
        "</defs>",
        f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="8" fill="#0d1117" stroke="#30363d"/>',
    ]

    # wordmark
    fs, lh, x0, y0 = 20, 25, 40, 64
    for n, line in enumerate(WORDMARK):
        out.append(f'<text x="{x0}" y="{y0 + n * lh}" font-size="{fs}" '
                   f'fill="url(#sweep)">{escape(line)}</text>')

    # right column
    rx = 700
    for n, t in enumerate(TAGLINES):
        out.append(f'<text class="tag" x="{rx}" y="{y0 + 14 + n * 24}">{escape(t)}</text>')
    out.append(f'<text class="dim" x="{rx}" y="{y0 + 14 + len(TAGLINES) * 24 + 6}">x86-64 / PE / ELF</text>')

    # rule
    ry = 218
    out.append(f'<rect x="{x0}" y="{ry}" width="{W - 2 * x0}" height="1" fill="url(#rule)"/>')

    # listing
    fs2, lh2, ly = 13, 19, 246
    for i, (a, b, mn, op, cm) in enumerate(LISTING):
        out.append(
            f'<text class="l{i}" x="{x0}" y="{ly + i * lh2}" font-size="{fs2}" xml:space="preserve">'
            f'<tspan class="addr">{a}</tspan>  <tspan class="bytes">{pad(b, 14)}</tspan>  '
            f'<tspan class="mn">{pad(mn, 5)}</tspan> <tspan class="op">{pad(escape(op), 12)}</tspan>'
            f'<tspan class="cm">{escape(cm)}</tspan></text>'
        )
    last = len(LISTING)
    out.append(
        f'<text class="l{last}" x="{x0}" y="{ly + last * lh2}" font-size="{fs2}" xml:space="preserve">'
        f'<tspan class="addr">$ </tspan><tspan class="cur" fill="#c9d1d9">_</tspan></text>'
    )
    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(build())
    print(f"wrote {OUT}")
