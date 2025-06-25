# Use slim Python base image
FROM python:3.12-slim

# Avoid .pyc and enable unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies required to build `psutil` and other packages
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    python3-dev \
    libffi-dev \
    libssl-dev \
    build-essential \
    pkg-config \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app source code
COPY . .

# Create database directory
RUN mkdir -p /app/data && \
    chmod 755 /app/data

# Expose the port Render will map to
EXPOSE 10000

# Start the FastAPI app using Uvicorn
CMD ["uvicorn", "run:app", "--host", "0.0.0.0", "--port", "10000"]
