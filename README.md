# Job Watcher

[![Tests](https://github.com/plarin-star/job-watcherPL/actions/workflows/tests.yml/badge.svg)](https://github.com/plarin-star/job-watcherPL/actions/workflows/tests.yml)
[![Daily run](https://github.com/plarin-star/job-watcherPL/actions/workflows/daily.yml/badge.svg)](https://github.com/plarin-star/job-watcherPL/actions/workflows/daily.yml)

A tool that watches the job market for **investment and banking analyst** roles. Every day, on its
own, it pulls the open positions at 25 employers, compares them with the day before, records what
is new and what is gone, and publishes the result.

**Live site:** https://plarin-star.github.io/job-watcherPL/

## How it works

GitHub Actions runs the pipeline once a day at 12:23 UTC. Each run:

1. **Fetches** every source and saves what it returns, compressed, in
   `data/raw/<UTC date>/<source>.json.gz`. A source that fails writes no raw file and does not stop
   the run. The result of every source, success or failure, is recorded in
   `data/raw/<UTC date>/_run.json`.
2. **Builds** `data/history.csv` from the raw files alone, replaying them day by day.
3. **Writes** `data/status.json`.
4. **Commits** the raw files, the history file and the status file.
5. **Opens a GitHub Issue** titled with the date that lists the new and removed postings with
   links, and closes the previous day's issue. It is opened every day, even with no changes.

A second run on the same day replaces that day's raw files, rebuilds the history, and updates that
day's issue, so each day counts once.

## Build the history from the raw files

```
python -m watcher.build
```

This rebuilds `data/history.csv` and `data/status.json` from `data/raw/` and nothing else. Running
it again gives the same files, and a change to a rule (for example the title rule) applies to every
day of the history.

Other commands:

```
python -m watcher.fetch      # fetch every source into data/raw/<today>/
python -m watcher.issue      # open or update today's issue (needs GITHUB_TOKEN, GITHUB_REPOSITORY)
pip install -r requirements-dev.txt && python -m pytest   # run the tests
```

## Sources

25 employers, each read through the JSON API of the applicant tracking system that hosts its job
board, with no login.

| Employer | Source name | Applicant tracking system |
|---|---|---|
| Goldman Sachs | `goldmansachs` | Goldman Sachs careers API (higher.gs.com) |
| JPMorgan Chase | `jpmorgan` | Oracle Recruiting Cloud |
| Morgan Stanley | `morganstanley` | Workday |
| Bank of America | `bankofamerica` | Workday |
| Wells Fargo | `wellsfargo` | Workday |
| Barclays | `barclays` | Workday |
| Deutsche Bank | `deutschebank` | Workday |
| Deloitte | `deloitte` | SmartRecruiters |
| Raymond James | `raymondjames` | Workday |
| Houlihan Lokey | `houlihanlokey` | Workday |
| PJT Partners | `pjtpartners` | Workday |
| William Blair | `williamblair` | Greenhouse |
| Lincoln International | `lincolninternational` | Greenhouse |
| RBC | `rbc` | Workday |
| BMO | `bmo` | Workday |
| BlackRock | `blackrock` | Workday |
| Blackstone | `blackstone` | Workday |
| Fidelity Investments | `fidelity` | Workday |
| T. Rowe Price | `troweprice` | Workday |
| PIMCO | `pimco` | Workday |
| Carlyle | `carlyle` | Workday |
| Point72 | `point72` | Greenhouse |
| Ares Management | `ares` | Workday |
| Invesco | `invesco` | Workday |
| Vanguard | `vanguard` | Workday |

**Search term.** JPMorgan Chase's board returns more than 5,000 postings (about 7,000), so it is
requested with the search term **`analyst`**. Every other board is requested in full.

The code also has converters for Lever and Ashby boards, which were used while choosing the list.

## Title rule

A posting is marked `in_role` when its title, matched on whole words and ignoring case:

1. has a role word: `analyst` or `associate`; **and**
2. has a field word: `investment(s)`, `equity research`, `credit research`, `fixed income`,
   `capital markets`, `m&a`, `mergers`, `corporate development`, `private equity`, `valuation(s)`,
   `portfolio` or `trading`; **and**
3. has no seniority word: `senior`, `sr`, `principal`, `lead`, `manager`, `director`,
   `vice president`, `vp`, `head`, `chief` or `managing`; **and**
4. has no excluded word: `advisor`, `adviser`, `sales`, `insurance`, `compliance`, `fraud`,
   `crime(s)`, `sanctions`, `aml` or `kyc`.

Goldman Sachs keeps the level (Analyst, Associate, Vice President) in a separate field, so the
converter adds it to the title before the rule is applied. The rule lives in
`watcher/title_rule.py`. Every posting a board returns is kept in the history; the rule only sets
the `in_role` column.

## Files

| File | What it does |
|---|---|
| `watcher/sources.py` | The watch list: every employer, its applicant tracking system and board address |
| `watcher/fetch.py` | Calls every source, saves the raw files, records each source's result |
| `watcher/normalize.py` | Converts each tracking system's JSON to the common columns |
| `watcher/title_rule.py` | The title rule that sets `in_role` |
| `watcher/build.py` | Builds `data/history.csv` and `data/status.json` from the raw files |
| `watcher/issue.py` | Opens or updates the day's GitHub Issue and closes the previous one |
| `watcher/__init__.py` | Marks `watcher` as a Python package |
| `data/raw/<date>/<source>.json.gz` | What each source returned on each day |
| `data/raw/<date>/_run.json` | Run time and the result of every source for that day |
| `data/history.csv` | One row per posting: first seen, last seen, status, removed date |
| `data/status.json` | The latest run: time, counts and source results |
| `index.html`, `today.js` | Today page: last run, source status, counts, new and removed postings |
| `browse.html`, `browse.js` | Browse page: open postings with role switch, filters, search, sort, apply links, shortlist |
| `market.html`, `market.js` | Market page: six findings calculated in the browser from the history file |
| `charts.js` | The SVG charts used on the Market page |
| `app.js` | Shared navigation bar, data loading and helpers for all three pages |
| `style.css` | One set of fonts and colors for all three pages |
| `manifest.webmanifest`, `sw.js`, `icons/` | Make the site installable and let it open offline with the last data it loaded |
| `tests/test_normalize.py` | Tests the conversion of each source type to the common columns |
| `tests/test_title_rule.py` | Tests the title rule |
| `tests/test_history.py` | Tests first-seen, last-seen, removed and reopened logic, the status file, and a failed source |
| `.github/workflows/daily.yml` | The scheduled daily run |
| `.github/workflows/tests.yml` | Runs the tests on every push |
| `.github/workflows/probe.yml`, `tools/probe_sources.py`, `tools/probe_results.json` | Manual check of which candidate job boards answer; used to choose the watch list |
| `requirements-dev.txt` | The one development dependency (pytest) |
| `.nojekyll` | Tells GitHub Pages to serve the files as they are |

## Data columns

`data/history.csv`: `posting_id` (source and the source's own ID), `source`, `source_id`,
`employer`, `title`, `location`, `department`, `posted_date`, `url`, `in_role`, `first_run`,
`first_seen`, `last_seen`, `status` (`open` or `removed`), `removed_date`. Dates are UTC,
`YYYY-MM-DD`. A column a source does not provide is left empty.

`data/status.json`: `run_time`, `first_run_date`, `days_with_success`, `open`, `new_today`,
`removed_today`, and `sources` (a list of `name`, `ok`, `count`).

## Built with

Built with Claude Code.
