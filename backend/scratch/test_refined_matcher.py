import re
import difflib
from datetime import datetime, timezone, timedelta

def normalize_title(title: str) -> str:
    t = title.lower()
    t = re.sub(r'\(.*?\)', '', t)
    t = re.sub(r'\b(m/m|y/y|q/q|mom|yoy|qoq|flash|prelim|final)\b', '', t)
    t = re.sub(r'[^a-z0-9\s]', ' ', t)
    return " ".join(t.split())

def match_score(ff_title: str, tv_title: str) -> float:
    # Exclude speeches/statements from numeric matching
    ff_lower = ff_title.lower()
    tv_lower = tv_title.lower()
    
    non_numeric_kw = ["speaks", "statement", "press conference", "meeting minutes"]
    if any(k in ff_lower for k in non_numeric_kw):
        return 0.0

    # Period frequency consistency check
    ff_has_mom = any(k in ff_lower for k in ["m/m", "mom", "month"])
    ff_has_yoy = any(k in ff_lower for k in ["y/y", "yoy", "year"])
    ff_has_qoq = any(k in ff_lower for k in ["q/q", "qoq", "quarter"])

    tv_has_mom = any(k in tv_lower for k in ["mom", "month"])
    tv_has_yoy = any(k in tv_lower for k in ["yoy", "year"])
    tv_has_qoq = any(k in tv_lower for k in ["qoq", "quarter"])

    # If both specify different frequencies, penalize heavily
    if (ff_has_mom and tv_has_yoy) or (ff_has_yoy and tv_has_mom):
        return 0.0
    if (ff_has_qoq and (tv_has_mom or tv_has_yoy)) or ((ff_has_mom or ff_has_yoy) and tv_has_qoq):
        return 0.0

    n1 = normalize_title(ff_title)
    n2 = normalize_title(tv_title)
    if n1 == n2:
        return 1.0
    if n1 in n2 or n2 in n1:
        return 0.95

    s1 = set(n1.split())
    s2 = set(n2.split())
    if not s1 or not s2:
        return 0.0
    overlap = len(s1.intersection(s2)) / min(len(s1), len(s2))
    diff = difflib.SequenceMatcher(None, n1, n2).ratio()
    return max(overlap, diff)

# Test
print("CB Consumer Confidence match:", match_score("CB Consumer Confidence", "CB Consumer Confidence"))
print("Cash Rate match:", match_score("Cash Rate", "RBA Interest Rate Decision"))
print("RBA Rate Statement match (should be 0):", match_score("RBA Rate Statement", "RBA Interest Rate Decision"))
print("Household Spending m/m vs YoY (should be 0):", match_score("Household Spending m/m", "Household Spending YoY"))
print("JOLTS Job Openings match:", match_score("JOLTS Job Openings", "JOLTs Job Openings"))
print("Core PCE Price Index m/m match:", match_score("Core PCE Price Index m/m", "Core PCE Price Index MoM"))
