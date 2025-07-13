import logging
import re
import time
import random
from datetime import datetime, timedelta
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    WebDriverException,
    TimeoutException,
    NoSuchElementException,
)
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.action_chains import ActionChains


from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)


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
    # Get page height
    page_height = driver.execute_script("return document.body.scrollHeight")

    # Scroll in chunks with random pauses
    current_position = 0
    while current_position < page_height:
        # Random scroll distance (between 300-800 pixels)
        scroll_distance = random.randint(300, 800)
        current_position += scroll_distance

        # Smooth scroll with JavaScript
        driver.execute_script(f"window.scrollTo(0, {current_position});")

        # Random pause between scrolls
        random_delay(0.5, scroll_pause_time)

        # Occasionally scroll back up a bit (human behavior)
        if random.random() < 0.1:  # 10% chance
            back_scroll = random.randint(50, 200)
            current_position -= back_scroll
            driver.execute_script(f"window.scrollTo(0, {current_position});")
            random_delay(0.3, 1.0)


def human_like_mouse_movement(driver: uc.Chrome, element: WebElement | None = None):
    """Simulate human-like mouse movements."""
    actions = ActionChains(driver)

    if element:
        # Move to element with slight offset
        actions.move_to_element_with_offset(
            element, random.randint(-5, 5), random.randint(-5, 5)
        )
    else:
        # Random mouse movement
        x = random.randint(100, 800)
        y = random.randint(100, 600)
        actions.move_by_offset(x, y)

    actions.perform()
    random_delay(0.1, 0.5)


def detect_blocking(driver: uc.Chrome) -> bool:
    """Detect if the site is blocking the scraper."""
    try:
        # Check for common blocking indicators
        blocking_indicators = [
            "403 Forbidden",
            "Access Denied",
            "Blocked",
            "CAPTCHA",
            "Robot",
            "Automation",
            "Too many requests",
            "Rate limit",
            "Security check",
        ]

        page_source = driver.page_source.lower()
        for indicator in blocking_indicators:
            if indicator.lower() in page_source:
                logger.warning(f"Blocking detected: {indicator}")
                return True

        # Check for CAPTCHA elements
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

    # Basic stealth options
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

    # Enhanced stealth options
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

    # Set random user agent
    user_agent = random.choice(USER_AGENTS)
    options.add_argument(f"user-agent={user_agent}")

    # Add experimental options for better stealth
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
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
        driver = uc.Chrome(options=options)

        # Execute stealth scripts
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

    random_delay(2.0, 5.0)  # Wait before restarting
    return get_selenium_driver(headers)


def _parse_datetime_attribute(date_element: WebElement | None) -> datetime | None:
    """Tries to parse date from a 'datetime' attribute."""
    if date_element and date_element.tag_name == "time":
        datetime_attr = date_element.get_attribute("datetime")
        if datetime_attr:
            try:
                return datetime.fromisoformat(datetime_attr.replace("Z", "+00:00"))
            except ValueError:
                pass
    return None


def _parse_relative_date(date_str_lower: str) -> datetime | None:
    """Parses relative date strings like '2 days ago'."""
    match_en = re.search(
        r"(\d+)\s+(minute|hour|day|week|month|year)s?\s+ago", date_str_lower
    )
    if match_en:
        value = int(match_en.group(1))
        unit = match_en.group(2)
        if unit == "minute":
            return datetime.now() - timedelta(minutes=value)
        elif unit == "hour":
            return datetime.now() - timedelta(hours=value)
        elif unit == "day":
            return datetime.now() - timedelta(days=value)
        elif unit == "week":
            return datetime.now() - timedelta(weeks=value)
        elif unit == "month":
            return datetime.now() - timedelta(days=value * 30.437)
        elif unit == "year":
            return datetime.now() - timedelta(days=value * 365.25)
    return None


def _parse_arabic_relative_date(date_str: str) -> datetime | None:
    """Parses Arabic relative date strings like 'منذ 2 يوم'."""
    match_ar = re.search(
        r"منذ\s+(\d+)\s+(يوم|أيام|شهر|شهور|ساعة|ساعات|دقيقة|دقائق)", date_str
    )
    if match_ar:
        value = int(match_ar.group(1))
        unit_ar = match_ar.group(2)
        if unit_ar in ["يوم", "أيام"]:
            return datetime.now() - timedelta(days=value)
        elif unit_ar in ["شهر", "شهور"]:
            return datetime.now() - timedelta(days=value * 30.437)
        elif unit_ar in ["ساعة", "ساعات"]:
            return datetime.now() - timedelta(hours=value)
        elif unit_ar in ["دقيقة", "دقائق"]:
            return datetime.now() - timedelta(minutes=value)
    return None


def _parse_month_day_date(date_str: str) -> datetime | None:
    """Parses month-day formats like 'Jul 09'."""
    month_day_match = re.search(r"([A-Za-z]{3})\s+(\d{1,2})", date_str)
    if month_day_match:
        try:
            month_name = month_day_match.group(1)
            day = int(month_day_match.group(2))
            current_year = datetime.now().year
            dt_obj = datetime.strptime(f"{month_name} {day} {current_year}", "%b %d %Y")
            if dt_obj > datetime.now():
                dt_obj = datetime.strptime(
                    f"{month_name} {day} {current_year - 1}", "%b %d %Y"
                )
            return dt_obj
        except ValueError:
            pass
    return None


def parse_date_string(
    date_str: str, date_element: WebElement | None = None
) -> datetime:
    """
    Parses a human-readable date string or extracts from a datetime attribute.
    Tries various parsing strategies sequentially.
    """
    date_str_lower = date_str.lower()
    now = datetime.now()

    parsing_strategies = [
        lambda: _parse_datetime_attribute(date_element),
        lambda: now if "today" in date_str_lower else None,
        lambda: now - timedelta(days=1) if "yesterday" in date_str_lower else None,
        lambda: _parse_relative_date(date_str_lower),
        lambda: now - timedelta(days=30) if "30+ days ago" in date_str_lower else None,
        lambda: _parse_arabic_relative_date(date_str),
        lambda: _parse_month_day_date(date_str),
    ]

    for strategy in parsing_strategies:
        parsed_date = strategy()
        if parsed_date:
            return parsed_date

    logger.warning(
        f"Could not parse date string '{date_str}'. Defaulting to current time."
    )
    return now


def _extract_title(card: WebElement, selector: str, site_name: str) -> str:
    """Extracts job title from the card."""
    try:
        return str(card.find_element(By.CSS_SELECTOR, selector).text.strip())
    except NoSuchElementException:
        logger.warning(
            f"Title element not found on {site_name} for a job card. "
            "Returning empty string."
        )
        return ""


# --- Refined Helper Functions for _extract_link ---


def _get_href_from_element(
    element: WebElement, site_name: str, method_name: str
) -> str | None:
    """Safely extracts href attribute from a WebElement, logging debug info."""
    try:
        link = element.get_attribute("href")
        # Only return if it's a real string (not a mock or None)
        if isinstance(link, str) and link:
            return link
    except Exception as e:
        logger.debug(
            f"Error getting href from {method_name} on {site_name}: {e}", exc_info=False
        )
    return None


def _attempt_link_from_selector(
    card: WebElement, selector: str | None, site_name: str
) -> str | None:
    """Attempts to find an element by CSS selector and extract its link."""
    if not selector:
        return None
    try:
        link_element = card.find_element(By.CSS_SELECTOR, selector)
        return _get_href_from_element(
            link_element, site_name, "primary selector element"
        )
    except NoSuchElementException:
        logger.debug(f"Primary link selector '{selector}' not found on {site_name}.")
    except Exception as e:
        logger.warning(
            f"Error during primary link selector search on {site_name}: {e}. "
            "Attempting fallback.",
            exc_info=True,
        )
    return None


def _attempt_link_from_title_element(
    title_element: WebElement, site_name: str
) -> str | None:
    """Attempts to extract a link from the title element itself or a nested link."""
    if not title_element:
        return None

    # Only try title element itself if it's actually an <a> tag
    if title_element.tag_name == "a":
        link = _get_href_from_element(
            title_element, site_name, "title element (direct)"
        )
        if link:
            return link

    # Try nested link within title element
    try:
        nested_link_element = title_element.find_element(By.TAG_NAME, "a")
        return _get_href_from_element(
            nested_link_element, site_name, "nested title link"
        )
    except NoSuchElementException:
        logger.debug(f"No nested link found in title_element on {site_name}.")
    except Exception as e:
        logger.warning(
            f"Error searching for nested link in title_element on {site_name}: {e}. "
            "Attempting next fallback.",
            exc_info=True,
        )
    return None


def _attempt_link_from_card_direct(card: WebElement, site_name: str) -> str | None:
    """Attempts to extract a link if the card element itself is an <a> tag."""
    if card.tag_name == "a":
        return _get_href_from_element(card, site_name, "card element (direct a)")
    return None


def _extract_link(
    card: WebElement, title_element: WebElement, selector: str | None, site_name: str
) -> str:
    """Extracts job link from the card using sequential fallbacks."""

    # Attempt 1: Specific link selector
    link = _attempt_link_from_selector(card, selector, site_name)
    if link:
        return link

    # Attempt 2: Title element (direct or nested)
    link = _attempt_link_from_title_element(title_element, site_name)
    if link:
        return link

    # Attempt 3: Card element itself
    link = _attempt_link_from_card_direct(card, site_name)
    if link:
        return link

    logger.warning(
        f"Could not find link for a job on {site_name}. "
        "Skipping this job link extraction."
    )
    return ""


def _extract_description(card: WebElement, selector: str | None, site_name: str) -> str:
    """Extracts job description from the card."""
    if not selector:
        return ""
    try:
        return str(card.find_element(By.CSS_SELECTOR, selector).text.strip())
    except NoSuchElementException:
        logger.debug(
            f"Description not found on {site_name} for a job card. "
            "Skipping description extraction."
        )
        return ""


def _extract_tags(card: WebElement, selector: str | None, site_name: str) -> list[str]:
    """Extracts job tags from the card."""
    if not selector:
        return []
    try:
        tag_elements = card.find_elements(By.CSS_SELECTOR, selector)
        return [tag.text.strip() for tag in tag_elements if tag.text.strip()]
    except NoSuchElementException:
        logger.debug(
            f"Tags not found on {site_name} for a job card. " "Skipping tag extraction."
        )
        return []


def enhance_job_dates_from_pages(driver: uc.Chrome, jobs: list, site_name: str) -> list:
    """Enhance job dates by visiting job pages for jobs that show 'Recently' with stealth measures."""
    enhanced_jobs = []

    for i, job in enumerate(jobs):
        if job.get("posted_date") == "Recently":
            try:
                logger.debug(f"Enhancing date for job: {job.get('title', 'Unknown')}")

                # Add random delay before visiting job page
                random_delay(1.0, 3.0)

                driver.get(job["link"])

                # Check for blocking after navigation
                if detect_blocking(driver):
                    logger.warning(
                        f"Blocking detected while enhancing date for job on {site_name}"
                    )
                    # Keep the original 'Recently' date
                    enhanced_jobs.append(job)
                    continue

                # Wait for the date element to appear
                date_elem = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".css-182mrdn"))
                )

                enhanced_date = date_elem.text.strip()
                job["posted_date"] = enhanced_date
                logger.debug(f"Enhanced date: {enhanced_date}")

            except Exception as e:
                logger.warning(f"Error enhancing date for job on {site_name}: {e}")
                # Keep the original 'Recently' date

        enhanced_jobs.append(job)

        # Add delay between processing jobs to avoid rate limiting
        if i % 3 == 0:  # Every 3 jobs
            random_delay(2.0, 4.0)

    return enhanced_jobs


def _extract_date(card: WebElement, selector: str | None, site_name: str) -> str:
    """Extracts job posted date from the card as relative text."""
    if not selector:
        return "Recently"
    try:
        date_element = card.find_element(By.CSS_SELECTOR, selector)
        date_text: str = str(date_element.text.strip())
        # Return the relative date text directly (e.g., "Posted 6 days ago")
        return date_text
    except NoSuchElementException:
        logger.debug(
            f"Posted date not found on {site_name} for a job card. "
            "Defaulting to 'Recently'."
        )
        return "Recently"
    except Exception as e:
        logger.warning(
            f"Error parsing date on {site_name} for a job card: {e}. "
            "Defaulting to 'Recently'."
        )
        return "Recently"


def _extract_job_details_from_card(
    card: WebElement, website_config: dict
) -> dict | None:
    """
    Extracts title, link, description, tags, and posted date from a job card.
    """
    site_name = website_config["name"]

    try:
        title = _extract_title(card, website_config["title_selector"], site_name)
        if not title:
            return None

        # Pass the card directly to find title element for link extraction
        title_element = card.find_element(
            By.CSS_SELECTOR, website_config["title_selector"]
        )
        link = _extract_link(
            card, title_element, website_config.get("link_selector"), site_name
        )
        if not link:
            return None

        description = _extract_description(
            card, website_config.get("description_selector"), site_name
        )
        tags = _extract_tags(card, website_config.get("tags_selector"), site_name)
        posted_date = _extract_date(
            card, website_config.get("date_selector"), site_name
        )

        return {
            "title": title,
            "link": link,
            "description": description,
            "source": site_name,
            "tags": tags,
            "posted_date": posted_date,
        }

    except NoSuchElementException as e:
        logger.warning(
            f"Skipping job card on {site_name} due to missing primary element: {e}. "
            "Card HTML might be malformed or selectors are incorrect."
        )
        return None
    except Exception as e:
        logger.warning(
            f"An unexpected error occurred while processing a job card on "
            f"{site_name}: {e}",
            exc_info=True,
        )
        return None


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((TimeoutException, WebDriverException)),
)
def _safe_driver_get(driver: uc.Chrome, url: str):
    """Wrapper for driver.get() with retry logic and stealth measures."""
    logger.info(f"Attempting to navigate to {url}")

    # Add random delay before navigation
    random_delay(1.0, 3.0)

    driver.get(url)

    # Check for blocking after navigation
    if detect_blocking(driver):
        raise WebDriverException("Blocking detected after navigation")

    # Add random delay after navigation
    random_delay(2.0, 4.0)

    logger.info(f"Successfully navigated to {url}")


def _handle_scraping_retry(
    driver: uc.Chrome, website_config: dict, retry_count: int, max_retries: int
) -> tuple[bool, uc.Chrome]:
    """Handle retry logic for scraping failures."""
    site_name = website_config["name"]

    if retry_count < max_retries:
        logger.info(f"Retrying {site_name} (attempt {retry_count + 1}/{max_retries})")
        random_delay(5.0, 10.0)  # Longer delay before retry
        return True, driver
    return False, driver


def _handle_timeout_exception(
    driver: uc.Chrome, website_config: dict, retry_count: int, max_retries: int
) -> tuple[bool, uc.Chrome]:
    """Handle timeout exceptions during scraping."""
    site_name = website_config["name"]
    url = website_config["url"]

    logger.error(
        f"Timeout while loading or finding elements on {site_name} ({url}). "
        "Page might not have loaded correctly or selectors are invalid after "
        "40 seconds."
    )
    return _handle_scraping_retry(driver, website_config, retry_count, max_retries)


def _handle_webdriver_exception(
    driver: uc.Chrome,
    website_config: dict,
    retry_count: int,
    max_retries: int,
    e: Exception,
) -> tuple[bool, uc.Chrome]:
    """Handle WebDriver exceptions during scraping."""
    site_name = website_config["name"]

    logger.error(f"WebDriver error during scraping {site_name}: {e}", exc_info=True)
    should_retry, driver = _handle_scraping_retry(
        driver, website_config, retry_count, max_retries
    )
    if should_retry:
        driver = restart_driver_on_block(driver)
    return should_retry, driver


def _handle_general_exception(
    driver: uc.Chrome,
    website_config: dict,
    retry_count: int,
    max_retries: int,
    e: Exception,
) -> tuple[bool, uc.Chrome]:
    """Handle general exceptions during scraping."""
    site_name = website_config["name"]

    logger.critical(
        f"An unhandled error occurred during scraping of {site_name}: {e}",
        exc_info=True,
    )
    return _handle_scraping_retry(driver, website_config, retry_count, max_retries)


def _perform_initial_scraping_setup(driver: uc.Chrome, website_config: dict) -> bool:
    """Perform initial setup for scraping including navigation and blocking check."""
    url = website_config["url"]
    site_name = website_config["name"]
    job_card_selector = website_config["job_card_selector"]

    _safe_driver_get(driver, url)

    # Check for blocking after navigation
    if detect_blocking(driver):
        logger.warning(f"Blocking detected on {site_name}, restarting driver...")
        driver = restart_driver_on_block(driver)
        return False

    WebDriverWait(driver, 40).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, job_card_selector))
    )
    logger.debug(f"Successfully loaded and found job cards on {site_name}.")
    return True


def _perform_scraping_logic(driver: uc.Chrome, website_config: dict) -> list:
    """Perform the actual scraping logic based on website type."""
    url = website_config["url"]

    # Handle pagination for Wuzzuf sites
    if "wuzzuf.net" in url:
        return _scrape_wuzzuf_with_pagination(driver, website_config)
    else:
        # For other sites, use the enhanced scrolling method
        return _scrape_single_page_with_scroll(driver, website_config)


def _scrape_jobs_with_retry_logic(driver: uc.Chrome, website_config: dict) -> list:
    """Core scraping logic with retry mechanism."""
    jobs: list = []

    max_retries = 3
    retry_count = 0

    while retry_count < max_retries:
        try:
            if not _perform_initial_scraping_setup(driver, website_config):
                retry_count += 1
                continue

            jobs = _perform_scraping_logic(driver, website_config)

            # If we got here successfully, break out of retry loop
            break

        except TimeoutException:
            should_retry, driver = _handle_timeout_exception(
                driver, website_config, retry_count, max_retries
            )
            if not should_retry:
                break
            retry_count += 1
        except WebDriverException as e:
            should_retry, driver = _handle_webdriver_exception(
                driver, website_config, retry_count, max_retries, e
            )
            if not should_retry:
                break
            retry_count += 1
        except Exception as e:
            should_retry, driver = _handle_general_exception(
                driver, website_config, retry_count, max_retries, e
            )
            if not should_retry:
                break
            retry_count += 1

    return jobs


def scrape_jobs_from_website(driver: uc.Chrome, website_config: dict) -> list:
    """
    Navigates to a specified website and scrapes job postings based on its
    configuration. Utilizes WebDriverWait for robust element location,
    accounting for dynamic content loading and pagination with stealth measures.
    """
    jobs: list = []
    url = website_config["url"]
    site_name = website_config["name"]

    logger.info(f"Visiting {site_name} ({url}) to scrape job postings.")

    jobs = _scrape_jobs_with_retry_logic(driver, website_config)

    logger.info(f"Finished scraping {len(jobs)} jobs from {site_name}.")

    # Enhance dates for jobs that show 'Recently'
    if jobs and "wuzzuf.net" in url:
        logger.info(f"Enhancing dates for {site_name} jobs...")
        jobs = enhance_job_dates_from_pages(driver, jobs, site_name)
        logger.info(f"Date enhancement completed for {site_name}")

    return jobs


def _scrape_single_page_with_scroll(driver: uc.Chrome, website_config: dict) -> list:
    """Scrapes jobs from a single page using human-like scrolling to load more content."""
    jobs: list = []
    site_name = website_config["name"]
    job_card_selector = website_config["job_card_selector"]

    # Use human-like scrolling instead of basic scrolling
    logger.info(f"Starting human-like scrolling on {site_name}")
    human_like_scroll(driver, scroll_pause_time=2.0)

    # Add random delay after scrolling
    random_delay(1.0, 2.0)

    job_cards = driver.find_elements(By.CSS_SELECTOR, job_card_selector)
    if not job_cards:
        logger.warning(
            f"No job cards found using selector '{job_card_selector}' on "
            f"{site_name}. This might indicate a selector issue or no jobs."
        )
        return []

    logger.info(f"Found {len(job_cards)} job cards on {site_name}")

    for i, card in enumerate(job_cards):
        # Add human-like interactions for each job card
        try:
            # Simulate mouse movement to the card
            human_like_mouse_movement(driver, card)

            # Extract job details
            job_details = _extract_job_details_from_card(card, website_config)
            if job_details:
                jobs.append(job_details)

            # Add small delay between processing cards
            if i % 5 == 0:  # Every 5 cards
                random_delay(0.5, 1.0)

        except Exception as e:
            logger.warning(f"Error processing job card {i} on {site_name}: {e}")
            continue

    return jobs


def _try_css_next_button(driver: uc.Chrome) -> bool:
    """Try to find and click next button using CSS selectors."""
    next_page_selectors = [
        "button.css-zye1os a.css-1fcv3il",  # Exact Wuzzuf next button structure
        "button.css-zye1os a",  # Button with link inside
        "a.css-1fcv3il",  # Direct link with Wuzzuf class
        "button[class*='css-zye1os'] a",  # Button with CSS class containing css-zye1os
        "a[aria-label='Next']",
        "a.next",
        "a[rel='next']",
        "button[aria-label='Next']",
        ".pagination a:last-child",
        "a[data-testid='pagination-next']",
        "a[data-testid='next']",
        "a[aria-label='التالي']",  # Arabic next
        "button[aria-label='التالي']",  # Arabic next button
    ]

    for selector in next_page_selectors:
        try:
            next_button = driver.find_element(By.CSS_SELECTOR, selector)
            if next_button.is_enabled() and next_button.is_displayed():
                class_attr = next_button.get_attribute("class")
                if class_attr and "disabled" not in class_attr.lower():
                    next_button.click()
                    time.sleep(3)  # Wait for page to load
                    return True
        except NoSuchElementException:
            continue
    return False


def _try_xpath_next_button(driver: uc.Chrome) -> bool:
    """Try to find and click next button using XPath text search."""
    try:
        next_links = driver.find_elements(
            By.XPATH,
            "//a[contains(text(), 'Next') or contains(text(), 'التالي')]",
        )
        for link in next_links:
            if link.is_enabled() and link.is_displayed():
                class_attr = link.get_attribute("class")
                if class_attr and "disabled" not in class_attr.lower():
                    link.click()
                    time.sleep(3)
                    return True
    except Exception:
        pass
    return False


def _find_next_page_button(driver: uc.Chrome) -> bool:
    """Attempts to find and click the next page button. Returns True if successful."""
    # Try CSS selectors first
    if _try_css_next_button(driver):
        return True

    # If CSS selectors failed, try XPath for text-based search
    return _try_xpath_next_button(driver)


def _process_single_wuzzuf_page(
    driver: uc.Chrome, website_config: dict, page: int
) -> tuple[list, bool]:
    """Process a single page of Wuzzuf jobs."""
    jobs: list[dict] = []
    job_card_selector = website_config["job_card_selector"]

    # Check for blocking before processing
    if detect_blocking(driver):
        logger.warning(f"Blocking detected on page {page}, restarting driver...")
        driver = restart_driver_on_block(driver)
        return jobs, True  # Continue flag

    # Wait for job cards to load
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, job_card_selector))
        )
    except TimeoutException:
        logger.warning(f"Timeout waiting for job cards on page {page}")
        return jobs, False  # Stop flag

    # Get job cards from current page
    job_cards = driver.find_elements(By.CSS_SELECTOR, job_card_selector)
    if not job_cards:
        logger.warning(f"No job cards found on page {page}")
        return jobs, False  # Stop flag

    # Extract jobs from current page with human-like interactions
    page_jobs = 0
    for i, card in enumerate(job_cards):
        try:
            # Simulate mouse movement to the card
            human_like_mouse_movement(driver, card)

            job_details = _extract_job_details_from_card(card, website_config)
            if job_details:
                jobs.append(job_details)
                page_jobs += 1

            # Add small delay between processing cards
            if i % 5 == 0:  # Every 5 cards
                random_delay(0.5, 1.0)

        except Exception as e:
            logger.warning(f"Error processing job card {i} on page {page}: {e}")
            continue

    logger.info(f"Found {page_jobs} jobs on page {page}")
    return jobs, True  # Continue flag


def _scrape_wuzzuf_pages(driver: uc.Chrome, website_config: dict) -> list:
    """Scrape all pages from Wuzzuf with pagination."""
    jobs: list[dict] = []

    page = 1
    max_pages = 50  # Safety limit to prevent infinite loops

    while page <= max_pages:
        logger.info(f"Scraping page {page} from {website_config['name']}")

        page_jobs, should_continue = _process_single_wuzzuf_page(
            driver, website_config, page
        )
        jobs.extend(page_jobs)

        if not should_continue:
            break

        # Try to go to next page
        if not _find_next_page_button(driver):
            logger.info(f"No more pages found after page {page}")
            break

        page += 1
        random_delay(2.0, 4.0)  # Random pause between pages

    logger.info(
        f"Completed pagination scraping: {len(jobs)} total jobs from {page-1} pages"
    )
    return jobs


def _scrape_wuzzuf_with_pagination(driver: uc.Chrome, website_config: dict) -> list:
    """Scrapes jobs from Wuzzuf using pagination to get all pages with stealth measures."""
    return _scrape_wuzzuf_pages(driver, website_config)


def is_job_posting(
    title: str,
    description: str,
    title_keywords: list[str],
    description_keywords: list[str],
) -> bool:
    """
    Determines if a job posting is relevant based on predefined keywords in its title
    and description. Performs case-insensitive matching for robustness.
    """
    title_lower = title.lower()
    description_lower = description.lower()

    if not any(keyword.lower() in title_lower for keyword in title_keywords):
        return False

    if description_keywords:
        if not any(
            keyword.lower() in description_lower for keyword in description_keywords
        ):
            return False

    logger.debug(f"Job '{title}' matches all relevance criteria.")
    return True
