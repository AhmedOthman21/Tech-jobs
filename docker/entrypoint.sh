#!/bin/sh

# Ensure the mounted posted_jobs.txt has correct permissions
# Use 'set -x' for debugging if needed: set -x

if [ -f "$POSTED_JOBS_FILE" ]; then
    echo "Setting write permissions for $POSTED_JOBS_FILE"
    chmod +w "$POSTED_JOBS_FILE"
else
    echo "$POSTED_JOBS_FILE not found, will be created by the application."
fi

# Execute the main application
exec python main.py
