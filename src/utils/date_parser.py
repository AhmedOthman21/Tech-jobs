import logging
import re
from datetime import datetime, timedelta

from selenium.webdriver.remote.webelement import WebElement

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
