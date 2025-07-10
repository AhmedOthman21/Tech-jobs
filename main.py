import asyncio
from datetime import datetime
import logging
import os # Required for environment variable access for debug mode
import re # Not directly used in main.py, but often useful for string manipulation
from datetime import timedelta # Explicitly imported as a dependency for other modules like scraper.py if date parsing is involved
from selenium.common.exceptions import WebDriverException, TimeoutException

# Import core configuration and utility modules
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, JOB_WEBSITES, JOB_KEYWORDS, JOB_TITLE_KEYWORDS, HEADERS, POSTED_JOBS_FILE
from scraper import get_selenium_driver, scrape_jobs_from_website, is_job_posting
from telegram_notifier import send_telegram_message, load_posted_job_links, add_posted_job_link


# --- Logging Configuration ---
# Configure robust logging for operational visibility and debugging.
# Log level is dynamically set based on environment variable to facilitate debugging in different environments (local, CI/CD).
LOG_LEVEL = logging.DEBUG if os.getenv("DEBUG_ENABLED", "false").lower() == "true" else logging.INFO
logging.basicConfig(level=LOG_LEVEL, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    """
    Orchestrates the job scraping, filtering, and notification process.
    Handles driver lifecycle, error reporting, and duplicate job management.
    """
    logger.info(f"Initiating job search and notification cycle at {datetime.now()}")

    all_found_jobs = []
    driver = None # Ensure driver is initialized to None for proper cleanup in finally block
    
    # Load previously posted job links to prevent duplicate notifications.
    # This state is persisted across runs, crucial for long-term operation.
    posted_job_links = load_posted_job_links(POSTED_JOBS_FILE)
    logger.debug(f"Loaded {len(posted_job_links)} existing posted job links.")

    try:
        # Validate critical Telegram credentials. Without these, notification cannot proceed.
        if TELEGRAM_BOT_TOKEN is None:
            logger.critical("TELEGRAM_BOT_TOKEN is not configured. Aborting job search.")
            return
        if TELEGRAM_CHAT_ID is None:
            logger.critical("TELEGRAM_CHAT_ID is not configured. Aborting job search.")
            return

        # Initialize Selenium WebDriver. This step is critical and can fail if browser setup is incorrect.
        driver = get_selenium_driver(HEADERS, run_headless=False)

        # Iterate through configured job websites and scrape postings.
        # This aggregates all raw job data before filtering.
        for website_config in JOB_WEBSITES:
            logger.debug(f"Attempting to scrape from: {website_config['name']} ({website_config['url']})")
            jobs_from_site = scrape_jobs_from_website(driver, website_config)
            all_found_jobs.extend(jobs_from_site)
            logger.debug(f"Found {len(jobs_from_site)} jobs from {website_config['name']}.")

        # Filter jobs based on predefined keywords and check for duplicates.
        # Only truly new and relevant jobs proceed to notification.
        new_relevant_job_postings = []
        for job in all_found_jobs:
            if is_job_posting(job["title"], job["description"], JOB_TITLE_KEYWORDS, JOB_KEYWORDS):
                logger.debug(f"Job identified as relevant: {job['title']} (Link: {job['link']})")
                if job["link"] not in posted_job_links:
                    new_relevant_job_postings.append(job)
                else:
                    logger.info(f"Skipping duplicate job: '{job['title']}' (Link: {job['link']}) - already notified.")
            else:
                logger.debug(f"Job NOT relevant based on criteria: '{job['title']}' (Source: {job['source']})")

        # Handle notification logic based on findings.
        if not new_relevant_job_postings:
            logger.info("No NEW relevant job postings found in this cycle. Sending an informational message.")
            # Sending 'No New Jobs' helps confirm the script ran, without spamming.
            await send_telegram_message(
                bot_token=TELEGRAM_BOT_TOKEN,
                chat_id=TELEGRAM_CHAT_ID,
                job_post={
                    "title": "No New Jobs Today",
                    "link": "#", # Placeholder link as no specific job applies
                    "description": "No new job postings found for your criteria in this run.",
                    "source": "Job Scraper",
                    "tags": [],
                    "posted_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            )
        else:
            logger.info(f"Identified {len(new_relevant_job_postings)} NEW relevant job postings. Initiating Telegram notifications...")
            # Send each new relevant job and record its link to prevent future duplicates.
            for job_post in new_relevant_job_postings:
                logger.debug(f"Attempting to send Telegram message for: '{job_post['title']}'")
                message_sent = await send_telegram_message(
                    bot_token=TELEGRAM_BOT_TOKEN,
                    chat_id=TELEGRAM_CHAT_ID,
                    job_post=job_post
                )
                if message_sent:
                    add_posted_job_link(POSTED_JOBS_FILE, job_post["link"])
                    posted_job_links.add(job_post["link"]) # Update in-memory set to prevent duplicates within the same run
                    logger.debug(f"Successfully sent and recorded job link: {job_post['link']}")
                else:
                    logger.warning(f"Failed to send Telegram message for '{job_post['title']}'. This job will NOT be marked as posted and may be resent.")

    except Exception as e:
        # Catch any unexpected exceptions during the main execution flow.
        logger.critical(f"An unhandled exception occurred during main execution: {e}", exc_info=True)
    finally:
        # Ensure the Selenium WebDriver is properly closed to release resources, regardless of success or failure.
        if driver:
            try:
                driver.quit()
                logger.info("Selenium driver successfully terminated.")
            except WebDriverException as e:
                logger.warning(f"WebDriverException during driver.quit(): {e}. This might indicate the browser process was already closed or an invalid session.")
            except OSError as e:
                logger.warning(f"OSError during driver.quit() (e.g., 'Handle invalid' on Windows): {e}. This suggests a system-level issue with process management.")
            except Exception as e:
                logger.warning(f"An unforeseen error occurred while attempting to quit the driver: {e}")

    logger.info("Job search and notification cycle complete.")

if __name__ == "__main__":
    # Entry point for the script. Handles graceful shutdown on KeyboardInterrupt.
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Script execution interrupted by user (KeyboardInterrupt). Shutting down gracefully.")
    except Exception as e:
        # Catch any exceptions occurring outside the main async function call.
        logger.critical(f"An unexpected error occurred during script initialization or shutdown: {e}", exc_info=True)