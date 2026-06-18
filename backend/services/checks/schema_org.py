import json
import re

import httpx
from bs4 import BeautifulSoup

from backend.schemas.simulation import StandardsCheckResult

IMPORTANT_TYPES = {
    "Organization": 15,
    "Person": 15,
    "Product": 15,
    "Offer": 15,
    "Article": 10,
    "BlogPosting": 10,
    "FAQPage": 10,
    "HowTo": 10,
    "BreadcrumbList": 10,
    "Review": 10,
    "AggregateRating": 10,
    "LocalBusiness": 10,
}


def _extract_types(obj, found: set, depth: int = 0) -> int:
    """Recursively extract @type values and return max nesting depth."""
    max_depth = depth
    if isinstance(obj, dict):
        t = obj.get("@type")
        if t:
            if isinstance(t, list):
                found.update(t)
            else:
                found.add(t)
        for v in obj.values():
            d = _extract_types(v, found, depth + 1)
            max_depth = max(max_depth, d)
    elif isinstance(obj, list):
        for item in obj:
            d = _extract_types(item, found, depth)
            max_depth = max(max_depth, d)
    return max_depth


async def check_schema_org(base_url: str) -> StandardsCheckResult:
    """
    Scoring (weight 25%):
      No JSON-LD                → 0
      JSON-LD present           → 20
      + Organization/Person     → +15
      + Product/Offer           → +15
      + Article/BlogPosting     → +10
      + FAQPage/HowTo           → +10
      + BreadcrumbList          → +10
      + nesting depth >= 3      → +10
      + multiple types          → +10
      Cap at 100
    """
    issues = []
    details = {}

    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            resp = await client.get(base_url)
    except Exception as e:
        return StandardsCheckResult(
            check_name="schema_org", score=0,
            details={"error": str(e)},
            issues=["Could not fetch page to check JSON-LD"],
        )

    soup = BeautifulSoup(resp.text, "lxml")
    ld_scripts = soup.find_all("script", {"type": "application/ld+json"})

    if not ld_scripts:
        return StandardsCheckResult(
            check_name="schema_org", score=0,
            details={"json_ld_count": 0},
            issues=["No JSON-LD structured data found on homepage"],
        )

    found_types: set[str] = set()
    max_depth = 0
    parse_errors = 0

    for script in ld_scripts:
        try:
            data = json.loads(script.string)
            d = _extract_types(data, found_types)
            max_depth = max(max_depth, d)
        except (json.JSONDecodeError, TypeError):
            parse_errors += 1

    details["json_ld_count"] = len(ld_scripts)
    details["types_found"] = sorted(found_types)
    details["max_nesting_depth"] = max_depth
    details["parse_errors"] = parse_errors

    if not found_types:
        return StandardsCheckResult(
            check_name="schema_org", score=20,
            details=details,
            issues=["JSON-LD present but no @type detected"],
        )

    score = 20  # JSON-LD present

    # Check for important types
    has_org_person = bool(found_types & {"Organization", "Person"})
    has_product_offer = bool(found_types & {"Product", "Offer"})
    has_article = bool(found_types & {"Article", "BlogPosting", "NewsArticle"})
    has_faq_howto = bool(found_types & {"FAQPage", "HowTo"})
    has_breadcrumb = "BreadcrumbList" in found_types

    if has_org_person:
        score += 15
    else:
        issues.append("No Organization or Person schema found")

    if has_product_offer:
        score += 15

    if has_article:
        score += 10

    if has_faq_howto:
        score += 10

    if has_breadcrumb:
        score += 10

    if max_depth >= 3:
        score += 10

    if len(found_types) >= 3:
        score += 10
    elif len(found_types) < 2:
        issues.append("Only one schema type found — limited structured data")

    return StandardsCheckResult(
        check_name="schema_org",
        score=min(score, 100),
        details=details,
        issues=issues,
    )
