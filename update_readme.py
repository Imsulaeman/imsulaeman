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
        contributionCalendar { totalContributions weeks { contributionDays { contributionCount } } }
    } } }"""
    r = requests.post(
        "https://api.github.com/graphql",
        json={"query": query},
        headers=GH_HEADERS,
    )
    data = r.json()["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    year_total = data["totalContributions"]
    days = []
    for week in data["weeks"]:
        for day in week["contributionDays"]:
            days.append(day["contributionCount"])
    return year_total, days[-90:]


def render_svg(year_total, days):
    W, H = 700, 300
    BG = "#131722"
    PRIMARY = "#d1d4dc"
    DIM = "#787b86"
    GREEN = "#26a69a"
    RED = "#ef5350"

    today = days[-1]
    yesterday = days[-2] if len(days) >= 2 else 0
    delta = today - yesterday

    if delta > 0:
        t_icon, t_color = "▲", GREEN
        t_str = f"+{delta}"
    elif delta < 0:
        t_icon, t_color = "▼", RED
        t_str = str(delta)
    else:
        t_icon, t_color = "-", DIM
        t_str = "0"

    pct_str = f" ({abs(delta)/yesterday*100:.1f}%)" if yesterday > 0 and delta != 0 else ""
    today_text = f"{t_icon} {t_str}{pct_str}  Today"
    ytd_text = f"▲ {year_total:,}  YTD"

    # Chart area
    CHART_TOP = 185
    CHART_BOT = H - 24
    ch = CHART_BOT - CHART_TOP
    PX = 24
    cw = W - 2 * PX
    n = len(days)
    lo, hi = min(days), max(days)
    rng = (hi - lo) or 1

    def sx(i): return PX + (i / (n - 1)) * cw
    def sy(v): return CHART_TOP + ch * 0.05 + ch * 0.9 * (1 - (v - lo) / rng)

    pts = " ".join(f"{sx(i):.1f},{sy(v):.1f}" for i, v in enumerate(days))
    lx, ly = sx(n - 1), sy(days[-1])

    F = "font-family=\"Arial,sans-serif\""

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
        f'<rect width="{W}" height="{H}" fill="{BG}" rx="8"/>',
        f'<text x="24" y="40" {F} font-size="13" font-weight="bold" fill="{DIM}">GIT</text>',
        f'<text x="24" y="102" {F} font-size="54" font-weight="bold" fill="{PRIMARY}">{year_total:,}</text>',
        f'<text x="24" y="132" {F} font-size="15" fill="{t_color}">{today_text}</text>',
        f'<text x="24" y="158" {F} font-size="15" fill="{GREEN}">{ytd_text}</text>',
        f'<polyline points="{pts}" fill="none" stroke="{GREEN}" stroke-width="1.5" stroke-linejoin="round" stroke-linecap="round"/>',
        f'<circle cx="{lx:.1f}" cy="{ly:.1f}" r="3.5" fill="{GREEN}"/>',
        f'<text x="24" y="{H-6}" {F} font-size="9" fill="{DIM}">last 90 days</text>',
        '</svg>',
    ]
    return "\n".join(lines)


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

    return title, excerpt, f"https://brain.imsulaeman.me/note/{note_id}"


def update_readme(title, excerpt, url):
    with open("README.md", "r") as f:
        text = f.read()

    chart_block = '<!-- CHART_START -->\n<img src="chart.svg" alt="contributions" />\n<!-- CHART_END -->'
    compounding_block = (
        f'<!-- COMPOUNDING_START -->\n'
        f'> **currently compounding:** [{title}]({url})\n>\n> {excerpt}\n'
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
    year_total, days = fetch_contributions()

    with open("chart.svg", "w") as f:
        f.write(render_svg(year_total, days))
    print("INFO: chart.svg generated")

    title, excerpt, note_url = fetch_random_note(today)
    print(f"INFO: note: {title} -> {note_url}")

    update_readme(title, excerpt, note_url)
    print("INFO: README.md updated")


if __name__ == "__main__":
    main()
