# Use slim Python base
FROM python:3.12-slim

# Set environment vars
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app source
COPY . .

# Create the persistent data directory
RUN mkdir -p /app/data

# Use the persistent volume for SQLite
ENV DATABASE_URL=sqlite:////app/data/books.db

# Expose the port Gunicorn will run on
EXPOSE 5054

# Start the app using Gunicorn
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5054", "run:app"]