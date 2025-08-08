"""
Job Scraper Module - Backward compatibility layer

This module imports all functions from the split modules to maintain
backward compatibility with existing code.
"""

# Import all functions from data_extractors
from src.data_extractors.data_extractors import (
    _attempt_link_from_card_direct,
    _attempt_link_from_selector,
    _attempt_link_from_title_element,
    _extract_date,
    _extract_description,
    _extract_job_details_from_card,
    _extract_link,
    _extract_tags,
    _extract_title,
    _get_href_from_element,
    parse_date_string,
)

# Import main public interface from job_scraper
from src.scrapers.job_scraper import scrape_jobs_from_website

# Import all functions from pagination
from src.scrapers.pagination import (
    _find_next_page_button,
    _process_single_wuzzuf_page,
    _scrape_wuzzuf_pages,
    _scrape_wuzzuf_with_pagination,
    _try_css_next_button,
    _try_xpath_next_button,
)

# Import all functions from scraping_logic
from src.scrapers.scraping_logic import (
    _handle_general_exception,
    _handle_scraping_retry,
    _handle_timeout_exception,
    _handle_webdriver_exception,
    _perform_initial_scraping_setup,
    _perform_scraping_logic,
    _safe_driver_get,
    _scrape_jobs_with_retry_logic,
    _scrape_single_page_with_scroll,
)

# Import all functions from browser_utils
from src.utils.browser_utils import (
    USER_AGENTS,
    detect_blocking,
    get_selenium_driver,
    human_like_mouse_movement,
    human_like_scroll,
    random_delay,
    restart_driver_on_block,
)

# Re-export all functions for backward compatibility
__all__ = [
    # Browser utilities
    "random_delay",
    "human_like_scroll",
    "human_like_mouse_movement",
    "detect_blocking",
    "get_selenium_driver",
    "restart_driver_on_block",
    "USER_AGENTS",
    # Data extraction functions
    "parse_date_string",
    "_extract_title",
    "_get_href_from_element",
    "_attempt_link_from_selector",
    "_attempt_link_from_title_element",
    "_attempt_link_from_card_direct",
    "_extract_link",
    "_extract_description",
    "_extract_tags",
    "_extract_date",
    "_extract_job_details_from_card",
    # Scraping logic functions
    "_safe_driver_get",
    "_handle_scraping_retry",
    "_handle_timeout_exception",
    "_handle_webdriver_exception",
    "_handle_general_exception",
    "_perform_initial_scraping_setup",
    "_perform_scraping_logic",
    "_scrape_jobs_with_retry_logic",
    "_scrape_single_page_with_scroll",
    # Pagination functions
    "_try_css_next_button",
    "_try_xpath_next_button",
    "_find_next_page_button",
    "_process_single_wuzzuf_page",
    "_scrape_wuzzuf_pages",
    "_scrape_wuzzuf_with_pagination",
    # Main public interface
    "scrape_jobs_from_website",
]
