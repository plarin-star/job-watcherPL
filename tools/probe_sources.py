"""Probe candidate job boards and report which ones return JSON with no login.

Used while choosing the watch list. Writes tools/probe_results.json with, for each
candidate that answered, its applicant tracking system, the exact target to use,
and how many postings the board reports. Candidates that never answered are
listed under "failed".

Run: python tools/probe_sources.py
"""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import json
import re
import urllib.request

HEADERS = {"User-Agent": "job-watcher-student-project/1.0", "Accept": "application/json"}
WD_NUMBERS = [1, 5, 3, 12, 2, 10, 101, 103, 108, 501, 503]

GREENHOUSE = [
    "point72", "bridgewater89", "aqr", "generalatlantic", "blueowl", "moelis", "lincolninternational",
    "pjtpartners", "perellaweinberg", "guggenheimpartners", "williamblair", "hamiltonlane",
    "stepstonegroup", "apollo", "carlyle", "janestreet", "twosigma", "hudsonrivertrading", "drweng",
    "jumptrading", "imc", "optiver", "akunacapital", "virtu", "clearstreet", "schonfeld", "balyasny",
    "lazard", "evercore", "houlihanlokey", "jefferies", "stephens", "raymondjames", "pipersandler",
    "oppenheimer", "stifel", "citadel", "towerresearchcapital", "sig", "mangroup", "warburgpincusllc",
    "tpg", "bain", "baincapital", "silverlake", "thomabravo", "vistaequitypartners", "ares",
    "oaktree", "golubcapital", "antares", "cantorfitzgerald", "stonex", "marketaxess", "tradeweb",
    "morningstar", "pitchbook", "addepar", "carta", "robinhood", "coinbase", "sofi", "betterment",
    "wealthfront", "galaxydigitalservices", "bitgo", "fidelity", "dvtrading", "oldmissioncapital",
    "wolverinetrading", "chathamfinancial", "harriswilliams", "centerview", "greenhill", "cowen",
]
LEVER = ["wealthfront", "moelis", "lincolninternational", "point72", "blueowl", "hamiltonlane",
         "stepstone", "generalatlantic", "addepar", "arcesium", "belvederetrading", "gtsx", "clearstreet"]
ASHBY = ["ramp", "kraken.com", "plaid", "clearstreet", "addepar", "carta", "mercury", "brex", "arcesium"]
SMARTRECRUITERS = ["Deloitte6", "Deloitte", "Deloitte2", "DeloitteUS", "KPMG", "KPMGUS", "EY", "PwC",
                   "Jefferies", "Evercore", "Lazard", "Nomura", "Macquarie", "UBS", "Barclays",
                   "SocieteGenerale", "BNPParibas", "CreditAgricole", "Natixis", "RothschildCo",
                   "Visa", "Experian", "Equifax", "SPGlobal", "MoodysCorporation", "Mizuho", "Allianz"]
# Workday: tenant -> career site names to try (the site at the board's root is also tried)
WORKDAY = {
    "ms": ["External"], "citi": ["2"], "wf": ["WellsFargoJobs"], "blackrock": ["BlackRock_Professional"],
    "blackstone": ["Blackstone_Careers"], "kkr": ["KKR_Careers", "KKR"], "raymondjames": ["RaymondJamesCareers"],
    "jefferies": ["jefferies", "Jefferies"], "hl": ["HL", "Experienced", "Campus"], "lazard": ["Lazard"],
    "pjtpartners": ["PJT", "Careers"], "stifel": ["Stifel", "Search"], "rwbaird": ["Baird", "BairdCareers"],
    "stephens": ["Stephens"], "troweprice": ["TRowePrice"], "ntrs": ["northerntrust"],
    "statestreet": ["Global"], "invesco": ["IVZ"], "franklintempleton": ["Primary-External-1"],
    "pimco": ["pimco-careers"], "vanguard": ["vanguard_external"], "aresmgmt": ["External"],
    "mlp": ["mlpcareers"], "nb": ["NBCareers"], "tiaa": ["Search"], "wellington": ["Wellington"],
    "db": ["DBWebsite"], "rbc": ["RBCGLOBAL1"], "bmo": ["External"], "td": ["TD_Bank_Careers"],
    "mq": ["CareersatMQ"], "pwc": ["Global_Experienced_Careers"], "carlyle": ["Carlyle"], "tpg": ["TPG"],
    "oaktree": ["Oaktree"], "brookfield": ["brookfield"], "apollo": ["Apollo"], "williamblair": ["WilliamBlair"],
    "pipersandler": ["PiperSandler"], "guggenheim": ["Guggenheim"], "evercore": ["Evercore"],
    "moelis": ["Moelis"], "pnc": ["External"], "truist": ["Careers"], "usbank": ["US_Bank_Careers"],
    "abglobal": ["alliancebernsteincareers"], "lordabbett": ["LordAbbett"], "janushenderson": ["Careers"],
    "nomura": ["Nomura"], "mizuho": ["Mizuho"], "mufgub": ["MUFG-Careers"], "cibc": ["search"],
    "keybank": ["External_Career_Site"], "fifththird": ["53careers"], "citizensbank": ["Citizens"],
    "cantor": ["Cantor"], "stonex": ["StoneX"], "lpl": ["External"], "ameriprise": ["Ameriprise"],
    "principal": ["Principal"], "nuveen": ["Nuveen"], "deloitte": ["Deloitte"], "kpmg": ["KPMG"],
    "barclays": ["External_Career_Site_Barclays"], "ubs": ["UBS"], "hsbc": ["HSBC"],
    "santander": ["SantanderCareers"], "bbh": ["BBH"], "bnymellon": ["BNY"], "bny": ["BNY"],
    "goldmansachs": ["GS"], "jpmc": ["JPMC"], "msci": ["MSCI"], "spgi": ["SPGI_Careers"],
    "moodys": ["Moodys"], "factset": ["FactSetCareers"], "nasdaq": ["Global_External_Site"],
    "cmegroup": ["cme_careers"], "ice": ["ICE"], "schwab": ["External"], "voya": ["VoyaCareers"],
    "manulife": ["MFCJH_Jobs"], "sunlife": ["Experienced-Jobs"], "macquarie": ["CareersatMQ"],
    "lincolninternational": ["Lincoln"], "harriswilliams": ["HW"], "houlihanlokey": ["HL"],
    "generalatlantic": ["GA"], "warburgpincus": ["WP"], "baincapital": ["External_Public"],
    "hamiltonlane": ["HL"], "stepstonegroup": ["StepStone"], "blueowl": ["BlueOwl"],
    "regions": ["Regions_Careers"], "huntington": ["HNBcareers"], "mtb": ["MTB"], "firstcitizens": ["FCB"],
    "synchronyfinancial": ["careers"], "discover": ["Discover"], "aexp": ["AEXP"], "usaa": ["USAAJOBSWD"],
}
ORACLE = {  # host -> site numbers to try
    "jpmc.fa.oraclecloud.com": ["CX_1001", "CX_1002"],
    "eofd.fa.us6.oraclecloud.com": ["CX_1001"],
    "hdpc.fa.us2.oraclecloud.com": ["CX_1", "CX_1001"],
    "fa-evmr-saasfaprod1.fa.ocs.oraclecloud.com": ["CX_1", "CX_1001"],
}


def request(url, body=None, extra=None):
    headers = dict(HEADERS)
    headers.update(extra or {})
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers)
    return urllib.request.urlopen(req, timeout=20)


def get_json(url, body=None):
    with request(url, body) as resp:
        return json.loads(resp.read().decode("utf-8"))


def try_count(fn):
    try:
        return fn(), None
    except Exception as exc:
        return None, repr(exc)[:120]


def probe_simple(ats, target):
    if ats == "greenhouse":
        fn = lambda: len(get_json(f"https://boards-api.greenhouse.io/v1/boards/{target}/jobs")["jobs"])
    elif ats == "lever":
        fn = lambda: len(get_json(f"https://api.lever.co/v0/postings/{target}?mode=json"))
    elif ats == "ashby":
        fn = lambda: len(get_json(f"https://api.ashbyhq.com/posting-api/job-board/{target}")["jobs"])
    else:
        fn = lambda: get_json(f"https://api.smartrecruiters.com/v1/companies/{target}/postings?limit=1")["totalFound"]
    count, error = try_count(fn)
    return {"ats": ats, "target": target, "count": count or 0, "error": error}


def workday_count(host, tenant, site):
    d = get_json(f"https://{host}/wday/cxs/{tenant}/{site}/jobs",
                 {"appliedFacets": {}, "limit": 1, "offset": 0, "searchText": ""})
    return d.get("total") or 0


def probe_workday(tenant, sites):
    best = {"ats": "workday", "target": tenant, "count": 0, "error": "no working host/site"}
    for n in WD_NUMBERS:
        host = f"{tenant}.wd{n}.myworkdayjobs.com"
        candidates = list(sites)
        try:  # the board's root usually redirects to its default career site
            with request(f"https://{host}/", extra={"Accept": "text/html"}) as resp:
                m = re.search(r"myworkdayjobs\.com/(?:[a-z]{2}-[A-Z]{2}/)?([^/?#]+)", resp.geturl())
                if m and m.group(1) not in candidates:
                    candidates.insert(0, m.group(1))
        except Exception as exc:
            if "HTTP Error" not in repr(exc) and "HTTPError" not in repr(exc):
                continue  # host does not exist on this data center
        for site in candidates:
            count, error = try_count(lambda: workday_count(host, tenant, site))
            if count:
                return {"ats": "workday", "target": f"{host}|{tenant}|{site}", "count": count, "error": None}
            best["error"] = f"{host}/{site}: {error}"
    return best


def probe_oracle(host, sites):
    for site in sites:
        url = (f"https://{host}/hcmRestApi/resources/latest/recruitingCEJobRequisitions?onlyData=true"
               f"&expand=requisitionList&finder=findReqs;siteNumber={site},limit=1,offset=0")
        count, error = try_count(lambda: get_json(url)["items"][0]["TotalJobsCount"])
        if count:
            return {"ats": "oracle", "target": f"{host}|{site}", "count": count, "error": None}
    return {"ats": "oracle", "target": host, "count": 0, "error": error}


def probe_goldman():
    query = ("query GetRoles($searchQueryInput: RoleSearchQueryInput!) { roleSearch(searchQueryInput: "
             "$searchQueryInput) { totalCount items { roleId jobTitle corporateTitle division "
             "locations { city state country } externalSource { sourceId } } } }")
    body = {"operationName": "GetRoles", "query": query, "variables": {"searchQueryInput": {
        "page": {"pageSize": 5, "pageNumber": 0}, "sort": {"sortStrategy": "POSTED_DATE", "sortOrder": "DESC"},
        "filters": [], "experiences": ["PROFESSIONAL", "EARLY_CAREER"], "searchTerm": ""}}}
    def fn():
        d = get_json("https://api-higher.gs.com/gateway/api/v1/graphql", body)
        return d["data"]["roleSearch"]["totalCount"]
    count, error = try_count(fn)
    return {"ats": "goldman-graphql", "target": "api-higher.gs.com", "count": count or 0, "error": error}


def main():
    jobs = [lambda t=t: probe_simple("greenhouse", t) for t in GREENHOUSE]
    jobs += [lambda t=t: probe_simple("lever", t) for t in LEVER]
    jobs += [lambda t=t: probe_simple("ashby", t) for t in ASHBY]
    jobs += [lambda t=t: probe_simple("smartrecruiters", t) for t in SMARTRECRUITERS]
    jobs += [lambda t=t, s=s: probe_workday(t, s) for t, s in WORKDAY.items()]
    jobs += [lambda h=h, s=s: probe_oracle(h, s) for h, s in ORACLE.items()]
    jobs.append(probe_goldman)
    with ThreadPoolExecutor(max_workers=16) as pool:
        results = list(pool.map(lambda job: job(), jobs))
    ok = sorted((r for r in results if r["count"]), key=lambda r: (r["ats"], r["target"]))
    failed = sorted((r for r in results if not r["count"]), key=lambda r: (r["ats"], r["target"]))
    for r in ok:
        print(f"OK   {r['ats']:16} {r['count']:6}  {r['target']}")
    print(f"{len(ok)} worked, {len(failed)} failed")
    Path("tools/probe_results.json").write_text(json.dumps({"ok": ok, "failed": failed}, indent=1) + "\n")


if __name__ == "__main__":
    main()
