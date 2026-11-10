import pytest

from watcher.title_rule import in_role


@pytest.mark.parametrize("title", [
    "Investment Banking Analyst",
    "KippsDeSanto - Investment Banking Analyst",
    "TripleTree - Investment Banking Associate",
    "Equity Research Associate",
    "Analyst/ Associate: Equity Research, Metals & Mining",
    "Associate Analyst, Capital Markets & Analytics",
    "Fixed Income Research Analyst, Structured Products",
    "Portfolio Analyst",
    "INVESTMENT ANALYST",
])
def test_titles_in_role(title):
    assert in_role(title)


@pytest.mark.parametrize("title", [
    "Software Engineer",
    "Data Analyst",
    "Senior Associate, Capital Markets & Risk Analyst",     # seniority
    "Sr. Analyst, Capital Markets & Risk",                  # seniority
    "Principal Financial Analyst, International Markets",   # seniority
    "Associate/ Vice President: Credit Research",           # seniority
    "Analyst, Specialty Underwriter and Portfolio Manager", # seniority
    "Alternative Investments Sales Strategy Analyst",       # sales
    "Investment Advisor Associate",                         # advisor
    "Insurance Investment Analyst",                         # insurance
    "Compliance Analyst, Trading",                          # compliance
    "GFC Investigations Analyst",                           # "investigations" is not "investment"
    "Investment Banking Intern",                            # no role word
    "",
    None,
])
def test_titles_not_in_role(title):
    assert not in_role(title)
