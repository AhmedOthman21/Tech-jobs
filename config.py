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
        "url": "https://wuzzuf.net/a/devops-jobs-in-egypt",
        "job_card_selector": "div.css-1gatmva.e1v1l3u10", # Most specific and stable
        "title_selector": "h2.css-m604qf a",
        "link_selector": "h2.css-m604qf a",
        "description_selector": "div.css-y4udm8",
        "tags_selector": "div.css-y4udm8 a[class^='css-'], div.css-y4udm8 span.eoyjyou0",
        "date_selector": "div.css-d7j1kk > div" # Robust against dynamic class names
    },
    {
        "name": "NaukriGulf",
        "url": "https://www.naukrigulf.com/devops-jobs",
        # Corrected based on your new HTML snippet
        "job_card_selector": "div.ng-box.srp-tuple",
        "title_selector": "a.info-position p.designation-title", # Title text is inside a <p> within the <a>
        "link_selector": "a.info-position", # The href of this <a> is the job link
        "description_selector": "p.description", # Short description snippet
        "tags_selector": "", # No explicit tags in the provided snippet beyond exp/loc, so leaving empty
        "date_selector": "span.foot span.time" # Date is inside <span class="time"> within <span class="foot">
    },
    {
        "name": "Forasna",
        "url": "https://forasna.com/%D9%88%D8%B8%D8%A7%D8%A6%D9%81-%D8%AE%D8%A7%D9%84%D9%8A%D8%A9?query=it", # Using 'devops' query
        # The HTML snippet provided was too minimal (<a class="mobile-job-link"></a>)
        # Sticking to previous desktop selectors which show a full job card,
        # assuming Selenium will get a more complete page.
        "job_card_selector": "a.job-card",
        "title_selector": "h2.job-card__title",
        "link_selector": "", # The job_card_selector itself is the link, so it will use its href
        "description_selector": "div.job-card__skills",
        "tags_selector": "div.job-card__skills span",
        "date_selector": "span.job-card__date" # E.g., "منذ 2 يوم" (2 days ago) - requires Arabic date parsing
    },
    {
        "name": "Bayt",
        "url": "https://www.bayt.com/en/egypt/jobs/devops-jobs/",
        # Corrected based on your new HTML snippet
        "job_card_selector": "li.has-pointer-d", # Main container for each job listing
        "title_selector": "h2.t-large a", # Title text is inside <a> within <h2 class="t-large">
        "link_selector": "h2.t-large a", # The href of this <a> is the job link
        "description_selector": "div.jb-descr", # Short description snippet
        "tags_selector": "", # "div.tags-box a" was not present in the new snippet, leaving empty for now
        "date_selector": "span[data-automation-id=\"job-active-date\"]" # Robust selector for the date span
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
    "Infrastructure Engineer", "Automation Engineer", "IT", "system administrator",
]

# Keywords used to filter job descriptions. Can be more specific technical skills.
JOB_KEYWORDS = [
    "Docker", "Kubernetes", "AWS", "Azure", "GCP", "Terraform", "Ansible",
    "Jenkins", "GitLab CI", "CI/CD", "Linux", "Scripting", "Python",
    "Bash", "Monitoring", "Prometheus", "Grafana", "ELK", "Splunk",
    "Microservices", "Containerization", "CloudFormation", "Helm", "ArgoCD",
    "IaC", "Infrastructure as Code", "CI/CD Pipeline", "IT", "system administrator"
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