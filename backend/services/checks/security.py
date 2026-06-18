import httpx

from backend.schemas.simulation import StandardsCheckResult


async def check_security(base_url: str) -> StandardsCheckResult:
    """
    Scoring (weight 10%):
      HTTP only (no redirect)    → 0
      HTTPS available            → 50
      + HTTP→HTTPS redirect      → +20
      + HSTS header              → +15
      + X-Content-Type-Options   → +5
      + CSP header               → +10
      Cap at 100
    """
    issues = []
    details = {}

    # Ensure we're testing the base domain
    clean_url = base_url.rstrip("/")
    http_url = clean_url.replace("https://", "http://")
    https_url = clean_url.replace("http://", "https://")

    score = 0

    async with httpx.AsyncClient(timeout=10) as client:
        # Check HTTPS
        try:
            https_resp = await client.get(https_url, follow_redirects=True)
            details["https_status"] = https_resp.status_code
            if https_resp.status_code < 400:
                score = 50
                details["https_available"] = True
            else:
                details["https_available"] = False
                issues.append("HTTPS not available or returns error")
        except Exception as e:
            details["https_available"] = False
            details["https_error"] = str(e)
            issues.append(f"HTTPS connection failed: {e}")
            return StandardsCheckResult(
                check_name="security", score=0,
                details=details, issues=issues,
            )

        # Check HTTP→HTTPS redirect
        try:
            http_resp = await client.get(http_url, follow_redirects=False)
            redirects_to_https = (
                http_resp.status_code in (301, 302, 307, 308)
                and "https" in http_resp.headers.get("location", "").lower()
            )
            details["http_redirects_to_https"] = redirects_to_https
            if redirects_to_https:
                score += 20
            else:
                issues.append("HTTP does not redirect to HTTPS")
        except Exception:
            details["http_redirects_to_https"] = False

        # Check security headers from HTTPS response
        headers = https_resp.headers

        has_hsts = "strict-transport-security" in headers
        details["has_hsts"] = has_hsts
        if has_hsts:
            score += 15
        else:
            issues.append("Missing Strict-Transport-Security (HSTS) header")

        has_xcto = headers.get("x-content-type-options", "").lower() == "nosniff"
        details["has_x_content_type_options"] = has_xcto
        if has_xcto:
            score += 5

        has_csp = "content-security-policy" in headers
        details["has_csp"] = has_csp
        if has_csp:
            score += 10
        else:
            issues.append("Missing Content-Security-Policy header")

    return StandardsCheckResult(
        check_name="security",
        score=min(score, 100),
        details=details,
        issues=issues,
    )
