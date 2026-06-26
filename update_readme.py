import os
import re
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
            contributionCount
        } } }
    } } }"""
    r = requests.post(
        "https://api.github.com/graphql",
        json={"query": query},
        headers=GH_HEADERS,
    )
    days = []
    for week in r.json()["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]:
        for day in week["contributionDays"]:
            days.append(day["contributionCount"])
    return days[-90:]


def render_svg(days):
    W, H = 700, 160
    PX, PY = 28, 16
    chart_w = W - 2 * PX
    chart_h = H - 2 * PY - 16  # leave room for label
    BG, GREEN, DIM, GRID, LABEL = "#131722", "#26a69a", "#2a2e39", "#1e2130", "#787b86"

    n = len(days)
    max_val = max(days) or 1
    slot = chart_w / n
    bw = max(slot * 0.7, 1.5)

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}">',
        f'<rect width="{W}" height="{H}" fill="{BG}" rx="4"/>',
    ]

    for i in range(1, 4):
        y = PY + chart_h * (1 - i / 4)
        out.append(f'<line x1="{PX}" y1="{y:.1f}" x2="{W-PX}" y2="{y:.1f}" stroke="{GRID}" stroke-width="1"/>')

    out.append(f'<text x="{PX}" y="{H-4}" font-family="monospace" font-size="9" fill="{LABEL}">contributions — last 90 days</text>')

    for i, count in enumerate(days):
        xc = PX + (i + 0.5) * slot
        bar_h = max((count / max_val) * chart_h, 1.5)
        y = PY + chart_h - bar_h
        color = GREEN if count > 0 else DIM
        out.append(f'<rect x="{xc - bw/2:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{bar_h:.1f}" fill="{color}" rx="1"/>')

    out.append("</svg>")
    return "\n".join(out)


def fetch_random_note(today):
    api = "https://api.github.com"
    h = {"Authorization": f"token {TOKEN}"}
    files = []
    for d in ["content/concepts", "content/synthesis"]:
        r = requests.get(f"{api}/repos/imsulaeman/second-brain-site/contents/{d}", headers=h)
        if r.status_code == 200:
            for f in r.json():
                if f["name"].endswith(".md"):
                    # id = "concepts/5-whys" from path "content/concepts/5-whys.md"
                    note_id = f["path"].replace("content/", "").replace(".md", "")
                    files.append((note_id, f["download_url"]))

    seed = int(hashlib.md5(str(today).encode()).hexdigest(), 16)
    random.seed(seed)
    note_id, url = random.choice(files)

    content = requests.get(url).text

    title_m = re.search(r'^title:\s*["\']?(.+?)["\']?\s*$', content, re.MULTILINE)
    title = title_m.group(1) if title_m else note_id.split("/")[-1].replace("-", " ").title()

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

    url_slug = f"https://brain.imsulaeman.me/note/{note_id}"
    return title, excerpt, url_slug


def update_readme(title, excerpt, url):
    with open("README.md", "r") as f:
        text = f.read()

    chart_block = '<!-- CHART_START -->\n<img src="./chart.svg" alt="contributions" />\n<!-- CHART_END -->'
    compounding_block = (
        f'<!-- COMPOUNDING_START -->\n'
        f'> **currently compounding:** [{title}]({url})\n'
        f'>\n'
        f'> {excerpt}\n'
        f'<!-- COMPOUNDING_END -->'
    )

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

    days = fetch_contributions()
    with open("chart.svg", "w") as f:
        f.write(render_svg(days))
    print("INFO: chart.svg generated")

    title, excerpt, url = fetch_random_note(today)
    print(f"INFO: note selected: {title} -> {url}")

    update_readme(title, excerpt, url)
    print("INFO: README.md updated")


if __name__ == "__main__":
    main()
