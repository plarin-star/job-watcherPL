"""First-seen, last-seen, removed and reopened logic, built from raw files alone."""

import json

from watcher import build, fetch

SOURCES = {
    "alpha": {"name": "alpha", "employer": "Alpha", "ats": "greenhouse", "slug": "alpha"},
    "beta": {"name": "beta", "employer": "Beta", "ats": "greenhouse", "slug": "beta"},
}


def board(*jobs):
    return {"jobs": [{"id": i, "title": t, "absolute_url": f"https://x/{i}"} for i, t in jobs]}


def write_day(raw, day, boards, failed=()):
    (raw / day).mkdir(parents=True)
    for name, payload in boards.items():
        fetch.write_gz(raw / day / f"{name}.json.gz", payload)
    results = [{"name": n, "ok": True, "count": len(p["jobs"]), "error": None} for n, p in boards.items()]
    results += [{"name": n, "ok": False, "count": 0, "error": "boom"} for n in failed]
    (raw / day / "_run.json").write_text(json.dumps({"run_time": f"{day}T12:00:00Z", "sources": results}))


def history(raw):
    return {r["posting_id"]: r for r in build.build_history(raw, SOURCES)}


def make_three_days(raw):
    write_day(raw, "2026-11-10", {"alpha": board((1, "Investment Analyst"), (2, "Engineer"))})
    write_day(raw, "2026-11-11", {"alpha": board((2, "Engineer"), (3, "Designer")),
                                  "beta": board((9, "Equity Research Associate"))})
    write_day(raw, "2026-11-12", {"alpha": board((1, "Investment Analyst"), (3, "Designer"))}, failed=["beta"])


def test_first_seen_last_seen_and_first_run(tmp_path):
    make_three_days(tmp_path)
    h = history(tmp_path)
    assert h["alpha:1"]["first_seen"] == "2026-11-10" and h["alpha:1"]["first_run"] == "true"
    assert h["alpha:3"]["first_seen"] == "2026-11-11" and h["alpha:3"]["first_run"] == "false"
    assert h["alpha:3"]["last_seen"] == "2026-11-12"
    # beta's first raw file is on the 11th, so its posting is a first-run posting
    assert h["beta:9"]["first_seen"] == "2026-11-11" and h["beta:9"]["first_run"] == "true"


def test_removed_when_source_no_longer_lists_it(tmp_path):
    make_three_days(tmp_path)
    h = history(tmp_path)
    assert h["alpha:2"]["status"] == "removed"
    assert h["alpha:2"]["removed_date"] == "2026-11-12"
    assert h["alpha:2"]["last_seen"] == "2026-11-11"


def test_reopened_posting_keeps_first_seen_and_clears_removed_date(tmp_path):
    make_three_days(tmp_path)
    h = history(tmp_path)  # alpha:1 was missing on the 11th and listed again on the 12th
    assert h["alpha:1"]["status"] == "open"
    assert h["alpha:1"]["removed_date"] == ""
    assert h["alpha:1"]["first_seen"] == "2026-11-10"
    assert h["alpha:1"]["last_seen"] == "2026-11-12"


def test_not_removed_when_source_has_no_raw_file_that_day(tmp_path):
    make_three_days(tmp_path)
    h = history(tmp_path)  # beta failed on the 12th: no raw file, so nothing is removed
    assert h["beta:9"]["status"] == "open"
    assert h["beta:9"]["last_seen"] == "2026-11-11"


def test_rows_sorted_and_in_role_marked(tmp_path):
    make_three_days(tmp_path)
    rows = build.build_history(tmp_path, SOURCES)
    ids = [r["posting_id"] for r in rows]
    assert ids == sorted(ids)
    marks = {r["posting_id"]: r["in_role"] for r in rows}
    assert marks == {"alpha:1": "true", "alpha:2": "false", "alpha:3": "false", "beta:9": "true"}


def test_build_is_reproducible(tmp_path):
    make_three_days(tmp_path)
    first, second = tmp_path / "a.csv", tmp_path / "b.csv"
    build.write_history(build.build_history(tmp_path, SOURCES), first)
    build.write_history(build.build_history(tmp_path, SOURCES), second)
    assert first.read_bytes() == second.read_bytes()
    assert first.read_text().splitlines()[0] == ",".join(build.COLUMNS)


def test_status(tmp_path):
    make_three_days(tmp_path)
    status = build.build_status(build.build_history(tmp_path, SOURCES), tmp_path)
    assert status["run_time"] == "2026-11-12T12:00:00Z"
    assert status["first_run_date"] == "2026-11-10"
    assert status["days_with_success"] == 3
    assert status["open"] == 3            # alpha:1, alpha:3, beta:9
    assert status["new_today"] == 0       # nothing first seen on the 12th
    assert status["removed_today"] == 1   # alpha:2
    assert {"name": "beta", "ok": False, "count": 0} in status["sources"]


def test_new_today_leaves_out_first_run_postings(tmp_path):
    write_day(tmp_path, "2026-11-10", {"alpha": board((1, "A"))})
    write_day(tmp_path, "2026-11-11", {"alpha": board((1, "A"), (2, "B")), "beta": board((9, "C"))})
    status = build.build_status(build.build_history(tmp_path, SOURCES), tmp_path)
    assert status["new_today"] == 1  # alpha:2 only; beta:9 is a first-run posting


def test_failed_source_does_not_stop_the_run(tmp_path, monkeypatch):
    def fake(source):
        if source["name"] == "beta":
            raise RuntimeError("blocked")
        return board((1, "A"))
    monkeypatch.setitem(fetch.FETCHERS, "greenhouse", fake)
    info = fetch.run(list(SOURCES.values()), tmp_path)
    day = tmp_path / info["date"]
    assert (day / "alpha.json.gz").exists() and not (day / "beta.json.gz").exists()
    by_name = {s["name"]: s for s in json.loads((day / "_run.json").read_text())["sources"]}
    assert by_name["alpha"]["ok"] is True and by_name["alpha"]["count"] == 1
    assert by_name["beta"]["ok"] is False
