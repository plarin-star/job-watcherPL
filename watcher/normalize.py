"""Convert each applicant tracking system's raw JSON into one common set of columns.

Every converter takes the raw payload saved for one source on one day, the source's
config, and the UTC date of the raw file, and returns a list of dicts with the keys in
POSTING_COLUMNS. A column a source does not provide is left as an empty string.
"""

from datetime import date, datetime, timedelta, timezone
import re

POSTING_COLUMNS = [
    "posting_id", "source", "source_id", "employer", "title",
    "location", "department", "posted_date", "url",
]


def _clean(value) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split())


def iso_to_utc_date(value) -> str:
    """'2026-11-03T14:05:00-05:00' -> '2026-11-03' (in UTC). Empty if missing or unreadable."""
    if not value:
        return ""
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).date().isoformat()


def ms_to_utc_date(value) -> str:
    """Epoch milliseconds -> 'YYYY-MM-DD' in UTC."""
    if value in (None, ""):
        return ""
    try:
        return datetime.fromtimestamp(int(value) / 1000, tz=timezone.utc).date().isoformat()
    except (TypeError, ValueError, OverflowError):
        return ""


def workday_posted_date(posted_on: str, snapshot_date: str) -> str:
    """Workday gives relative text like 'Posted Today' or 'Posted 3 Days Ago'.

    Turn it into a date relative to the raw file's date. '30+ Days Ago' has no exact
    date, so it is left empty.
    """
    text = (posted_on or "").lower()
    day = date.fromisoformat(snapshot_date)
    if "today" in text:
        return day.isoformat()
    if "yesterday" in text:
        return (day - timedelta(days=1)).isoformat()
    m = re.search(r"(\d+)\s*day", text)
    if m and "+" not in text:
        return (day - timedelta(days=int(m.group(1)))).isoformat()
    return ""


def _row(source, source_id, title, location, department, posted_date, url):
    sid = _clean(source_id)
    return {
        "posting_id": f"{source['name']}:{sid}",
        "source": source["name"],
        "source_id": sid,
        "employer": source["employer"],
        "title": _clean(title),
        "location": _clean(location),
        "department": _clean(department),
        "posted_date": posted_date or "",
        "url": _clean(url),
    }


def from_greenhouse(raw, source, snapshot_date):
    rows = []
    for job in raw.get("jobs", []):
        depts = ", ".join(d.get("name", "") for d in job.get("departments") or [] if d.get("name"))
        rows.append(_row(
            source, job.get("id"), job.get("title"),
            (job.get("location") or {}).get("name"), depts,
            iso_to_utc_date(job.get("first_published")), job.get("absolute_url"),
        ))
    return rows


def from_lever(raw, source, snapshot_date):
    rows = []
    for job in raw if isinstance(raw, list) else []:
        cats = job.get("categories") or {}
        dept = cats.get("department") or cats.get("team")
        rows.append(_row(
            source, job.get("id"), job.get("text"), cats.get("location"), dept,
            ms_to_utc_date(job.get("createdAt")), job.get("hostedUrl"),
        ))
    return rows


def from_ashby(raw, source, snapshot_date):
    rows = []
    for job in raw.get("jobs", []):
        if job.get("isListed") is False:
            continue
        rows.append(_row(
            source, job.get("id"), job.get("title"), job.get("location"),
            job.get("department") or job.get("team"),
            iso_to_utc_date(job.get("publishedAt")), job.get("jobUrl"),
        ))
    return rows


def from_smartrecruiters(raw, source, snapshot_date):
    rows = []
    company = source["company_id"]
    for job in raw.get("content", []):
        loc = job.get("location") or {}
        location = loc.get("fullLocation") or ", ".join(
            p for p in [loc.get("city"), loc.get("region"), (loc.get("country") or "").upper()] if p
        )
        rows.append(_row(
            source, job.get("id"), job.get("name"), location,
            (job.get("department") or {}).get("label"),
            iso_to_utc_date(job.get("releasedDate")),
            f"https://jobs.smartrecruiters.com/{company}/{job.get('id')}",
        ))
    return rows


def workday_id(external_path: str) -> str:
    """'/job/Bentonville-AR/Financial-Analyst_R-2034567' -> 'R-2034567'."""
    last = (external_path or "").rstrip("/").split("/")[-1]
    return last.rsplit("_", 1)[-1] if "_" in last else last


def from_workday(raw, source, snapshot_date):
    rows = []
    base = f"https://{source['host']}/en-US/{source['site']}"
    for job in raw.get("jobPostings", []):
        path = job.get("externalPath") or ""
        rows.append(_row(
            source, workday_id(path), job.get("title"), job.get("locationsText"), "",
            workday_posted_date(job.get("postedOn"), snapshot_date), base + path,
        ))
    return rows


def from_oracle(raw, source, snapshot_date):
    """Oracle Recruiting Cloud (requisitionList merged from every page)."""
    rows = []
    base = f"https://{source['host']}/hcmUI/CandidateExperience/en/sites/{source['site']}/job"
    for job in raw.get("requisitionList", []):
        rows.append(_row(
            source, job.get("Id"), job.get("Title"), job.get("PrimaryLocation"),
            job.get("JobFunction") or job.get("JobFamily"),
            iso_to_utc_date(job.get("PostedDate")), f"{base}/{job.get('Id')}",
        ))
    return rows


def from_goldman(raw, source, snapshot_date):
    """Goldman Sachs' own careers API (higher.gs.com).

    Goldman keeps the level ("Analyst", "Associate", "Vice President") in a separate
    corporateTitle field, so it is added to the title when the title does not have it.
    The API gives no posted date.
    """
    rows = []
    for job in raw.get("items", []):
        title = _clean(job.get("jobTitle"))
        level = _clean(job.get("corporateTitle"))
        if level and level.lower() not in title.lower():
            title = f"{title} - {level}"
        locs = job.get("locations") or []
        location = ""
        if locs:
            first = next((l for l in locs if l.get("primary")), locs[0])
            location = ", ".join(p for p in [first.get("city"), first.get("state"), first.get("country")] if p)
            if len(locs) > 1:
                location += f" (+{len(locs) - 1} more)"
        source_id = (job.get("externalSource") or {}).get("sourceId") or job.get("roleId")
        rows.append(_row(
            source, job.get("roleId"), title, location, job.get("division"), "",
            f"https://higher.gs.com/roles/{source_id}",
        ))
    return rows


CONVERTERS = {
    "oracle": from_oracle,
    "goldman": from_goldman,
    "greenhouse": from_greenhouse,
    "lever": from_lever,
    "ashby": from_ashby,
    "smartrecruiters": from_smartrecruiters,
    "workday": from_workday,
}


def convert(raw, source, snapshot_date):
    """Convert one raw payload, dropping postings without an id and duplicate ids."""
    seen = {}
    for row in CONVERTERS[source["ats"]](raw, source, snapshot_date):
        if row["source_id"] and row["posting_id"] not in seen:
            seen[row["posting_id"]] = row
    return list(seen.values())
