import logging

from playwright.async_api import async_playwright
from playwright_stealth import Stealth

from backend.services.fetcher.base import PageFetcher

logger = logging.getLogger("axo_agent.fetcher")

# GPT-4/Claude handle 128K tokens (~500K chars). 15K chars (~4K tokens) is safe
# and captures most page content without wasting context on boilerplate.
MAX_CONTENT_LENGTH = 15000
MAX_LINKS = 50
BLOCKED_SIGNALS = [
    "captcha",
    "recaptcha",
    "hcaptcha",
    "cf-browser-verification",
    "cf-challenge",
    "cloudflare",
    "please verify you are a human",
    "are you a robot",
    "access denied",
    "rate limit",
]


class PlaywrightFetcher(PageFetcher):
    """Headless Chromium with stealth — handles JS-rendered pages."""

    def __init__(self):
        self._pw = None
        self._browser = None
        self._page = None

    async def launch(self) -> None:
        self._pw = await async_playwright().start()
        self._browser = await self._pw.chromium.launch(headless=True)
        context = await self._browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1920, "height": 1080},
        )
        self._page = await context.new_page()
        stealth = Stealth()
        await stealth.apply_stealth_async(self._page)

    async def goto(self, url: str) -> str:
        try:
            await self._page.goto(url, wait_until="domcontentloaded", timeout=30000)
            # Give JS a moment to render dynamic content
            await self._page.wait_for_timeout(2000)
        except Exception as e:
            logger.warning(f"Navigation to {url} issue: {e}")
        return await self._page.content()

    async def get_page_content(self) -> str:
        text = await self._page.evaluate("() => document.body.innerText")
        if len(text) > MAX_CONTENT_LENGTH:
            text = text[:MAX_CONTENT_LENGTH] + "\n... [content truncated]"
        return text

    async def get_links(self) -> list[dict]:
        links = await self._page.evaluate(
            """() => {
                return Array.from(document.querySelectorAll('a[href]'))
                    .map(a => ({
                        href: a.href,
                        text: a.innerText.trim().substring(0, 100)
                    }))
                    .filter(l => l.text.length > 0 && l.href.startsWith('http'))
                    .slice(0, %d)
            }"""
            % MAX_LINKS
        )
        return links

    async def check_blocked(self) -> dict:
        content = (await self._page.content()).lower()
        title = (await self._page.title()).lower()
        url = self._page.url

        signals = {}
        for signal in BLOCKED_SIGNALS:
            if signal in content or signal in title:
                signals[signal] = True

        is_blocked = len(signals) > 0
        return {"is_blocked": is_blocked, "signals": signals, "url": url}

    async def current_url(self) -> str:
        return self._page.url

    async def close(self) -> None:
        if self._browser:
            await self._browser.close()
        if self._pw:
            await self._pw.stop()
        self._browser = None
        self._pw = None
        self._page = None
