"""Step 1 of the pipeline: call every source and save what it returns.

Writes data/raw/<UTC date>/<source>.json.gz for every source that answers, and
data/raw/<UTC date>/_run.json recording the result of every source (success or
failure). One source failing does not stop the run, and a failed source writes
no raw file. A second run on the same day replaces that day's files.

Run: python -m watcher.fetch
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
import gzip
import json
import shutil
import time
import urllib.parse
import urllib.request

from .normalize import convert
from .sources import SOURCES

RAW_DIR = Path("data/raw")
HEADERS = {"User-Agent": "job-watcher-student-project/1.0", "Accept": "application/json"}
MAX_POSTINGS = 5000


def get_json(url, body=None, attempts=3):
    """GET (or POST when body is given) and parse JSON, retrying a few times."""
    headers = dict(HEADERS)
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    last_error = None
    for attempt in range(attempts):
        try:
            req = urllib.request.Request(url, data=data, headers=headers)
            with urllib.request.urlopen(req, timeout=45) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            last_error = exc
            time.sleep(2 * (attempt + 1))
    raise last_error


def fetch_greenhouse(source):
    return get_json(f"https://boards-api.greenhouse.io/v1/boards/{source['slug']}/jobs?content=false")


def fetch_lever(source):
    return get_json(f"https://api.lever.co/v0/postings/{source['slug']}?mode=json")


def fetch_ashby(source):
    return get_json(f"https://api.ashbyhq.com/posting-api/job-board/{source['slug']}")


def fetch_smartrecruiters(source):
    """Paginated: 100 postings per request. Pages are merged into one payload."""
    content, offset, total = [], 0, None
    while True:
        page = get_json(
            f"https://api.smartrecruiters.com/v1/companies/{source['company_id']}/postings?limit=100&offset={offset}"
        )
        if total is None:
            total = page.get("totalFound", 0)
        items = page.get("content", [])
        content.extend(items)
        offset += len(items)
        if not items or offset >= total or offset >= MAX_POSTINGS:
            break
    return {"totalFound": total, "content": content}


def fetch_workday(source):
    """Paginated POST: 20 postings per request. Pages are merged into one payload."""
    url = f"https://{source['host']}/wday/cxs/{source['tenant']}/{source['site']}/jobs"
    postings, offset, total = [], 0, None
    while True:
        page = get_json(url, {"appliedFacets": {}, "limit": 20, "offset": offset, "searchText": ""})
        if total is None:  # Workday only reports the total on the first page
            total = page.get("total", 0)
        items = page.get("jobPostings", [])
        postings.extend(items)
        offset += len(items)
        if not items or offset >= total or offset >= MAX_POSTINGS:
            break
        time.sleep(0.1)
    return {"total": total, "jobPostings": postings}


def fetch_oracle(source):
    """Oracle Recruiting Cloud. Paginated: 100 postings per request, merged into one payload.

    A board with more than 5,000 postings is requested with the source's search term.
    """
    finder = f"findReqs;siteNumber={source['site']}"
    if source.get("search_term"):
        finder += f",keyword=%22{urllib.parse.quote(source['search_term'])}%22"
    reqs, offset, total = [], 0, None
    while True:
        page = get_json(
            f"https://{source['host']}/hcmRestApi/resources/latest/recruitingCEJobRequisitions?onlyData=true"
            f"&expand=requisitionList&finder={finder},sortBy=POSTING_DATES_DESC,limit=100,offset={offset}"
        )
        item = (page.get("items") or [{}])[0]
        if total is None:
            total = item.get("TotalJobsCount", 0)
        items = item.get("requisitionList") or []
        reqs.extend(items)
        offset += len(items)
        if not items or offset >= total or offset >= MAX_POSTINGS:
            break
    return {"TotalJobsCount": total, "search_term": source.get("search_term", ""), "requisitionList": reqs}


GS_QUERY = (
    "query GetRoles($searchQueryInput: RoleSearchQueryInput!) { roleSearch(searchQueryInput: $searchQueryInput) "
    "{ totalCount items { roleId corporateTitle jobTitle jobFunction division "
    "locations { primary state country city } externalSource { sourceId } } } }"
)


def fetch_goldman(source):
    """Goldman Sachs' own careers API. Paginated: 100 roles per request, merged."""
    roles, page_number, total = [], 0, None
    while True:
        page = get_json("https://api-higher.gs.com/gateway/api/v1/graphql", {
            "operationName": "GetRoles", "query": GS_QUERY,
            "variables": {"searchQueryInput": {
                "page": {"pageSize": 100, "pageNumber": page_number},
                "sort": {"sortStrategy": "POSTED_DATE", "sortOrder": "DESC"},
                "filters": [], "experiences": ["PROFESSIONAL", "EARLY_CAREER"], "searchTerm": "",
            }},
        })
        if page.get("errors"):
            raise RuntimeError(json.dumps(page["errors"])[:200])
        result = page["data"]["roleSearch"]
        if total is None:
            total = result.get("totalCount", 0)
        items = result.get("items") or []
        roles.extend(items)
        page_number += 1
        if not items or len(roles) >= total or len(roles) >= MAX_POSTINGS:
            break
    return {"totalCount": total, "items": roles}


FETCHERS = {
    "oracle": fetch_oracle,
    "goldman": fetch_goldman,
    "greenhouse": fetch_greenhouse,
    "lever": fetch_lever,
    "ashby": fetch_ashby,
    "smartrecruiters": fetch_smartrecruiters,
    "workday": fetch_workday,
}


def write_gz(path, payload):
    """Write JSON gzip-compressed, with no timestamp so the same data gives the same file."""
    text = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    with open(path, "wb") as fh:
        with gzip.GzipFile(filename="", fileobj=fh, mode="wb", mtime=0) as gz:
            gz.write(text.encode("utf-8"))


def fetch_one(source, day_dir, day):
    """Fetch one source. Never raises: returns the result entry for _run.json."""
    try:
        raw = FETCHERS[source["ats"]](source)
        count = len(convert(raw, source, day))
        if count == 0:
            raise ValueError("board returned no postings")
        write_gz(day_dir / f"{source['name']}.json.gz", raw)
        return {"name": source["name"], "ok": True, "count": count, "error": None}
    except Exception as exc:
        return {"name": source["name"], "ok": False, "count": 0, "error": repr(exc)[:300]}


def run(sources=SOURCES, raw_dir=RAW_DIR, now=None):
    now = now or datetime.now(timezone.utc)
    day = now.date().isoformat()
    day_dir = Path(raw_dir) / day
    if day_dir.exists():  # second run on the same day replaces that day's files
        shutil.rmtree(day_dir)
    day_dir.mkdir(parents=True)

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda s: fetch_one(s, day_dir, day), sources))

    run_info = {"run_time": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "date": day, "sources": results}
    (day_dir / "_run.json").write_text(json.dumps(run_info, indent=2) + "\n")
    for r in results:
        print(f"{'OK  ' if r['ok'] else 'FAIL'} {r['name']:15} {r['count']:6}  {r['error'] or ''}")
    ok = sum(r["ok"] for r in results)
    print(f"{ok}/{len(results)} sources succeeded for {day}")
    if ok == 0:
        raise SystemExit("every source failed; nothing to commit")
    return run_info


if __name__ == "__main__":
    run()
