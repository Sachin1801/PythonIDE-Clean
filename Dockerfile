# Multi-stage build for Python IDE
FROM node:18-alpine AS frontend-builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install ALL dependencies (including devDependencies for build)
RUN npm ci

# Copy source files
COPY babel.config.js ./
COPY vue.config.js ./
COPY jsconfig.json ./
COPY public ./public
COPY src ./src

# Build the frontend
RUN npm run build

# Python backend stage
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install
COPY server/requirements.txt server/
RUN pip install --no-cache-dir -r server/requirements.txt

# Copy backend code
COPY server/ server/

# Copy built frontend from previous stage
COPY --from=frontend-builder /app/dist dist/

# Create necessary directories
RUN mkdir -p server/projects/ide/Local \
    server/projects/ide/"Lecture Notes" \
    server/projects/ide/Assignments \
    server/projects/ide/Tests

# Expose port (Railway will override with PORT env var)
EXPOSE 8080

# Start the server
CMD ["python", "server/server.py"]