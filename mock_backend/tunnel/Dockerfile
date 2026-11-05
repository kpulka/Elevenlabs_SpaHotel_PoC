# Mock backend for Bukowy Dwór — container image (Podman/Docker)
FROM python:3.12-slim

WORKDIR /app

# Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application
COPY main.py .
COPY data/ ./data/

# API port
EXPOSE 8011

# Start command (0.0.0.0 so the container port and the tunnel can reach it)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8011"]
