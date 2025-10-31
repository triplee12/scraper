import asyncio
import random
import time
import urllib.parse
from typing import Dict, List, Optional

from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeoutError

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119 Safari/537.36",
]

STEALTH_JS = r"""
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
window.chrome = window.chrome || { runtime: {} };
Object.defineProperty(navigator, 'languages', { get: () => ['en-US','en'] });
Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3] });

const _origPermQuery = navigator.permissions && navigator.permissions.query;
if (_origPermQuery) {
  navigator.permissions.query = (p) => {
    if (p && p.name === 'notifications') {
      return Promise.resolve({ state: Notification.permission });
    }
    return _origPermQuery(p);
  };
}
"""


class AmazonScraper:
    BASE_URL = "https://www.amazon.com/s?k="

    def __init__(self, proxies: Optional[List[str]] = None, headless: bool = False,
                 max_retries: int = 3, screenshot_on_error: bool = True):
        self.proxies = proxies or []
        self.headless = headless
        self.max_retries = max_retries
        self.screenshot_on_error = screenshot_on_error
        self._bad_proxies = set()

    def _pick_proxy(self) -> Optional[Dict]:
        candidates = [p for p in self.proxies if p not in self._bad_proxies]
        if not candidates:
            return None
        raw = random.choice(candidates)
        parsed = urllib.parse.urlparse(raw)
        if not parsed.scheme or not parsed.hostname or not parsed.port:
            return None
        proxy = {"server": f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"}
        if parsed.username:
            proxy["username"] = urllib.parse.unquote(parsed.username)
        if parsed.password:
            proxy["password"] = urllib.parse.unquote(parsed.password)
        return proxy

    async def _human_like(self, page: Page):
        try:
            for _ in range(random.randint(3, 6)):
                await page.mouse.move(
                    random.randint(150, 900),
                    random.randint(100, 700),
                    steps=random.randint(5, 15)
                )
                await asyncio.sleep(random.uniform(0.04, 0.18))
        except Exception:
            pass

    async def _extract_category_from_product(self, page: Page) -> Optional[str]:
        """
        Try several breadcrumb selectors on the product page.
        Returns breadcrumb joined by ' > ' or None.
        """
        selectors = [
            "#wayfinding-breadcrumbs_feature_div ul.a-unordered-list li a",
            "ul.a-unordered-list.a-horizontal li a",
            "div#nav-subnav a",
        ]
        try:
            for sel in selectors:
                elems = await page.query_selector_all(sel)
                if elems:
                    parts = []
                    for e in elems:
                        try:
                            txt = (await e.inner_text()).strip()
                            if txt:
                                parts.append(txt)
                        except Exception:
                            continue
                    if parts:
                        return " > ".join(parts)
        except Exception:
            pass

        try:
            meta = await page.query_selector("meta[name='category'], meta[property='og:category']")
            if meta:
                val = await meta.get_attribute("content")
                if val:
                    return val.strip()
        except Exception:
            pass

        return None

    async def scrape(self, query: str, max_items: int = 12) -> List[Dict]:
        """
        Scrape Amazon search results for `query`.
        Returns list of dicts: {name, url, price, category}
        """
        query_encoded = urllib.parse.quote_plus(query)
        url = f"{self.BASE_URL}{query_encoded}"

        attempts = 0
        last_exception = None

        while attempts < self.max_retries:
            attempts += 1
            proxy = self._pick_proxy()
            print(f"[Attempt {attempts}/{self.max_retries}] proxy: {proxy.get('server') if proxy else 'no-proxy'}")

            try:
                async with async_playwright() as pw:
                    launch_args = {
                        "headless": self.headless,
                        "args": [
                            "--disable-blink-features=AutomationControlled",
                            "--no-sandbox",
                            "--disable-dev-shm-usage",
                            "--disable-gpu",
                            "--disable-infobars",
                        ],
                    }
                    if proxy:
                        launch_args["proxy"] = proxy

                    browser: Browser = await pw.chromium.launch(**launch_args)

                    context = await browser.new_context(
                        user_agent=random.choice(USER_AGENTS),
                        viewport={"width": 1200, "height": 800},
                        locale="en-US",
                    )
                    await context.add_init_script(STEALTH_JS)

                    page = await context.new_page()
                    await page.set_extra_http_headers({
                        "accept-language": "en-US,en;q=0.9",
                        "upgrade-insecure-requests": "1",
                    })

                    print("navigating to:", url)
                    await page.goto(url, timeout=90000, wait_until="domcontentloaded")
                    await asyncio.sleep(random.uniform(1.2, 2.8))
                    await self._human_like(page)

                    html = (await page.content()).lower()
                    if any(token in html for token in ("captcha", "bot check", "enter the characters", "press and hold")):
                        print("CAPTCHA/bot-check detected on search page.")
                        if proxy:
                            self._bad_proxies.add(proxy.get("server"))
                            print("blacklisting proxy:", proxy.get("server"))
                        if self.screenshot_on_error:
                            ts = int(time.time())
                            try:
                                await page.screenshot(path=f"captcha_search_{attempts}_{ts}.png", full_page=True)
                                print("screenshot written.")
                            except Exception:
                                pass
                        await context.close()
                        await browser.close()
                        last_exception = RuntimeError("CAPTCHA detected on search page")
                        continue

                    try:
                        await page.wait_for_selector("div.s-main-slot [data-component-type='s-search-result']", timeout=60000)
                    except PlaywrightTimeoutError:
                        print("Timed out waiting for search results.")
                        last_exception = PlaywrightTimeoutError("No search results")
                        await context.close()
                        await browser.close()
                        if proxy:
                            self._bad_proxies.add(proxy.get("server"))
                        continue

                    items = await page.query_selector_all("div.s-main-slot [data-component-type='s-search-result']")
                    products = []

                    links = []
                    for item in items[: max_items]:
                        try:
                            link_el = await item.query_selector("h2 a")
                            href = await link_el.get_attribute("href") if link_el else None
                            if href:
                                full = urllib.parse.urljoin("https://www.amazon.com", href)
                                links.append(full)
                        except Exception:
                            continue

                    for link in links:
                        try:
                            p = await context.new_page()
                            await p.set_extra_http_headers({
                                "accept-language": "en-US,en;q=0.9",
                                "upgrade-insecure-requests": "1",
                            })
                            await p.goto(link, timeout=90000, wait_until="domcontentloaded")
                            await asyncio.sleep(random.uniform(1.0, 2.4))
                            await self._human_like(p)

                            prod_html = (await p.content()).lower()
                            if any(token in prod_html for token in ("captcha", "bot check", "enter the characters", "press and hold")):
                                print("CAPTCHA detected on product page:", link)
                                if self.screenshot_on_error:
                                    ts = int(time.time())
                                    try:
                                        await p.screenshot(path=f"captcha_product_{attempts}_{ts}.png", full_page=True)
                                    except Exception:
                                        pass
                                if proxy:
                                    self._bad_proxies.add(proxy.get("server"))
                                await p.close()
                                raise RuntimeError("CAPTCHA on product page")

                            title = None
                            try:
                                t_sel = await p.query_selector("#productTitle")
                                if t_sel:
                                    title = (await t_sel.inner_text()).strip()
                                else:
                                    h1 = await p.query_selector("h1 span")
                                    title = (await h1.inner_text()).strip() if h1 else None
                            except Exception:
                                title = None

                            price = None
                            price_selectors = [
                                ".a-price .a-offscreen",
                                "#price_inside_buybox",
                                "#priceblock_ourprice",
                                "#priceblock_dealprice",
                            ]
                            for ps in price_selectors:
                                try:
                                    pe = await p.query_selector(ps)
                                    if pe:
                                        txt = (await pe.inner_text()).strip()
                                        cleaned = txt.replace("$", "").replace(",", "").strip()
                                        try:
                                            price = float(re.sub(r"[^\d\.]", "", cleaned))
                                            break
                                        except Exception:
                                            price = None
                                except Exception:
                                    continue

                            category = await self._extract_category_from_product(p)

                            products.append({
                                "name": title,
                                "url": link,
                                "price": price,
                                "category": category
                            })

                            await p.close()
                            await asyncio.sleep(random.uniform(0.6, 1.6))

                        except Exception as e:
                            print("Error scraping product page:", e)
                            try:
                                await p.close()
                            except Exception:
                                pass
                            if "captcha" in str(e).lower() and proxy:
                                self._bad_proxies.add(proxy.get("server"))
                            continue

                    await context.close()
                    await browser.close()

                    if products:
                        print(f"Found {len(products)} products (with categories).")
                        return products

                    if proxy:
                        self._bad_proxies.add(proxy.get("server"))
                    last_exception = RuntimeError("No products found on search page")
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
    import re
    async def main():
        proxies = []

        scraper = AmazonScraper(proxies=proxies, headless=False, max_retries=3)
        try:
            items = await scraper.scrape("iphone", max_items=8)
            for i, it in enumerate(items, 1):
                print(i, it)
        except Exception as exc:
            print("Scraper failed:", exc)

    asyncio.run(main())
