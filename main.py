from datetime import datetime
from zoneinfo import ZoneInfo
import gifos


def main():
    t = gifos.Terminal(700, 340, 15, 15)

    git = gifos.utils.fetch_github_stats("imsulaeman")

    t.toggle_show_cursor(False)
    t.gen_text("", 1, count=10)

    # whoami
    t.gen_prompt(2, count=3)
    t.toggle_show_cursor(True)
    t.gen_typing_text("whoami", 2, contin=True)
    t.toggle_show_cursor(False)
    t.gen_text("\x1b[93mIlham Maulana Sulaeman\x1b[0m -- Bandung, Indonesia", 3)
    t.gen_text("student @ Bina Nusantara |  reads finance, builds tools", 4, count=8)

    # ls -la why/
    t.gen_prompt(6, count=3)
    t.toggle_show_cursor(True)
    t.gen_typing_text("ls -la why/", 6, contin=True)
    t.toggle_show_cursor(False)
    t.gen_text("\x1b[94mleverage/\x1b[0m   force multipliers -- money, knowledge", 7)
    t.gen_text("\x1b[94mtools/\x1b[0m      build when something bothers me enough", 8)
    t.gen_text("\x1b[94mknowledge/\x1b[0m  second brain, not just notes", 9, count=8)

    # stats
    t.gen_prompt(11, count=3)
    t.toggle_show_cursor(True)
    t.gen_typing_text("git log --stat", 11, contin=True)
    t.toggle_show_cursor(False)
    t.gen_text(
        f"stars: \x1b[93m{git.total_stargazers}\x1b[0m  |  commits: \x1b[93m{git.total_commits_last_year}\x1b[0m",
        12, count=8
    )

    # closing
    t.gen_prompt(14, count=3)
    t.toggle_show_cursor(True)
    t.gen_typing_text("# if it bothers me enough, i'll build it", 14, contin=True)
    t.gen_text("", 14, count=80, contin=True)

    t.gen_gif()


if __name__ == "__main__":
    main()
