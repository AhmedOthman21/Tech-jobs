<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/python-3.10%2B-blue"/>
  <img alt="License" src="https://img.shields.io/badge/license-MIT-green"/>
  <a href="https://github.com/ahmedothman21/DevOps-jobs/actions">
    <img alt="CI" src="https://github.com/ahmedothman21/DevOps-jobs/actions/workflows/ci.yml/badge.svg"/>
  </a>
  <img alt="code style: black" src="https://img.shields.io/badge/code%20style-black-000000"/>
</p>

# Job Scraper

A robust job scraping solution that monitors job postings and sends notifications via Telegram.

## Features

- Automated job scraping from multiple sources
- Real-time Telegram notifications
- Customizable search criteria
- Duplicate detection
- Detailed job information extraction
- Docker support for easy deployment

## Project Structure

```
src/
├── scrapers/        # Job scraping implementation
├── utils/           # Utility functions and helpers
└── data_extractors/ # Data extraction and processing

docs/               # Documentation
├── api/            # API documentation
├── examples/       # Usage examples
└── guides/         # Setup and development guides

docker/            # Docker-related files
├── Dockerfile
└── Dockerfile.multi-stage
```

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd job-scraper
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure the application:
- Edit `config.py` with your desired settings
- Set up your Telegram bot token if using notifications

## Usage

1. Basic usage:
```bash
python main.py
```

2. With custom configuration:
```bash
python main.py --config custom_config.py
```

## Development

### Setup Development Environment

1. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

2. Set up pre-commit hooks:
```bash
pre-commit install
```

### Code Style

- We use isort for import sorting
- Follow Google Python Style Guide for docstrings
- Maximum line length is 88 characters

### Testing

Run tests using pytest:
```bash
pytest
```

## Docker Support

Build and run using Docker:

```bash
# Single-stage build
docker build -t job-scraper .

# Multi-stage build (recommended for production)
docker build -f docker/Dockerfile.multi-stage -t job-scraper .

# Run the container
docker run -d job-scraper
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- ChromeDriver - WebDriver for Chrome
- Selenium - Web browser automation
- python-telegram-bot - Telegram Bot API wrapper