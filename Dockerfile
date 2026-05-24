# Production-Ready Dockerfile for Job Market Analytics Dashboard
# Uses a lightweight, secure base image

FROM python:3.11-slim

# Set system environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8501

# Set workspace directory
WORKDIR /app

# Copy dependency requirements
COPY requirements.txt .

# Install dependencies (only standard python libraries are required for server.py)
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application directories & compiled databases
COPY src/ ./src/
COPY app/ ./app/
COPY data/ ./data/
COPY models/ ./models/

# Expose port
EXPOSE 8501

# Launch the pure-Python server
CMD ["python", "app/server.py"]
