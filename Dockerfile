# Use slim Python base image for smaller footprint
FROM python:3.12-slim

# Avoid writing .pyc files and enable unbuffered logging (good for Docker)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies required for psutil and other packages
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all source code
COPY . .

# Create directory for SQLite database (used in volume)
RUN mkdir -p /app/data

# Set environment variables for multi-user authentication
ENV DATABASE_URL=sqlite:////app/data/books.db
ENV WTF_CSRF_ENABLED=True

# Default admin credentials (override with docker run -e or docker-compose)
# These defaults should be changed in production via environment variables
ENV ADMIN_EMAIL=admin@bibliotheca.local
ENV ADMIN_USERNAME=admin

# Flask environment (using FLASK_DEBUG instead of deprecated FLASK_ENV)
ENV FLASK_DEBUG=false

# Create entrypoint script for initialization
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Expose internal port used by Gunicorn
EXPOSE 5054

# Use custom entrypoint that handles migration
ENTRYPOINT ["docker-entrypoint.sh"]

# Start the app with Gunicorn in production mode
# Use WORKERS environment variable for Gunicorn workers Default to 6 workers if not specified
ENV WORKERS=6
CMD ["sh", "-c", "gunicorn -w $WORKERS -b 0.0.0.0:5054 run:app"]
