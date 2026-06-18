from langchain_core.tools import tool

from backend.services.fetcher.base import PageFetcher


def create_browser_tools(fetcher: PageFetcher) -> list:
    """Factory: creates LangChain tools that share the same browser page via closure."""

    @tool
    async def navigate_to(url: str) -> str:
        """Navigate the browser to a URL and return the visible text content of the page.
        Use this to visit any webpage. The URL must be a full URL starting with http."""
        await fetcher.goto(url)
        content = await fetcher.get_page_content()
        current = await fetcher.current_url()
        return f"[Navigated to {current}]\n\n{content}"

    @tool
    async def get_page_links() -> str:
        """Get all links on the current page. Returns a formatted list of links
        with their text and URLs. Use this to discover navigation options."""
        links = await fetcher.get_links()
        if not links:
            return "No links found on the current page."
        formatted = "\n".join(
            f"- [{l['text']}]({l['href']})" for l in links
        )
        return f"Found {len(links)} links:\n{formatted}"

    @tool
    async def read_current_page() -> str:
        """Read the visible text content of the current page. Use this when you
        need to re-read the page content after it may have changed."""
        content = await fetcher.get_page_content()
        current = await fetcher.current_url()
        return f"[Current page: {current}]\n\n{content}"

    @tool
    async def check_if_blocked() -> str:
        """Check if the current page is blocked by CAPTCHA, Cloudflare, or rate limiting.
        Use this if the page content seems unusual or empty."""
        result = await fetcher.check_blocked()
        if result["is_blocked"]:
            triggers = list(result["signals"].keys())
            return f"BLOCKED at {result['url']}: detected {', '.join(triggers)}"
        return f"NOT BLOCKED: Page at {result['url']} is accessible."

    return [navigate_to, get_page_links, read_current_page, check_if_blocked]
