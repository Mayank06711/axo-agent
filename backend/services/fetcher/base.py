from abc import ABC, abstractmethod


class PageFetcher(ABC):
    """Abstract interface for page fetching. Swap implementations via Strategy pattern."""

    @abstractmethod
    async def launch(self) -> None:
        """Launch the browser / session."""

    @abstractmethod
    async def goto(self, url: str) -> str:
        """Navigate to URL, return raw HTML."""

    @abstractmethod
    async def get_page_content(self) -> str:
        """Return visible text of the current page (truncated for LLM context)."""

    @abstractmethod
    async def get_links(self) -> list[dict]:
        """Extract all links from the current page."""

    @abstractmethod
    async def check_blocked(self) -> dict:
        """Detect CAPTCHA, Cloudflare, 403, rate limiting on current page."""

    @abstractmethod
    async def current_url(self) -> str:
        """Return the current page URL."""

    @abstractmethod
    async def close(self) -> None:
        """Clean up browser / session resources."""
