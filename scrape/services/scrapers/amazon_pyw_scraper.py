import asyncio
import random
import time
import urllib.parse
from typing import Dict, List, Optional

from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeoutError

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
]

STEALTH_JS = r"""
// Basic manual stealth tweaks:
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
window.chrome = window.chrome || { runtime: {} };
Object.defineProperty(navigator, 'languages', { get: () => ['en-US','en'] });
Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3,4,5] });

// permissions fix for notifications
const _origPermQuery = window.navigator.permissions && window.navigator.permissions.query;
if (_origPermQuery) {
  window.navigator.permissions.query = (parameters) => {
    if (parameters && parameters.name === 'notifications') {
      return Promise.resolve({ state: Notification.permission });
    }
    return _origPermQuery(parameters);
  };
}
"""


class AmazonScraper:
    BASE_URL = "https://www.amazon.com/s?k="

    def __init__(
        self,
        proxies: Optional[List[str]] = None,
        headless: bool = False,
        max_retries: int = 3,
        screenshot_on_error: bool = True,
    ):
        """
        proxies: list of proxy strings:
            - http://host:port
            - http://user:pass@host:port
            - socks5://host:port
            - socks5://user:pass@host:port
        headless: whether to run headless (headless is more detectable)
        max_retries: number of attempts (rotates proxy on failures)
        """
        self.proxies = proxies or []
        self.headless = headless
        self.max_retries = max_retries
        self.screenshot_on_error = screenshot_on_error
        self._bad_proxies = set()

    def _pick_proxy(self) -> Optional[Dict]:
        """Pick a random healthy proxy and return Playwright proxy dict or None."""
        candidates = [p for p in self.proxies if p not in self._bad_proxies]
        if not candidates:
            return None
        raw = random.choice(candidates)
        parsed = urllib.parse.urlparse(raw)
        if not parsed.scheme or not parsed.hostname or not parsed.port:
            return None
        server = f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"
        proxy = {"server": server}
        if parsed.username:
            proxy["username"] = urllib.parse.unquote(parsed.username)
        if parsed.password:
            proxy["password"] = urllib.parse.unquote(parsed.password)
        return proxy

    async def _apply_stealth(self, page: Page):
        """Inject stealth JS to page before navigation."""
        await page.add_init_script(STEALTH_JS)

    async def _human_like(self, page: Page):
        """Do a few small mouse moves and random wait to mimic a person."""
        try:
            width, height = 1200, 800
            await page.mouse.move(random.randint(100, 400), random.randint(100, 400))
            for _ in range(random.randint(2, 6)):
                await page.mouse.move(random.randint(100, width - 100), random.randint(100, height - 100), steps=random.randint(5, 20))
                await asyncio.sleep(random.uniform(0.05, 0.25))
            await asyncio.sleep(random.uniform(0.3, 1.2))
        except Exception:
            pass

    async def _safe_text(self, el, selector: str) -> Optional[str]:
        """Helper to get inner_text with try/except"""
        if el is None:
            return None
        try:
            return (await el.inner_text(selector)).strip()
        except Exception:
            return None

    async def scrape(self, query: str) -> List[Dict]:
        """Scrape Amazon search results for a query. Returns list of items dict{name,url,price}."""
        query_encoded = urllib.parse.quote_plus(query)
        url = f"{self.BASE_URL}{query_encoded}"

        attempts = 0
        last_exception = None

        while attempts < self.max_retries:
            attempts += 1
            proxy = self._pick_proxy()
            proxy_info = proxy.get("server") if proxy else "no-proxy"
            print(f"[attempt {attempts}/{self.max_retries}] using proxy: {proxy_info}")

            try:
                async with async_playwright() as pw:
                    launch_args = {
                        "headless": self.headless,
                        "args": ["--disable-blink-features=AutomationControlled", "--no-sandbox"],
                    }
                    if proxy:
                        launch_args["proxy"] = proxy

                    browser: Browser = await pw.chromium.launch(**launch_args)

                    ua = random.choice(USER_AGENTS)
                    context = await browser.new_context(
                        user_agent=ua,
                        viewport={"width": 1200, "height": 800},
                        locale="en-US",
                    )
                    await context.set_extra_http_headers({
                        "accept-language": "en-US,en;q=0.9",
                        "upgrade-insecure-requests": "1",
                    })

                    page = await context.new_page()

                    await self._apply_stealth(page)

                    print("navigating to:", url)
                    await page.goto(url, timeout=90000, wait_until="domcontentloaded")

                    await asyncio.sleep(random.uniform(1.2, 2.8))
                    await self._human_like(page)

                    html = await page.content()
                    lower_html = html.lower()
                    if "captcha" in lower_html or "enter the characters you see below" in lower_html or "press and hold" in lower_html:
                        print("CAPTCHA or bot-check detected on page content.")
                        if self.screenshot_on_error:
                            ts = int(time.time())
                            pth = f"captcha_{attempts}_{ts}.png"
                            try:
                                await page.screenshot(path=pth, full_page=True)
                                print("Wrote screenshot:", pth)
                            except Exception:
                                pass
                        if proxy:
                            self._bad_proxies.add(proxy.get("server"))
                            print("Blacklisting proxy:", proxy.get("server"))
                        await browser.close()
                        last_exception = RuntimeError("CAPTCHA detected")
                        continue

                    await page.wait_for_selector("div.s-main-slot [data-component-type='s-search-result']", timeout=60000)

                    items = await page.query_selector_all("div.s-main-slot [data-component-type='s-search-result']")
                    products = []
                    for item in items[:12]:
                        try:
                            title_el = await item.query_selector("h2 a span")
                            title = (await title_el.inner_text()).strip() if title_el else None
                        except Exception:
                            title = None

                        try:
                            link_el = await item.query_selector("h2 a")
                            link_suffix = await link_el.get_attribute("href") if link_el else None
                            link = f"https://www.amazon.com{link_suffix}" if link_suffix else None
                        except Exception:
                            link = None

                        price = None
                        try:
                            whole_el = await item.query_selector(".a-price .a-price-whole")
                            frac_el = await item.query_selector(".a-price .a-price-fraction")
                            if whole_el and frac_el:
                                whole = (await whole_el.inner_text()).replace(",", "").replace("$", "").strip()
                                frac = (await frac_el.inner_text()).strip()
                                price = float(f"{whole}.{frac}")
                        except Exception:
                            price = None

                        if title and link:
                            products.append({"name": title, "url": link, "price": price})

                    await browser.close()
                    if products:
                        print(f"Found {len(products)} products.")
                        return products

                    if self.screenshot_on_error:
                        ts = int(time.time())
                        pth = f"no_results_{attempts}_{ts}.png"
                        try:
                            await page.screenshot(path=pth, full_page=True)
                            print("Wrote screenshot (no results):", pth)
                        except Exception:
                            pass
                    await browser.close()
                    last_exception = RuntimeError("No products found on page")
                    if proxy:
                        self._bad_proxies.add(proxy.get("server"))
                    continue

            except PlaywrightTimeoutError as e:
                print(f"TimeoutError on attempt {attempts}: {e}")
                last_exception = e
                if proxy:
                    self._bad_proxies.add(proxy.get("server"))
                continue
            except Exception as e:
                print(f"Error on attempt {attempts}: {e}")
                last_exception = e
                if proxy:
                    self._bad_proxies.add(proxy.get("server"))
                continue

        raise RuntimeError(f"Failed to scrape after {self.max_retries} attempts. Last error: {last_exception}")

if __name__ == "__main__":
    async def main():
        proxies = [
            "http://user:pass@1.2.3.4:8000",
            "http://5.6.7.8:8000",
            "socks5://user:pass@9.10.11.12:1080",
        ]

        scraper = AmazonScraper(proxies=proxies, headless=False, max_retries=3)
        try:
            items = await scraper.scrape("iphone")
            for i, it in enumerate(items, 1):
                print(i, it)
        except Exception as exc:
            print("Scraper failed:", exc)

    asyncio.run(main())
