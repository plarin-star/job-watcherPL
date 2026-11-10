"""Step 4 of the pipeline: open (or update) today's GitHub Issue and close the previous one.

The issue is titled with the date of the latest run and lists the new postings and
the removed postings, each with a link. It is opened every day, even with no changes.
A second run on the same day updates the same issue.

Needs the GITHUB_TOKEN and GITHUB_REPOSITORY environment variables (set by GitHub Actions).
Run: python -m watcher.issue
"""

import csv
import json
import os
import urllib.request

from .build import HISTORY_PATH, STATUS_PATH

TITLE_PREFIX = "Job Watcher "
MAX_BODY = 60000  # GitHub's limit for an issue body is 65,536 characters


def latest_day(status):
    return status["run_time"][:10]


def changes(rows, day):
    new = [r for r in rows if r["first_seen"] == day and r["first_run"] == "false"]
    removed = [r for r in rows if r["removed_date"] == day]
    key = lambda r: (r["in_role"] != "true", r["employer"], r["title"])  # in-role first
    return sorted(new, key=key), sorted(removed, key=key)


def _lines(rows):
    out = []
    for r in rows:
        star = " ⭐" if r["in_role"] == "true" else ""
        where = f" — {r['location']}" if r["location"] else ""
        out.append(f"- [{r['title']}]({r['url']}) · {r['employer']}{where}{star}")
    return out


def build_body(rows, status, site_url=""):
    day = latest_day(status)
    new, removed = changes(rows, day)
    failed = [s["name"] for s in status["sources"] if not s["ok"]]
    head = [
        f"Run at {status['run_time']} · day {status['days_with_success']} of watching",
        "",
        f"**Open:** {status['open']} · **New today:** {status['new_today']} · "
        f"**Removed today:** {status['removed_today']}",
        f"**Sources:** {len(status['sources']) - len(failed)} of {len(status['sources'])} succeeded"
        + (f" (failed: {', '.join(failed)})" if failed else ""),
        "",
        "⭐ marks postings in my role (financial analyst / FP&A).",
    ]
    if site_url:
        head.append(f"Full lists: {site_url}")
    sections = []
    budget = MAX_BODY - len("\n".join(head))
    for label, items in ((f"New postings ({len(new)})", new), (f"Removed postings ({len(removed)})", removed)):
        lines, used, shown = [], 0, 0
        for line in _lines(items):
            if used + len(line) + 1 > budget // 2:
                break
            lines.append(line)
            used += len(line) + 1
            shown += 1
        if not items:
            lines = ["None today."]
        elif shown < len(items):
            lines.append(f"- … and {len(items) - shown} more (see the site)")
        sections += ["", f"## {label}", ""] + lines
    return "\n".join(head + sections) + "\n"


def api(method, path, payload=None):
    req = urllib.request.Request(
        f"https://api.github.com/repos/{os.environ['GITHUB_REPOSITORY']}{path}",
        data=json.dumps(payload).encode() if payload is not None else None,
        method=method,
        headers={
            "Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "job-watcher",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    status = json.loads(STATUS_PATH.read_text())
    with open(HISTORY_PATH, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    owner, _, repo = os.environ["GITHUB_REPOSITORY"].partition("/")
    title = TITLE_PREFIX + latest_day(status)
    body = build_body(rows, status, f"https://{owner.lower()}.github.io/{repo}/")

    issues = [
        i for i in api("GET", "/issues?state=all&per_page=100&sort=created&direction=desc")
        if "pull_request" not in i and i["title"].startswith(TITLE_PREFIX)
    ]
    today = next((i for i in issues if i["title"] == title), None)
    if today:  # second run on the same day: update the same issue
        api("PATCH", f"/issues/{today['number']}", {"body": body, "state": "open"})
        print(f"updated issue #{today['number']}: {title}")
    else:
        created = api("POST", "/issues", {"title": title, "body": body})
        print(f"opened issue #{created['number']}: {title}")
    for i in issues:
        if i["state"] == "open" and i["title"] != title:
            api("PATCH", f"/issues/{i['number']}", {"state": "closed"})
            print(f"closed issue #{i['number']}: {i['title']}")


if __name__ == "__main__":
    main()
