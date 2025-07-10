import asyncio
from datetime import datetime
import logging
import re
from datetime import timedelta # Needed for parse_date_string in scraper.py if it's there
from selenium.common.exceptions import WebDriverException, TimeoutException # Ensure WebDriverException is here

# Import modules
# Add POSTED_JOBS_FILE to the import list from config
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, JOB_WEBSITES, JOB_KEYWORDS, JOB_TITLE_KEYWORDS, HEADERS, POSTED_JOBS_FILE
# Add load_posted_job_links and add_posted_job_link to the import list from telegram_notifier
from scraper import get_selenium_driver, scrape_jobs_from_website, is_job_posting
from telegram_notifier import send_telegram_message, load_posted_job_links, add_posted_job_link


# --- Logging Configuration ---
# Configure logging to show info messages and above in the console
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    """
    Main function to fetch jobs, identify relevant ones, and send to Telegram.
    """
    logger.info(f"Starting job search and notification at {datetime.now()}")

    all_found_jobs = []
    driver = None # Initialize driver to None
    
    # Load existing posted job links at the start of the run
    posted_job_links = load_posted_job_links(POSTED_JOBS_FILE)

    try:
        if TELEGRAM_BOT_TOKEN is None:
            logger.critical("TELEGRAM_BOT_TOKEN is not set. Please provide a valid Telegram bot token in config.py.")
            return
        if TELEGRAM_CHAT_ID is None:
            logger.critical("TELEGRAM_CHAT_ID is not set. Please provide a valid Telegram chat ID in config.py.")
            return

        driver = get_selenium_driver(HEADERS) # Get the configured Selenium driver

        for website_config in JOB_WEBSITES:
            jobs_from_site = scrape_jobs_from_website(driver, website_config)
            all_found_jobs.extend(jobs_from_site)

        new_relevant_job_postings = [] # Renamed for clarity: these are truly *new* jobs
        for job in all_found_jobs:
            if is_job_posting(job["title"], job["description"], JOB_TITLE_KEYWORDS, JOB_KEYWORDS):
                # Check if the job link has been posted before
                if job["link"] not in posted_job_links:
                    new_relevant_job_postings.append(job)
                else:
                    logger.info(f"Skipping duplicate job: {job['title']} (Link: {job['link']})")

        if not new_relevant_job_postings:
            logger.info("No NEW relevant job postings found today for your criteria.")
            # Only send "No New Jobs" message if no jobs were found AT ALL, or if all found were duplicates.
            # To avoid spamming, we might only send this once a day or not at all.
            # For now, if no new jobs, we can send a message.
            # You can add logic here to prevent daily "no new jobs" if desired.
            # You might also want to check if a "No New Jobs" message was already sent recently
            # to avoid sending it on every single run where no new jobs are found.
            await send_telegram_message(
                bot_token=TELEGRAM_BOT_TOKEN,
                chat_id=TELEGRAM_CHAT_ID,
                job_post={
                    "title": "No New Jobs Today", # Slightly changed title
                    "link": "#",
                    "description": "No new job postings found for your criteria in this run.",
                    "source": "Job Scraper",
                    "tags": [],
                    "posted_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            )
        else:
            logger.info(f"Found {len(new_relevant_job_postings)} NEW relevant job postings. Sending to Telegram...")
            for job_post in new_relevant_job_postings:
                # Send message and record link only if sending was successful
                message_sent = await send_telegram_message(
                    bot_token=TELEGRAM_BOT_TOKEN,
                    chat_id=TELEGRAM_CHAT_ID,
                    job_post=job_post
                )
                if message_sent:
                    add_posted_job_link(POSTED_JOBS_FILE, job_post["link"])
                    posted_job_links.add(job_post["link"]) # Also add to the in-memory set to prevent duplicates within the same run

    except Exception as e:
        logger.critical(f"An unexpected error occurred in main execution: {e}", exc_info=True)
    finally:
        if driver:
            try:
                driver.quit()
                logger.info("Selenium driver quit successfully.")
            except WebDriverException as e:
                logger.warning(f"Error during driver.quit() (WebDriverException): {e}")
            except OSError as e:
                logger.warning(f"OSError during driver.quit() (Handle invalid): {e}. This might be a system-level issue on Windows.")
            except Exception as e: # Catch any other unexpected exceptions during quit
                logger.warning(f"An unknown error occurred during driver.quit(): {e}")


    logger.info("Job search and notification complete.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Script stopped by user.")
    except Exception as e:
        logger.critical(f"An unexpected error occurred outside main: {e}", exc_info=True)