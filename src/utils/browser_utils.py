import logging
import os
import random
import time

import undetected_chromedriver as uc
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

logger = logging.getLogger(__name__)

# Rotating User-Agents for stealth
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
]


def random_delay(min_seconds: float = 1.0, max_seconds: float = 3.0):
    """Add random delay to simulate human behavior."""
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)


def human_like_scroll(driver: uc.Chrome, scroll_pause_time: float = 2.0):
    """Perform human-like scrolling with random patterns."""
    page_height = driver.execute_script("return document.body.scrollHeight")
    current_position = 0
    while current_position < page_height:
        scroll_distance = random.randint(300, 800)
        current_position += scroll_distance
        driver.execute_script(f"window.scrollTo(0, {current_position});")
        random_delay(0.5, scroll_pause_time)
        if random.random() < 0.1:
            back_scroll = random.randint(50, 200)
            current_position -= back_scroll
            driver.execute_script(f"window.scrollTo(0, {current_position});")
            random_delay(0.3, 1.0)


def human_like_mouse_movement(driver: uc.Chrome, element: WebElement | None = None):
    """Simulate human-like mouse movements."""
    actions = ActionChains(driver)
    if element:
        actions.move_to_element_with_offset(
            element, random.randint(-5, 5), random.randint(-5, 5)
        )
    else:
        x = random.randint(100, 800)
        y = random.randint(100, 600)
        actions.move_by_offset(x, y)
    actions.perform()
    random_delay(0.1, 0.5)


def detect_blocking(driver: uc.Chrome) -> bool:  # noqa: C901
    """Detect if the site is blocking the scraper."""
    try:
        blocking_indicators = [
            "403 Forbidden",
            "Access Denied",
            "Blocked",
            "CAPTCHA",
            # Generic terms removed: "Robot", "Rate limit", "Security check"
        ]

        non_fatal_indicators = [
            "Rate limit",
        ]

        page_source = driver.page_source.lower()
        for indicator in blocking_indicators:
            if indicator.lower() in page_source:
                logger.warning(f"Blocking detected: {indicator}")
                return True
        for indicator in non_fatal_indicators:
            if indicator.lower() in page_source:
                logger.warning(
                    f"Possible transient block keyword: {indicator}. Backing off..."
                )
                time.sleep(random.uniform(5, 10))
                return False
        captcha_selectors = [
            "iframe[src*='captcha']",
            ".captcha",
            "#captcha",
            "[class*='captcha']",
            "[id*='captcha']",
        ]
        for selector in captcha_selectors:
            try:
                if driver.find_element(By.CSS_SELECTOR, selector):
                    logger.warning("CAPTCHA detected")
                    return True
            except NoSuchElementException:
                continue
        return False
    except Exception as e:
        logger.warning(f"Error detecting blocking: {e}")
        return False


def get_selenium_driver(headers: dict | None = None):
    """
    Initializes and returns a configured undetected_chromedriver instance.
    Configures browser options for headless operation, user-agent spoofing,
    and comprehensive anti-detection measures.
    """
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_argument("--proxy-server='direct://'")
    options.add_argument("--proxy-bypass-list=*")
    options.add_argument("--disable-features=IsolateOrigins,site-per-process")
    options.add_argument("--enable-features=NetworkService,NetworkServiceInProcess")
    options.add_argument("--headless=new")
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-features=VizDisplayCompositor")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--disable-field-trial-config")
    options.add_argument("--disable-ipc-flooding-protection")
    options.add_argument("--disable-default-apps")
    options.add_argument("--disable-sync")
    options.add_argument("--disable-translate")
    options.add_argument("--hide-scrollbars")
    options.add_argument("--mute-audio")
    options.add_argument("--no-first-run")
    options.add_argument("--safebrowsing-disable-auto-update")
    options.add_argument("--disable-client-side-phishing-detection")
    options.add_argument("--disable-component-update")
    options.add_argument("--disable-domain-reliability")
    options.add_argument("--disable-features=TranslateUI")
    options.add_argument("--disable-print-preview")
    options.add_argument("--disable-prompt-on-repost")
    options.add_argument("--disable-background-networking")
    options.add_argument("--disable-background-downloads")
    options.add_argument("--disable-background-upload")
    options.add_argument("--disable-background-media-suspend")
    user_agent = random.choice(USER_AGENTS)
    options.add_argument(f"user-agent={user_agent}")
    # Remove problematic experimental options that may be unsupported in some driver versions
    # options.add_experimental_option("excludeSwitches", ["enable-automation"])
    # options.add_experimental_option("useAutomationExtension", False)
    options.add_experimental_option(
        "prefs",
        {
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_settings.popups": 0,
            "profile.managed_default_content_settings.images": 2,
            "profile.default_content_setting_values.media_stream": 2,
        },
    )
    try:
        # Prefer explicit chromedriver path if provided by environment
        # Fallback to default behavior of undetected_chromedriver which manages the binary
        chromedriver_path = os.environ.get("CHROMEDRIVER_PATH")
        if chromedriver_path and os.path.exists(chromedriver_path):
            driver = uc.Chrome(
                driver_executable_path=chromedriver_path, options=options
            )
        else:
            driver = uc.Chrome(options=options)
        driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        driver.execute_script(
            "Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})"
        )
        driver.execute_script(
            "Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})"
        )
        driver.execute_script(
            "Object.defineProperty(navigator, 'permissions', {"
            "get: () => ({query: () => Promise.resolve({state: 'granted'})})"
            "})"
        )
        driver.set_page_load_timeout(60)
        logger.info(
            "Selenium driver successfully initialized with enhanced stealth configuration."
        )
        return driver
    except WebDriverException as e:
        logger.critical(
            "Failed to initialize Selenium driver: %s. Verify Chromium installation, "
            "undetected-chromedriver compatibility, and system dependencies.",
            e,
            exc_info=True,
        )
        raise
    except Exception as e:
        logger.critical(
            f"An unexpected error occurred during driver initialization: {e}",
            exc_info=True,
        )
        raise


def restart_driver_on_block(
    driver: uc.Chrome, headers: dict | None = None
) -> uc.Chrome:
    """Restart the driver with fresh settings when blocking is detected."""
    logger.warning("Blocking detected. Restarting driver with fresh settings...")
    try:
        driver.quit()
    except Exception as e:
        logger.warning(f"Error closing driver: {e}")
    random_delay(2.0, 5.0)
    return get_selenium_driver(headers)
