"""Probe candidate job boards and report which ones return JSON with no login.

Used once while choosing the watch list. Writes tools/probe_results.json with,
for each candidate, whether the request worked, how many postings the board
reports, and the error if it failed.

Run: python tools/probe_sources.py
"""

import json
import urllib.request
from pathlib import Path

HEADERS = {
    "User-Agent": "job-watcher-student-project/1.0",
    "Accept": "application/json",
}

# (name, ats, target) — target is a slug, company id, or "host|tenant|site" for Workday
CANDIDATES = [
    # Greenhouse
    ("stripe", "greenhouse", "stripe"),
    ("robinhood", "greenhouse", "robinhood"),
    ("affirm", "greenhouse", "affirm"),
    ("coinbase", "greenhouse", "coinbase"),
    ("brex", "greenhouse", "brex"),
    ("sofi", "greenhouse", "sofi"),
    ("chime", "greenhouse", "chime"),
    ("toast", "greenhouse", "toast"),
    ("nerdwallet", "greenhouse", "nerdwallet"),
    ("marqeta", "greenhouse", "marqeta"),
    ("airbnb", "greenhouse", "airbnb"),
    ("doordash", "greenhouse", "doordashusa"),
    ("dropbox", "greenhouse", "dropbox"),
    ("figma", "greenhouse", "figma"),
    ("carta", "greenhouse", "carta"),
    ("betterment", "greenhouse", "betterment"),
    # Lever
    ("plaid", "lever", "plaid"),
    ("palantir", "lever", "palantir"),
    ("spotify", "lever", "spotify"),
    ("wealthfront", "lever", "wealthfront"),
    ("kraken", "lever", "kraken"),
    # Ashby
    ("ramp", "ashby", "ramp"),
    ("mercury", "ashby", "mercury"),
    ("notion", "ashby", "notion"),
    ("openai", "ashby", "openai"),
    ("deel", "ashby", "deel"),
    ("kraken_ashby", "ashby", "kraken.com"),
    ("plaid_ashby", "ashby", "plaid"),
    # SmartRecruiters
    ("visa", "smartrecruiters", "Visa"),
    ("bosch", "smartrecruiters", "BoschGroup"),
    ("servicenow", "smartrecruiters", "ServiceNow"),
    ("mcdonalds", "smartrecruiters", "McDonaldsCorporation"),
    # Workday
    ("walmart", "workday", "walmart.wd5.myworkdayjobs.com|walmart|WalmartExternal"),
    ("nvidia", "workday", "nvidia.wd5.myworkdayjobs.com|nvidia|NVIDIAExternalCareerSite"),
    ("capitalone", "workday", "capitalone.wd12.myworkdayjobs.com|capitalone|Capital_One"),
    ("salesforce", "workday", "salesforce.wd12.myworkdayjobs.com|salesforce|External_Career_Site"),
    ("mastercard", "workday", "mastercard.wd1.myworkdayjobs.com|mastercard|CorporateCareers"),
    ("fidelity", "workday", "fmr.wd1.myworkdayjobs.com|fmr|FidelityCareers"),
    ("bankofamerica", "workday", "ghr.wd1.myworkdayjobs.com|ghr|Lateral-US"),
    ("tyson", "workday", "tysonfoods.wd5.myworkdayjobs.com|tysonfoods|TSN"),
    ("jbhunt", "workday", "jbhunt.wd1.myworkdayjobs.com|jbhunt|JBHuntCareers"),
]


def get_json(url, body=None):
    data = None
    headers = dict(HEADERS)
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def probe(ats, target):
    if ats == "greenhouse":
        d = get_json(f"https://boards-api.greenhouse.io/v1/boards/{target}/jobs")
        return len(d.get("jobs", []))
    if ats == "lever":
        d = get_json(f"https://api.lever.co/v0/postings/{target}?mode=json")
        return len(d)
    if ats == "ashby":
        d = get_json(f"https://api.ashbyhq.com/posting-api/job-board/{target}")
        return len(d.get("jobs", []))
    if ats == "smartrecruiters":
        d = get_json(f"https://api.smartrecruiters.com/v1/companies/{target}/postings?limit=1")
        return d.get("totalFound")
    if ats == "workday":
        host, tenant, site = target.split("|")
        d = get_json(
            f"https://{host}/wday/cxs/{tenant}/{site}/jobs",
            {"appliedFacets": {}, "limit": 1, "offset": 0, "searchText": ""},
        )
        return d.get("total")
    raise ValueError(ats)


def main():
    results = []
    for name, ats, target in CANDIDATES:
        try:
            count = probe(ats, target)
            ok = bool(count)
            results.append({"name": name, "ats": ats, "target": target, "ok": ok, "count": count, "error": None})
        except Exception as exc:  # record every failure and keep going
            results.append({"name": name, "ats": ats, "target": target, "ok": False, "count": 0, "error": repr(exc)[:200]})
        r = results[-1]
        print(f"{'OK  ' if r['ok'] else 'FAIL'} {name:15} {ats:16} {r['count']}  {r['error'] or ''}")
    Path("tools/probe_results.json").write_text(json.dumps(results, indent=2) + "\n")


if __name__ == "__main__":
    main()
