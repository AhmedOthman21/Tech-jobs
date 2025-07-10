import logging
import re
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
        return card.find_element(By.CSS_SELECTOR, selector).text.strip()
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
        if link:
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

    # Try title element itself
    link = _get_href_from_element(title_element, site_name, "title element (direct)")
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
    return _get_href_from_element(card, site_name, "card element (direct a)")


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
        return card.find_element(By.CSS_SELECTOR, selector).text.strip()
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


def _extract_date(card: WebElement, selector: str | None, site_name: str) -> datetime:
    """Extracts job posted date from the card."""
    if not selector:
        return datetime.now()
    try:
        date_element = card.find_element(By.CSS_SELECTOR, selector)
        date_text = date_element.text.strip()
        return parse_date_string(date_text, date_element=date_element)
    except NoSuchElementException:
        logger.debug(
            f"Posted date not found on {site_name} for a job card. "
            "Defaulting to current time."
        )
        return datetime.now()
    except Exception as e:
        logger.warning(
            f"Error parsing date on {site_name} for a job card: {e}. "
            "Defaulting to current time."
        )
        return datetime.now()


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
            "posted_date": posted_date.isoformat(),
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
    accounting for dynamic content loading.
    """
    jobs = []
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
    return jobs


def is_job_posting(
    title: str, description: str, title_keywords: list, description_keywords: list
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
