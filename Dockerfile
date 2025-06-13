# Use slim Python base image for smaller footprint
FROM python:3.12-slim

# Avoid writing .pyc files and enable unbuffered logging (good for Docker)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all source code
COPY . .

# Create directory for SQLite database (used in volume)
RUN mkdir -p /app/data

# Set environment variable for database URI (will point to volume-mounted path)
ENV DATABASE_URL=sqlite:////app/data/books.db

# Expose internal port used by Gunicorn
EXPOSE 5054

# Start the app with Gunicorn in production mode
# Use WORKERS environment variable for Gunicorn workers Default to 6 workers if not specified
ENV WORKERS=6
CMD ["sh", "-c", "gunicorn -w $WORKERS -b 0.0.0.0:5054 run:app"]
