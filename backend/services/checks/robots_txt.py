import httpx

from backend.schemas.simulation import StandardsCheckResult

AI_BOT_AGENTS = [
    "GPTBot", "ChatGPT-User", "OAI-SearchBot",
    "ClaudeBot", "Claude-User", "Claude-SearchBot",
    "Google-Extended", "PerplexityBot", "Bytespider",
    "CCBot", "Amazonbot", "Applebot-Extended",
]


async def check_robots_txt(base_url: str) -> StandardsCheckResult:
    """
    Scoring (weight 25%):
      Not found              → 30 (not blocking, but no guidance)
      Found, blocks all (/)  → 0
      Found, blocks AI bots  → 20
      Found, allows AI bots  → 60
      + has Sitemap directive → +20
      + has AI-specific rules → +20
      Cap at 100
    """
    url = f"{base_url.rstrip('/')}/robots.txt"
    issues = []
    details = {"url": url}

    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            resp = await client.get(url)
    except Exception as e:
        return StandardsCheckResult(
            check_name="robots_txt", score=30,
            details={"error": str(e)},
            issues=["Could not fetch robots.txt"],
        )

    if resp.status_code != 200:
        return StandardsCheckResult(
            check_name="robots_txt", score=30,
            details={"status_code": resp.status_code},
            issues=["robots.txt not found or inaccessible"],
        )

    content = resp.text.lower()
    lines = content.splitlines()
    details["length"] = len(content)

    # Check for global block
    global_block = False
    current_agent = None
    for line in lines:
        line = line.strip()
        if line.startswith("user-agent:"):
            current_agent = line.split(":", 1)[1].strip()
        elif line.startswith("disallow:") and current_agent == "*":
            path = line.split(":", 1)[1].strip()
            if path == "/":
                global_block = True

    if global_block:
        details["global_block"] = True
        return StandardsCheckResult(
            check_name="robots_txt", score=0,
            details=details,
            issues=["robots.txt globally blocks all crawlers (Disallow: /)"],
        )

    # Check AI bot mentions
    ai_bots_mentioned = []
    ai_bots_blocked = []
    for bot in AI_BOT_AGENTS:
        bot_lower = bot.lower()
        if bot_lower in content:
            ai_bots_mentioned.append(bot)
            # Check if this bot is blocked
            in_bot_section = False
            for line in lines:
                line = line.strip()
                if line.startswith("user-agent:") and bot_lower in line:
                    in_bot_section = True
                elif line.startswith("user-agent:"):
                    in_bot_section = False
                elif in_bot_section and line.startswith("disallow:"):
                    path = line.split(":", 1)[1].strip()
                    if path == "/":
                        ai_bots_blocked.append(bot)

    has_sitemap = "sitemap:" in content
    has_ai_rules = len(ai_bots_mentioned) > 0

    details["has_sitemap_directive"] = has_sitemap
    details["ai_bots_mentioned"] = ai_bots_mentioned
    details["ai_bots_blocked"] = ai_bots_blocked

    # Calculate score
    all_ai_blocked = len(ai_bots_blocked) == len(ai_bots_mentioned) and len(ai_bots_mentioned) > 0
    if all_ai_blocked:
        score = 20
        issues.append(f"All mentioned AI bots are blocked: {', '.join(ai_bots_blocked)}")
    else:
        score = 60
        if ai_bots_blocked:
            issues.append(f"Some AI bots blocked: {', '.join(ai_bots_blocked)}")

    if has_sitemap:
        score += 20
    else:
        issues.append("No Sitemap directive in robots.txt")

    if has_ai_rules:
        score += 20
    else:
        issues.append("No AI-specific user-agent rules in robots.txt")

    return StandardsCheckResult(
        check_name="robots_txt",
        score=min(score, 100),
        details=details,
        issues=issues,
    )
