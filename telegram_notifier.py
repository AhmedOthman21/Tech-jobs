import telegram
import asyncio
import html
from datetime import datetime
import logging
import os # Import os for file path checks

# Set up logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# No need to import POSTED_JOBS_FILE here, main.py will pass it.

def load_posted_job_links(file_path: str) -> set:
    """
    Loads previously posted job links from a file.
    Returns a set for efficient lookup.
    """
    links = set()
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    links.add(line.strip())
            logger.info(f"Loaded {len(links)} previously posted job links from {file_path}")
        except IOError as e:
            logger.error(f"Error reading posted jobs file {file_path}: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred while loading posted jobs: {e}")
    else:
        logger.info(f"Posted jobs file not found: {file_path}. A new one will be created.")
    return links

def add_posted_job_link(file_path: str, link: str):
    """
    Adds a new job link to the posted jobs file.
    """
    try:
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(link + "\n")
        logger.debug(f"Added link to posted jobs file: {link}")
    except IOError as e:
        logger.error(f"Error writing to posted jobs file {file_path}: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred while adding posted job link: {e}")


async def send_telegram_message(bot_token: str, chat_id: str, job_post: dict):
    """
    Sends a single job posting message to the specified Telegram chat/channel.
    """
    bot = telegram.Bot(token=bot_token)

    current_scrape_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    job_posted_date = job_post.get("posted_date", "N/A") # Get the extracted date or default

    clean_title = html.escape(job_post.get("title", "No Title"))
    clean_description = html.escape(job_post.get("description", "No description available."))
    clean_tags = ", ".join(job_post.get("tags", []))
    if clean_tags:
        clean_tags = html.escape(clean_tags)

    message_parts = [
        f"✨ <b><u>New Job Posting - {job_post.get('source', 'Unknown')}</u></b> ✨",
        f"<b>Title:</b> {clean_title}",
        f"<b>Link:</b> <a href='{job_post.get('link', '#')}'>View Job</a>",
        f"<b>Posted:</b> {job_posted_date}" # Include the extracted or scrape date
    ]

    if clean_tags:
        message_parts.append(f"<b>Tags:</b> {clean_tags}")

    message_parts.append("\n<b>Full Description:</b>")
    message_parts.append(f"<pre>{clean_description}</pre>")

    full_message = "\n".join(message_parts)

    # Estimate max length for truncation more accurately.
    # Base message length without description and tags.
    base_message_len = len(f"✨ <b><u>New Job Posting - {job_post.get('source', 'Unknown')}</u></b> ✨\n<b>Title:</b> {clean_title}\n<b>Link:</b> <a href='{job_post.get('link', '#')}'>View Job</a>\n<b>Posted:</b> {job_posted_date}\n")
    if clean_tags:
        base_message_len += len(f"<b>Tags:</b> {clean_tags}\n")
    base_message_len += len("\n<b>Full Description:</b>\n<pre></pre>") # account for pre tags

    if len(full_message) > 4096:
        max_desc_len = 4096 - base_message_len - len("\n\n... (description truncated due to length limit)")
        if max_desc_len < 50: # Ensure at least some description is left
            max_desc_len = 50
        truncated_description = clean_description[:max_desc_len] + "\n\n... (description truncated due to length limit)"
        message_parts[-1] = f"<pre>{truncated_description}</pre>"
        full_message = "\n".join(message_parts)

    try:
        await bot.send_message(
            chat_id=chat_id,
            text=full_message,
            parse_mode=telegram.constants.ParseMode.HTML,
            disable_web_page_preview=True
        )
        logger.info(f"Telegram message sent for: {job_post['title']} (Source: {job_post['source']})")
        return True # Indicate success
    except telegram.error.TelegramError as e:
        logger.error(f"Error sending Telegram message for {job_post['title']}: {e}")
        if "chat not found" in str(e).lower() or "bad request: chat_id is empty" in str(e).lower():
            logger.error("Invalid Telegram Chat ID or bot not in chat. Please double-check your CHAT_ID and bot's admin status.")
        elif "message is too long" in str(e).lower():
            logger.error(f"Telegram message for {job_post['title']} is too long. Consider further truncation or splitting.")
        return False # Indicate failure
    except Exception as e:
        logger.error(f"An unexpected error occurred during Telegram sending for {job_post['title']}: {e}")
        return False # Indicate failure