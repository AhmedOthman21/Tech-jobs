from unittest.mock import AsyncMock, mock_open, patch

import pytest
import telegram

from src.utils.telegram_notifier import (
    add_posted_job_link,
    load_posted_job_links,
    send_telegram_message,
)


# Test load_posted_job_links
def test_load_posted_job_links_existing_file():
    """Test loading links from an existing file."""
    mock_file_content = "link1\nlink2\nlink3\n"
    with patch("builtins.open", mock_open(read_data=mock_file_content)), patch(
        "os.path.exists", return_value=True
    ):
        links = load_posted_job_links("test_file.txt")
        assert links == {"link1", "link2", "link3"}


def test_load_posted_job_links_non_existing_file():
    """Test loading links when file does not exist."""
    with patch("os.path.exists", return_value=False):
        links = load_posted_job_links("non_existent.txt")
        assert links == set()


def test_load_posted_job_links_empty_file():
    """Test loading links from an empty file."""
    with patch("builtins.open", mock_open(read_data="")), patch(
        "os.path.exists", return_value=True
    ):
        links = load_posted_job_links("empty.txt")
        assert links == set()


# Test add_posted_job_link
def test_add_posted_job_link():
    """Test adding a link to the file."""
    m = mock_open()
    with patch("builtins.open", m):
        add_posted_job_link("new_links.txt", "new_link_4")
        m.assert_called_once_with("new_links.txt", "a", encoding="utf-8")
        handle = m()
        handle.write.assert_called_once_with("new_link_4\n")


# Test send_telegram_message (Requires async mocking)
@pytest.mark.asyncio
@patch("src.utils.telegram_notifier.telegram.Bot")
async def test_send_telegram_message_success(mock_bot_class):
    """Test successful sending of a Telegram message."""
    mock_bot_instance = AsyncMock()
    mock_bot_class.return_value = mock_bot_instance

    job_post = {
        "title": "Test Job",
        "link": "http://test.com/job",
        "description": "This is a test description.",
        "source": "TestSource",
        "tags": ["python", "devops"],
        "posted_date": "2024-01-01",
    }

    result = await send_telegram_message("fake_token", "fake_chat_id", job_post, False)

    assert result is True
    mock_bot_class.assert_called_once_with(token="fake_token")
    mock_bot_instance.send_message.assert_called_once()
    args, kwargs = mock_bot_instance.send_message.call_args
    assert kwargs["chat_id"] == "fake_chat_id"
    assert "Test Job" in kwargs["text"]
    assert "This is a test description" in kwargs["text"]
    assert "python, devops" in kwargs["text"]
    assert kwargs["parse_mode"] == telegram.constants.ParseMode.HTML


@pytest.mark.asyncio
@patch("src.utils.telegram_notifier.telegram.Bot")
async def test_send_telegram_message_too_long(mock_bot_class):
    """Test handling of message too long error."""
    mock_bot_instance = AsyncMock()
    mock_bot_class.return_value = mock_bot_instance
    mock_bot_instance.send_message.side_effect = telegram.error.TelegramError(
        "message is too long"
    )

    job_post = {
        "title": "Long Test Job",
        "link": "http://test.com/long_job",
        "description": "a" * 5000,  # Very long description
        "source": "LongSource",
        "tags": [],
        "posted_date": "2024-01-01",
    }

    result = await send_telegram_message("fake_token", "fake_chat_id", job_post, False)
    assert result is False  # Should not retry, just fail
    # Ensure truncation logic was applied
    args, kwargs = mock_bot_instance.send_message.call_args
    assert "... (description truncated due to length limit)" in kwargs["text"]


@pytest.mark.asyncio
@patch("src.utils.telegram_notifier.telegram.Bot")
async def test_send_telegram_message_chat_not_found(mock_bot_class):
    """Test handling of chat not found error (non-retriable)."""
    mock_bot_instance = AsyncMock()
    mock_bot_class.return_value = mock_bot_instance
    mock_bot_instance.send_message.side_effect = telegram.error.TelegramError(
        "chat not found"
    )

    job_post = {
        "title": "Error Job",
        "link": "http://error.com",
        "description": "",
        "source": "Err",
        "tags": [],
        "posted_date": "N/A",
    }

    result = await send_telegram_message(
        "fake_token", "invalid_chat_id", job_post, False
    )
    assert result is False  # Should not retry, just fail


@pytest.mark.asyncio
@patch("src.utils.telegram_notifier.telegram.Bot")
async def test_send_telegram_message_network_error_retries(mock_bot_class):
    """Test that transient network errors trigger retries."""
    mock_bot_instance = AsyncMock()
    mock_bot_class.return_value = mock_bot_instance
    # Simulate a transient network error on first two attempts, success on third
    mock_bot_instance.send_message.side_effect = [
        telegram.error.TelegramError("A timeout occurred"),
        telegram.error.TelegramError("Failed to connect to Telegram API"),
        None,  # Success on the third call
    ]

    job_post = {
        "title": "Retry Job",
        "link": "http://retry.com",
        "description": "",
        "source": "Retry",
        "tags": [],
        "posted_date": "N/A",
    }

    # We expect send_telegram_message to return True after 3 attempts,
    # as tenacity will handle the retries within this call.
    result = await send_telegram_message("fake_token", "fake_chat_id", job_post, False)
    assert result is True
    assert (
        mock_bot_instance.send_message.call_count == 3
    )  # Should have been called 3 times


@pytest.mark.asyncio
@patch("src.utils.telegram_notifier.telegram.Bot")
async def test_send_telegram_message_with_date(mock_bot_class):
    """Test sending a Telegram message with date included."""
    mock_bot_instance = AsyncMock()
    mock_bot_class.return_value = mock_bot_instance

    job_post = {
        "title": "Test Job with Date",
        "link": "http://test.com/job",
        "description": "This is a test description.",
        "source": "TestSource",
        "tags": ["python", "devops"],
        "posted_date": "2024-01-01",
    }

    result = await send_telegram_message("fake_token", "fake_chat_id", job_post, True)

    assert result is True
    mock_bot_class.assert_called_once_with(token="fake_token")
    mock_bot_instance.send_message.assert_called_once()
    args, kwargs = mock_bot_instance.send_message.call_args
    assert kwargs["chat_id"] == "fake_chat_id"
    assert "Test Job with Date" in kwargs["text"]
    assert "<b>Posted:</b> 2024-01-01" in kwargs["text"]
    assert kwargs["parse_mode"] == telegram.constants.ParseMode.HTML


@pytest.mark.asyncio
@patch("src.utils.telegram_notifier.telegram.Bot")
async def test_send_telegram_message_without_date(mock_bot_class):
    """Test sending a Telegram message without date included."""
    mock_bot_instance = AsyncMock()
    mock_bot_class.return_value = mock_bot_instance

    job_post = {
        "title": "Test Job without Date",
        "link": "http://test.com/job",
        "description": "This is a test description.",
        "source": "TestSource",
        "tags": ["python", "devops"],
        "posted_date": "2024-01-01",
    }

    result = await send_telegram_message("fake_token", "fake_chat_id", job_post, False)

    assert result is True
    mock_bot_class.assert_called_once_with(token="fake_token")
    mock_bot_instance.send_message.assert_called_once()
    args, kwargs = mock_bot_instance.send_message.call_args
    assert kwargs["chat_id"] == "fake_chat_id"
    assert "Test Job without Date" in kwargs["text"]
    assert (
        "<b>Posted:</b> 2024-01-01" not in kwargs["text"]
    )  # Date should not be included
    assert kwargs["parse_mode"] == telegram.constants.ParseMode.HTML
