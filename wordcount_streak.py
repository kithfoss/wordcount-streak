#!/usr/bin/env python3
"""
wordcount-streak — Writing streak tracker.

Counts words in a file or directory, tracks your daily progress,
and shows a streak and 7-day bar chart. No cloud. No account.

Usage:
    wordcount-streak <target> [--goal N] [--history] [--reset]

Target can be a file (.txt, .md, .rst, etc.) or a directory
(scans recursively for writing files).

Storage: ~/.wordcount-streak/<hash>.json per target path.
"""

import os
import sys
import json
import hashlib
import pathlib
import datetime
import argparse
import re
import textwrap

# ── Constants ─────────────────────────────────────────────────────────────────

WRITING_EXTENSIONS = {".txt", ".md", ".rst", ".tex", ".org", ".fountain", ".fdx"}
DATA_DIR = pathlib.Path.home() / ".wordcount-streak"
DEFAULT_GOAL = 250
BAR_WIDTH = 10
BAR_FULL = "█"
BAR_EMPTY = "░"
DAYS_TO_SHOW = 7

# ── Word counting ─────────────────────────────────────────────────────────────

def count_words_in_file(path):
    """Count whitespace-delimited words in a single file."""
    try:
        text = pathlib.Path(path).read_text(encoding="utf-8", errors="replace")
        return len(text.split())
    except (OSError, PermissionError):
        return 0


def count_words(target):
    """Count total words for a file or directory (recursive for writing files)."""
    p = pathlib.Path(target).expanduser().resolve()
    if not p.exists():
        raise FileNotFoundError(f"Target not found: {target}")
    if p.is_file():
        return count_words_in_file(p)
    total = 0
    for f in p.rglob("*"):
        if f.is_file() and f.suffix.lower() in WRITING_EXTENSIONS:
            total += count_words_in_file(f)
    return total


# ── Storage ───────────────────────────────────────────────────────────────────

def target_hash(path):
    """Stable short hash for a resolved path, used as storage filename."""
    resolved = str(pathlib.Path(path).expanduser().resolve())
    return hashlib.sha1(resolved.encode()).hexdigest()[:12]


def data_file(path):
    DATA_DIR.mkdir(exist_ok=True)
    return DATA_DIR / f"{target_hash(path)}.json"


def load_data(path):
    df = data_file(path)
    if df.exists():
        try:
            return json.loads(df.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    resolved = str(pathlib.Path(path).expanduser().resolve())
    return {"path": resolved, "goal": DEFAULT_GOAL, "days": {}}


def save_data(path, data):
    data_file(path).write_text(json.dumps(data, indent=2))


# ── Streak calculation ────────────────────────────────────────────────────────

def daily_delta(days_data, goal):
    """
    Return a list of (date_str, delta, goal_met) tuples sorted ascending.
    delta = words added that day (today's total - previous day's total).
    The first recorded day has no baseline, so its delta is None.
    """
    if not days_data:
        return []

    sorted_dates = sorted(days_data.keys())
    result = []
    for i, d in enumerate(sorted_dates):
        words_today = days_data[d]["words"]
        if i == 0:
            result.append((d, None, False))
        else:
            prev_words = days_data[sorted_dates[i - 1]]["words"]
            delta = max(0, words_today - prev_words)
            result.append((d, delta, delta >= goal))
    return result


def calc_streak(days_data, goal, today_str, today_words=None):
    """Current consecutive-days streak ending on today.

    today_words: current word count for today if not yet saved in days_data.
    """
    deltas = daily_delta(days_data, goal)

    # Build a dict: date -> goal_met (only for days with a measurable delta)
    met = {d: gm for d, delta, gm in deltas if delta is not None}

    # Include today's live word count if today isn't in history yet
    if today_words is not None and today_str not in days_data:
        sorted_dates = sorted(days_data.keys())
        if sorted_dates:
            prev_words = days_data[sorted_dates[-1]]["words"]
            today_delta = max(0, today_words - prev_words)
            met[today_str] = today_delta >= goal

    streak = 0
    check = datetime.date.fromisoformat(today_str)
    while True:
        ds = check.isoformat()
        if ds in met and met[ds]:
            streak += 1
            check -= datetime.timedelta(days=1)
        else:
            break
    return streak


# ── Display ───────────────────────────────────────────────────────────────────

def render_bar(value, max_val, width=BAR_WIDTH):
    if max_val == 0:
        return BAR_EMPTY * width
    filled = round((value / max_val) * width)
    filled = max(0, min(width, filled))
    return BAR_FULL * filled + BAR_EMPTY * (width - filled)


def day_abbrev(date_str):
    d = datetime.date.fromisoformat(date_str)
    return d.strftime("%a")


def display_report(path, data, today_str, current_words):
    goal = data.get("goal", DEFAULT_GOAL)
    days = data.get("days", {})

    # Compute today's delta
    today_delta = None
    sorted_dates = sorted(days.keys())
    if today_str in days and len(sorted_dates) >= 2:
        idx = sorted_dates.index(today_str)
        if idx > 0:
            prev = days[sorted_dates[idx - 1]]["words"]
            today_delta = max(0, current_words - prev)
    elif today_str not in days and sorted_dates:
        last = days[sorted_dates[-1]]["words"]
        today_delta = max(0, current_words - last)

    streak = calc_streak(days, goal, today_str, today_words=current_words)

    # Header
    display_path = str(pathlib.Path(path).expanduser())
    print(f"\n📝  {display_path}")
    print()

    # Today summary
    delta_str = f"+{today_delta:,}" if today_delta is not None else "—"
    goal_tag = ""
    if today_delta is not None and today_delta >= goal:
        goal_tag = "  ✓ Goal met!"
    elif today_delta is not None:
        remaining = goal - today_delta
        goal_tag = f"  ({remaining:,} to go)"

    print(f"Today:   {current_words:>7,} words  ({delta_str} today){goal_tag}")

    if streak > 0:
        flame = "🔥" if streak >= 3 else "✦"
        print(f"Streak:  {flame} {streak} day{'s' if streak != 1 else ''}")
    else:
        print(f"Streak:  0 days")

    # 7-day chart
    print()
    print(f"Last {DAYS_TO_SHOW} days  (goal: {goal:,} words/day):")
    print()

    all_deltas = daily_delta(days, goal)
    delta_map = {d: (delta, gm) for d, delta, gm in all_deltas if delta is not None}

    # Also add today if not yet saved
    if today_str not in days and today_delta is not None:
        delta_map[today_str] = (today_delta, today_delta >= goal)

    # Build list of last N days
    end = datetime.date.fromisoformat(today_str)
    chart_days = [(end - datetime.timedelta(days=i)).isoformat() for i in range(DAYS_TO_SHOW - 1, -1, -1)]

    max_delta = max((v for v, _ in delta_map.values()), default=goal)
    max_delta = max(max_delta, goal)  # bar scale always fits goal

    for d in chart_days:
        abbrev = day_abbrev(d)
        is_today = d == today_str
        today_marker = " ←" if is_today else ""
        if d in delta_map:
            val, met = delta_map[d]
            bar = render_bar(val, max_delta)
            check = "✓" if met else "✗"
            print(f"  {abbrev}  {bar}  {val:>5,}  {check}{today_marker}")
        else:
            bar = BAR_EMPTY * BAR_WIDTH
            print(f"  {abbrev}  {bar}    —  {today_marker}".rstrip())

    print()


def display_history(data):
    days = data.get("days", {})
    goal = data.get("goal", DEFAULT_GOAL)
    if not days:
        print("No history yet.")
        return

    deltas = daily_delta(days, goal)
    print(f"\nHistory for: {data['path']}")
    print(f"Goal: {goal:,} words/day\n")
    print(f"  {'Date':<12} {'Words':>7}  {'Delta':>7}  {'Met?'}")
    print(f"  {'─'*12} {'─'*7}  {'─'*7}  {'─'*4}")
    for d, delta, gm in deltas:
        words = days[d]["words"]
        delta_str = f"+{delta:,}" if delta is not None else "  (base)"
        check = "✓" if gm else ("✗" if delta is not None else " ")
        print(f"  {d:<12} {words:>7,}  {delta_str:>7}  {check}")
    print()


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        prog="wordcount-streak",
        description="Writing streak tracker. Run it daily to log your progress.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
            Examples:
              wordcount-streak ~/writing/novel.txt
              wordcount-streak ~/writing/ --goal 500
              wordcount-streak ~/writing/novel.txt --history
              wordcount-streak ~/writing/novel.txt --reset
        """),
    )
    parser.add_argument("target", nargs="?", help="File or directory to track")
    parser.add_argument("--goal", type=int, default=None, help=f"Daily word goal (default: {DEFAULT_GOAL})")
    parser.add_argument("--history", action="store_true", help="Show full history instead of today's snapshot")
    parser.add_argument("--reset", action="store_true", help="Clear all stored history for this target")
    parser.add_argument("--no-save", action="store_true", help="Show today's count without updating history")

    args = parser.parse_args()

    if args.target is None:
        parser.print_help()
        sys.exit(0)

    target = args.target
    today = datetime.date.today().isoformat()

    # Count words first (validates target exists)
    try:
        current_words = count_words(target)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    data = load_data(target)

    # Apply goal if provided
    if args.goal is not None:
        data["goal"] = args.goal

    if args.reset:
        data["days"] = {}
        save_data(target, data)
        print(f"History cleared for: {pathlib.Path(target).expanduser().resolve()}")
        return

    if args.history:
        display_history(data)
        return

    # Show today and save (unless --no-save)
    display_report(target, data, today, current_words)

    if not args.no_save:
        data["days"][today] = {
            "words": current_words,
            "at": datetime.datetime.now().strftime("%H:%M:%S"),
        }
        save_data(target, data)


if __name__ == "__main__":
    main()
