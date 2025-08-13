FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for pty operations
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the server code
COPY . .

# Create projects directory structure
RUN mkdir -p projects/ide/Local projects/ide/Python

# Expose the port
EXPOSE 8080

# Run the server
CMD ["python", "server.py", "--port", "8080", "--address", "0.0.0.0"]