import os
import re
import json
import random
import hashlib
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

TOKEN = os.environ["GITHUB_TOKEN"]
GH_HEADERS = {"Authorization": f"bearer {TOKEN}"}


def fetch_contributions():
    query = """{ user(login: "imsulaeman") { contributionsCollection {
        contributionCalendar { weeks { contributionDays {
            contributionCount weekday
        } } }
    } } }"""
    r = requests.post(
        "https://api.github.com/graphql",
        json={"query": query},
        headers=GH_HEADERS,
    )
    return r.json()["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]


def weeks_to_ohlc(weeks):
    ohlc = []
    for week in weeks[-26:]:
        counts = [d["contributionCount"] for d in week["contributionDays"]]
        if not counts:
            continue
        ohlc.append((counts[0], max(counts), min(counts), counts[-1]))
    return ohlc


def render_svg(ohlc):
    W, H = 700, 160
    PX, PY = 28, 16
    cw = H - 2 * PY
    BG, GREEN, RED, GRID, LABEL = "#131722", "#26a69a", "#ef5350", "#2a2e39", "#787b86"

    all_vals = [v for c in ohlc for v in c]
    lo, hi = min(all_vals), max(all_vals)
    rng = (hi - lo) or 1

    def sy(v):
        return PY + cw * 0.05 + cw * 0.9 * (1 - (v - lo) / rng)

    n = len(ohlc)
    slot = (W - 2 * PX) / n
    bw = max(slot * 0.5, 3)

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}">',
           f'<rect width="{W}" height="{H}" fill="{BG}" rx="4"/>']

    for i in range(1, 4):
        y = PY + cw * i / 4
        out.append(f'<line x1="{PX}" y1="{y:.1f}" x2="{W-PX}" y2="{y:.1f}" stroke="{GRID}" stroke-width="1"/>')

    out.append(f'<text x="{PX}" y="{H-4}" font-family="monospace" font-size="9" fill="{LABEL}">github contributions — last 26 weeks</text>')

    for i, (o, h, l, c) in enumerate(ohlc):
        xc = PX + (i + 0.5) * slot
        color = GREEN if c >= o else RED
        yo, yc, yh, yl = sy(o), sy(c), sy(h), sy(l)
        top, bot = min(yo, yc), max(yo, yc)
        bh = max(bot - top, 1.5)
        out.append(f'<line x1="{xc:.1f}" y1="{yh:.1f}" x2="{xc:.1f}" y2="{yl:.1f}" stroke="{color}" stroke-width="1"/>')
        out.append(f'<rect x="{xc - bw/2:.1f}" y="{top:.1f}" width="{bw:.1f}" height="{bh:.1f}" fill="{color}"/>')

    out.append("</svg>")
    return "\n".join(out)


def fetch_random_note(today):
    api = "https://api.github.com"
    h = {"Authorization": f"token {TOKEN}"}
    files = []
    for d in ["content/concepts", "content/synthesis"]:
        r = requests.get(f"{api}/repos/imsulaeman/second-brain-site/contents/{d}", headers=h)
        if r.status_code == 200:
            files += [f["download_url"] for f in r.json() if f["name"].endswith(".md")]

    seed = int(hashlib.md5(str(today).encode()).hexdigest(), 16)
    random.seed(seed)
    url = random.choice(files)

    content = requests.get(url).text

    title_m = re.search(r'^title:\s*["\']?(.+?)["\']?\s*$', content, re.MULTILINE)
    title = title_m.group(1) if title_m else "Unknown"

    body = re.sub(r'^---.*?---\s*', '', content, flags=re.DOTALL)
    body = re.sub(r'^#.+\n', '', body, flags=re.MULTILINE).strip()
    paras = [p.strip() for p in body.split('\n\n') if p.strip() and not p.startswith('#')]
    excerpt = paras[0] if paras else ""
    excerpt = re.sub(r'\[\[.*?\|(.*?)\]\]', r'\1', excerpt)
    excerpt = re.sub(r'\[\[.*?\]\]', '', excerpt)
    excerpt = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', excerpt)
    excerpt = excerpt.replace('\n', ' ').strip()
    if len(excerpt) > 180:
        excerpt = excerpt[:180].rsplit(' ', 1)[0] + '...'

    return title, excerpt


def update_readme(title, excerpt):
    with open("README.md", "r") as f:
        text = f.read()

    chart_block = f'<!-- CHART_START -->\n<img src="./chart.svg" alt="contributions" />\n<!-- CHART_END -->'
    compounding_block = f'<!-- COMPOUNDING_START -->\n> **currently compounding:** {title}\n>\n> {excerpt}\n<!-- COMPOUNDING_END -->'

    if "<!-- CHART_START -->" in text:
        text = re.sub(r'<!-- CHART_START -->.*?<!-- CHART_END -->', chart_block, text, flags=re.DOTALL)
    else:
        text = text.replace('<img src="terminal.gif"', f'{chart_block}\n\n<img src="terminal.gif"', 1)

    if "<!-- COMPOUNDING_START -->" in text:
        text = re.sub(r'<!-- COMPOUNDING_START -->.*?<!-- COMPOUNDING_END -->', compounding_block, text, flags=re.DOTALL)
    else:
        text = text.rstrip() + f'\n\n{compounding_block}\n'

    with open("README.md", "w") as f:
        f.write(text)


def main():
    today = datetime.now(ZoneInfo("Asia/Jakarta")).date()

    ohlc = weeks_to_ohlc(fetch_contributions())
    with open("chart.svg", "w") as f:
        f.write(render_svg(ohlc))
    print("INFO: chart.svg generated")

    title, excerpt = fetch_random_note(today)
    print(f"INFO: note selected: {title}")

    update_readme(title, excerpt)
    print("INFO: README.md updated")


if __name__ == "__main__":
    main()
