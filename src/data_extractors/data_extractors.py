import logging
import re
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException

logger = logging.getLogger(__name__)


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
