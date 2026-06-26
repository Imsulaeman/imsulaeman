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
        contributionCalendar { weeks { contributionDays { contributionCount } } }
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
    PX, PY = 20, 20
    chart_w = W - 2 * PX
    chart_h = H - 2 * PY - 14
    BG, LINE, DOT, LABEL = "#131722", "#26a69a", "#26a69a", "#787b86"

    n = len(days)
    max_val = max(days) or 1
    min_val = min(days)
    rng = (max_val - min_val) or 1

    def sx(i):
        return PX + (i / (n - 1)) * chart_w

    def sy(v):
        normalized = (v - min_val) / rng
        return PY + chart_h * 0.05 + chart_h * 0.9 * (1 - normalized)

    # build polyline points
    points = " ".join(f"{sx(i):.1f},{sy(v):.1f}" for i, v in enumerate(days))
    last_x, last_y = sx(n - 1), sy(days[-1])

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}">',
        f'<rect width="{W}" height="{H}" fill="{BG}" rx="4"/>',
        f'<polyline points="{points}" fill="none" stroke="{LINE}" stroke-width="1.5" stroke-linejoin="round" stroke-linecap="round"/>',
        f'<circle cx="{last_x:.1f}" cy="{last_y:.1f}" r="3" fill="{DOT}"/>',
        f'<text x="{PX}" y="{H-3}" font-family="monospace" font-size="9" fill="{LABEL}">contributions — last 90 days</text>',
        '</svg>',
    ]
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

    note_url = f"https://brain.imsulaeman.me/note/{note_id}"
    return title, excerpt, note_url


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
