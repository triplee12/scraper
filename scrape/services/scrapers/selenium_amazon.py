from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import random, time, re

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/117.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15",
]

def build_driver(headless=True, remote_url=None):
    options = Options()
    if headless:
        options.add_argument("--headless=new")

    options.add_argument(f"--user-agent={random.choice(USER_AGENTS)}")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-infobars")
    options.add_argument("--window-size=1920,1080")

    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Remote(command_executor=remote_url, options=options) \
        if remote_url else webdriver.Chrome(options=options)

    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US','en']});
            Object.defineProperty(navigator, 'platform', {get: () => 'Win32'});
        """
    })
    return driver


class AmazonScraper:
    def __init__(self, headless=True, remote_url=None):
        self.driver = build_driver(headless, remote_url)

    def _extract_price(self):
        selectors = [
            "span.a-price > span.a-offscreen",
            "#price_inside_buybox",
            "#priceblock_ourprice",
            "#priceblock_dealprice",
        ]
        for sel in selectors:
            try:
                el = self.driver.find_element(By.CSS_SELECTOR, sel)
                if el.text.strip():
                    cleaned = re.sub(r"[^\d\.]", "", el.text)
                    return float(cleaned)
            except:
                pass
        return None

    def _extract_category(self):
        try:
            elems = self.driver.find_elements(By.CSS_SELECTOR, "ul.a-unordered-list.a-horizontal li a")
            cats = [e.text.strip() for e in elems if e.text.strip()]
            return " > ".join(cats)
        except:
            return None

    def scrape_search_page(self, url, limit=10):
        self.driver.get(url)
        time.sleep(random.uniform(1.5, 2.8))

        self.driver.execute_script("window.scrollBy(0, 800);")
        time.sleep(1.2)

        products = self.driver.find_elements(By.CSS_SELECTOR, "h2 a.a-link-normal")[:limit]
        links = [p.get_attribute("href") for p in products]

        results = []

        for link in links:
            self.driver.execute_script("window.open(arguments[0]);", link)
            self.driver.switch_to.window(self.driver.window_handles[-1])

            try:
                title_el = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "productTitle"))
                )
                title = title_el.text.strip()
                price = self._extract_price()
                category = self._extract_category()

                results.append({
                    "name": title,
                    "price": price,
                    "category": category,
                    "url": self.driver.current_url
                })

            except Exception as e:
                results.append({"error": str(e), "url": link})

            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])
            time.sleep(random.uniform(1.3, 2.7))

        return results

    def close(self):
        self.driver.quit()
