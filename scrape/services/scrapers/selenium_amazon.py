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

    ua = random.choice(USER_AGENTS)
    options.add_argument(f"user-agent={ua}")

    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-infobars")
    options.add_argument("--window-size=1920,1080")

    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    if remote_url:
        driver = webdriver.Remote(command_executor=remote_url, options=options)
    else:
        driver = webdriver.Chrome(options=options)

    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            Object.defineProperty(navigator, 'platform', { get: () => 'Win32' });
        """
    })
    return driver


class SeleniumAmazonScraper:
    def __init__(self, headless=True, remote_url=None):
        self.driver = build_driver(headless, remote_url)

    def _open_first_product(self):
        product = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'h2 a.a-link-normal'))
        )
        product.click()
        time.sleep(1.2)

    def _extract_price(self):
        selectors = [
            "#price_inside_buybox",
            "#priceblock_ourprice",
            "#priceblock_dealprice",
            "span.a-price > span.a-offscreen"
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

    def fetch(self, url):
        try:
            self.driver.get(url)
            time.sleep(random.uniform(1.2, 2))

            if "amazon.com/s?" in url or "?k=" in url:
                self._open_first_product()

            title_el = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "productTitle"))
            )
            title = title_el.text.strip()
            price = self._extract_price()

            return {"name": title, "price": price, "url": self.driver.current_url}
        except Exception as e:
            return {"error": str(e), "url": url}

    def close(self):
        try:
            self.driver.quit()
        except:
            pass
