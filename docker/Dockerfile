# Use Alpine Linux for a much smaller base image
FROM python:3.10-alpine

# Set the working directory for the application inside the container.
# All subsequent commands will operate relative to this directory.
WORKDIR /app

# Install essential system dependencies for Chromium on Alpine
# Alpine uses apk package manager and has different package names
RUN apk add --no-cache \
    chromium \
    nss \
    freetype \
    freetype-dev \
    harfbuzz \
    ca-certificates \
    ttf-freefont

# Copy the Python dependency file first.
# This leverages Docker's layer caching: if requirements.txt doesn't change,
# pip install step won't rerun, speeding up subsequent builds.
COPY requirements.txt .

# Install build dependencies, Python dependencies, and then remove build dependencies
RUN apk add --no-cache --virtual .build-deps gcc musl-dev libffi-dev && \
    pip install --no-cache-dir -r requirements.txt && \
    apk del .build-deps

# Copy the entire application code into the container.
# This should be done after dependencies to maximize caching efficiency.
COPY . .

# Add a non-root user and switch to it
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser

# Set environment variables for Chromium to work properly in Alpine
ENV CHROME_BIN=/usr/bin/chromium-browser
ENV CHROME_PATH=/usr/lib/chromium/
ENV POSTED_JOBS_FILE="posted_jobs.txt"

# Change permissions of the /app directory to ensure all users can read and execute files
RUN chmod -R 755 /app

# CMD instruction is omitted here. The execution command will be explicitly defined
# in the GitHub Actions workflow using `docker run` to provide maximum flexibility
# for passing runtime arguments and mounting volumes.
CMD ["python", "main.py"]