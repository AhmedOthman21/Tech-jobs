import logging
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    WebDriverException,
    TimeoutException,
)

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from src.utils.browser_utils import (
    random_delay,
    human_like_scroll,
    human_like_mouse_movement,
    detect_blocking,
    get_selenium_driver,
    restart_driver_on_block,
)
from src.data_extractors.data_extractors import _extract_job_details_from_card
from src.scrapers.pagination import _scrape_wuzzuf_with_pagination

logger = logging.getLogger(__name__)


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


def enhance_job_dates_from_pages(  # noqa: C901
    driver: uc.Chrome, jobs: list, site_name: str
) -> list:
    enhanced_jobs = []
    current_driver = driver
    batch_size = 5  # Process jobs in batches to balance speed and reliability

    for i in range(0, len(jobs), batch_size):
        batch = jobs[i : i + batch_size]
        for job in batch:
            if job.get("posted_date") == "Recently":
                retry_count = 0
                max_retries = 3

                while retry_count < max_retries:
                    try:
                        logger.debug(
                            f"Enhancing date for job: {job.get('title', 'Unknown')}"
                        )
                        random_delay(0.5, 1.0)  # Reduced delay

                        try:
                            current_driver.get(job["link"])
                        except WebDriverException:
                            logger.info("Session expired, creating new driver...")
                            if current_driver != driver:
                                try:
                                    current_driver.quit()
                                except Exception:
                                    pass
                            current_driver = get_selenium_driver()
                            current_driver.get(job["link"])

                        if detect_blocking(current_driver):
                            logger.warning(
                                f"Blocking detected while enhancing date for job on {site_name}"
                            )
                            if retry_count < max_retries - 1:
                                retry_count += 1
                                random_delay(2.0, 4.0)  # Reduced backoff
                                continue
                            break

                        # Reduced timeout from 10s to 5s
                        date_elem = WebDriverWait(current_driver, 5).until(
                            EC.presence_of_element_located(
                                (By.CSS_SELECTOR, ".css-182mrdn")
                            )
                        )

                        enhanced_date = date_elem.text.strip()
                        job["posted_date"] = enhanced_date
                        logger.debug(f"Enhanced date: {enhanced_date}")
                        break

                    except Exception as e:
                        logger.warning(
                            f"Error enhancing date for job on {site_name}: {e}"
                        )
                        if retry_count < max_retries - 1:
                            retry_count += 1
                            random_delay(2.0, 4.0)
                            continue
                        break

            enhanced_jobs.append(job)

        # Small delay between batches
        random_delay(1.0, 2.0)

    if current_driver != driver:
        try:
            current_driver.quit()
        except Exception:
            pass

    return enhanced_jobs
