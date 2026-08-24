# Mock Backend Bukowy Dwór — obraz kontenera (Podman/Docker)
FROM python:3.12-slim

WORKDIR /app

# zależności
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# aplikacja
COPY main.py .
COPY data/ ./data/

# port API
EXPOSE 8011

# uruchomienie (0.0.0.0 — dostęp z maszyny Podman i tunelu)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8011"]
