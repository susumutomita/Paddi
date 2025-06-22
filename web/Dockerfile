# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy the main app directory to access agents
COPY ../app /app/app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8080

# Run the application with gunicorn for production
CMD ["gunicorn", "--bind", ":8080", "--workers", "2", "--threads", "8", "--timeout", "120", "wsgi:app"]