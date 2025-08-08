import asyncio
import logging
import os
import random
import time
from typing import Dict, List, Set

from config import (
    GENERAL_SETTINGS,
    LOGGER_SETTINGS,
    SCRAPER_SETTINGS,
    TELEGRAM_SETTINGS,
    WEBSITE_CONFIGS,
)
from src.scrapers.scraper import scrape_jobs_from_website
from src.utils.browser_utils import get_selenium_driver
from src.utils.telegram_notifier import (
    add_posted_job_link,
    load_posted_job_links,
    send_telegram_message,
)


# Setup logging based on configurations
def setup_logging() -> None:
    logging.basicConfig(
        level=LOGGER_SETTINGS["log_level"],
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(LOGGER_SETTINGS["log_file_path"]),
            logging.StreamHandler(),
        ],
    )


def process_scraped_jobs(
    all_scraped_jobs: List[Dict], already_posted_links: Set[str]
) -> List[Dict]:
    """
    Filters scraped jobs to remove duplicates.
    """
    logger = logging.getLogger(__name__)
    new_jobs = []
    for job in all_scraped_jobs:
        if job["link"] not in already_posted_links:
            new_jobs.append(job)
            already_posted_links.add(job["link"])
        else:
            logger.debug(f"Job '{job.get('title')}' already posted. Skipping.")
    return new_jobs


async def notify_new_jobs(new_jobs: List[Dict], posted_jobs_file: str) -> None:
    """
    Sends new job postings to Telegram and records them.
    Uses adaptive delays to avoid rate limits.
    """
    logger = logging.getLogger(__name__)
    if TELEGRAM_SETTINGS["bot_token"] and TELEGRAM_SETTINGS["chat_id"]:
        base_delay = 3  # Start with 3 second delay
        for i, job in enumerate(new_jobs):
            try:
                success = await send_telegram_message(
                    str(TELEGRAM_SETTINGS["bot_token"] or ""),
                    str(TELEGRAM_SETTINGS["chat_id"] or ""),
                    job,
                    bool(TELEGRAM_SETTINGS["include_date_in_message"]),
                )
                if success:
                    add_posted_job_link(posted_jobs_file, job["link"])

                # Adaptive delay: increase if we're sending many messages
                if i > 0 and i % 10 == 0:
                    base_delay = min(base_delay + 2, 10)  # Increase delay up to max 10s
                await asyncio.sleep(base_delay)  # Adaptive delay between messages

            except Exception as e:
                if "RetryAfter" in str(e):
                    retry_after = int(str(e).split()[-2])  # Extract seconds from error
                    logger.info(f"Rate limit hit, waiting {retry_after} seconds...")
                    await asyncio.sleep(
                        retry_after + 1
                    )  # Wait the required time plus 1s
                    # Retry this message
                    success = await send_telegram_message(
                        str(TELEGRAM_SETTINGS["bot_token"] or ""),
                        str(TELEGRAM_SETTINGS["chat_id"] or ""),
                        job,
                        bool(TELEGRAM_SETTINGS["include_date_in_message"]),
                    )
                    if success:
                        add_posted_job_link(posted_jobs_file, job["link"])
                else:
                    logger.error(
                        f"Error sending message for job {job.get('title')}: {e}"
                    )
    else:
        logger.warning(
            "Telegram bot token or chat ID not configured. Skipping Telegram "
            "notifications."
        )


async def main() -> None:
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("Starting job scraper application...")
    if GENERAL_SETTINGS["debug_mode"]:
        logger.info("DEBUG_MODE is ENABLED.")

    posted_jobs_file = SCRAPER_SETTINGS["posted_jobs_file"]
    if isinstance(posted_jobs_file, list):
        posted_jobs_file_path = posted_jobs_file[0]
    else:
        posted_jobs_file_path = posted_jobs_file
    already_posted_links = load_posted_job_links(posted_jobs_file_path)
    logger.info(f"Loaded {len(already_posted_links)} previously posted job links.")

    all_scraped_jobs: List[Dict] = []
    driver = None
    try:
        # Minimal Windows fix: pin UC driver to current Chrome major if not provided
        if os.name == "nt" and not os.environ.get("UC_CHROME_VERSION_MAIN"):
            os.environ["UC_CHROME_VERSION_MAIN"] = "138"
        driver = get_selenium_driver()

        for website_config in WEBSITE_CONFIGS:
            site_name = website_config["name"]
            logger.info(f"Initiating scraping for {site_name}...")

            try:
                jobs = scrape_jobs_from_website(driver, website_config)
                all_scraped_jobs.extend(jobs)
                logger.info(f"Successfully scraped {len(jobs)} jobs from {site_name}.")
            except Exception as e:
                logger.error(
                    f"Failed to scrape jobs from {site_name}: {e}", exc_info=True
                )
            finally:
                time.sleep(random.uniform(5, 10))  # Delay between website scrapes

        logger.info(f"Total jobs scraped across all sites: {len(all_scraped_jobs)}")

        new_jobs_found = process_scraped_jobs(all_scraped_jobs, already_posted_links)
        logger.info(f"Found {len(new_jobs_found)} new relevant jobs.")

        await notify_new_jobs(new_jobs_found, posted_jobs_file_path)

    except Exception as e:
        logger.critical(f"An unhandled error occurred in main: {e}", exc_info=True)
    finally:
        if driver:
            logger.info("Closing Selenium driver.")
            driver.quit()
        logger.info("Job scraper application finished.")


if __name__ == "__main__":
    asyncio.run(main())
