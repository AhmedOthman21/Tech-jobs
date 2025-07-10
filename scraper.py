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

def parse_date_string(date_str: str, date_element=None) -> datetime:
    """
    Parses a human-readable date string (e.g., '2 days ago', '1 hour ago', 'منذ 2 يوم')
    or extracts from a datetime attribute if date_element is provided.
    """
    date_str_lower = date_str.lower()

    # Try to extract from 'datetime' attribute first if element is provided
    if date_element and date_element.tag_name == 'time':
        datetime_attr = date_element.get_attribute('datetime')
        if datetime_attr:
            try:
                return datetime.fromisoformat(datetime_attr.replace('Z', '+00:00'))
            except ValueError:
                pass # Fallback to text parsing if datetime attribute is malformed

    # Handle "Today" and "Yesterday"
    if "today" in date_str_lower:
        return datetime.now()
    elif "yesterday" in date_str_lower:
        return datetime.now() - timedelta(days=1)

    # Handle numerical relative times (e.g., "5 hours ago", "2 days ago", "30+ days ago")
    # For English
    match_en = re.search(r'(\d+)\s+(minute|hour|day|week|month|year)s?\s+ago', date_str_lower)
    if match_en:
        value = int(match_en.group(1))
        unit = match_en.group(2)
        if unit == 'minute':
            return datetime.now() - timedelta(minutes=value)
        elif unit == 'hour':
            return datetime.now() - timedelta(hours=value)
        elif unit == 'day':
            return datetime.now() - timedelta(days=value)
        elif unit == 'week':
            return datetime.now() - timedelta(weeks=value)
        elif unit == 'month':
            return datetime.now() - timedelta(days=value * 30.437) # Average days in a month
        elif unit == 'year':
            return datetime.now() - timedelta(days=value * 365.25) # Average days in a year
    
    # Handle "30+ days ago" (NaukriGulf)
    if "30+ days ago" in date_str_lower:
        return datetime.now() - timedelta(days=30) # Treat as 30 days ago or more

    # Handle Arabic relative times (Forasna: "منذ X يوم", "منذ X شهر")
    # Example: "منذ 2 يوم" (2 days ago), "منذ 1 شهر" (1 month ago)
    match_ar = re.search(r'منذ\s+(\d+)\s+(يوم|أيام|شهر|شهور|ساعة|ساعات|دقيقة|دقائق)', date_str)
    if match_ar:
        value = int(match_ar.group(1))
        unit_ar = match_ar.group(2)
        if unit_ar in ['يوم', 'أيام']:
            return datetime.now() - timedelta(days=value)
        elif unit_ar in ['شهر', 'شهور']:
            return datetime.now() - timedelta(days=value * 30.437) # Approximation
        elif unit_ar in ['ساعة', 'ساعات']:
            return datetime.now() - timedelta(hours=value)
        elif unit_ar in ['دقيقة', 'دقائق']:
            return datetime.now() - timedelta(minutes=value)

    # Handle month-day formats (e.g., "Jul 09") - assuming current year
    # This might be less precise if the year isn't explicitly given and it's from previous year
    month_day_match = re.search(r'([A-Za-z]{3})\s+(\d{1,2})', date_str)
    if month_day_match:
        try:
            month_name = month_day_match.group(1)
            day = int(month_day_match.group(2))
            current_year = datetime.now().year
            # Attempt to parse assuming current year
            dt_obj = datetime.strptime(f"{month_name} {day} {current_year}", "%b %d %Y")
            # If the parsed date is in the future, assume it's from the previous year
            if dt_obj > datetime.now():
                dt_obj = datetime.strptime(f"{month_name} {day} {current_year - 1}", "%b %d %Y")
            return dt_obj
        except ValueError:
            pass # Fallback to default if parsing fails


    # If no specific pattern matches, return current time as a fallback
    logger.warning(f"Could not parse date string '{date_str}'. Defaulting to current time.")
    return datetime.now()


def scrape_jobs_from_website(driver: uc.Chrome, website_config: dict) -> list:
    """
    Navigates to a specified website and scrapes job postings based on its configuration.
    Utilizes WebDriverWait for robust element location, accounting for dynamic content loading.
    """
    jobs = []
    url = website_config["url"]
    site_name = website_config["name"]
    job_card_selector = website_config["job_card_selector"]
    title_selector = website_config["title_selector"]
    link_selector = website_config.get("link_selector")
    description_selector = website_config.get("description_selector")
    tags_selector = website_config.get("tags_selector")
    date_selector = website_config.get("date_selector")

    logger.info(f"Visiting {site_name} ({url}) to scrape job postings.")
    try:
        driver.get(url)
        
        # Increased wait time for job cards to be present.
        # This will wait up to 40 seconds for AT LEAST ONE job card to appear.
        WebDriverWait(driver, 40).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, job_card_selector))
        )
        logger.debug(f"Successfully loaded and found job cards on {site_name}.")

        job_cards = driver.find_elements(By.CSS_SELECTOR, job_card_selector)
        if not job_cards:
            logger.warning(f"No job cards found using selector '{job_card_selector}' on {site_name}. This might indicate a selector issue or no jobs.")
            return []

        for i, card in enumerate(job_cards):
            title = ""
            link = ""
            description = ""
            tags = []
            posted_date = datetime.now() # Default to now

            try:
                # 1. Extract Title
                title_element = card.find_element(By.CSS_SELECTOR, title_selector)
                title = title_element.text.strip()
                
                # 2. Extract Link
                if link_selector: # If a specific link selector is provided
                    try:
                        link_element = card.find_element(By.CSS_SELECTOR, link_selector)
                        link = link_element.get_attribute('href')
                    except NoSuchElementException:
                        logger.debug(f"Specific link element not found for job '{title}' on {site_name}. Trying title element href.")
                        link = title_element.get_attribute('href')
                else: # If no specific link_selector, try title_element or the card itself (e.g., Forasna)
                    link = title_element.get_attribute('href')
                    if not link and card.tag_name == 'a': # For cases like Forasna where the card itself is the link
                        link = card.get_attribute('href')
                
                if not link:
                    logger.warning(f"Could not find link for job '{title}' on {site_name}. Skipping this job.")
                    continue # Skip this job if no link is found

                # 3. Extract Description
                if description_selector:
                    try:
                        description_element = card.find_element(By.CSS_SELECTOR, description_selector)
                        description = description_element.text.strip()
                    except NoSuchElementException:
                        logger.debug(f"Description not found for job '{title}' on {site_name}. Skipping description extraction.")

                # 4. Extract Tags
                if tags_selector:
                    try:
                        tag_elements = card.find_elements(By.CSS_SELECTOR, tags_selector)
                        tags = [tag.text.strip() for tag in tag_elements if tag.text.strip()]
                    except NoSuchElementException:
                        logger.debug(f"Tags not found for job '{title}' on {site_name}. Skipping tag extraction.")
                
                # 5. Extract Date
                if date_selector:
                    try:
                        date_element = card.find_element(By.CSS_SELECTOR, date_selector)
                        date_text = date_element.text.strip()
                        posted_date = parse_date_string(date_text, date_element=date_element)
                    except NoSuchElementException:
                        logger.debug(f"Posted date not found for job '{title}' on {site_name}. Defaulting to current time.")
                    except Exception as e:
                        logger.warning(f"Error parsing date for job '{title}' on {site_name}: {e}. Defaulting to current time.")

                jobs.append({
                    "title": title,
                    "link": link,
                    "description": description,
                    "source": site_name,
                    "tags": tags,
                    "posted_date": posted_date.isoformat()
                })
                logger.debug(f"Extracted job: '{title}' from {site_name}.")

            except NoSuchElementException as e:
                logger.warning(f"Skipping job card {i+1} on {site_name} due to missing core element (e.g., title): {e}. Card HTML might be malformed or selectors are incorrect for this specific card.")
            except Exception as e:
                logger.warning(f"An unexpected error occurred while processing job card {i+1} on {site_name}: {e}", exc_info=True)

    except TimeoutException:
        logger.error(f"Timeout while loading or finding elements on {site_name} ({url}). Page might not have loaded correctly or selectors are invalid after 40 seconds.")
    except WebDriverException as e:
        logger.error(f"WebDriver error during scraping {site_name}: {e}", exc_info=True)
    except Exception as e:
        logger.critical(f"An unhandled error occurred during scraping of {site_name}: {e}", exc_info=True)

    logger.info(f"Finished scraping {len(jobs)} jobs from {site_name}.")
    return jobs

def is_job_posting(title: str, description: str, title_keywords: list, description_keywords: list) -> bool:
    """
    Determines if a job posting is relevant based on predefined keywords in its title and description.
    Performs case-insensitive matching for robustness.
    """
    title_lower = title.lower()
    description_lower = description.lower() # ensure description is lowercased for consistent behavior

    # Check for title keywords (typically more critical for initial filtering)
    if not any(keyword.lower() in title_lower for keyword in title_keywords):
        return False # No relevant title keyword found

    # Check for description keywords (more detailed filtering)
    if not any(keyword.lower() in description_lower for keyword in description_keywords):
        return False # No relevant description keyword found

    logger.debug(f"Job '{title}' matches all relevance criteria.")
    return True