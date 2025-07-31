FROM python:3.10-alpine

# Prevent Python from writing .pyc files to disc
ENV PYTHONDONTWRITEBYTECODE=1

# Ensure Python's output is unbuffered
ENV PYTHONUNBUFFERED=1

# Install Chromium and ChromeDriver dependencies
RUN apk add --no-cache \
    chromium \
    chromium-chromedriver \
    nss \
    freetype \
    freetype-dev \
    harfbuzz \
    ca-certificates \
    ttf-freefont \
    libjpeg-turbo \
    libpng

# Set environment variables for Chromium and ChromeDriver
ENV CHROME_BIN=/usr/bin/chromium-browser
ENV CHROME_PATH=/usr/lib/chromium/
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application code into the container
COPY . .

# Set the command to run the main application script
CMD ["python", "main.py"]
