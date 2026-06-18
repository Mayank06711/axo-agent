import httpx

from backend.schemas.simulation import StandardsCheckResult


async def check_llms_txt(base_url: str) -> StandardsCheckResult:
    """
    Scoring (weight 15%):
      Not found              → 0
      Found but invalid/empty→ 20
      Found, valid markdown  → 50
      + has H1 heading       → +15
      + has H2 sections      → +20
      + has ## Optional       → +15
      Cap at 100
    """
    issues = []
    details = {}

    # Try multiple paths per spec
    paths = ["/llms.txt", "/llms-full.txt"]
    content = None
    found_path = None

    async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
        for path in paths:
            url = f"{base_url.rstrip('/')}{path}"
            try:
                resp = await client.get(url)
                if resp.status_code == 200 and len(resp.text.strip()) > 0:
                    content = resp.text
                    found_path = path
                    break
            except Exception:
                continue

    if content is None:
        return StandardsCheckResult(
            check_name="llms_txt", score=0,
            details={"searched": paths},
            issues=["No llms.txt or llms-full.txt found"],
        )

    details["path"] = found_path
    details["length"] = len(content)
    lines = content.splitlines()

    if len(content.strip()) < 10:
        return StandardsCheckResult(
            check_name="llms_txt", score=20,
            details=details,
            issues=["llms.txt exists but is empty or too short"],
        )

    score = 50  # Valid file found

    # Check for H1 heading (# Title)
    has_h1 = any(line.strip().startswith("# ") and not line.strip().startswith("## ") for line in lines)
    if has_h1:
        score += 15
        details["has_h1"] = True
    else:
        issues.append("llms.txt missing H1 heading (required by spec)")
        details["has_h1"] = False

    # Check for H2 sections (## Section)
    h2_sections = [line.strip() for line in lines if line.strip().startswith("## ")]
    details["h2_sections"] = [s.lstrip("# ").strip() for s in h2_sections]
    if h2_sections:
        score += 20
    else:
        issues.append("llms.txt has no H2 sections with link lists")

    # Check for ## Optional section
    has_optional = any("## optional" in line.lower() for line in lines)
    details["has_optional_section"] = has_optional
    if has_optional:
        score += 15

    # Check for links in markdown format [Title](URL)
    link_count = sum(1 for line in lines if "](http" in line)
    details["link_count"] = link_count
    if link_count == 0:
        issues.append("llms.txt has no markdown links")

    return StandardsCheckResult(
        check_name="llms_txt",
        score=min(score, 100),
        details=details,
        issues=issues,
    )
