"""The title rule: decides whether a posting is in my role.

My role is investment / banking analyst at entry and mid level.

A title is in the role when, matching whole words in the lower-cased title:

1. it has a role word:  "analyst" or "associate"; and
2. it has a field word: "investment(s)", "equity research", "credit research",
   "fixed income", "capital markets", "m&a", "mergers", "corporate development",
   "private equity", "valuation(s)", "portfolio" or "trading"; and
3. it has no seniority word: "senior", "sr", "principal", "lead", "manager",
   "director", "vice president", "vp", "head", "chief" or "managing"; and
4. it has no excluded word: "advisor", "adviser", "sales", "insurance",
   "compliance", "fraud", "crime(s)", "sanctions", "aml" or "kyc".

Examples in:  "Investment Banking Analyst", "Equity Research Associate",
              "Associate Analyst, Capital Markets & Analytics", "Portfolio Analyst".
Examples out: "Senior Associate, Capital Markets" (seniority),
              "Alternative Investments Sales Strategy Analyst" (sales),
              "GFC Investigations Analyst" (no field word), "Software Engineer".
"""

import re


def _words(*phrases):
    return re.compile(r"(?<![a-z])(?:" + "|".join(re.escape(p) for p in phrases) + r")(?![a-z])")


ROLE = _words("analyst", "associate")
FIELD = _words(
    "investment", "investments", "equity research", "credit research", "fixed income",
    "capital markets", "m&a", "mergers", "corporate development", "private equity",
    "valuation", "valuations", "portfolio", "trading",
)
SENIORITY = _words(
    "senior", "sr", "principal", "lead", "manager", "director", "vice president", "vp",
    "head", "chief", "managing",
)
EXCLUDE = _words(
    "advisor", "adviser", "sales", "insurance", "compliance", "fraud", "crime", "crimes",
    "sanctions", "aml", "kyc",
)


def in_role(title: str) -> bool:
    t = " ".join((title or "").lower().split())
    if SENIORITY.search(t) or EXCLUDE.search(t):
        return False
    return bool(ROLE.search(t) and FIELD.search(t))
