import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Telegram Configuration ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Basic validation for Telegram config
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables. Please set it in .env.")
if not TELEGRAM_CHAT_ID:
    raise ValueError("TELEGRAM_CHAT_ID not found in environment variables. Please set it in .env.")

# --- Keywords ---
JOB_KEYWORDS = [
    "job opening", "apply", "we're looking for", "hiring", "position available",
    "career opportunity", "join our team", "cloud engineer", "sre",
    "azure devops", "aws devops", "gcp devops", "kubernetes", "docker",
    "ci/cd", "automation", "infrastructure", "ansible", "terraform",
    "jenkins", "gitlab ci", "github actions", "monitoring", "logging",
    "networking", "security", "pipelines"
]

JOB_TITLE_KEYWORDS = [
    "devops", "dev ops", "site reliability engineer", "sre",
    "cloud engineer", "platform engineer"
]

# --- Website Configurations ---
JOB_WEBSITES = [
    {
        "name": "Wuzzuf.net (Egypt - DevOps)",
        "url": "https://wuzzuf.net/search/jobs/?q=devops&a=hpb",
        "selector": "div.e1v1l3u10", # Main job card div
        "title_selector": "h2 a", # Title link
        "link_selector": "h2 a", # Job link. We will filter this in scraper.py
        "description_selector": "div.css-1uobp1k", # Main div for description on detail page
        "tags_selector": "div.css-1uobp1k a, div.css-1uobp1k li, div.css-1o2t7az a, div.css-1f9g2g8 a", # Combined tags selector on detail page
        "date_selector": "span.css-1ve4m0s", # Date/time on listing page (e.g., 'X days ago')
        "visit_detail_page_for_description": True
    },
]

# --- Selenium/Browser Configuration ---
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# --- Persistence Configuration ---
POSTED_JOBS_FILE = os.getenv("POSTED_JOBS_FILE", "posted_jobs.txt")