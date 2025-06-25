# Use slim base image
FROM python:3.12-slim

# Set environment
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set workdir
WORKDIR /app

# Install OS dependencies required for building packages like psutil, cryptography
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    build-essential \
    libffi-dev \
    libssl-dev \
    python3-dev \
    pkg-config \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt

# Copy app code
COPY . .

# Ensure the database directory exists
RUN mkdir -p /app/data && chmod 755 /app/data

# Expose the port (Render assigns a dynamic port via $PORT)
EXPOSE 10000

# Use Gunicorn to run Flask app from run.py
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:10000", "run:app"]
