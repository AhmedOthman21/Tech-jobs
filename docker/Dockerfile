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

# Install Python dependencies from requirements.txt.
# `--no-cache-dir` prevents pip from storing its cache, further reducing image size.
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application code into the container.
# This should be done after dependencies to maximize caching efficiency.
COPY . .

# Set environment variables for Chromium to work properly in Alpine
ENV CHROME_BIN=/usr/bin/chromium-browser
ENV CHROME_PATH=/usr/lib/chromium/
ENV POSTED_JOBS_FILE="posted_jobs.txt"

# CMD instruction is omitted here. The execution command will be explicitly defined
# in the GitHub Actions workflow using `docker run` to provide maximum flexibility
# for passing runtime arguments and mounting volumes.
CMD ["python", "main.py"]