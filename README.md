# wordcount-streak

Track your daily writing progress. Counts words, measures streaks, shows a 7-day bar chart. No cloud. No account.

```
📝  ~/writing/novel.txt

Today:     1,205 words  (+342 today)  ✓ Goal met!
Streak:  🔥 5 days

Last 7 days  (goal: 250 words/day):

  Wed  ████████░░    320  ✓
  Thu  █████████░    350  ✓
  Fri  ░░░░░░░░░░      0  ✗
  Sat  █████░░░░░    210  ✗
  Sun  ██████████    410  ✓
  Mon  ████████░░    338  ✓
  Tue  █████░░░░░    342  ✓ ←
```

## Install

```bash
bash install.sh
```

This creates a `wcs` symlink in `~/.local/bin`. Make sure that directory is on your PATH.

## Usage

```bash
wcs <file-or-directory> [options]
```

Run it once a day — after your writing session — to log your progress. Each run records the current word count and shows how much you added.

```bash
wcs ~/writing/novel.txt            # track a single file
wcs ~/writing/                     # track all .txt/.md files in a directory
wcs ~/writing/ --goal 500          # set a custom daily word goal (default: 250)
wcs ~/writing/novel.txt --history  # show full history table
wcs ~/writing/novel.txt --no-save  # show stats without saving to history
wcs ~/writing/novel.txt --reset    # clear all history for this target
```

## How it works

- Each run records today's total word count
- "Words today" = today's total minus yesterday's total (net positive change)
- A streak day = you added ≥ goal words
- Streak = consecutive days ending today where goal was met
- History is stored in `~/.wordcount-streak/<hash>.json` per target path

## Supported file types

When scanning a directory: `.txt`, `.md`, `.rst`, `.tex`, `.org`, `.fountain`, `.fdx`

## Limitations

- Measures net word increase, not gross words typed (deletions reduce the count)
- One snapshot per day — run it at the end of your session for accurate delta
- Does not sync across machines

## Free to use

No license restrictions. Do what you want with it.
