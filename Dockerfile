FROM python:3.11-slim

WORKDIR /app

# Install minimal system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose ports for GUI and API
EXPOSE 8080 5000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV NEXUSFORGE_ENV=production

# Run the main application
CMD ["python", "-m", "nexusforge.main"]
