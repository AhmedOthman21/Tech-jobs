import os

from dotenv import load_dotenv

load_dotenv()


class LoggerConfig:
    """Configuration for logging."""

    LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", "job_scraper.log")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()


class WebDriverConfig:
    """Configuration for Selenium WebDriver."""

    HEADLESS_MODE = os.getenv("HEADLESS_MODE", "True").lower() == "true"
    DEFAULT_TIMEOUT_SECONDS = int(os.getenv("DEFAULT_TIMEOUT_SECONDS", 30))
    PAGE_LOAD_TIMEOUT_SECONDS = int(os.getenv("PAGE_LOAD_TIMEOUT_SECONDS", 60))
    DRIVER_PATH = os.getenv(
        "DRIVER_PATH"
    )  # Optional, if using specific driver location


class WebsiteConfig:
    """Configuration for job scraping websites."""

    # Wuzzuf configuration (from previous successful scrapes)
    WUZZUF_URL = os.getenv(
        "WUZZUF_URL",
        "https://wuzzuf.net/a/this-week-devops-jobs-in-egypt?"
        "filters%5Bpost_date%5D%5B0%5D=within_1_week",
    )
    WUZZUF_URL_IT = os.getenv(
        "WUZZUF_URL_IT",
        "https://wuzzuf.net/search/jobs/?a=navbg&filters%5Bpost_date%5D%5B0%5D=within_24_hours&q=it",
    )
    WUZZUF_URL_DEVELOPER = os.getenv(
        "WUZZUF_URL_DEVELOPER",
        "https://wuzzuf.net/search/jobs/?a=navbg%7Cspbg&filters%5Bpost_date%5D%5B0%5D="
        "within_24_hours&q=developer",
    )
    WUZZUF_JOB_CARD_SELECTOR = os.getenv(
        "WUZZUF_JOB_CARD_SELECTOR", "div.css-ghe2tq.e1v1l3u10"
    )
    WUZZUF_TITLE_SELECTOR = os.getenv(
        "WUZZUF_TITLE_SELECTOR", "h2.css-193uk2c a.css-o171kl"
    )
    WUZZUF_LINK_SELECTOR = os.getenv(
        "WUZZUF_LINK_SELECTOR", "h2.css-193uk2c a.css-o171kl"
    )
    WUZZUF_DESCRIPTION_SELECTOR = os.getenv(
        "WUZZUF_DESCRIPTION_SELECTOR", "div.css-1rhj4yg"
    )
    WUZZUF_TAGS_SELECTOR = os.getenv(
        "WUZZUF_TAGS_SELECTOR",
        ("div.css-1rhj4yg a[class^='css-'], " "div.css-1rhj4yg span[class^='css-']"),
    )
    WUZZUF_DATE_SELECTOR = os.getenv(
        "WUZZUF_DATE_SELECTOR",
        "div.css-1k5ee52 div.css-eg55jf, div.css-1k5ee52 div.css-1jldrig",
    )

    """ # NaukriGulf configuration
    NAUKRIGULF_URL = os.getenv(
        "NAUKRIGULF_URL", "https://www.naukrigulf.com/devops-jobs"
    )
    NAUKRIGULF_JOB_CARD_SELECTOR = os.getenv(
        "NAUKRIGULF_JOB_CARD_SELECTOR",
        # Breaking this line further to fit within 100 characters
        "div.ng-box.srp-tuple",
    )
    NAUKRIGULF_TITLE_SELECTOR = os.getenv(
        "NAUKRIGULF_TITLE_SELECTOR", "a.info-position p.designation-title"
    )
    NAUKRIGULF_LINK_SELECTOR = os.getenv("NAUKRIGULF_LINK_SELECTOR", "a.info-position")
    NAUKRIGULF_DESCRIPTION_SELECTOR = os.getenv(
        "NAUKRIGULF_DESCRIPTION_SELECTOR", "p.description"
    )
    NAUKRIGULF_TAGS_SELECTOR = os.getenv("NAUKRIGULF_TAGS_SELECTOR", "")
    NAUKRIGULF_DATE_SELECTOR = os.getenv(
        "NAUKRIGULF_DATE_SELECTOR", "span.foot span.time"
    )

    # Forasna configuration
    FORASNA_URL = os.getenv(
        "FORASNA_URL",
        "https://forasna.com/%D9%88%D8%B8%D8%A7%D8%A6%D9%81-%D8%AE%D8%A7%D9%84%D9%8A%D8%A9?query=devops",
    )
    FORASNA_JOB_CARD_SELECTOR = os.getenv("FORASNA_JOB_CARD_SELECTOR", "a.job-card")
    FORASNA_TITLE_SELECTOR = os.getenv("FORASNA_TITLE_SELECTOR", "h2.job-card__title")
    FORASNA_LINK_SELECTOR = os.getenv(
        "FORASNA_LINK_SELECTOR", ""
    )  # Card itself is link
    FORASNA_DESCRIPTION_SELECTOR = os.getenv(
        "FORASNA_DESCRIPTION_SELECTOR", "div.job-card__skills"
    )
    FORASNA_TAGS_SELECTOR = os.getenv(
        "FORASNA_TAGS_SELECTOR", "div.job-card__skills span"
    )
    FORASNA_DATE_SELECTOR = os.getenv("FORASNA_DATE_SELECTOR", "span.job-card__date")

    # Bayt configuration
    BAYT_URL = os.getenv("BAYT_URL", "https://www.bayt.com/en/egypt/jobs/devops-jobs/")
    BAYT_JOB_CARD_SELECTOR = os.getenv("BAYT_JOB_CARD_SELECTOR", "li.has-pointer-d")
    BAYT_TITLE_SELECTOR = os.getenv("BAYT_TITLE_SELECTOR", "h2.t-large a")
    BAYT_LINK_SELECTOR = os.getenv("BAYT_LINK_SELECTOR", "h2.t-large a")
    BAYT_DESCRIPTION_SELECTOR = os.getenv("BAYT_DESCRIPTION_SELECTOR", "div.jb-descr")
    BAYT_TAGS_SELECTOR = os.getenv("BAYT_TAGS_SELECTOR", "")
    BAYT_DATE_SELECTOR = os.getenv(
        "BAYT_DATE_SELECTOR", 'span[data-automation-id="job-active-date"]'
    )"""


class ScraperConfig:
    """General configuration for the job scraper."""

    JOB_KEYWORDS = list(
        os.getenv(
            "JOB_KEYWORDS",
            "DevOps Engineer,SRE,Cloud Engineer,Site Reliability Engineer,"
            "Platform Engineer,Infrastructure Engineer,"
            "IT,System Administrator,IT Support,IT Manager,IT Director,"
            "IT Consultant,IT Analyst,Engineer,Developer,Specialist,"
            "Administrator,Support,Manager,Consultant,Analyst,"
            "Technical,Technology,Software,Hardware,Network,"
            "System,Security,Database,Web,Application,"
            "Computer,Information,Digital,Technical Support,"
            "Help Desk,Support Specialist,Technical Specialist",
        ).split(",")
    )
    JOB_TITLE_KEYWORDS = list(
        os.getenv(
            "JOB_TITLE_KEYWORDS",
            "DevOps,SRE,Cloud,Site Reliability,Platform,Infrastructure,"
            "IT,System Administrator,IT Support,IT Manager,IT Director,"
            "IT Consultant,IT Analyst,Engineer,Developer,Specialist,"
            "Administrator,Support,Manager,Consultant,Analyst,"
            "Technical,Technology,Software,Hardware,Network,"
            "System,Security,Database,Web,Application,"
            "Computer,Information,Digital,Technical Support,"
            "Help Desk,Support Specialist,Technical Specialist",
        ).split(",")
    )

    MAX_JOB_AGE_DAYS = int(os.getenv("MAX_JOB_AGE_DAYS", 7))
    POSTED_JOBS_FILE = os.getenv("POSTED_JOBS_FILE", "posted_jobs.txt")
    MAX_SCROLL_PAUSES = int(os.getenv("MAX_SCROLL_PAUSES", 5))
    SCROLL_PAUSE_TIME = int(os.getenv("SCROLL_PAUSE_TIME", 2))
    JOB_DESCRIPTION_MAX_LENGTH = int(os.getenv("JOB_DESCRIPTION_MAX_LENGTH", 100))
    MIN_JOBS_PER_WEBSITE = int(os.getenv("MIN_JOBS_PER_WEBSITE", 10))


class TelegramConfig:
    """Configuration for Telegram notifications."""

    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    INCLUDE_DATE_IN_MESSAGE = (
        os.getenv("INCLUDE_DATE_IN_MESSAGE", "False").lower() == "true"
    )


class GeneralConfig:
    """General application settings."""

    DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"
    APP_VERSION = "1.0.0"


# Grouping configurations for easier access
LOGGER_SETTINGS = {
    "log_file_path": LoggerConfig.LOG_FILE_PATH,
    "log_level": LoggerConfig.LOG_LEVEL,
}

WEBDRIVER_SETTINGS = {
    "headless_mode": WebDriverConfig.HEADLESS_MODE,
    "default_timeout_seconds": WebDriverConfig.DEFAULT_TIMEOUT_SECONDS,
    "page_load_timeout_seconds": WebDriverConfig.PAGE_LOAD_TIMEOUT_SECONDS,
    "driver_path": WebDriverConfig.DRIVER_PATH,
}

WEBSITE_CONFIGS = [
    {
        "name": "DevOps",
        "url": WebsiteConfig.WUZZUF_URL,
        "job_card_selector": WebsiteConfig.WUZZUF_JOB_CARD_SELECTOR,
        "title_selector": WebsiteConfig.WUZZUF_TITLE_SELECTOR,
        "link_selector": WebsiteConfig.WUZZUF_LINK_SELECTOR,
        "description_selector": WebsiteConfig.WUZZUF_DESCRIPTION_SELECTOR,
        "tags_selector": WebsiteConfig.WUZZUF_TAGS_SELECTOR,
        "date_selector": WebsiteConfig.WUZZUF_DATE_SELECTOR,
    },
    {
        "name": "IT",
        "url": WebsiteConfig.WUZZUF_URL_IT,
        "job_card_selector": WebsiteConfig.WUZZUF_JOB_CARD_SELECTOR,
        "title_selector": WebsiteConfig.WUZZUF_TITLE_SELECTOR,
        "link_selector": WebsiteConfig.WUZZUF_LINK_SELECTOR,
        "description_selector": WebsiteConfig.WUZZUF_DESCRIPTION_SELECTOR,
        "tags_selector": WebsiteConfig.WUZZUF_TAGS_SELECTOR,
        "date_selector": WebsiteConfig.WUZZUF_DATE_SELECTOR,
    },
    {
        "name": "Developer",
        "url": WebsiteConfig.WUZZUF_URL_DEVELOPER,
        "job_card_selector": WebsiteConfig.WUZZUF_JOB_CARD_SELECTOR,
        "title_selector": WebsiteConfig.WUZZUF_TITLE_SELECTOR,
        "link_selector": WebsiteConfig.WUZZUF_LINK_SELECTOR,
        "description_selector": WebsiteConfig.WUZZUF_DESCRIPTION_SELECTOR,
        "tags_selector": WebsiteConfig.WUZZUF_TAGS_SELECTOR,
        "date_selector": WebsiteConfig.WUZZUF_DATE_SELECTOR,
    },
    # {
    #     "name": "NaukriGulf",
    #     "url": WebsiteConfig.NAUKRIGULF_URL,
    #     "job_card_selector": WebsiteConfig.NAUKRIGULF_JOB_CARD_SELECTOR,
    #     "title_selector": WebsiteConfig.NAUKRIGULF_TITLE_SELECTOR,
    #     "link_selector": WebsiteConfig.NAUKRIGULF_LINK_SELECTOR,
    #     "description_selector": WebsiteConfig.NAUKRIGULF_DESCRIPTION_SELECTOR,
    #     "tags_selector": WebsiteConfig.NAUKRIGULF_TAGS_SELECTOR,
    #     "date_selector": WebsiteConfig.NAUKRIGULF_DATE_SELECTOR,
    # },
    # {
    #     "name": "Forasna",
    #     "url": WebsiteConfig.FORASNA_URL,
    #     "job_card_selector": WebsiteConfig.FORASNA_JOB_CARD_SELECTOR,
    #     "title_selector": WebsiteConfig.FORASNA_TITLE_SELECTOR,
    #     "link_selector": WebsiteConfig.FORASNA_LINK_SELECTOR,
    #     "description_selector": WebsiteConfig.FORASNA_DESCRIPTION_SELECTOR,
    #     "tags_selector": WebsiteConfig.FORASNA_TAGS_SELECTOR,
    #     "date_selector": WebsiteConfig.FORASNA_DATE_SELECTOR,
    # },
    # {
    #     "name": "Bayt",
    #     "url": WebsiteConfig.BAYT_URL,
    #     "job_card_selector": WebsiteConfig.BAYT_JOB_CARD_SELECTOR,
    #     "title_selector": WebsiteConfig.BAYT_TITLE_SELECTOR,
    #     "link_selector": WebsiteConfig.BAYT_LINK_SELECTOR,
    #     "description_selector": WebsiteConfig.BAYT_DESCRIPTION_SELECTOR,
    #     "tags_selector": WebsiteConfig.BAYT_TAGS_SELECTOR,
    #     "date_selector": WebsiteConfig.BAYT_DATE_SELECTOR,
    # },
]

SCRAPER_SETTINGS = {
    "job_keywords": list(
        os.getenv(
            "JOB_KEYWORDS",
            "DevOps Engineer,SRE,Cloud Engineer,Site Reliability Engineer,"
            "Platform Engineer,Infrastructure Engineer,"
            "IT,System Administrator,IT Support,IT Manager,IT Director,"
            "IT Consultant,IT Analyst,Engineer,Developer,Specialist,"
            "Administrator,Support,Manager,Consultant,Analyst,"
            "Technical,Technology,Software,Hardware,Network,"
            "System,Security,Database,Web,Application,"
            "Computer,Information,Digital,Technical Support,"
            "Help Desk,Support Specialist,Technical Specialist",
        ).split(",")
    ),
    "job_title_keywords": list(
        os.getenv(
            "JOB_TITLE_KEYWORDS",
            "DevOps,SRE,Cloud,Site Reliability,Platform,Infrastructure,"
            "IT,System Administrator,IT Support,IT Manager,IT Director,"
            "IT Consultant,IT Analyst,Engineer,Developer,Specialist,"
            "Administrator,Support,Manager,Consultant,Analyst,"
            "Technical,Technology,Software,Hardware,Network,"
            "System,Security,Database,Web,Application,"
            "Computer,Information,Digital,Technical Support,"
            "Help Desk,Support Specialist,Technical Specialist",
        ).split(",")
    ),
    "posted_jobs_file": os.getenv("POSTED_JOBS_FILE", "posted_jobs.txt"),
}

TELEGRAM_SETTINGS = {
    "bot_token": TelegramConfig.TELEGRAM_BOT_TOKEN,
    "chat_id": TelegramConfig.TELEGRAM_CHAT_ID,
    "include_date_in_message": TelegramConfig.INCLUDE_DATE_IN_MESSAGE,
}

GENERAL_SETTINGS = {
    "debug_mode": GeneralConfig.DEBUG_MODE,
    "app_version": GeneralConfig.APP_VERSION,
}
