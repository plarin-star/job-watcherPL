"""The title rule: decides whether a posting is in my role (financial analyst / FP&A).

A title is in the role when, after lower-casing it:

1. it contains none of the exclude words (financial-crime and compliance jobs), and
2. either
   a. it names FP&A or finance planning directly
      ("fp&a", "fp & a", "fpa", "financial planning", "strategic finance", "business finance"), or
   b. it has a role word ("analyst" or "associate") AND a field word
      ("financ", "treasury", "investment", "valuation", "corporate development", "capital markets").

Examples in:  "Financial Analyst", "Senior FP&A Analyst", "Associate, Strategic Finance",
              "Treasury Analyst", "Analyst, Corporate Finance".
Examples out: "Data Analyst", "Financial Crimes Analyst", "Software Engineer, Payments",
              "Accounting Manager".
"""

import re

DIRECT = ["fp&a", "fp & a", "financial planning", "strategic finance", "business finance"]
DIRECT_RE = re.compile(r"\bfpa\b")
ROLE_WORDS = ["analyst", "associate"]
FIELD_WORDS = ["financ", "treasury", "investment", "valuation", "corporate development", "capital markets"]
EXCLUDE = ["crime", "fraud", "sanction", "compliance"]
EXCLUDE_RE = re.compile(r"\b(aml|kyc)\b")


def in_role(title: str) -> bool:
    t = (title or "").lower()
    if any(word in t for word in EXCLUDE) or EXCLUDE_RE.search(t):
        return False
    if any(word in t for word in DIRECT) or DIRECT_RE.search(t):
        return True
    return any(w in t for w in ROLE_WORDS) and any(w in t for w in FIELD_WORDS)
