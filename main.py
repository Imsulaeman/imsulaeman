from datetime import datetime
from zoneinfo import ZoneInfo
import gifos


def main():
    t = gifos.Terminal(750, 500, 15, 15)

    # BIOS boot
    t.gen_text("", 1, count=20)
    t.toggle_show_cursor(False)
    year_now = datetime.now(ZoneInfo("Asia/Jakarta")).strftime("%Y")
    t.gen_text("BINA OS Modular BIOS v1.0.0", 1)
    t.gen_text(f"Copyright (C) {year_now}, \x1b[31mImsulaeman Corp.\x1b[0m", 2)
    t.gen_text("\x1b[94mGitHub Profile Terminal\x1b[0m", 4)
    t.gen_text("Bandung(tm) GIFCPU - 250Hz", 6)
    t.gen_text(
        "Press \x1b[94mDEL\x1b[0m to enter SETUP, \x1b[94mESC\x1b[0m to cancel Memory Test",
        t.num_rows,
    )
    for i in range(0, 65653, 7168):
        t.delete_row(7)
        if i < 30000:
            t.gen_text(f"Memory Test: {i}", 7, count=2, contin=True)
        else:
            t.gen_text(f"Memory Test: {i}", 7, contin=True)
    t.delete_row(7)
    t.gen_text("Memory Test: 64KB OK", 7, count=10, contin=True)
    t.gen_text("", 11, count=10, contin=True)

    t.clear_frame()
    t.gen_text("Initiating Boot Sequence ", 1, contin=True)
    t.gen_typing_text(".....", 1, contin=True)

    # Login
    t.clear_frame()
    t.clone_frame(5)
    t.toggle_show_cursor(False)
    t.gen_text("\x1b[93mBINA OS v1.0.0 (tty1)\x1b[0m", 1, count=5)
    t.gen_text("login: ", 3, count=5)
    t.toggle_show_cursor(True)
    t.gen_typing_text("imsulaeman", 3, contin=True)
    t.gen_text("", 4, count=5)
    t.toggle_show_cursor(False)
    t.gen_text("password: ", 4, count=5)
    t.toggle_show_cursor(True)
    t.gen_typing_text("*********", 4, contin=True)
    t.toggle_show_cursor(False)
    time_now = datetime.now(ZoneInfo("Asia/Jakarta")).strftime(
        "%a %b %d %I:%M:%S %p %Z %Y"
    )
    t.gen_text(f"Last login: {time_now} on tty1", 6)

    # clear
    t.gen_prompt(7, count=5)
    prompt_col = t.curr_col
    t.toggle_show_cursor(True)
    t.gen_typing_text("\x1b[91mclea", 7, contin=True)
    t.delete_row(7, prompt_col)
    t.gen_text("\x1b[92mclear\x1b[0m", 7, count=3, contin=True)

    # GitHub stats
    git_user_details = gifos.utils.fetch_github_stats("imsulaeman")
    top_languages = [lang[0] for lang in git_user_details.languages_sorted]

    t.clear_frame()
    user_details = f"""
    \x1b[30; 101mimsulaeman@GitHub\x1b[0m
    -----------------
    \x1b[96mOS:      \x1b[93mWindows 11 / Android\x1b[0m
    \x1b[96mHost:    \x1b[93mBina Nusantara University, Bandung\x1b[0m
    \x1b[96mRole:    \x1b[93mStudent & Builder\x1b[0m
    \x1b[96mEditor:  \x1b[93mVS Code\x1b[0m

    \x1b[30; 101mContact:\x1b[0m
    -----------------
    \x1b[96mEmail:   \x1b[93mImsulaeman@gmail.com\x1b[0m
    \x1b[96mThreads: \x1b[93m@ulanghidup\x1b[0m
    \x1b[96mWeb:     \x1b[93mimsulaeman.me\x1b[0m

    \x1b[30; 101mProjects:\x1b[0m
    -----------------
    \x1b[96mFolio       \x1b[93mOffline study companion\x1b[0m
    \x1b[96mSecond Brain \x1b[93mPersonal knowledge garden\x1b[0m
    \x1b[96mRutin       \x1b[93mAndroid health habit tracker\x1b[0m

    \x1b[30; 101mGitHub Stats:\x1b[0m
    -----------------
    \x1b[96mRating:       \x1b[93m{git_user_details.user_rank.level}\x1b[0m
    \x1b[96mStars Earned: \x1b[93m{git_user_details.total_stargazers}\x1b[0m
    \x1b[96mCommits ({int(year_now) - 1}): \x1b[93m{git_user_details.total_commits_last_year}\x1b[0m
    \x1b[96mTop Langs:    \x1b[93m{", ".join(top_languages[:4])}\x1b[0m
    """

    t.gen_prompt(1)
    prompt_col = t.curr_col
    t.clone_frame(10)
    t.toggle_show_cursor(True)
    t.gen_typing_text("\x1b[91mfetch.s", 1, contin=True)
    t.delete_row(1, prompt_col)
    t.gen_text("\x1b[92mfetch.sh\x1b[0m", 1, contin=True)
    t.gen_typing_text(" -u imsulaeman", 1, contin=True)

    t.toggle_show_cursor(False)
    t.gen_text(user_details, 2, count=5, contin=True)
    t.toggle_show_cursor(True)
    t.gen_prompt(t.curr_row)
    t.gen_typing_text(
        "\x1b[92m# Building tools when something bothers me enough.",
        t.curr_row,
        contin=True,
    )
    t.gen_text("", t.curr_row, count=120, contin=True)

    t.gen_gif()


if __name__ == "__main__":
    main()
