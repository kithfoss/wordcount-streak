# NOTES.md — wordcount-streak

## 2026-04-28 — Initial build

**Session:** Tuesday afternoon, ~16:00–17:00 CT. Scope day ran long; built the tool in the same session.

**Design decisions:**

- Net word delta (today - yesterday) rather than gross typed. This is simpler and more honest: if you delete 500 words and add 400, you wrote -100 words. That's real.
- One snapshot per run. Writers run it at session end. No watch loop, no daemon.
- History stored per-target (hash of resolved path). Targets are independent. One directory, one .json.
- Streak counts consecutive days ending today, including today's live word count (even before saving). So `--no-save` still shows the right streak.
- Bar chart scales to the max delta in the window, with a floor at the goal value. This prevents the chart from going all-zeros if goal is higher than any actual count.
- `--no-save` flag for checking stats mid-session without corrupting the day's final count.

**Bug fixed during build:**
Streak showed 0 even when today met the goal, because today's words weren't in `days_data` yet (pre-save path). Fixed by passing `today_words` to `calc_streak`, which computes today's delta inline against the most recent saved day.

**What works:**
- Word counting (files and directories, recursive)
- Streak calculation including live today
- 7-day bar chart with ✓/✗ goal markers and today indicator
- `--history` full table view
- `--reset` to clear history for a target
- `--no-save` for read-only checks
- `--goal` to override default (250)
- Install script to `~/.local/bin/wcs`

**What's not implemented:**
- `--watch` mode (real-time word count during writing session) — decided against for v1; adds complexity, questionable value
- Multiple targets in one command — not needed yet
- Goal persistence across sessions — `--goal` sets it in history.json for that target, but there's no global config; next run without `--goal` uses stored goal. Actually this IS implemented via `data["goal"]`.

**v1.0.0 shipped criteria:**
- [ ] Test on real writing files (not just tmp)
- [ ] Install and run as `wcs`
- [ ] Push to kithfoss GitHub

## Next

- After a few days of real use, consider adding: streak freeze (skip one day), best streak tracking, total words written to date.
