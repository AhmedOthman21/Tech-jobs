import logging
import re
from datetime import datetime, timedelta
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException, NoSuchElementException

# Configure logging for the scraper module
logger = logging.getLogger(__name__)

def get_selenium_driver(headers: dict):
    """
    Initializes and returns a configured undetected_chromedriver instance.
    Configures browser options for headless operation, user-agent spoofing,
    and anti-detection measures, crucial for web scraping.
    """
    options = uc.ChromeOptions()
    # Essential for running Chromium in a Docker container or headless environments,
    # as root user in Docker often cannot use the sandbox.
    options.add_argument("--no-sandbox") 
    # Prevents Chromium from writing shared memory files to /dev/shm,
    # important for constrained environments like Docker.
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(f"user-agent={headers['User-Agent']}")
    # These arguments attempt to evade detection as an automated browser.
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized") # Useful for consistent page rendering, even if ignored in headless
    options.add_argument("--window-size=1920,1080") # Ensures a consistent viewport size in headless mode
    options.add_argument("--disable-gpu") # Recommended for headless environments to avoid rendering issues
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_argument("--proxy-server='direct://'") # Direct connection, no proxy
    options.add_argument("--proxy-bypass-list=*") # Bypass proxy for all hosts
    options.add_argument("--disable-features=IsolateOrigins,site-per-process")
    options.add_argument("--enable-features=NetworkService,NetworkServiceInProcess")
    options.add_argument("--headless=new") # Explicitly enables the new headless mode for efficiency and stability

    try:
        driver = uc.Chrome(options=options)
        driver.set_page_load_timeout(60) # Set a generous timeout for page loads to prevent hanging
        logger.info("Selenium driver successfully initialized with headless configuration.")
        return driver
    except WebDriverException as e:
        logger.critical(f"Failed to initialize Selenium driver: {e}. Verify Chromium installation, "
                        "undetected-chromedriver compatibility, and system dependencies.", exc_info=True)
        raise # Re-raise to halt execution if driver cannot be initialized
    except Exception as e:
        logger.critical(f"An unexpected error occurred during driver initialization: {e}", exc_info=True)
        raise

def parse_date_string(date_str: str) -> datetime:
    """
    Parses a human-readable date string (e.g., '2 days ago', '1 hour ago') into a datetime object.
    This function handles common relative time formats.
    """
    date_str = date_str.lower()
    
    # Handle "Today" and "Yesterday"
    if "today" in date_str:
        return datetime.now()
    elif "yesterday" in date_str:
        return datetime.now() - timedelta(days=1)

    # Handle numerical relative times (e.g., "5 hours ago", "2 days ago")
    match = re.search(r'(\d+)\s+(minute|hour|day|week|month|year)s?\s+ago', date_str)
    if match:
        value = int(match.group(1))
        unit = match.group(2)
        if unit == 'minute':
            return datetime.now() - timedelta(minutes=value)
        elif unit == 'hour':
            return datetime.now() - timedelta(hours=value)
        elif unit == 'day':
            return datetime.now() - timedelta(days=value)
        elif unit == 'week':
            return datetime.now() - timedelta(weeks=value)
        elif unit == 'month':
            return datetime.now() - timedelta(days=value * 30) # Approximation
        elif unit == 'year':
            return datetime.now() - timedelta(days=value * 365) # Approximation
            
    # If no specific pattern matches, return current time as a fallback
    # A more robust solution might log a warning or raise an error for unparsable dates
    logger.warning(f"Could not parse date string '{date_str}'. Defaulting to current time.")
    return datetime.now()


def scrape_jobs_from_website(driver: uc.Chrome, website_config: dict) -> list:
    """
    Navigates to a specified website and scrapes job postings based on its configuration.
    Utilizes WebDriverWait for robust element location, accounting for dynamic content loading.
    """
    jobs = []
    url = website_config["url"]
    job_card_selector = website_config["job_card_selector"]
    title_selector = website_config["title_selector"]
    link_selector = website_config["link_selector"]
    description_selector = website_config["description_selector"]
    tags_selector = website_config.get("tags_selector") # Optional
    date_selector = website_config.get("date_selector") # Optional

    logger.info(f"Visiting {website_config['name']} ({url}) to scrape job postings.")
    try:
        driver.get(url)
        # Wait for job cards to be present, indicating page content has loaded.
        WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, job_card_selector))
        )
        logger.debug(f"Successfully loaded and found job cards on {website_config['name']}.")

        job_cards = driver.find_elements(By.CSS_SELECTOR, job_card_selector)
        if not job_cards:
            logger.warning(f"No job cards found using selector '{job_card_selector}' on {website_config['name']}.")
            return []

        for i, card in enumerate(job_cards):
            try:
                title_element = card.find_element(By.CSS_SELECTOR, title_selector)
                title = title_element.text.strip()
                link = title_element.get_attribute('href') or card.find_element(By.CSS_SELECTOR, link_selector).get_attribute('href')
                
                description = ""
                try:
                    description_element = card.find_element(By.CSS_SELECTOR, description_selector)
                    description = description_element.text.strip()
                except NoSuchElementException:
                    logger.debug(f"Description not found for job '{title}' on {website_config['name']}. Skipping description extraction.")

                tags = []
                if tags_selector:
                    try:
                        tag_elements = card.find_elements(By.CSS_SELECTOR, tags_selector)
                        tags = [tag.text.strip() for tag in tag_elements if tag.text.strip()]
                    except NoSuchElementException:
                        logger.debug(f"Tags not found for job '{title}' on {website_config['name']}. Skipping tag extraction.")
                
                posted_date = datetime.now() # Default to now
                if date_selector:
                    try:
                        date_element = card.find_element(By.CSS_SELECTOR, date_selector)
                        date_text = date_element.text.strip()
                        posted_date = parse_date_string(date_text)
                    except NoSuchElementException:
                        logger.debug(f"Posted date not found for job '{title}' on {website_config['name']}. Defaulting to current time.")
                    except Exception as e:
                        logger.warning(f"Error parsing date for job '{title}': {e}. Defaulting to current time.")

                jobs.append({
                    "title": title,
                    "link": link,
                    "description": description,
                    "source": website_config["name"],
                    "tags": tags,
                    "posted_date": posted_date.isoformat() # Store as ISO format string for consistency
                })
                logger.debug(f"Extracted job: '{title}' from {website_config['name']}.")

            except NoSuchElementException as e:
                logger.warning(f"Skipping job card {i+1} on {website_config['name']} due to missing element: {e}. Card HTML might be malformed.")
            except Exception as e:
                logger.warning(f"An unexpected error occurred while processing job card {i+1} on {website_config['name']}: {e}", exc_info=True)

    except TimeoutException:
        logger.error(f"Timeout while loading or finding elements on {website_config['name']} ({url}). Page might not have loaded correctly or selectors are invalid.")
    except WebDriverException as e:
        logger.error(f"WebDriver error during scraping {website_config['name']}: {e}", exc_info=True)
    except Exception as e:
        logger.critical(f"An unhandled error occurred during scraping of {website_config['name']}: {e}", exc_info=True)

    logger.info(f"Finished scraping {len(jobs)} jobs from {website_config['name']}.")
    return jobs

def is_job_posting(title: str, description: str, title_keywords: list, description_keywords: list) -> bool:
    """
    Determines if a job posting is relevant based on predefined keywords in its title and description.
    Performs case-insensitive matching for robustness.
    """
    title_lower = title.lower()
    description_lower = description.lower()

    # Check for title keywords (typically more critical for initial filtering)
    if not any(keyword.lower() in title_lower for keyword in title_keywords):
        return False # No relevant title keyword found

    # Check for description keywords (more detailed filtering)
    if not any(keyword.lower() in description_lower for keyword in description_keywords):
        return False # No relevant description keyword found

    logger.debug(f"Job '{title}' matches all relevance criteria.")
    return True