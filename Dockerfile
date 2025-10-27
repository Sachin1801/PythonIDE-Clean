# Multi-stage build for better efficiency
# Stage 1: Frontend build
FROM node:18-alpine AS frontend-builder

WORKDIR /app

# Copy frontend package files
COPY package*.json ./

# Create production environment file for build
# For local testing on main IDE, use port 10086
RUN echo "VUE_APP_WS_URL=ws://localhost:10086" > .env.production

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

# Copy deployment scripts
COPY deployment/ ./deployment/

# Copy built frontend from previous stage
COPY --from=frontend-builder /app/dist/ ./dist/

# Create mount points for both local and AWS EFS
RUN mkdir -p /tmp/pythonide-data/ide /mnt/efs/pythonide-data/ide

# Set environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV IDE_DATA_PATH=/mnt/efs/pythonide-data

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Start the application with initialization
WORKDIR /app/server

# Copy adminData directory for exam credentials
COPY adminData/ /app/adminData/

# Conditional startup based on IS_EXAM_MODE environment variable
CMD ["sh", "-c", "if [ \"$IS_EXAM_MODE\" = \"true\" ]; then echo 'Starting in EXAM mode...' && python /app/server/init_exam_users.py && python /app/server/ensure_efs_directories.py && python server.py; else echo 'Starting in NORMAL mode...' && /app/deployment/sync-student-directories.sh && python /app/server/auto_init_users.py && python /app/server/ensure_efs_directories.py && python server.py; fi"]