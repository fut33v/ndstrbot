# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy poetry files
COPY pyproject.toml poetry.lock* ./

# Install poetry
RUN pip install poetry

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --only=main --no-root

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p storage/uploads logs

# Expose port (if needed for webhooks)
EXPOSE 8000

# Run the bot
CMD ["python", "run.py"]