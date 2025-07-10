import os
from dotenv import load_dotenv

# Load environment variables from a .env file (for local development).
# In production/CI/CD, these values are typically injected directly as environment variables.
load_dotenv()

# --- Telegram Bot Configuration ---
# Telegram bot token for API interaction. MUST be kept secret.
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
# Telegram chat ID where job notifications will be sent. Can be a channel or group ID.
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- Job Search Criteria ---
# List of job websites to scrape, each with its specific selectors.
# This structure allows easy extension for new websites without code changes.
JOB_WEBSITES = [
    {
        "name": "Wuzzuf",
        "url": "https://wuzzuf.net/a/devops-jobs-in-egypt", # Example URL, adjust as needed
        "job_card_selector": "div.job-card",
        "title_selector": "h2.job-card__title a",
        "link_selector": "h2.job-card__title a",
        "description_selector": "p.job-card__job-info",
        "tags_selector": ".job-card__tag-item", # Example selector for tags
        "date_selector": ".job-card__date" # Example selector for posted date
    },
    # Add more job websites here following the same structure
    # {
    #     "name": "ExampleJobs",
    #     "url": "https://examplejobs.com/devops",
    #     "job_card_selector": ".job-listing",
    #     "title_selector": ".job-title a",
    #     "link_selector": ".job-title a",
    #     "description_selector": ".job-description",
    #     "tags_selector": ".job-tag",
    #     "date_selector": ".job-date"
    # },
]

# Keywords used to filter job titles. Broader terms are acceptable here.
JOB_TITLE_KEYWORDS = [
    "DevOps", "SRE", "Site Reliability Engineer", "Cloud Engineer",
    "Kubernetes", "AWS DevOps", "Azure DevOps", "GCP DevOps",
    "Infrastructure Engineer", "Automation Engineer"
]

# Keywords used to filter job descriptions. Can be more specific technical skills.
JOB_KEYWORDS = [
    "Docker", "Kubernetes", "AWS", "Azure", "GCP", "Terraform", "Ansible",
    "Jenkins", "GitLab CI", "CI/CD", "Linux", "Scripting", "Python",
    "Bash", "Monitoring", "Prometheus", "Grafana", "ELK", "Splunk",
    "Microservices", "Containerization", "CloudFormation", "Helm", "ArgoCD",
    "IaC", "Infrastructure as Code", "CI/CD Pipeline"
]

# --- WebDriver Configuration ---
# Standard HTTP headers for web requests. Includes a common User-Agent to mimic a real browser.
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# --- Persistence Configuration ---
# File path for storing links of already posted jobs.
# This ensures that duplicate notifications are avoided across different runs.
# Prioritizes an environment variable for flexible deployment (e.g., mounting a volume in Docker).
POSTED_JOBS_FILE = os.getenv("POSTED_JOBS_FILE", "posted_jobs.txt")