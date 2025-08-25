# Multi-stage build for better efficiency
# Stage 1: Frontend build
FROM node:18-alpine AS frontend-builder

WORKDIR /app

# Copy frontend package files
COPY package*.json ./
COPY .env.production ./

# Install dependencies (including dev dependencies for build)
RUN npm ci

# Copy frontend source
COPY src/ ./src/
COPY public/ ./public/
COPY vue.config.js ./
COPY babel.config.js ./

# Build frontend
RUN npm run build

# Stage 2: Python runtime
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install only essential system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY server/requirements.txt ./server/
RUN pip install --no-cache-dir -r server/requirements.txt

# Copy server code
COPY server/ ./server/

# Copy built frontend from previous stage
COPY --from=frontend-builder /app/dist/ ./dist/

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
    CMD curl -f http://localhost:8080/health || exit 1

# Start the application
WORKDIR /app/server
CMD ["python", "server.py"]