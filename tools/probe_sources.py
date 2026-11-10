"""Probe candidate job boards and report which ones return JSON with no login.

Used while choosing the watch list. Each candidate can have several guesses
(variants); the first one that answers with postings wins. Writes
tools/probe_results.json.

Run: python tools/probe_sources.py
"""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import json
import urllib.error
import urllib.request

HEADERS = {"User-Agent": "job-watcher-student-project/1.0", "Accept": "application/json"}

GS_QUERY = (
    "query GetRoles($searchQueryInput: RoleSearchQueryInput!) { roleSearch(searchQueryInput: $searchQueryInput) "
    "{ totalCount items { roleId corporateTitle jobTitle jobFunction locations { primary state country city } "
    "division externalSource { sourceId } } } }"
)


def wd(tenant, nums, sites, host=None):
    return [("workday", f"{host or f'{tenant}.wd{n}.myworkdayjobs.com'}|{tenant}|{s}") for n in nums for s in sites]


def gh(*slugs):
    return [("greenhouse", s) for s in slugs]


def oracle(host, *sites):
    return [("oracle", f"{host}|{s}") for s in sites]


GENERIC = ["External", "Careers", "External_Career_Site", "Experienced", "Search"]

CANDIDATES = {
    # Big names
    "goldmansachs": [("goldman", "")],
    "jpmorgan": oracle("jpmc.fa.oraclecloud.com", "CX_1001", "CX_1002"),
    "morganstanley": wd("ms", [5], ["External", "Experienced"]),
    "citi": wd("citi", [5], ["2", "External"]),
    "wellsfargo": wd("wf", [1], ["WellsFargoJobs"], host="wd1.myworkdaysite.com"),
    "deloitte": [("smartrecruiters", "Deloitte6"), ("smartrecruiters", "Deloitte"), ("smartrecruiters", "DeloitteUS")]
    + wd("deloitte", [1, 5], ["External", "Careers"]),
    "pwc": wd("pwc", [3], ["Global_Experienced_Careers", "US_Entry_Level_Careers"]),
    "kpmg": wd("kpmg", [1, 5], ["External", "KPMG_Careers"]) + [("smartrecruiters", "KPMG")],
    "ubs": wd("ubs", [3], GENERIC),
    "barclays": wd("barclays", [3], ["External_Career_Site_Barclays", "External"]),
    "deutschebank": wd("db", [3], ["DBWebsite"]),
    "rbc": wd("rbc", [3], ["RBCGLOBAL1"]),
    "bmo": wd("bmo", [3], ["External"]),
    "td": wd("td", [3], ["TD_Bank_Careers"]),
    "bny": oracle("eofe.fa.us2.oraclecloud.com", "CX_1001", "CX_1", "CX"),
    "usbank": wd("usbank", [1], ["US_Bank_Careers"]),
    "pnc": wd("pnc", [5], ["External"]),
    "truist": wd("truist", [1], ["Careers"]),
    "keybank": wd("keybank", [5], ["External_Career_Site"]),
    "schwab": wd("schwab", [1, 5], GENERIC),
    "nomura": wd("nomura", [1, 3, 5], GENERIC + ["Nomura"]),
    # Middle-market and boutique investment banks
    "jefferies": wd("jefferies", [1, 5], GENERIC + ["Jefferies"]) + gh("jefferies"),
    "raymondjames": wd("raymondjames", [1], ["RaymondJamesCareers", "External", "Careers"]),
    "stifel": wd("stifel", [1, 5], GENERIC + ["Stifel"]),
    "baird": wd("rwbaird", [1, 5], GENERIC + ["Baird"]) + wd("baird", [1, 5], GENERIC),
    "williamblair": wd("williamblair", [1, 5], GENERIC + ["WilliamBlair"]) + gh("williamblair"),
    "pipersandler": wd("pipersandler", [1, 5], GENERIC + ["PiperSandler", "Piper_Sandler"]),
    "houlihanlokey": wd("hl", [1], ["Campus", "Experienced", "External"]) + wd("houlihanlokey", [1, 5], GENERIC),
    "stephens": wd("stephens", [1, 5], GENERIC + ["Stephens"]),
    "moelis": wd("moelis", [1, 5], GENERIC + ["Moelis"]) + gh("moelis"),
    "evercore": wd("evercore", [1, 5], GENERIC) + gh("evercore"),
    "lazard": wd("lazard", [1, 5], GENERIC) + gh("lazard"),
    "guggenheim": wd("guggenheimpartners", [1, 5], GENERIC + ["GP", "Guggenheim"]) + gh("guggenheimpartners"),
    "pjt": gh("pjtpartners", "pjt") + wd("pjtpartners", [1, 5], GENERIC),
    "perellaweinberg": gh("pwp", "perellaweinberg", "pwpartners"),
    "centerview": gh("centerview", "centerviewpartners"),
    "lincolninternational": wd("lincolninternational", [1, 5], GENERIC) + gh("lincolninternational"),
    "harriswilliams": gh("harriswilliams") + wd("harriswilliams", [1, 5], GENERIC),
    "cantor": wd("cantor", [1, 5], GENERIC) + gh("cantorfitzgerald"),
    "oppenheimer": wd("opco", [1, 5], GENERIC) + wd("oppenheimer", [1, 5], GENERIC),
    # Asset managers and private equity
    "blackrock": wd("blackrock", [1], ["BlackRock_Professional"]),
    "blackstone": wd("blackstone", [1], ["Blackstone_Careers", "Blackstone_Campus_Careers"]),
    "kkr": wd("kkr", [1, 5], GENERIC + ["KKR", "KKR_Careers"]) + gh("kkr"),
    "carlyle": wd("carlyle", [1, 5], GENERIC + ["Carlyle"]) + gh("carlyle"),
    "apollo": wd("apollo", [1, 5], GENERIC + ["Apollo"]) + gh("apollo", "apolloglobal"),
    "ares": wd("aresmgmt", [1], ["External"]),
    "troweprice": wd("troweprice", [5], ["TRowePrice"]),
    "northerntrust": wd("ntrs", [1], ["northerntrust"]),
    "statestreet": wd("statestreet", [1], ["Global"]),
    "invesco": wd("invesco", [1], ["IVZ"]),
    "franklintempleton": wd("franklintempleton", [5], ["Primary-External-1"]),
    "pimco": wd("pimco", [1], ["pimco-careers"]),
    "vanguard": wd("vanguard", [5], ["vanguard_external"]),
    "wellington": wd("wellington", [5, 1], GENERIC + ["Wellington"]) + gh("wellington"),
    "nuveen": wd("tiaa", [1], ["Search"]),
    "point72": gh("point72"),
    "aqr": gh("aqr"),
    "bridgewater": gh("bridgewater89", "bridgewater"),
    "generalatlantic": gh("generalatlantic"),
    "citadel": gh("citadel", "citadelsecurities"),
    "drw": gh("drweng", "drw"),
    "jumptrading": gh("jumptrading"),
    "virtu": gh("virtu"),
    "tworivers": gh("twosigma"),
}


def get_json(url, body=None):
    headers = dict(HEADERS)
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code}: {exc.read()[:160]!r}") from None


def probe(ats, target):
    """Return (count, sample title)."""
    if ats == "greenhouse":
        jobs = get_json(f"https://boards-api.greenhouse.io/v1/boards/{target}/jobs").get("jobs", [])
        return len(jobs), jobs[0]["title"] if jobs else ""
    if ats == "smartrecruiters":
        d = get_json(f"https://api.smartrecruiters.com/v1/companies/{target}/postings?limit=1")
        c = d.get("content", [])
        return d.get("totalFound"), c[0]["name"] if c else ""
    if ats == "workday":
        host, tenant, site = target.split("|")
        d = get_json(f"https://{host}/wday/cxs/{tenant}/{site}/jobs",
                     {"appliedFacets": {}, "limit": 1, "offset": 0, "searchText": ""})
        p = d.get("jobPostings", [])
        return d.get("total"), p[0].get("title", "") if p else ""
    if ats == "oracle":
        host, site = target.split("|")
        d = get_json(f"https://{host}/hcmRestApi/resources/latest/recruitingCEJobRequisitions?onlyData=true"
                     f"&expand=requisitionList&finder=findReqs;siteNumber={site},limit=2,offset=0")
        item = (d.get("items") or [{}])[0]
        reqs = item.get("requisitionList") or []
        sample = json.dumps(reqs[0])[:400] if reqs else ""
        return item.get("TotalJobsCount"), sample
    if ats == "goldman":
        d = get_json("https://api-higher.gs.com/gateway/api/v1/graphql", {
            "operationName": "GetRoles", "query": GS_QUERY,
            "variables": {"searchQueryInput": {
                "page": {"pageSize": 2, "pageNumber": 0},
                "sort": {"sortStrategy": "RELEVANCE", "sortOrder": "DESC"},
                "filters": [], "experiences": ["PROFESSIONAL", "EARLY_CAREER"], "searchTerm": "",
            }},
        })
        if d.get("errors"):
            raise RuntimeError(json.dumps(d["errors"])[:300])
        rs = d["data"]["roleSearch"]
        return rs["totalCount"], json.dumps(rs["items"][0])[:400] if rs["items"] else ""
    raise ValueError(ats)


def probe_candidate(item):
    name, variants = item
    errors = []
    for ats, target in variants:
        try:
            count, sample = probe(ats, target)
            if count:
                return {"name": name, "ok": True, "ats": ats, "target": target, "count": count, "sample": sample}
            errors.append(f"{ats}:{target} -> empty")
        except Exception as exc:
            errors.append(f"{ats}:{target} -> {str(exc)[:120]}")
    return {"name": name, "ok": False, "ats": None, "target": None, "count": 0, "errors": errors[:6]}


def main():
    with ThreadPoolExecutor(max_workers=12) as pool:
        results = list(pool.map(probe_candidate, CANDIDATES.items()))
    for r in results:
        print(f"{'OK  ' if r['ok'] else 'FAIL'} {r['name']:22} {r['ats'] or '':16} {r['count']}  {r['target'] or ''}")
    Path("tools/probe_results.json").write_text(json.dumps(results, indent=2) + "\n")


if __name__ == "__main__":
    main()
