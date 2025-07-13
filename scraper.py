"""
Job Scraper Module - Backward compatibility layer

This module imports all functions from the split modules to maintain
backward compatibility with existing code.
"""

# Import all functions from browser_utils
from browser_utils import (
    random_delay,
    human_like_scroll,
    human_like_mouse_movement,
    detect_blocking,
    get_selenium_driver,
    restart_driver_on_block,
    USER_AGENTS,
)

# Import all functions from data_extractors
from data_extractors import (
    parse_date_string,
    _extract_title,
    _get_href_from_element,
    _attempt_link_from_selector,
    _attempt_link_from_title_element,
    _attempt_link_from_card_direct,
    _extract_link,
    _extract_description,
    _extract_tags,
    _extract_date,
    _extract_job_details_from_card,
    is_job_posting,
)

# Import all functions from scraping_logic
from scraping_logic import (
    _safe_driver_get,
    _handle_scraping_retry,
    _handle_timeout_exception,
    _handle_webdriver_exception,
    _handle_general_exception,
    _perform_initial_scraping_setup,
    _perform_scraping_logic,
    _scrape_jobs_with_retry_logic,
    _scrape_single_page_with_scroll,
    enhance_job_dates_from_pages,
)

# Import all functions from pagination
from pagination import (
    _try_css_next_button,
    _try_xpath_next_button,
    _find_next_page_button,
    _process_single_wuzzuf_page,
    _scrape_wuzzuf_pages,
    _scrape_wuzzuf_with_pagination,
)

# Import main public interface from job_scraper
from job_scraper import scrape_jobs_from_website

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
    "is_job_posting",
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
    "enhance_job_dates_from_pages",
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
