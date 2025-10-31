import time, random, re, json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/117.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15",
]

def build_driver(headless=True, remote_url=None, proxy=None):
    options = Options()
    if headless:
        options.add_argument("--headless=new")

    options.add_argument(f"--user-agent={random.choice(USER_AGENTS)}")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-infobars")
    options.add_argument("--window-size=1920,1080")

    if proxy:
        options.add_argument(f"--proxy-server={proxy}")

    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Remote(command_executor=remote_url, options=options) \
        if remote_url else webdriver.Chrome(options=options)

    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            Object.defineProperty(navigator, 'platform', { get: () => 'Win32' });
        """
    })
    return driver


class JumiaScraper:
    def __init__(self, headless=True, remote_url=None, proxy=None):
        self.driver = build_driver(headless, remote_url, proxy)

    def fetch_products(self, url: str, timeout: int = 15):
        try:
            self.driver.get(url)
            time.sleep(random.uniform(1.2, 2.5))

            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "article.prd"))
            )

            products = []
            items = self.driver.find_elements(By.CSS_SELECTOR, "article.prd")

            for item in items:
                try:
                    title = item.find_element(By.CSS_SELECTOR, "div.name").text.strip()
                    product_url = item.find_element(By.CSS_SELECTOR, "a.core").get_attribute("href")

                    try:
                        price_txt = item.find_element(By.CSS_SELECTOR, "div.prc").text.strip()
                        clean_price = re.sub(r"[^\d.]", "", price_txt.replace(",", ""))
                        price = float(clean_price) if clean_price else None
                    except:
                        price = None

                    products.append({
                        "name": title,
                        "price": price,
                        "url": product_url
                    })

                except Exception:
                    continue

            return products

        except Exception as e:
            return {"error": str(e), "url": url}


    def close(self):
        try:
            self.driver.quit()
        except:
            pass


if __name__ == "__main__":
    scraper = JumiaScraper(headless=True)
    data = scraper.fetch_products("https://www.jumia.com.ng/phones-tablets/")
    print(json.dumps(data, indent=2))
    scraper.close()
