# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy bot requirements
COPY requirements-bot.txt .

# Install dependencies
RUN pip install -r requirements-bot.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p storage/uploads logs

# Expose port (if needed for webhooks)
EXPOSE 8000

# Run the bot
CMD ["python", "run.py", "bot"]