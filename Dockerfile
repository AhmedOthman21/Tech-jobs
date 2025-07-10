# Use a slim Python image as base, which is good for smaller container sizes
FROM python:3.10-slim-bullseye

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies required for Chromium and general build tools
# 'chromium' is the browser itself.
# 'fonts-liberation', 'libasound2', etc., are common dependencies for Chromium in headless environments.
RUN apt-get update && apt-get install -y \
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
    libxshmfence6 \
    libxtst6 \
    xdg-utils \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Copy the requirements file first to leverage Docker caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code into the container
COPY . .

# Set environment variables for the Telegram Bot Token and Chat ID
# These will be populated by GitHub Actions secrets or Docker run commands
ENV TELEGRAM_BOT_TOKEN=""
ENV TELEGRAM_CHAT_ID=""
ENV POSTED_JOBS_FILE="posted_jobs.txt"
