import logging
import re
import time
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

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)


logger = logging.getLogger(__name__)


def get_selenium_driver(headers: dict):
    """
    Initializes and returns a configured undetected_chromedriver instance.
    Configures browser options for headless operation, user-agent spoofing,
    and anti-detection measures, crucial for web scraping.
    """
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(f"user-agent={headers['User-Agent']}")
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

    try:
        driver = uc.Chrome(options=options)
        driver.set_page_load_timeout(60)
        logger.info(
            "Selenium driver successfully initialized with headless configuration."
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
    """Enhance job dates by visiting job pages for jobs that show 'Recently'."""
    enhanced_jobs = []

    for job in jobs:
        if job.get("posted_date") == "Recently":
            try:
                logger.debug(f"Enhancing date for job: {job.get('title', 'Unknown')}")
                driver.get(job["link"])

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

    return enhanced_jobs


def _extract_date(card: WebElement, selector: str | None, site_name: str) -> str:
    """Extracts job posted date from the card as relative text."""
    if not selector:
        return "Recently"
    try:
        date_element = card.find_element(By.CSS_SELECTOR, selector)
        date_text = date_element.text.strip()
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
    """Wrapper for driver.get() with retry logic."""
    logger.info(f"Attempting to navigate to {url}")
    driver.get(url)
    logger.info(f"Successfully navigated to {url}")


def scrape_jobs_from_website(driver: uc.Chrome, website_config: dict) -> list:
    """
    Navigates to a specified website and scrapes job postings based on its
    configuration. Utilizes WebDriverWait for robust element location,
    accounting for dynamic content loading and pagination.
    """
    jobs: list = []
    url = website_config["url"]
    site_name = website_config["name"]
    job_card_selector = website_config["job_card_selector"]

    logger.info(f"Visiting {site_name} ({url}) to scrape job postings.")
    try:
        _safe_driver_get(driver, url)

        WebDriverWait(driver, 40).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, job_card_selector))
        )
        logger.debug(f"Successfully loaded and found job cards on {site_name}.")

        # Handle pagination for Wuzzuf sites
        if "wuzzuf.net" in url:
            jobs = _scrape_wuzzuf_with_pagination(driver, website_config)
        else:
            # For other sites, use the original scrolling method
            jobs = _scrape_single_page_with_scroll(driver, website_config)

    except TimeoutException:
        logger.error(
            f"Timeout while loading or finding elements on {site_name} ({url}). "
            "Page might not have loaded correctly or selectors are invalid after "
            "40 seconds."
        )
    except WebDriverException as e:
        logger.error(f"WebDriver error during scraping {site_name}: {e}", exc_info=True)
    except Exception as e:
        logger.critical(
            f"An unhandled error occurred during scraping of {site_name}: {e}",
            exc_info=True,
        )

    logger.info(f"Finished scraping {len(jobs)} jobs from {site_name}.")

    # Enhance dates for jobs that show 'Recently'
    if jobs and "wuzzuf.net" in url:
        logger.info(f"Enhancing dates for {site_name} jobs...")
        jobs = enhance_job_dates_from_pages(driver, jobs, site_name)
        logger.info(f"Date enhancement completed for {site_name}")

    return jobs


def _scrape_single_page_with_scroll(driver: uc.Chrome, website_config: dict) -> list:
    """Scrapes jobs from a single page using scrolling to load more content."""
    jobs: list = []
    site_name = website_config["name"]
    job_card_selector = website_config["job_card_selector"]

    # Scroll to load more jobs
    from config import ScraperConfig

    max_scroll_pauses = ScraperConfig.MAX_SCROLL_PAUSES
    scroll_pause_time = ScraperConfig.SCROLL_PAUSE_TIME

    for scroll_attempt in range(max_scroll_pauses):
        # Scroll to bottom to load more content
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause_time)

        # Check if new jobs were loaded
        current_job_cards = driver.find_elements(By.CSS_SELECTOR, job_card_selector)
        logger.debug(
            f"Scroll attempt {scroll_attempt + 1}: Found {len(current_job_cards)} job cards"
        )

        if len(current_job_cards) > len(jobs):
            logger.debug(f"New jobs loaded after scroll {scroll_attempt + 1}")
        else:
            logger.debug(f"No new jobs loaded after scroll {scroll_attempt + 1}")

    job_cards = driver.find_elements(By.CSS_SELECTOR, job_card_selector)
    if not job_cards:
        logger.warning(
            f"No job cards found using selector '{job_card_selector}' on "
            f"{site_name}. This might indicate a selector issue or no jobs."
        )
        return []

    for card in job_cards:
        job_details = _extract_job_details_from_card(card, website_config)
        if job_details:
            jobs.append(job_details)

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


def _scrape_wuzzuf_with_pagination(driver: uc.Chrome, website_config: dict) -> list:
    """Scrapes jobs from Wuzzuf using pagination to get all pages."""
    jobs = []
    site_name = website_config["name"]
    job_card_selector = website_config["job_card_selector"]

    page = 1
    max_pages = 50  # Safety limit to prevent infinite loops

    while page <= max_pages:
        logger.info(f"Scraping page {page} from {site_name}")

        # Wait for job cards to load
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, job_card_selector)
                )
            )
        except TimeoutException:
            logger.warning(f"Timeout waiting for job cards on page {page}")
            break

        # Get job cards from current page
        job_cards = driver.find_elements(By.CSS_SELECTOR, job_card_selector)
        if not job_cards:
            logger.warning(f"No job cards found on page {page}")
            break

        # Extract jobs from current page
        page_jobs = 0
        for card in job_cards:
            job_details = _extract_job_details_from_card(card, website_config)
            if job_details:
                jobs.append(job_details)
                page_jobs += 1

        logger.info(f"Found {page_jobs} jobs on page {page}")

        # Try to go to next page
        if not _find_next_page_button(driver):
            logger.info(f"No more pages found after page {page}")
            break

        page += 1
        time.sleep(2)  # Brief pause between pages

    logger.info(
        f"Completed pagination scraping: {len(jobs)} total jobs from {page-1} pages"
    )
    return jobs


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
