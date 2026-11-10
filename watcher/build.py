"""Steps 2 and 3 of the pipeline: build data/history.csv and data/status.json.

Both files are built from the files under data/raw/ alone, replayed day by day,
so running the build again gives the same files and a rule change (for example
to the title rule) applies to every day of the history.

Run: python -m watcher.build
"""

from pathlib import Path
import csv
import gzip
import json

from .normalize import convert
from .sources import SOURCES_BY_NAME
from .title_rule import in_role

RAW_DIR = Path("data/raw")
HISTORY_PATH = Path("data/history.csv")
STATUS_PATH = Path("data/status.json")

COLUMNS = [
    "posting_id", "source", "source_id", "employer", "title", "location", "department",
    "posted_date", "url", "in_role", "first_run", "first_seen", "last_seen", "status",
    "removed_date",
]


def raw_days(raw_dir=RAW_DIR):
    """The dated folders that hold at least one raw file, oldest first."""
    days = []
    for d in sorted(Path(raw_dir).glob("*")):
        if d.is_dir() and any(d.glob("*.json.gz")):
            days.append(d)
    return days


def load_day(day_dir, sources_by_name=SOURCES_BY_NAME):
    """{source name: list of converted postings} for every raw file of one day."""
    out = {}
    for path in sorted(day_dir.glob("*.json.gz")):
        name = path.name[: -len(".json.gz")]
        source = sources_by_name.get(name)
        if source is None:
            continue
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            raw = json.load(fh)
        out[name] = convert(raw, source, day_dir.name)
    return out


def apply_day(history, source_first_day, day, postings_by_source):
    """Update the history (a dict keyed by posting_id) with one day's raw files."""
    for source, postings in postings_by_source.items():
        source_first_day.setdefault(source, day)
        listed = set()
        for p in postings:
            pid = p["posting_id"]
            listed.add(pid)
            row = history.get(pid)
            if row is None:
                row = {"first_run": source_first_day[source] == day, "first_seen": day}
                history[pid] = row
            row.update(p)  # keep the latest title, location, url ...
            row["last_seen"] = day
            row["status"] = "open"  # a removed posting that is listed again reopens
            row["removed_date"] = ""
        for pid, row in history.items():
            if row["source"] == source and row["status"] == "open" and pid not in listed:
                row["status"] = "removed"
                row["removed_date"] = day
    return history


def build_history(raw_dir=RAW_DIR, sources_by_name=SOURCES_BY_NAME):
    history, source_first_day = {}, {}
    for day_dir in raw_days(raw_dir):
        apply_day(history, source_first_day, day_dir.name, load_day(day_dir, sources_by_name))
    rows = []
    for pid in sorted(history):
        row = dict(history[pid])
        row["in_role"] = "true" if in_role(row["title"]) else "false"
        row["first_run"] = "true" if row["first_run"] else "false"
        rows.append(row)
    return rows


def build_status(rows, raw_dir=RAW_DIR):
    days = raw_days(raw_dir)
    if not days:
        return {}
    latest = days[-1]
    run_file = latest / "_run.json"
    run_info = json.loads(run_file.read_text()) if run_file.exists() else {}
    sources = [
        {"name": s["name"], "ok": bool(s["ok"]), "count": s["count"]}
        for s in run_info.get("sources", [])
    ]
    day = latest.name
    return {
        "run_time": run_info.get("run_time", f"{day}T00:00:00Z"),
        "first_run_date": days[0].name,
        "days_with_success": len(days),
        "open": sum(r["status"] == "open" for r in rows),
        "new_today": sum(r["first_seen"] == day and r["first_run"] == "false" for r in rows),
        "removed_today": sum(r["removed_date"] == day for r in rows),
        "sources": sources,
    }


def write_history(rows, path=HISTORY_PATH):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main(raw_dir=RAW_DIR, history_path=HISTORY_PATH, status_path=STATUS_PATH):
    rows = build_history(raw_dir)
    write_history(rows, history_path)
    status = build_status(rows, raw_dir)
    Path(status_path).write_text(json.dumps(status, indent=2) + "\n")
    print(f"history: {len(rows)} postings; open {status.get('open')}, "
          f"new {status.get('new_today')}, removed {status.get('removed_today')}, "
          f"days {status.get('days_with_success')}")


if __name__ == "__main__":
    main()
