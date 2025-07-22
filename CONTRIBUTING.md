# Contributing to Job Scraper

Thank you for taking the time to contribute! ✨

1. **Fork & clone**
   ```bash
   git clone https://github.com/YOURNAME/job-scraper.git
   cd job-scraper
   ```
2. **Set up environment**
   ```bash
   python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt -r requirements-dev.txt
   pre-commit install  # optional but recommended
   ```
3. **Create a branch**
   ```bash
   git checkout -b feature/my-awesome-feature
   ```
4. **Add tests & code**
   • Keep `black` formatting and import order (`isort`).
   • Run `pytest -q` before committing.
5. **Open a Pull Request**
   • Describe *what* and *why* clearly.
   • The CI must be green before review. 