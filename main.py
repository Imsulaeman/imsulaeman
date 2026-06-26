from datetime import datetime
from zoneinfo import ZoneInfo
import gifos


def main():
    t = gifos.Terminal(700, 380, 15, 15)

    git = gifos.utils.fetch_github_stats("imsulaeman")
    top_langs = [lang[0] for lang in git.languages_sorted]
    year_now = datetime.now(ZoneInfo("Asia/Jakarta")).strftime("%Y")

    t.toggle_show_cursor(False)
    t.gen_text("", 1, count=10)

    # whoami
    t.gen_prompt(2, count=3)
    t.toggle_show_cursor(True)
    t.gen_typing_text("whoami", 2, contin=True)
    t.toggle_show_cursor(False)
    t.gen_text("\x1b[93mIlham Maulana Sulaeman\x1b[0m -- Bandung, Indonesia", 3)
    t.gen_text("student @ Bina Nusantara |  reads finance, builds tools", 4, count=8)

    # ls projects
    t.gen_prompt(6, count=3)
    t.toggle_show_cursor(True)
    t.gen_typing_text("ls projects/", 6, contin=True)
    t.toggle_show_cursor(False)
    t.gen_text(
        "\x1b[94mFolio\x1b[0m   \x1b[94mSecond-Brain\x1b[0m   \x1b[94mRutin\x1b[0m   \x1b[94mimsulaeman.me\x1b[0m",
        7, count=8
    )

    # git log
    t.gen_prompt(9, count=3)
    t.toggle_show_cursor(True)
    t.gen_typing_text("git log --oneline -3", 9, contin=True)
    t.toggle_show_cursor(False)
    t.gen_text(f"\x1b[33m{git.total_commits_last_year}\x1b[0m commits in {int(year_now) - 1}  |  top langs: \x1b[93m{', '.join(top_langs[:3])}\x1b[0m", 10)
    t.gen_text(f"stars earned: \x1b[93m{git.total_stargazers}\x1b[0m  |  rank: \x1b[93m{git.user_rank.level}\x1b[0m", 11, count=8)

    # closing line
    t.gen_prompt(13, count=3)
    t.toggle_show_cursor(True)
    t.gen_typing_text("# if it bothers me enough, i'll build it", 13, contin=True)
    t.gen_text("", 13, count=80, contin=True)

    t.gen_gif()


if __name__ == "__main__":
    main()
