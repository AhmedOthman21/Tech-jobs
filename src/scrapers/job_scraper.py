"""
Job Scraper - Main Public Interface

This module provides the main public interface for job scraping functionality.
It imports and re-exports functions from the specialized modules.
"""

import logging

import undetected_chromedriver as uc

from src.scrapers.scraping_logic import _scrape_jobs_with_retry_logic
from src.utils.browser_utils import get_selenium_driver

logger = logging.getLogger(__name__)


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

    # Date enhancement removed per request; see backup in
    # src/scrapers/date_enhancement_backup.py if reinstating later.

    return jobs


# Re-export key functions for backward compatibility
__all__ = [
    "scrape_jobs_from_website",
    "get_selenium_driver",
]
