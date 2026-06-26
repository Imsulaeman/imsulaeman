import os
import re
import random
import hashlib
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from PIL import Image, ImageDraw, ImageFont

TOKEN = os.environ["GITHUB_TOKEN"]
GH_HEADERS = {"Authorization": f"bearer {TOKEN}"}

FONT_PATH = "/usr/share/fonts/truetype/liberation/LiberationSans-{}.ttf"

def load_font(style, size):
    try:
        return ImageFont.truetype(FONT_PATH.format(style), size)
    except Exception:
        return ImageFont.load_default()


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


def render_png(year_total, days):
    W, H = 700, 300
    BG      = (19, 23, 34)
    PRIMARY = (209, 212, 220)
    DIM     = (120, 123, 134)
    GREEN   = (38, 166, 154)
    RED     = (239, 83, 80)

    today     = days[-1]
    yesterday = days[-2] if len(days) >= 2 else 0
    delta     = today - yesterday

    if delta > 0:
        t_icon, t_color = "^", GREEN
        t_str = f"+{delta}"
    elif delta < 0:
        t_icon, t_color = "v", RED
        t_str = str(delta)
    else:
        t_icon, t_color = "-", DIM
        t_str = "0"

    pct_str   = f" ({abs(delta)/yesterday*100:.1f}%)" if yesterday > 0 and delta != 0 else ""
    today_txt = f"{t_icon} {t_str}{pct_str}  Today"
    ytd_txt   = f"^ {year_total:,}  YTD"

    img  = Image.new("RGB", (W, H), color=BG)
    draw = ImageDraw.Draw(img)

    f_ticker = load_font("Bold", 12)
    f_big    = load_font("Bold", 52)
    f_med    = load_font("Regular", 15)
    f_small  = load_font("Regular", 10)

    draw.text((24, 20),  "GIT",              font=f_ticker, fill=DIM)
    draw.text((24, 46),  f"{year_total:,}",  font=f_big,    fill=PRIMARY)
    draw.text((24, 110), today_txt,           font=f_med,    fill=t_color)
    draw.text((24, 132), ytd_txt,             font=f_med,    fill=GREEN)

    # Chart
    CHART_TOP = 170
    CHART_BOT = H - 22
    ch = CHART_BOT - CHART_TOP
    PX = 24
    cw = W - 2 * PX
    n  = len(days)
    lo, hi = min(days), max(days)
    rng = (hi - lo) or 1

    def sx(i): return PX + (i / (n - 1)) * cw
    def sy(v): return CHART_TOP + ch * 0.05 + ch * 0.9 * (1 - (v - lo) / rng)

    pts = [(sx(i), sy(v)) for i, v in enumerate(days)]
    draw.line(pts, fill=GREEN, width=2)

    lx, ly = pts[-1]
    r = 4
    draw.ellipse([lx - r, ly - r, lx + r, ly + r], fill=GREEN)

    draw.text((24, H - 16), "last 90 days", font=f_small, fill=DIM)

    img.save("chart.png")


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

    chart_block = '<!-- CHART_START -->\n<img src="chart.png" alt="contributions" />\n<!-- CHART_END -->'
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

    render_png(year_total, days)
    print("INFO: chart.png generated")

    title, excerpt, note_url = fetch_random_note(today)
    print(f"INFO: note: {title} -> {note_url}")

    update_readme(title, excerpt, note_url)
    print("INFO: README.md updated")


if __name__ == "__main__":
    main()
