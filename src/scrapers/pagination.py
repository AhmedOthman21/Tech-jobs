import logging
import time

import undetected_chromedriver as uc
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.data_extractors.data_extractors import _extract_job_details_from_card
from src.utils.browser_utils import (
    detect_blocking,
    human_like_mouse_movement,
    random_delay,
    restart_driver_on_block,
)

logger = logging.getLogger(__name__)

MAX_PAGES_PER_SITE = 25  # default safety limit


def _try_css_next_button(driver: uc.Chrome) -> bool:
    """Try to find and click next button using CSS selectors."""
    next_page_selectors = [
        "button.css-wq4g8g a.css-1fcv3il",  # New Wuzzuf specific next button selector
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
        "a.css-1evf01f",  # New Wuzzuf next button selector
        "button.css-1evf01f a",  # New Wuzzuf next button selector 2
    ]

    for selector in next_page_selectors:
        try:
            next_button = driver.find_element(By.CSS_SELECTOR, selector)
            if next_button.is_enabled() and next_button.is_displayed():
                class_attr = next_button.get_attribute("class")
                if class_attr and "disabled" not in class_attr.lower():
                    next_button.click()
                    random_delay(3, 5)  # Increased wait for page to load after click
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
        WebDriverWait(driver, 30).until(
            EC.visibility_of_all_elements_located((By.CSS_SELECTOR, job_card_selector))
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
    # Custom limit: Wuzzuf IT should stop at 25 pages
    if website_config.get("name", "").lower().startswith("wuzzuf it"):
        max_pages = 25
    else:
        max_pages = MAX_PAGES_PER_SITE

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
