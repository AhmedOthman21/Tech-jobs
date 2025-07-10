import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime, timedelta # Import timedelta
import logging
import re # Import re for regex

# Set up logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# --- Helper Functions ---

def is_job_posting(title: str, full_post_text: str, job_title_keywords: list, job_keywords: list) -> bool:
    """
    Checks if a given post is a relevant job posting based on title and overall text keywords.
    """
    normalized_title = title.lower()
    normalized_full_text = full_post_text.lower()

    # Condition 1: Must contain at least one keyword from JOB_TITLE_KEYWORDS in the title
    title_match = False
    for keyword in job_title_keywords:
        if keyword.lower() in normalized_title:
            title_match = True
            break

    if not title_match:
        return False

    # Condition 2: Must contain at least one keyword from JOB_KEYWORDS in the full text
    general_match = False
    for keyword in job_keywords:
        if keyword.lower() in normalized_full_text:
            general_match = True
            break

    return general_match

def parse_date_string(date_text: str) -> str:
    """
    Attempts to parse various date/time strings into a consistent format or returns original.
    This is a basic implementation and can be greatly expanded for more robustness.
    """
    date_text_lower = date_text.lower()
    today = datetime.now()

    if "today" in date_text_lower:
        return today.strftime("%Y-%m-%d")
    elif "yesterday" in date_text_lower:
        return (today - timedelta(days=1)).strftime("%Y-%m-%d")
    elif "hour" in date_text_lower or "hr" in date_text_lower or "minute" in date_text_lower or "min" in date_text_lower:
        # If it's hours/minutes ago, it means it's today
        return today.strftime("%Y-%m-%d %H:%M")
    elif "day" in date_text_lower:
        try:
            # Matches "X days ago"
            match = re.search(r'(\d+)\s+day', date_text_lower)
            if match:
                days_ago = int(match.group(1))
                return (today - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        except:
            pass # Fallback
    elif "week" in date_text_lower:
        try:
            # Matches "X weeks ago"
            match = re.search(r'(\d+)\s+week', date_text_lower)
            if match:
                weeks_ago = int(match.group(1))
                return (today - timedelta(weeks=weeks_ago)).strftime("%Y-%m-%d")
        except:
            pass # Fallback

    # Try common date formats (e.g., "Jul 10, 2025" or "10-07-2025")
    # Add more formats as you discover them
    date_formats = [
        "%b %d, %Y", # Jul 10, 2025 (e.g., Bayt)
        "%d-%m-%Y",  # 10-07-2025
        "%Y-%m-%d"   # 2025-07-10
    ]
    for fmt in date_formats:
        try:
            parsed_date = datetime.strptime(date_text, fmt)
            return parsed_date.strftime("%Y-%m-%d")
        except ValueError:
            pass # Not this format

    logger.warning(f"Could not parse date string: '{date_text}'. Returning original.")
    return date_text # Return original if no specific parsing rule matches

def scrape_full_description_and_tags(driver, job_link: str, site_name: str, description_selector: str, tags_selector: str) -> tuple[str, list]:
    """
    Navigates to a job's detail page and scrapes the full description and associated tags.
    """
    full_description = "No full description found."
    tags = []

    if not job_link or job_link == "#":
        logger.warning(f"Skipping detail page scrape: Invalid job link for {site_name}.")
        return full_description, tags

    # Specific check for Wuzzuf: Ensure link is a job detail page, not a search page or similar
    if site_name == "Wuzzuf.net" and not re.match(r"https?://wuzzuf\.net/jobs/p/[\w-]+", job_link):
        logger.warning(f"Wuzzuf link '{job_link}' does not appear to be a direct job detail page. Skipping detail scrape.")
        return full_description, tags


    try:
        logger.info(f"Navigating to job detail page: {job_link}")
        driver.get(job_link)

        # Wait for description element to be visible
        WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, description_selector))
        )

        detail_soup = BeautifulSoup(driver.page_source, 'html.parser')

        # --- Extract Description ---
        description_element = detail_soup.select_one(description_selector)
        if description_element:
            full_description = description_element.get_text(separator="\n", strip=True)
            logger.info(f"Successfully scraped full description for {site_name}.")
        else:
            logger.warning(f"Full description element '{description_selector}' not found on {job_link}.")

        # --- Extract Tags ---
        tag_elements = detail_soup.select(tags_selector)
        if tag_elements:
            tags = [tag.get_text(strip=True) for tag in tag_elements if tag.get_text(strip=True)]
            logger.info(f"Found {len(tags)} tags using selector '{tags_selector}' on {site_name} detail page.")
        else:
            logger.info(f"No tags found with selector '{tags_selector}' on {site_name} detail page.")

        tags = list(set(tags)) # Remove duplicates

    except TimeoutException:
        logger.error(f"Timeout: Detail page or description/tags not found on {job_link} after 20 seconds.")
    except Exception as e:
        logger.error(f"Error scraping full description/tags from {job_link}: {e}", exc_info=True)

    return full_description, tags

def get_selenium_driver(headers: dict):
    """Initializes and returns a configured undetected_chromedriver instance."""
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(f"user-agent={headers['User-Agent']}")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_argument("--proxy-server='direct://'")
    options.add_argument("--proxy-bypass-list=*")
    options.add_argument("--disable-features=IsolateOrigins,site-per-process")
    options.add_argument("--enable-features=NetworkService,NetworkServiceInProcess")
    options.add_argument("--headless") # Re-enable headless when deployment ready

    try:
        driver = uc.Chrome(options=options)
        driver.set_page_load_timeout(60) # Increased timeout for page load
        logger.info("Selenium driver initialized successfully.")
        return driver
    except WebDriverException as e:
        logger.critical(f"Failed to initialize Selenium driver: {e}. Ensure Chrome and undetected-chromedriver are compatible and installed correctly.", exc_info=True)
        raise
    except Exception as e:
        logger.critical(f"An unexpected error occurred during driver initialization: {e}", exc_info=True)
        raise

def scrape_jobs_from_website(driver, site_config: dict) -> list[dict]:
    """
    Scrapes job postings from a single website based on provided configuration,
    using Selenium.
    """
    logger.info(f"\n--- Attempting to scrape from: {site_config['name']} ---")
    logger.info(f"URL: {site_config['url']}")
    job_listings = []

    # Adjust timeout based on site for initial page load
    initial_page_load_timeout = 60 if "bayt.com" in site_config["url"] else 45


    try:
        driver.get(site_config["url"])

        logger.info(f"Attempting to wait for element with selector: '{site_config['selector']}' for {site_config['name']} (Timeout: {initial_page_load_timeout}s)")
        WebDriverWait(driver, initial_page_load_timeout).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, site_config["selector"]))
        )
        logger.info(f"Element with selector '{site_config['selector']}' found on {site_config['name']}. Proceeding to parse.")

        soup = BeautifulSoup(driver.page_source, 'html.parser')

    except TimeoutException:
        logger.error(f"Timeout: Elements not found on {site_config['name']} after {initial_page_load_timeout} seconds. Page might not have loaded completely or selector is incorrect.")
        return []
    except WebDriverException as e:
        logger.error(f"Selenium WebDriver Error for {site_config['name']}: {e}", exc_info=True)
        return []
    except Exception as e:
        logger.error(f"An unexpected error occurred with Selenium for {site_config['name']}: {e}", exc_info=True)
        return []

    job_elements = soup.select(site_config["selector"])

    if not job_elements:
        logger.warning(f"No job elements found with selector '{site_config['selector']}' on {site_config['name']}. Please re-inspect the HTML.")
    else:
        logger.info(f"Found {len(job_elements)} potential job elements using selector '{site_config['selector']}'.")

    for i, job_element in enumerate(job_elements):
        try:
            title_element = job_element.select_one(site_config["title_selector"])
            title = title_element.get_text(strip=True) if title_element else "N/A"

            link_element = job_element.select_one(site_config["link_selector"])
            raw_link = link_element['href'] if link_element and 'href' in link_element.attrs else None
            link = urljoin(site_config["url"], str(raw_link)) if raw_link else "#"

            # --- Wuzzuf specific link validation ---
            if site_config["name"] == "Wuzzuf.net" and not re.match(r"https?://wuzzuf\.net/jobs/p/[\w-]+", link):
                logger.warning(f"Skipping job {i+1} ('{title}') from Wuzzuf due to invalid link pattern: {link}")
                continue # Skip to the next job element

            logger.debug(f"Extracted Link for Job {i+1}: {link}")

            description_snippet = ""
            full_description = ""
            tags = []
            posted_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S") # Default to current scrape time

            # Try to get date from listing page first
            date_element = job_element.select_one(site_config.get("date_selector", ""))
            if date_element:
                posted_date_text = date_element.get_text(strip=True)
                posted_date = parse_date_string(posted_date_text) # Parse if possible
            else:
                logger.debug(f"No date element found on listing page for job {i+1} on {site_config['name']}.")


            if site_config.get("visit_detail_page_for_description"):
                current_url = driver.current_url

                full_description, tags = scrape_full_description_and_tags(
                    driver, link, site_config["name"], site_config["description_selector"], site_config["tags_selector"]
                )

                # After returning from detail page, navigate back if URL changed
                if driver.current_url != current_url:
                    try:
                        logger.debug(f"Navigating back to search results: {current_url}")
                        driver.get(current_url)
                        # Wait for the main elements to reappear to ensure navigation completed
                        WebDriverWait(driver, 10).until(
                            EC.visibility_of_element_located((By.CSS_SELECTOR, site_config["selector"]))
                        )
                    except TimeoutException:
                        logger.error(f"Timeout navigating back to original search results for {site_config['name']}.")
                        # This can lead to subsequent scrapes failing, but allows current one to finish.
                    except Exception as nav_e:
                        logger.error(f"Error navigating back to search results for {site_config['name']}: {nav_e}")

            else:
                # For sites not requiring detail page visits (like Bayt usually)
                desc_elem_on_list = job_element.select_one(site_config["description_selector"])
                if desc_elem_on_list:
                    description_snippet = desc_elem_on_list.get_text(separator="\n", strip=True)
                else:
                    description_snippet = "No description snippet available on listing page."

                tag_elements_on_list = job_element.select(site_config["tags_selector"])
                if tag_elements_on_list:
                    tags = [tag.get_text(strip=True) for tag in tag_elements_on_list]

                full_description = description_snippet

            final_description = full_description if full_description and full_description != "No full description found." else description_snippet
            full_post_text = f"{title}\n{final_description}\n{', '.join(tags)}"

            job_listings.append({
                "title": title,
                "link": link,
                "text": full_post_text,
                "source": site_config["name"],
                "description": final_description,
                "tags": tags,
                "posted_date": posted_date # Add the extracted date
            })
        except Exception as e:
            logger.error(f"Error processing a job element {i+1} on {site_config['name']}: {e}", exc_info=True)
            continue

    logger.info(f"Finished scraping {site_config['name']}. Found {len(job_listings)} raw listings.")
    return job_listings