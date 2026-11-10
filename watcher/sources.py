"""The watch list: every employer job board the pipeline reads, with its applicant tracking system.

Each board returns JSON to a request made with no login. None returns more than
5,000 postings, so no board is requested with a search term.
"""


def _gh(name, employer, slug=None):
    return {"name": name, "employer": employer, "ats": "greenhouse", "slug": slug or name}


def _lever(name, employer, slug=None):
    return {"name": name, "employer": employer, "ats": "lever", "slug": slug or name}


def _ashby(name, employer, slug=None):
    return {"name": name, "employer": employer, "ats": "ashby", "slug": slug or name}


def _sr(name, employer, company_id):
    return {"name": name, "employer": employer, "ats": "smartrecruiters", "company_id": company_id}


def _wd(name, employer, host, tenant, site):
    return {"name": name, "employer": employer, "ats": "workday", "host": host, "tenant": tenant, "site": site}


SOURCES = [
    # Greenhouse
    _gh("stripe", "Stripe"),
    _gh("robinhood", "Robinhood"),
    _gh("affirm", "Affirm"),
    _gh("coinbase", "Coinbase"),
    _gh("brex", "Brex"),
    _gh("sofi", "SoFi"),
    _gh("chime", "Chime"),
    _gh("toast", "Toast"),
    _gh("carta", "Carta"),
    _gh("betterment", "Betterment"),
    # Lever
    _lever("palantir", "Palantir"),
    _lever("spotify", "Spotify"),
    _lever("wealthfront", "Wealthfront"),
    # Ashby
    _ashby("ramp", "Ramp"),
    _ashby("notion", "Notion"),
    _ashby("plaid", "Plaid"),
    _ashby("kraken", "Kraken", "kraken.com"),
    # SmartRecruiters
    _sr("servicenow", "ServiceNow", "ServiceNow"),
    # Workday
    _wd("capitalone", "Capital One", "capitalone.wd12.myworkdayjobs.com", "capitalone", "Capital_One"),
    _wd("mastercard", "Mastercard", "mastercard.wd1.myworkdayjobs.com", "mastercard", "CorporateCareers"),
    _wd("fidelity", "Fidelity Investments", "fmr.wd1.myworkdayjobs.com", "fmr", "FidelityCareers"),
    _wd("bankofamerica", "Bank of America", "ghr.wd1.myworkdayjobs.com", "ghr", "Lateral-US"),
    _wd("salesforce", "Salesforce", "salesforce.wd12.myworkdayjobs.com", "salesforce", "External_Career_Site"),
    _wd("tyson", "Tyson Foods", "tysonfoods.wd5.myworkdayjobs.com", "tysonfoods", "TSN"),
]

SOURCES_BY_NAME = {s["name"]: s for s in SOURCES}
