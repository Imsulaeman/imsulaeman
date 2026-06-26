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
FONT = "/usr/share/fonts/truetype/liberation/LiberationSans-{}.ttf"


def load_font(style, size):
    try:
        return ImageFont.truetype(FONT.format(style), size)
    except Exception:
        return ImageFont.load_default()


def fetch_contributions():
    query = """{ user(login: "imsulaeman") { contributionsCollection {
        contributionCalendar { totalContributions weeks { contributionDays { contributionCount } } }
    } } }"""
    r = requests.post("https://api.github.com/graphql", json={"query": query}, headers=GH_HEADERS)
    cal = r.json()["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    days = [d["contributionCount"] for w in cal["weeks"] for d in w["contributionDays"]]
    return cal["totalContributions"], days[-90:]


def render_png(year_total, days):
    W, H, S = 700, 300, 2
    BG      = (19, 23, 34, 255)
    PRIMARY = (209, 212, 220, 255)
    DIM     = (120, 123, 134, 255)
    GREEN   = (38, 166, 154, 255)
    GREEN_F = (38, 166, 154, 40)
    RED     = (239, 83, 80, 255)

    today     = days[-1]
    yesterday = days[-2] if len(days) >= 2 else 0
    delta     = today - yesterday

    if delta > 0:
        t_color, t_up, t_str = GREEN, True, f"+{delta}"
    elif delta < 0:
        t_color, t_up, t_str = RED, False, str(delta)
    else:
        t_color, t_up, t_str = DIM, None, "0"

    pct = f" ({abs(delta)/yesterday*100:.1f}%)" if yesterday > 0 and delta != 0 else ""

    img  = Image.new("RGBA", (W*S, H*S), BG)
    draw = ImageDraw.Draw(img)

    ft = load_font("Bold",    13*S)
    fb = load_font("Bold",    52*S)
    fm = load_font("Regular", 15*S)
    fs = load_font("Regular", 10*S)

    draw.text((24*S, 20*S), "GIT", font=ft, fill=DIM)
    draw.text((24*S, 46*S), f"{year_total:,}", font=fb, fill=PRIMARY)

    SZ = 5 * S

    def tri_up(cx, cy):
        return [(cx, cy), (cx - SZ, cy + int(SZ*1.6)), (cx + SZ, cy + int(SZ*1.6))]

    def tri_dn(cx, cy):
        return [(cx - SZ, cy), (cx + SZ, cy), (cx, cy + int(SZ*1.6))]

    # today row
    r1x, r1y = 24*S, 112*S
    if t_up is True:
        draw.polygon(tri_up(r1x + SZ, r1y), fill=t_color)
    elif t_up is False:
        draw.polygon(tri_dn(r1x + SZ, r1y), fill=t_color)
    else:
        draw.text((r1x, r1y), "-", font=fm, fill=t_color)
    draw.text((r1x + SZ*2 + 5*S, r1y), f"  {t_str}{pct}  Today", font=fm, fill=t_color)

    # ytd row
    r2x, r2y = 24*S, 136*S
    draw.polygon(tri_up(r2x + SZ, r2y), fill=GREEN)
    draw.text((r2x + SZ*2 + 5*S, r2y), f"  {year_total:,}  YTD", font=fm, fill=GREEN)

    # chart
    CT = 174*S
    CB = (H - 22)*S
    ch = CB - CT
    px = 24*S
    cw = W*S - 2*px
    n  = len(days)
    lo, hi = min(days), max(days)
    rng = (hi - lo) or 1

    def sx(i): return px + (i / (n - 1)) * cw
    def sy(v): return CT + ch*0.05 + ch*0.9*(1 - (v - lo)/rng)

    pts = [(sx(i), sy(v)) for i, v in enumerate(days)]

    # area fill
    fill_img  = Image.new("RGBA", (W*S, H*S), (0, 0, 0, 0))
    fill_draw = ImageDraw.Draw(fill_img)
    fill_poly = [(int(x), int(y)) for x, y in pts]
    fill_poly += [(int(pts[-1][0]), CB), (int(pts[0][0]), CB)]
    fill_draw.polygon(fill_poly, fill=GREEN_F)
    img  = Image.alpha_composite(img, fill_img)
    draw = ImageDraw.Draw(img)

    # line + dot
    draw.line([(int(x), int(y)) for x, y in pts], fill=GREEN, width=3)
    lx, ly = int(pts[-1][0]), int(pts[-1][1])
    r = 5*S
    draw.ellipse([lx-r, ly-r, lx+r, ly+r], fill=GREEN)

    draw.text((24*S, (H-16)*S), "last 90 days", font=fs, fill=DIM)

    img.resize((W, H), Image.LANCZOS).convert("RGB").save("chart.png")


def fetch_random_note(today):
    api = "https://api.github.com"
    h   = {"Authorization": f"token {TOKEN}"}
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

    # remove terminal gif if still present
    text = re.sub(r'\n?<img src="terminal\.gif"[^>]*/>\n?', '\n', text)

    chart_block = '<!-- CHART_START -->\n<img src="chart.png" alt="contributions" />\n<!-- CHART_END -->'
    compounding_block = (
        f'<!-- COMPOUNDING_START -->\n'
        f'---\n\n'
        f'currently compounding · refreshed daily from my [Second Brain](https://brain.imsulaeman.me)\n\n'
        f'**[{title}]({url})**  \n'
        f'{excerpt}\n'
        f'<!-- COMPOUNDING_END -->'
    )

    if "<!-- CHART_START -->" in text:
        text = re.sub(r'<!-- CHART_START -->.*?<!-- CHART_END -->', chart_block, text, flags=re.DOTALL)
    else:
        text = chart_block + '\n\n' + text.lstrip()

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
