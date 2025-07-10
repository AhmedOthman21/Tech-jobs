# Use a slim Python image as base, which is good for smaller container sizes
FROM python:3.10-slim-bullseye

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies required for Chromium and general build tools
# 'chromium' is the browser itself.
# 'fonts-liberation', 'libasound2', etc., are common dependencies for Chromium in headless environments.
# Added apt-get clean and another update for robustness
RUN apt-get update && apt-get install -y --no-install-recommends \
    apt-utils && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
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
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy the requirements file first to leverage Docker caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code into the container
COPY . .

# Set environment variables for the Telegram Bot Token and Chat ID
# Removed sensitive ENV vars as they are passed via `docker run -e` in GitHub Actions
ENV POSTED_JOBS_FILE="posted_jobs.txt"
