# Base image selection: python:3.10-slim-bullseye provides a minimal Debian environment
# with Python installed, suitable for smaller and more secure container images.
FROM python:3.10-slim-bullseye

# Set the working directory for the application inside the container.
# All subsequent commands will operate relative to this directory.
WORKDIR /app

# Install essential system dependencies required for Chromium and general utilities.
# Chromium is the browser used by undetected_chromedriver.
# The list of libs (fonts, etc.) are common requirements for headless browser operation.
# `apt-utils` is included for robustness in apt operations.
# `apt-get clean` and `rm -rf /var/lib/apt/lists/*` are strategically placed to
# clear package cache, reducing the final image size and improving layer caching.
RUN apt-get update && apt-get install -y --no-install-recommends \
    apt-utils && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    \
    # Re-run update to ensure fresh package lists right before installation
    apt-get update && \
    apt-get install -y --no-install-recommends \
        chromium \
        fonts-liberation \
        libappindicator3-1 \
        libasound2 \
        libatk-bridge2.0-0 \
        libatk1.0-0 \
        libatspi2.0-0 \
        libcairo2 \
        libcups2 \
        libdbus-1-3 \
        libdrm2 \
        libgbm1 \
        libgdk-pixbuf2.0-0 \
        libglib2.0-0 \
        libnspr4 \
        libnss3 \
        libxcomposite1 \
        libxdamage1 \
        libxfixes3 \
        libxkbcommon0 \
        libxrandr2 \
        libxtst6 \
        xdg-utils && \
    # Final cleanup to remove downloaded package files and lists
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy the Python dependency file first.
# This leverages Docker's layer caching: if requirements.txt doesn't change,
# pip install step won't rerun, speeding up subsequent builds.
COPY requirements.txt .

# Install Python dependencies from requirements.txt.
# `--no-cache-dir` prevents pip from storing its cache, further reducing image size.
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application code into the container.
# This should be done after dependencies to maximize caching efficiency.
COPY . .

# Define an environment variable for the posted jobs file path.
# This allows the path to be overridden at runtime (e.g., by a volume mount in GitHub Actions)
# for persistence across container runs, while providing a sensible default.
# Sensitive environment variables (like API tokens) are NOT set here; they are injected
# at container runtime via secure mechanisms (e.g., GitHub Actions secrets).
ENV POSTED_JOBS_FILE="posted_jobs.txt"

# CMD instruction is omitted here. The execution command will be explicitly defined
# in the GitHub Actions workflow using `docker run` to provide maximum flexibility
# for passing runtime arguments and mounting volumes.
CMD ["python", "main.py"]