"""Each applicant tracking system's raw JSON converts to the common columns."""

from watcher.normalize import POSTING_COLUMNS, convert, workday_posted_date

DAY = "2026-11-10"


def src(ats, **extra):
    return {"name": "acme", "employer": "Acme Corp", "ats": ats, **extra}


def check_columns(rows):
    for row in rows:
        assert list(row.keys()) == POSTING_COLUMNS


def test_greenhouse():
    raw = {"jobs": [{
        "id": 7001, "title": "Investment  Analyst ",
        "location": {"name": "New York, NY"},
        "departments": [{"name": "Finance"}, {"name": "Treasury"}],
        "first_published": "2026-11-03T22:30:00-05:00",
        "absolute_url": "https://boards.greenhouse.io/acme/jobs/7001",
    }]}
    rows = convert(raw, src("greenhouse", slug="acme"), DAY)
    check_columns(rows)
    assert rows == [{
        "posting_id": "acme:7001", "source": "acme", "source_id": "7001",
        "employer": "Acme Corp", "title": "Investment Analyst",
        "location": "New York, NY", "department": "Finance, Treasury",
        "posted_date": "2026-11-04",  # 22:30 at UTC-5 is the next day in UTC
        "url": "https://boards.greenhouse.io/acme/jobs/7001",
    }]


def test_greenhouse_missing_fields_are_empty():
    raw = {"jobs": [{"id": 1, "title": "Analyst", "absolute_url": "https://x/1"}]}
    row = convert(raw, src("greenhouse", slug="acme"), DAY)[0]
    assert row["location"] == "" and row["department"] == "" and row["posted_date"] == ""


def test_lever():
    raw = [{
        "id": "ab-12", "text": "Equity Research Associate",
        "categories": {"location": "London", "department": "Research", "team": "Equities"},
        "createdAt": 1793836800000,  # 2026-11-05 00:00 UTC
        "hostedUrl": "https://jobs.lever.co/acme/ab-12",
    }]
    rows = convert(raw, src("lever", slug="acme"), DAY)
    check_columns(rows)
    assert rows[0]["posting_id"] == "acme:ab-12"
    assert rows[0]["title"] == "Equity Research Associate"
    assert rows[0]["location"] == "London"
    assert rows[0]["department"] == "Research"
    assert rows[0]["posted_date"] == "2026-11-05"
    assert rows[0]["url"] == "https://jobs.lever.co/acme/ab-12"


def test_ashby_skips_unlisted():
    raw = {"jobs": [
        {"id": "u-1", "title": "Portfolio Analyst", "location": "Remote", "department": "Finance",
         "publishedAt": "2026-11-01T12:00:00.000+00:00", "jobUrl": "https://jobs.ashbyhq.com/acme/u-1",
         "isListed": True},
        {"id": "u-2", "title": "Hidden", "isListed": False},
    ]}
    rows = convert(raw, src("ashby", slug="acme"), DAY)
    check_columns(rows)
    assert [r["source_id"] for r in rows] == ["u-1"]
    assert rows[0]["department"] == "Finance"
    assert rows[0]["posted_date"] == "2026-11-01"
    assert rows[0]["url"] == "https://jobs.ashbyhq.com/acme/u-1"


def test_smartrecruiters():
    raw = {"totalFound": 1, "content": [{
        "id": "744000", "name": "Treasury Analyst",
        "location": {"city": "Dallas", "region": "TX", "country": "us"},
        "department": {"label": "Finance"},
        "releasedDate": "2026-10-30T08:00:00.000Z",
    }]}
    rows = convert(raw, src("smartrecruiters", company_id="AcmeCo"), DAY)
    check_columns(rows)
    assert rows[0]["posting_id"] == "acme:744000"
    assert rows[0]["location"] == "Dallas, TX, US"
    assert rows[0]["department"] == "Finance"
    assert rows[0]["posted_date"] == "2026-10-30"
    assert rows[0]["url"] == "https://jobs.smartrecruiters.com/AcmeCo/744000"


def test_workday():
    raw = {"total": 2, "jobPostings": [
        {"title": "Investment Banking Analyst", "locationsText": "2 Locations",
         "externalPath": "/job/Charlotte/Investment-Banking-Analyst_R-123", "postedOn": "Posted 3 Days Ago"},
        {"title": "Old Job", "locationsText": "Chicago",
         "externalPath": "/job/Chicago/Old-Job_R-9", "postedOn": "Posted 30+ Days Ago"},
    ]}
    source = src("workday", host="acme.wd1.myworkdayjobs.com", tenant="acme", site="Careers")
    rows = convert(raw, source, DAY)
    check_columns(rows)
    assert rows[0]["posting_id"] == "acme:R-123"
    assert rows[0]["location"] == "2 Locations"
    assert rows[0]["department"] == ""  # Workday's list does not provide it
    assert rows[0]["posted_date"] == "2026-11-07"
    assert rows[0]["url"] == (
        "https://acme.wd1.myworkdayjobs.com/en-US/Careers/job/Charlotte/Investment-Banking-Analyst_R-123"
    )
    assert rows[1]["posted_date"] == ""  # "30+ days ago" has no exact date


def test_workday_posted_date_words():
    assert workday_posted_date("Posted Today", DAY) == "2026-11-10"
    assert workday_posted_date("Posted Yesterday", DAY) == "2026-11-09"
    assert workday_posted_date("", DAY) == ""


def test_convert_drops_duplicates_and_missing_ids():
    raw = {"jobs": [
        {"id": 1, "title": "A", "absolute_url": "u"},
        {"id": 1, "title": "A again", "absolute_url": "u"},
        {"title": "No id", "absolute_url": "u"},
    ]}
    rows = convert(raw, src("greenhouse", slug="acme"), DAY)
    assert [r["posting_id"] for r in rows] == ["acme:1"]
