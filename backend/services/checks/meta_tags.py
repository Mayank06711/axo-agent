import httpx
from bs4 import BeautifulSoup

from backend.schemas.simulation import StandardsCheckResult

EXPECTED_TAGS = [
    "title",
    "meta_description",
    "og:title",
    "og:description",
    "og:image",
    "og:type",
    "og:url",
    "twitter:card",
]


async def check_meta_tags(base_url: str) -> StandardsCheckResult:
    """
    Scoring (weight 15%):
      score = (found_tags / 8) × 100
    """
    issues = []
    details = {}

    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            resp = await client.get(base_url)
    except Exception as e:
        return StandardsCheckResult(
            check_name="meta_tags", score=0,
            details={"error": str(e)},
            issues=["Could not fetch page to check meta tags"],
        )

    soup = BeautifulSoup(resp.text, "lxml")
    found = {}

    # Title tag
    title_tag = soup.find("title")
    found["title"] = bool(title_tag and title_tag.string and title_tag.string.strip())

    # Meta description
    desc = soup.find("meta", attrs={"name": "description"})
    found["meta_description"] = bool(desc and desc.get("content", "").strip())

    # Open Graph tags
    for og in ["og:title", "og:description", "og:image", "og:type", "og:url"]:
        tag = soup.find("meta", attrs={"property": og})
        found[og] = bool(tag and tag.get("content", "").strip())

    # Twitter card
    twitter = soup.find("meta", attrs={"name": "twitter:card"})
    found["twitter:card"] = bool(twitter and twitter.get("content", "").strip())

    found_count = sum(1 for v in found.values() if v)
    score = round((found_count / len(EXPECTED_TAGS)) * 100)

    details["tags"] = found
    details["found_count"] = found_count
    details["total_expected"] = len(EXPECTED_TAGS)

    missing = [tag for tag, present in found.items() if not present]
    if missing:
        issues.append(f"Missing meta tags: {', '.join(missing)}")

    return StandardsCheckResult(
        check_name="meta_tags",
        score=min(score, 100),
        details=details,
        issues=issues,
    )
