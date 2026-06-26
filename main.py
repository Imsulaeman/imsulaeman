from datetime import datetime
from zoneinfo import ZoneInfo
import gifos


def main():
    t = gifos.Terminal(750, 420, 15, 15)

    git = gifos.utils.fetch_github_stats("imsulaeman")
    top_langs = [lang[0] for lang in git.languages_sorted]
    year_now = datetime.now(ZoneInfo("Asia/Jakarta")).strftime("%Y")

    # boot straight into prompt
    t.toggle_show_cursor(False)
    t.gen_text("\x1b[93mBandung OS (tty1)\x1b[0m", 1, count=5)
    t.gen_text("login: ", 3, count=5)
    t.toggle_show_cursor(True)
    t.gen_typing_text("imsulaeman", 3, contin=True)
    t.gen_text("", 4, count=3)
    t.toggle_show_cursor(False)
    t.gen_text("password: ", 4)
    t.toggle_show_cursor(True)
    t.gen_typing_text("*********", 4, contin=True)
    t.toggle_show_cursor(False)

    t.clear_frame()

    # fetch command
    t.gen_prompt(1)
    prompt_col = t.curr_col
    t.clone_frame(8)
    t.toggle_show_cursor(True)
    t.gen_typing_text("fetch.sh", 1, contin=True)
    t.toggle_show_cursor(False)

    details = f"""
    \x1b[30; 101m ilham@github \x1b[0m
    ─────────────────────────
    \x1b[96mName    \x1b[0mIlham Maulana Sulaeman
    \x1b[96mFrom    \x1b[0mBandung, Indonesia
    \x1b[96mStudy   \x1b[0mBina Nusantara University
    \x1b[96mWeb     \x1b[0mimsulaeman.me

    \x1b[96mStars   \x1b[93m{git.total_stargazers}\x1b[0m
    \x1b[96mCommits \x1b[93m{git.total_commits_last_year}\x1b[0m  ({int(year_now) - 1})
    \x1b[96mLangs   \x1b[93m{", ".join(top_langs[:4])}\x1b[0m
    ─────────────────────────
    \x1b[90mReads finance. Builds tools.\x1b[0m
    \x1b[90mThreads: @ulanghidup\x1b[0m
    """

    t.gen_text(details, 3, count=5, contin=True)

    t.gen_prompt(t.curr_row)
    t.toggle_show_cursor(True)
    t.gen_text("", t.curr_row, count=100, contin=True)

    t.gen_gif()


if __name__ == "__main__":
    main()
