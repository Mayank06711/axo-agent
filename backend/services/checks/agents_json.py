import json

import httpx

from backend.schemas.simulation import StandardsCheckResult


async def check_agents_json(base_url: str) -> StandardsCheckResult:
    """
    Scoring (weight 10%):
      Not found             → 0
      Found, invalid JSON   → 10
      Found, valid JSON     → 40
      + schema_version      → +15
      + api_spec_url        → +25
      + display_name + desc → +10
      + task_examples       → +10
      Cap at 100
    """
    url = f"{base_url.rstrip('/')}/.well-known/agents.json"
    issues = []
    details = {"url": url}

    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            resp = await client.get(url)
    except Exception as e:
        return StandardsCheckResult(
            check_name="agents_json", score=0,
            details={"error": str(e)},
            issues=["Could not fetch /.well-known/agents.json"],
        )

    if resp.status_code != 200:
        return StandardsCheckResult(
            check_name="agents_json", score=0,
            details={"status_code": resp.status_code},
            issues=["No agents.json found at /.well-known/agents.json"],
        )

    try:
        data = resp.json()
    except (json.JSONDecodeError, ValueError):
        return StandardsCheckResult(
            check_name="agents_json", score=10,
            details={"raw_length": len(resp.text)},
            issues=["agents.json exists but contains invalid JSON"],
        )

    details["keys"] = list(data.keys()) if isinstance(data, dict) else []
    score = 40  # Valid JSON found

    if isinstance(data, dict):
        if data.get("schema_version"):
            score += 15
            details["schema_version"] = data["schema_version"]

        if data.get("api_spec_url"):
            score += 25
            details["api_spec_url"] = data["api_spec_url"]
        else:
            issues.append("agents.json missing api_spec_url (most important field)")

        has_name = bool(data.get("display_name") or data.get("name"))
        has_desc = bool(data.get("description"))
        if has_name and has_desc:
            score += 10
        else:
            issues.append("agents.json missing display_name or description")

        if data.get("task_examples") and isinstance(data["task_examples"], list):
            score += 10
            details["task_examples_count"] = len(data["task_examples"])
    else:
        issues.append("agents.json root is not a JSON object")

    return StandardsCheckResult(
        check_name="agents_json",
        score=min(score, 100),
        details=details,
        issues=issues,
    )
