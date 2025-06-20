FROM python:3.11-slim

WORKDIR /app

# Install system dependencies, pip, and then clean up
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    pip install --upgrade pip && \
    apt-get purge -y --auto-remove gcc && \
    rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make the entrypoint script executable inside the container
RUN chmod +x docker-entrypoint.sh

# Expose port and set the entrypoint
EXPOSE 8000
ENTRYPOINT ["./docker-entrypoint.sh"]
