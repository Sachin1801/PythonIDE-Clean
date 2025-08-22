# Production Dockerfile for Python IDE
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies and Node.js for frontend build
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY server/requirements.txt ./server/
RUN pip install --no-cache-dir -r server/requirements.txt

# Copy server code
COPY server/ ./server/

# Copy frontend source and build it
COPY package*.json ./
COPY src/ ./src/
COPY public/ ./public/
COPY .env.production ./
COPY vue.config.js ./
COPY babel.config.js ./

# Install frontend dependencies and build
RUN npm install && npm run build

# Create necessary directories
RUN mkdir -p server/projects/ide/Local \
    "server/projects/ide/Lecture Notes" \
    server/projects/ide/Assignments \
    server/projects/ide/Tests

# Set environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080').read()" || exit 1

# Start the application
WORKDIR /app/server
CMD ["python", "server.py"]