import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from .utils import parse_comments, detection_misattribution

BASE_URL = "https://portal.crt.gob.mx/ConsultaPublica/Detalle/"
CONSULTATION_ID = 19

async def _fetch() -> list[dict]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(f"{BASE_URL}{CONSULTATION_ID}", wait_until="networkidle")
        # Wait for comment container – placeholder selector, may need adjustment.
        try:
            await page.wait_for_selector("div.comment-list", timeout=15000)
        except Exception:
            # If selector not found, continue with whatever is loaded.
            pass
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")
        comments = parse_comments(soup)
        for c in comments:
            c["is_misattributed"] = detection_misattribution(c["text"])
        await browser.close()
        return comments

def fetch_comments() -> list[dict]:
    """Synchronously fetch comments using Playwright.
    This wrapper runs the async function in an event loop so callers can use a simple
    function signature.
    """
    return asyncio.run(_fetch())
