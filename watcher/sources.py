"""The watch list: every employer job board the pipeline reads, with its applicant tracking system.

Twenty-five employers for an investment / banking analyst search: big-name banks and firms,
middle-market and boutique investment banks, and asset managers.

Each board returns JSON to a request made with no login. JPMorgan Chase's board returns
more than 5,000 postings, so it is requested with the search term "analyst".
"""


def _gh(name, employer, slug=None):
    return {"name": name, "employer": employer, "ats": "greenhouse", "slug": slug or name}


def _lever(name, employer, slug=None):
    return {"name": name, "employer": employer, "ats": "lever", "slug": slug or name}


def _ashby(name, employer, slug=None):
    return {"name": name, "employer": employer, "ats": "ashby", "slug": slug or name}


def _sr(name, employer, company_id):
    return {"name": name, "employer": employer, "ats": "smartrecruiters", "company_id": company_id}


def _oracle(name, employer, host, site, search_term=""):
    return {"name": name, "employer": employer, "ats": "oracle", "host": host, "site": site,
            "search_term": search_term}


def _wd(name, employer, host, tenant, site):
    return {"name": name, "employer": employer, "ats": "workday", "host": host, "tenant": tenant, "site": site}


SOURCES = [
    # Big names
    {"name": "goldmansachs", "employer": "Goldman Sachs", "ats": "goldman"},
    _oracle("jpmorgan", "JPMorgan Chase", "jpmc.fa.oraclecloud.com", "CX_1001", search_term="analyst"),
    _wd("morganstanley", "Morgan Stanley", "ms.wd5.myworkdayjobs.com", "ms", "External"),
    _wd("bankofamerica", "Bank of America", "ghr.wd1.myworkdayjobs.com", "ghr", "Lateral-US"),
    _wd("wellsfargo", "Wells Fargo", "wf.wd1.myworkdayjobs.com", "wf", "WellsFargoJobs"),
    _wd("barclays", "Barclays", "barclays.wd3.myworkdayjobs.com", "barclays", "External_Career_Site_Barclays"),
    _wd("deutschebank", "Deutsche Bank", "db.wd3.myworkdayjobs.com", "db", "DBWebsite"),
    _sr("deloitte", "Deloitte", "Deloitte6"),
    # Middle-market and boutique investment banks
    _wd("raymondjames", "Raymond James", "raymondjames.wd1.myworkdayjobs.com", "raymondjames", "RaymondJamesCareers"),
    _wd("houlihanlokey", "Houlihan Lokey", "hl.wd1.myworkdayjobs.com", "hl", "Campus"),
    _wd("pjtpartners", "PJT Partners", "pjtpartners.wd1.myworkdayjobs.com", "pjtpartners", "Careers"),
    _gh("williamblair", "William Blair"),
    _gh("lincolninternational", "Lincoln International"),
    _wd("rbc", "RBC", "rbc.wd3.myworkdayjobs.com", "rbc", "RBCGLOBAL1"),
    _wd("bmo", "BMO", "bmo.wd3.myworkdayjobs.com", "bmo", "External"),
    # Asset managers and private equity
    _wd("blackrock", "BlackRock", "blackrock.wd1.myworkdayjobs.com", "blackrock", "BlackRock_Professional"),
    _wd("blackstone", "Blackstone", "blackstone.wd1.myworkdayjobs.com", "blackstone", "Blackstone_Careers"),
    _wd("fidelity", "Fidelity Investments", "fmr.wd1.myworkdayjobs.com", "fmr", "FidelityCareers"),
    _wd("troweprice", "T. Rowe Price", "troweprice.wd5.myworkdayjobs.com", "troweprice", "TRowePrice"),
    _wd("pimco", "PIMCO", "pimco.wd1.myworkdayjobs.com", "pimco", "pimco-careers"),
    _wd("carlyle", "Carlyle", "carlyle.wd1.myworkdayjobs.com", "carlyle", "Carlyle"),
    _gh("point72", "Point72"),
    _wd("ares", "Ares Management", "aresmgmt.wd1.myworkdayjobs.com", "aresmgmt", "External"),
    _wd("invesco", "Invesco", "invesco.wd1.myworkdayjobs.com", "invesco", "IVZ"),
    _wd("vanguard", "Vanguard", "vanguard.wd5.myworkdayjobs.com", "vanguard", "vanguard_external"),
]

SOURCES_BY_NAME = {s["name"]: s for s in SOURCES}
