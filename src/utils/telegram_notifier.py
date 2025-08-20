import html
import logging
import os  # Import os for file path checks

import telegram

# Import tenacity
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

# Set up logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


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
            logger.info(
                f"Loaded {len(links)} previously posted job links from {file_path}"
            )
        except IOError as e:
            logger.error(f"Error reading posted jobs file {file_path}: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred while loading posted jobs: {e}")
    else:
        logger.info(
            f"Posted jobs file not found: {file_path}. A new one will be created."
        )
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


def _format_telegram_message(job_post: dict, include_date: bool = False) -> str:
    """Constructs the core message parts for a job posting."""
    clean_title = html.escape(job_post.get("title", "No Title"))
    clean_description = html.escape(
        job_post.get("description", "No description available.")
    )
    clean_tags = ", ".join(job_post.get("tags", []))
    if clean_tags:
        clean_tags = html.escape(clean_tags)

    message_parts = [
        f"✨ <b><u>New Job Posting - {job_post.get('source', 'Unknown')}</u></b> ✨",
        f"<b>Title:</b> {clean_title}",
        f"<b>Link:</b> <a href='{job_post.get('link', '#')}'>View Job</a>",
    ]

    # Add date only if requested
    if include_date:
        message_parts.append(f"<b>Posted:</b> {job_post.get('posted_date', 'N/A')}")

    if clean_tags:
        message_parts.append(f"<b>Tags:</b> {clean_tags}")

    message_parts.append("\n<b>Full Description:</b>")
    message_parts.append(f"<pre>{clean_description}</pre>")
    return "\n".join(message_parts)


def _truncate_message(
    full_message: str, job_post: dict, include_date: bool = False
) -> str:
    """Truncates the message if it exceeds Telegram's length limit."""
    if len(full_message) <= 4096:
        return full_message

    # Reconstruct parts to find the description start and truncate only it
    clean_title = html.escape(job_post.get("title", "No Title"))
    clean_tags = ", ".join(job_post.get("tags", []))
    if clean_tags:
        clean_tags = html.escape(clean_tags)

    # Calculate length of static parts
    static_parts_base = (
        f"✨ <b><u>New Job Posting - {job_post.get('source', 'Unknown')}</u></b> "
        f"✨\n<b>Title:</b> {clean_title}\n<b>Link:</b> "
        f"<a href='{job_post.get('link', '#')}'>View Job Now!</a>"
    )

    static_parts_len = len(static_parts_base)

    # Add date length if included
    if include_date:
        static_parts_len += len(
            f"\n<b>Posted:</b> {job_post.get('posted_date', 'N/A')}"
        )

    if clean_tags:
        static_parts_len += len(f"\n<b>Tags:</b> {clean_tags}")
    static_parts_len += len("\n\n<b>Full Description:</b>\n<pre></pre>")

    max_desc_len = (
        4096
        - static_parts_len
        - len("\n\n... (description truncated due to length limit)")
    )

    if max_desc_len < 50:  # Ensure a minimum description length if possible
        max_desc_len = 50

    original_description = html.escape(
        job_post.get("description", "No description available.")
    )
    truncated_description = (
        original_description[:max_desc_len]
        + "\n\n... (description truncated due to length limit)"
    )

    message_parts = [
        f"✨ <b><u>New Job Posting - {job_post.get('source', 'Unknown')}</u></b> ✨",
        f"<b>Title:</b> {clean_title}",
        f"<b>Link:</b> <a href='{job_post.get('link', '#')}'>View Job Now!</a>",
    ]

    # Add date only if requested
    if include_date:
        message_parts.append(f"<b>Posted:</b> {job_post.get('posted_date', 'N/A')}")

    if clean_tags:
        message_parts.append(f"<b>Tags:</b> {clean_tags}")
    message_parts.append("\n<b>Full Description:</b>")
    message_parts.append(f"<pre>{truncated_description}</pre>")

    return "\n".join(message_parts)


@retry(
    stop=stop_after_attempt(3),  # Try sending message up to 3 times
    wait=wait_fixed(2),  # Wait 2 seconds between retries
    retry=retry_if_exception_type(telegram.error.TelegramError),
)
async def send_telegram_message(
    bot_token: str, chat_id: str, job_post: dict, include_date: bool = False
):
    """
    Sends a single job posting message to the specified Telegram chat/channel.
    Includes retry logic for network/API errors.

    Args:
        bot_token: Telegram bot token
        chat_id: Telegram chat ID
        job_post: Job posting dictionary
        include_date: Whether to include the posted date in the message (default: False)
    """
    bot = telegram.Bot(token=bot_token)
    full_message = _format_telegram_message(job_post, include_date)
    final_message = _truncate_message(full_message, job_post, include_date)

    try:
        await bot.send_message(
            chat_id=chat_id,
            text=final_message,
            parse_mode=telegram.constants.ParseMode.HTML,
            disable_web_page_preview=True,
            reply_markup=telegram.InlineKeyboardMarkup(
                [
                    [
                        telegram.InlineKeyboardButton(
                            text="View Job Now!", url=job_post.get("link", "#")
                        )
                    ]
                ]
            ),
        )
        logger.info(
            f"Telegram message sent for: {job_post['title']} "
            f"(Source: {job_post['source']})"
        )
        return True
    except telegram.error.TelegramError as e:
        logger.error(f"Error sending Telegram message for {job_post['title']}: {e}")
        # Re-raise the exception to trigger tenacity retry if it's a retriable error
        if "message is too long" in str(e).lower():
            # This is a non-retriable error for tenacity, as retrying won't fix length.
            # Handle specifically and do not re-raise to avoid useless retries.
            logger.error(
                f"Telegram message for {job_post['title']} is too long. "
                "Further truncation or manual review needed."
            )
            return False  # Indicate failure without retrying via tenacity
        elif (
            "chat not found" in str(e).lower()
            or "bad request: chat_id is empty" in str(e).lower()
            or "bot was blocked by the user" in str(e).lower()
        ):
            logger.error(
                "Invalid Telegram Chat ID or bot not in chat/blocked. "
                "This is likely a configuration error, not a transient network issue."
            )
            # These are typically configuration errors, not transient network issues,
            # so we return False without re-raising to prevent tenacity from retrying indefinitely.
            return False
        else:
            # For other Telegram errors (e.g., API issues, network problems), re-raise to retry
            raise e  # Tenacity will catch and retry

    except Exception as e:
        logger.error(
            f"An unexpected error occurred during Telegram sending for "
            f"{job_post['title']}: {e}"
        )
        # This is a general exception, let tenacity retry if configured to do so
        # or handle as a final failure. For this example, we let it pass through
        # to ensure it's logged and doesn't get stuck.
        return False
