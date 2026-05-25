FROM python:3.10-slim

# Set timezone to IST for accurate cron scheduling
ENV TZ=Asia/Kolkata
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY backend/ .

# Ensure data directory exists for SQLite
RUN mkdir -p /app/data

# Ensure start script is executable
RUN chmod +x /app/start.sh

# Run the API and scheduler
ENV PYTHONPATH=/app
CMD ["/app/start.sh"]
