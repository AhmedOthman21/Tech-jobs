import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

import scraper

parse_date_string = scraper.parse_date_string
is_job_posting = scraper.is_job_posting
_extract_link = scraper._extract_link
_extract_date = scraper._extract_date


# --- Tests for parse_date_string ---

def test_parse_date_string_today():
    """Test parsing 'today' date string."""
    parsed_date = parse_date_string("today")
    assert (datetime.now().date() - parsed_date.date()).days == 0


def test_parse_date_string_yesterday():
    """Test parsing 'yesterday' date string."""
    parsed_date = parse_date_string("yesterday")
    assert (datetime.now().date() - parsed_date.date()).days == 1


def test_parse_date_string_relative_days_ago():
    """Test parsing 'X days ago' string."""
    parsed_date = parse_date_string("5 days ago")
    assert (datetime.now().date() - parsed_date.date()).days == 5


def test_parse_date_string_arabic_relative():
    """Test parsing Arabic relative dates like 'منذ 2 يوم'."""
    parsed_date = parse_date_string("منذ 2 يوم")
    assert (datetime.now().date() - parsed_date.date()).days == 2


def test_parse_date_string_future_date():
    """Test parsing a future date string (should be today)."""
    parsed_date = parse_date_string("1 day from now")
    assert parsed_date.date() == datetime.now().date()


def test_parse_date_string_unparseable():
    """Test behavior for an unparseable date string (should default to today's date)."""
    parsed_date = parse_date_string("some random date string")
    assert parsed_date.date() == datetime.now().date()


# --- Tests for is_job_posting ---


@pytest.mark.parametrize(
    "title, description, title_keywords, desc_keywords, expected",
    [
        ("DevOps Engineer Position", "Requires cloud experience",
         ["devops"], ["cloud"], True),
        ("Software Developer", "Needs Python skills", ["sre"], ["python"], False),
        ("SRE opening", "Cloud operations", ["sre"], ["devops"], False),
        ("DevOps Lead", "Looking for senior", ["devops"], ["junior"], False),
        ("DevOps Junior", "Entry-level position", ["devops"],
         ["entry-level"], True),
        ("Cloud Architect", "AWS, Azure experience", ["cloud"],
         ["aws", "azure"], True),
        ("Site Reliability Engineer", "System monitoring", ["site reliability"],
         ["monitoring"], True),
        ("Not Relevant Title", "Not relevant description", ["devops"],
         ["cloud"], False),
        ("DevOps Engineer", "Contract role", ["devops"], [], True),
        ("DevOps Engineer", "Contract role", ["devops"], ["contract"], True),
    ],
)
def test_is_job_posting(title, description, title_keywords, desc_keywords, expected):
    """Test various scenarios for job posting relevance."""
    assert is_job_posting(title, description, title_keywords, desc_keywords) == expected


# --- Tests for _extract_link ---


def test_extract_link_from_link_selector():
    """Test extracting link using the primary link selector."""
    mock_card = Mock(spec=WebElement)
    mock_link_element = Mock(spec=WebElement)
    mock_link_element.get_attribute.return_value = "http://example.com/job1"
    mock_card.find_element.return_value = mock_link_element

    mock_title_element = Mock(spec=WebElement)
    mock_title_element.tag_name = 'div'
    mock_title_element.get_attribute.return_value = None
    mock_title_element.find_element.side_effect = NoSuchElementException

    link = _extract_link(mock_card, mock_title_element, "a.job-link", "Test Site")
    assert link == "http://example.com/job1"
    mock_card.find_element.assert_called_once_with(By.CSS_SELECTOR, "a.job-link")
    mock_title_element.get_attribute.assert_not_called()
    mock_title_element.find_element.assert_not_called()
    mock_card.get_attribute.assert_not_called()


def test_extract_link_from_title_element():
    """Test extracting link from title element as a fallback (title_element is <a>)."""
    mock_card = Mock(spec=WebElement)
    mock_title_element = Mock(spec=WebElement)
    mock_title_element.tag_name = 'a'
    mock_title_element.get_attribute.return_value = "http://example.com/job2"

    mock_card.find_element.side_effect = NoSuchElementException(
        "Mock: Primary link selector not found"
    )

    link = _extract_link(mock_card, mock_title_element, "a.job-link", "Test Site")
    assert link == "http://example.com/job2"
    mock_card.find_element.assert_called_once_with(By.CSS_SELECTOR, "a.job-link")
    mock_title_element.get_attribute.assert_called_once_with("href")
    mock_title_element.find_element.assert_not_called()
    mock_card.get_attribute.assert_not_called()


def test_extract_link_from_title_element_nested_link():
    """Test extracting link from a nested <a> tag within the title element."""
    mock_card = Mock(spec=WebElement)
    mock_title_element = Mock(spec=WebElement)
    mock_title_element.tag_name = 'div'

    mock_nested_link = Mock(spec=WebElement)
    mock_nested_link.get_attribute.return_value = "http://example.com/job_nested"
    mock_title_element.find_element.return_value = mock_nested_link

    mock_card.find_element.side_effect = NoSuchElementException(
        "Mock: Primary link selector not found"
    )

    link = _extract_link(mock_card, mock_title_element, "a.job-link", "Test Site")
    assert link == "http://example.com/job_nested"
    mock_card.find_element.assert_called_once_with(By.CSS_SELECTOR, "a.job-link")
    mock_title_element.get_attribute.assert_not_called()
    mock_title_element.find_element.assert_called_once_with(By.TAG_NAME, 'a')
    mock_nested_link.get_attribute.assert_called_once_with("href")
    mock_card.get_attribute.assert_not_called()


def test_extract_link_from_card_itself():
    """Test extracting link when the card itself is the link element."""
    mock_card = Mock(spec=WebElement)
    mock_card.tag_name = "a"
    mock_card.get_attribute.return_value = "http://example.com/job3"

    mock_card.find_element.side_effect = NoSuchElementException(
        "Mock: Link selector fails"
    )

    mock_title_element = Mock(spec=WebElement)
    mock_title_element.tag_name = 'span'
    mock_title_element.get_attribute.return_value = None
    mock_title_element.find_element.side_effect = NoSuchElementException(
        "Mock: No nested link in title"
    )

    link = _extract_link(mock_card, mock_title_element, "a.job-link", "Test Site")
    assert link == "http://example.com/job3"
    mock_card.find_element.assert_called_once_with(By.CSS_SELECTOR, "a.job-link")
    mock_title_element.get_attribute.assert_not_called()
    mock_title_element.find_element.assert_called_once_with(By.TAG_NAME, 'a')
    mock_card.get_attribute.assert_called_once_with("href")


def test_extract_link_not_found_all_fallbacks_fail():
    """Test when no link can be found through any fallback."""
    mock_card = Mock(spec=WebElement)
    mock_card.find_element.side_effect = NoSuchElementException(
        "Mock: Link selector fails"
    )

    mock_title_element = Mock(spec=WebElement)
    mock_title_element.tag_name = 'p'
    mock_title_element.get_attribute.return_value = None
    mock_title_element.find_element.side_effect = NoSuchElementException(
        "Mock: No nested link in title"
    )

    mock_card.tag_name = "div"

    link = _extract_link(mock_card, mock_title_element, "a.job-link", "Test Site")
    assert link == ""

    mock_card.find_element.assert_called_once_with(By.CSS_SELECTOR, "a.job-link")
    mock_title_element.get_attribute.assert_not_called()
    mock_title_element.find_element.assert_called_once_with(By.TAG_NAME, 'a')
    mock_card.get_attribute.assert_not_called()

# --- Tests for _extract_date ---


def test_extract_date_found():
    """Test extracting date when the element is found."""
    mock_card = Mock(spec=WebElement)
    mock_date_element = Mock(spec=WebElement)
    mock_date_element.text = "yesterday"
    mock_card.find_element.return_value = mock_date_element

    with pytest.MonkeyPatch.context() as monkeypatch:
        expected_datetime_yesterday = datetime.now() - timedelta(days=1)

        def mock_parse_date_string_with_element(date_str, date_element=None):
            if date_str == "yesterday":
                return expected_datetime_yesterday
            return datetime.now()
        monkeypatch.setattr(scraper, "parse_date_string",
                            mock_parse_date_string_with_element)

        date = _extract_date(mock_card, ".date", "Test Site")
        assert date.date() == expected_datetime_yesterday.date()
        mock_card.find_element.assert_called_once_with(By.CSS_SELECTOR, ".date")


def test_extract_date_not_found():
    """Test extracting date when the element is not found (should default to today's date)."""
    mock_card = Mock(spec=WebElement)
    mock_card.find_element.side_effect = NoSuchElementException(
        "Mock: Date element not found"
    )

    with pytest.MonkeyPatch.context() as monkeypatch:
        # No need for expected_now_datetime here, it was unused and removed.
        # The test directly asserts _extract_date's return when NoSuchElementException occurs.
        # We still mock parse_date_string for the sake of the test environment setup,
        # but in this specific branch of _extract_date, parse_date_string is not called.
        def mock_parse_date_string_with_element(date_str, date_element=None):
            # This mock won't be called in this specific test path, but it's good to define it
            # consistently with how it's set up in other date tests.
            return datetime.now()
        monkeypatch.setattr(scraper, "parse_date_string",
                            mock_parse_date_string_with_element)

        date = _extract_date(mock_card, ".date", "Test Site")
        assert date.date() == datetime.now().date()
        mock_card.find_element.assert_called_once_with(By.CSS_SELECTOR, ".date")
        # Removed assertion for parse_date_string as it's not called in this branch
