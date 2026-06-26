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

BG      = (19, 23, 34, 255)
PRIMARY = (209, 212, 220, 255)
DIM     = (120, 123, 134, 255)
GREEN   = (38, 166, 154, 255)
GREEN_F = (38, 166, 154, 40)
RED     = (239, 83, 80, 255)


def load_font(style, size):
    try:
        return ImageFont.truetype(FONT.format(style), size)
    except Exception:
        return ImageFont.load_default()


def wrap_text(draw, text, font, max_w, max_lines=2):
    words = text.split()
    lines, curr = [], []
    for word in words:
        test = " ".join(curr + [word])
        if draw.textlength(test, font=font) > max_w and curr:
            lines.append(" ".join(curr))
            if len(lines) >= max_lines:
                break
            curr = [word]
        else:
            curr.append(word)
    if curr and len(lines) < max_lines:
        lines.append(" ".join(curr))
    if lines and len(" ".join(lines).split()) < len(words):
        last = lines[-1]
        while last and draw.textlength(last + "...", font=font) > max_w:
            last = last.rsplit(" ", 1)[0]
        lines[-1] = last + "..."
    return lines


def fetch_contributions():
    now  = datetime.now(ZoneInfo("Asia/Jakarta"))
    y    = now.year
    query = """{{
      user(login: "imsulaeman") {{
        thisYear: contributionsCollection {{
          contributionCalendar {{ totalContributions weeks {{ contributionDays {{ contributionCount }} }} }}
        }}
        lastYear: contributionsCollection(from: "{ly}-01-01T00:00:00Z", to: "{ly}-12-31T23:59:59Z") {{
          contributionCalendar {{ totalContributions }}
        }}
      }}
    }}""".format(ly=y-1)
    r   = requests.post("https://api.github.com/graphql", json={"query": query}, headers=GH_HEADERS)
    data = r.json()["data"]["user"]
    cal  = data["thisYear"]["contributionCalendar"]
    days = [d["contributionCount"] for w in cal["weeks"] for d in w["contributionDays"]]
    last_year_total = data["lastYear"]["contributionCalendar"]["totalContributions"]
    return cal["totalContributions"], days[-90:], last_year_total


def render_chart(year_total, days, last_year_total):
    W, H, S = 700, 300, 2
    today     = days[-1]
    yesterday = days[-2] if len(days) >= 2 else 0
    delta     = today - yesterday

    if delta > 0:
        t_color, t_up, t_str = GREEN, True, f"+{delta}"
    elif delta < 0:
        t_color, t_up, t_str = RED, False, str(delta)
    else:
        t_color, t_up, t_str = DIM, None, "0"

    t_pct = f" ({abs(delta)/yesterday*100:.1f}%)" if yesterday > 0 and delta != 0 else ""

    ytd_delta = year_total - last_year_total
    if last_year_total > 0:
        ytd_pct = ytd_delta / last_year_total * 100
        ytd_str = f"+{ytd_pct:.1f}%" if ytd_pct >= 0 else f"{ytd_pct:.1f}%"
        ytd_up  = ytd_delta >= 0
        ytd_color = GREEN if ytd_delta >= 0 else RED
    else:
        ytd_str, ytd_up, ytd_color = "n/a", True, DIM

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

    r1x, r1y = 24*S, 112*S
    if t_up is True:
        draw.polygon(tri_up(r1x + SZ, r1y), fill=t_color)
    elif t_up is False:
        draw.polygon(tri_dn(r1x + SZ, r1y), fill=t_color)
    else:
        draw.text((r1x, r1y), "-", font=fm, fill=t_color)
    draw.text((r1x + SZ*2 + 5*S, r1y), f"  {t_str}{t_pct}  Today", font=fm, fill=t_color)

    r2x, r2y = 24*S, 136*S
    if ytd_up:
        draw.polygon(tri_up(r2x + SZ, r2y), fill=ytd_color)
    else:
        draw.polygon(tri_dn(r2x + SZ, r2y), fill=ytd_color)
    draw.text((r2x + SZ*2 + 5*S, r2y), f"  {ytd_str}  YTD", font=fm, fill=ytd_color)

    CT = 174*S; CB = (H-22)*S; ch = CB - CT
    cw = W*S

    chart_days = days[:]
    if chart_days[-1] == 0 and len(chart_days) >= 2:
        chart_days[-1] = chart_days[-2]

    n  = len(chart_days); lo, hi = min(chart_days), max(chart_days); rng = (hi - lo) or 1

    def sx(i): return (i / (n-1)) * cw
    def sy(v): return CT + ch*0.05 + ch*0.9*(1 - (v-lo)/rng)

    pts = [(sx(i), sy(v)) for i, v in enumerate(chart_days)]

    GREEN_DIM = (38, 110, 100)
    for i in range(len(pts) - 1):
        t = i / max(len(pts) - 2, 1)
        rc = int(GREEN_DIM[0] + t * (GREEN[0] - GREEN_DIM[0]))
        gc = int(GREEN_DIM[1] + t * (GREEN[1] - GREEN_DIM[1]))
        bc = int(GREEN_DIM[2] + t * (GREEN[2] - GREEN_DIM[2]))
        draw.line([(int(pts[i][0]), int(pts[i][1])), (int(pts[i+1][0]), int(pts[i+1][1]))],
                  fill=(rc, gc, bc), width=3)

    lx, ly = int(pts[-1][0]), int(pts[-1][1])
    r = 4*S
    draw.ellipse([lx-r, ly-r, lx+r, ly+r], fill=GREEN)
    draw.text((24*S, (H-16)*S), "last 90 days", font=fs, fill=DIM)

    img.resize((W, H), Image.LANCZOS).convert("RGB").save("chart.png")


def fetch_random_note(today):
    api = "https://api.github.com"
    h   = {"Authorization": f"token {TOKEN}"}
    files = []
    total = 0
    for d in ["content/concepts", "content/synthesis", "content/entities", "content/sources"]:
        r = requests.get(f"{api}/repos/imsulaeman/second-brain-site/contents/{d}", headers=h)
        if r.status_code == 200:
            md_files = [f for f in r.json() if f["name"].endswith(".md")]
            total += len(md_files)
            if d in ["content/concepts", "content/synthesis"]:
                for f in md_files:
                    note_id = f["path"].replace("content/", "").replace(".md", "")
                    files.append((note_id, f["download_url"]))

    seed = int(hashlib.md5(str(today).encode()).hexdigest(), 16)
    random.seed(seed)
    note_id, url = random.choice(files)
    content = requests.get(url).text

    title_m = re.search(r"^title:\s*[\"']?(.+?)[\"']?\s*$", content, re.MULTILINE)
    title = title_m.group(1) if title_m else note_id.split("/")[-1].replace("-", " ").title()

    type_m = re.search(r"^type:\s*(\w+)", content, re.MULTILINE)
    note_type = type_m.group(1) if type_m else None

    tags_m = re.search(r"^tags:\s*\[(.+?)\]", content, re.MULTILINE)
    tags = [t.strip() for t in tags_m.group(1).split(",")] if tags_m else []

    body = re.sub(r"^---.*?---\s*", "", content, flags=re.DOTALL)
    body = re.sub(r"^#{1,6}\s*.+\n?", "", body, flags=re.MULTILINE).strip()
    paras = [p.strip() for p in body.split("\n\n") if p.strip() and not p.strip().startswith("#")]
    excerpt = paras[0] if paras else ""
    excerpt = re.sub(r"\[\[.*?\|(.*?)\]\]", r"\1", excerpt)
    excerpt = re.sub(r"\[\[.*?\]\]", "", excerpt)
    excerpt = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", excerpt)
    excerpt = excerpt.replace("\n", " ").strip()

    return title, note_type, tags[:4], excerpt, total, f"https://brain.imsulaeman.me/note/{note_id}"


def render_compounding(title, note_type, tags, excerpt, total_notes):
    W, H, S = 700, 210, 2
    PX, PY  = 28, 24

    img  = Image.new("RGBA", (W*S, H*S), BG)
    draw = ImageDraw.Draw(img)

    fh = load_font("Bold",    11*S)
    fb = load_font("Bold",    22*S)
    fm = load_font("Regular", 13*S)
    ft = load_font("Regular", 11*S)
    fs = load_font("Regular", 10*S)

    header = "currently compounding"
    right  = f"{total_notes} notes  -  brain.imsulaeman.me"
    rw     = draw.textlength(right, font=fh)
    draw.text((PX*S, PY*S),               header, font=fh, fill=DIM)
    draw.text(((W-PX)*S - rw, PY*S),      right,  font=fh, fill=DIM)

    title_y = (PY + 20)*S
    max_w   = (W - 2*PX)*S
    t_lines = wrap_text(draw, title, fb, max_w, max_lines=2)
    line_h  = int(fb.size * 1.25)
    for i, line in enumerate(t_lines):
        draw.text((PX*S, title_y + i*line_h), line, font=fb, fill=PRIMARY)
    after_title = title_y + len(t_lines)*line_h + 10*S

    if note_type or tags:
        parts = []
        if note_type:
            parts.append(note_type)
        parts.extend(tags)
        tag_line = "  -  ".join(parts)
        draw.text((PX*S, after_title), tag_line, font=ft, fill=GREEN)
        after_tags = after_title + int(ft.size * 1.4) + 8*S
    else:
        after_tags = after_title

    ex_lines  = wrap_text(draw, excerpt, fm, max_w, max_lines=2)
    ex_line_h = int(fm.size * 1.4)
    for i, line in enumerate(ex_lines):
        draw.text((PX*S, after_tags + i*ex_line_h), line, font=fm, fill=DIM)

    draw.text((PX*S, (H-15)*S), "open in Second Brain  ->", font=fs, fill=DIM)

    img.resize((W, H), Image.LANCZOS).convert("RGB").save("compounding.png")


def update_readme(note_url):
    with open("README.md", "r") as f:
        text = f.read()

    text = re.sub(r"\n?<img src=\"terminal\.gif\"[^>]*/>\n?", "\n", text)

    chart_block = (
        "<!-- CHART_START -->\n"
        "<img src=\"chart.png\" alt=\"contributions\" />\n"
        "<!-- CHART_END -->"
    )
    compounding_block = (
        "<!-- COMPOUNDING_START -->\n"
        f"<a href=\"{note_url}\"><img src=\"compounding.png\" alt=\"currently compounding\" /></a>\n"
        "<!-- COMPOUNDING_END -->"
    )

    if "<!-- CHART_START -->" in text:
        text = re.sub(r"<!-- CHART_START -->.*?<!-- CHART_END -->", chart_block, text, flags=re.DOTALL)
    else:
        text = chart_block + "\n\n" + text.lstrip()

    if "<!-- COMPOUNDING_START -->" in text:
        text = re.sub(r"<!-- COMPOUNDING_START -->.*?<!-- COMPOUNDING_END -->", compounding_block, text, flags=re.DOTALL)
    else:
        text = text.rstrip() + f"\n\n{compounding_block}\n"

    with open("README.md", "w") as f:
        f.write(text)


def main():
    today = datetime.now(ZoneInfo("Asia/Jakarta")).date()

    year_total, days, last_year_total = fetch_contributions()
    render_chart(year_total, days, last_year_total)
    print("INFO: chart.png generated")

    title, note_type, tags, excerpt, total_notes, note_url = fetch_random_note(today)
    print(f"INFO: note: {title} ({note_type}) -> {note_url}")

    render_compounding(title, note_type, tags, excerpt, total_notes)
    print("INFO: compounding.png generated")

    update_readme(note_url)
    print("INFO: README.md updated")


if __name__ == "__main__":
    main()
