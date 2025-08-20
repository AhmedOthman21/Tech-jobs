FROM python:3.10-alpine

# Set the working directory for the application inside the container.
# All subsequent commands will operate relative to this directory.
WORKDIR /app

# Install essential system dependencies for Chromium on Alpine
RUN apk add --no-cache \
    chromium \
    chromium-chromedriver \
    nss \
    freetype \
    freetype-dev \
    harfbuzz \
    ca-certificates \
    ttf-freefont

COPY requirements.txt .

# Install build dependencies, Python dependencies, and then remove build dependencies
RUN apk add --no-cache --virtual .build-deps gcc musl-dev libffi-dev && \
    pip install --no-cache-dir -r requirements.txt && \
    apk del .build-deps

# Copy the entire application code into the container.
# This should be done after dependencies to maximize caching efficiency.
COPY . .

# Add a non-root user and group
RUN addgroup -S nonroot && adduser -S nonroot -G nonroot

# Prepare a writable chromedriver location for the non-root user
RUN mkdir -p /opt/chromedriver && \
    cp /usr/lib/chromium/chromedriver /opt/chromedriver/chromedriver && \
    chmod +x /opt/chromedriver/chromedriver && \
    chown -R nonroot:nonroot /opt/chromedriver && \
    chown -R nonroot:nonroot /app
USER nonroot

# Set environment variables for Chromium to work properly in Alpine
ENV CHROME_BIN=/usr/bin/chromium-browser
ENV CHROME_PATH=/usr/lib/chromium/
ENV CHROMEDRIVER_PATH=/opt/chromedriver/chromedriver
ENV POSTED_JOBS_FILE="posted_jobs.txt"

# Combined entrypoint logic and main command
CMD HOST_WORKSPACE_PATH="/gh_workspace"; \
    HOST_POSTED_JOBS_FILE="${HOST_WORKSPACE_PATH}/posted_jobs.txt"; \
    if [ -f "$HOST_POSTED_JOBS_FILE" ]; then \
        echo "Copying existing posted jobs from mounted workspace to /app/posted_jobs.txt"; \
        cp "$HOST_POSTED_JOBS_FILE" "$POSTED_JOBS_FILE"; \
    else \
        echo "Host posted_jobs.txt not found in mounted workspace, /app/posted_jobs.txt will be created by the application if needed."; \
        touch "$POSTED_JOBS_FILE"; \
    fi; \
    if [ ! -w "$POSTED_JOBS_FILE" ]; then \
        echo "Error: /app/posted_jobs.txt is not writable by the container user!"; \
        exit 1; \
    fi; \
    exec python main.py