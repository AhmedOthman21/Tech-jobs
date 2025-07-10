import asyncio
import logging
import random
import time
from typing import List, Dict

from config import (
    LOGGER_SETTINGS,
    SCRAPER_SETTINGS,
    WEBDRIVER_SETTINGS,
    WEBSITE_CONFIGS,
    TELEGRAM_SETTINGS,
    GENERAL_SETTINGS,
)
from scraper import get_selenium_driver, scrape_jobs_from_website, is_job_posting
from telegram_notifier import load_posted_job_links, add_posted_job_link, send_telegram_message


# Setup logging based on configurations
def setup_logging():
    logging.basicConfig(
        level=LOGGER_SETTINGS["log_level"],
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(LOGGER_SETTINGS["log_file_path"]),
            logging.StreamHandler(),
        ],
    )


async def main():
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("Starting job scraper application...")
    if GENERAL_SETTINGS["debug_mode"]:
        logger.info("DEBUG_MODE is ENABLED.")

    posted_jobs_file = SCRAPER_SETTINGS["posted_jobs_file"]
    already_posted_links = load_posted_job_links(posted_jobs_file)
    logger.info(f"Loaded {len(already_posted_links)} previously posted job links.")

    all_scraped_jobs: List[Dict] = []
    driver = None
    try:
        # User-Agent for the Selenium driver
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
            )
        }
        driver = get_selenium_driver(headers=headers)

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
                # Add a random delay between website scrapes to mimic human behavior
                time.sleep(random.uniform(5, 10))

        logger.info(f"Total jobs scraped across all sites: {len(all_scraped_jobs)}")

        new_jobs_found = []
        for job in all_scraped_jobs:
            if job["link"] not in already_posted_links:
                if is_job_posting(
                    job.get("title", ""),
                    job.get("description", ""),
                    SCRAPER_SETTINGS["job_title_keywords"],
                    SCRAPER_SETTINGS["job_keywords"],
                ):
                    new_jobs_found.append(job)
                    already_posted_links.add(job["link"])  # Add to the set
                else:
                    logger.debug(f"Job '{job.get('title')}' is not relevant.")
            else:
                logger.debug(f"Job '{job.get('title')}' already posted. Skipping.")

        logger.info(f"Found {len(new_jobs_found)} new relevant jobs.")

        # Send new jobs to Telegram
        if TELEGRAM_SETTINGS["bot_token"] and TELEGRAM_SETTINGS["chat_id"]:
            for job in new_jobs_found:
                success = await send_telegram_message(
                    TELEGRAM_SETTINGS["bot_token"], TELEGRAM_SETTINGS["chat_id"], job
                )
                if success:
                    add_posted_job_link(posted_jobs_file, job["link"])
                await asyncio.sleep(1)  # Delay between messages to avoid rate limits
        else:
            logger.warning(
                "Telegram bot token or chat ID not configured. Skipping Telegram "
                "notifications."
            )

    except Exception as e:
        logger.critical(f"An unhandled error occurred in main: {e}", exc_info=True)
    finally:
        if driver:
            logger.info("Closing Selenium driver.")
            driver.quit()
        logger.info("Job scraper application finished.")


if __name__ == "__main__":
    asyncio.run(main())
    