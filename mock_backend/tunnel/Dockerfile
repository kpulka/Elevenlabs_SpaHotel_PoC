# Mock Backend Bukowy Dwór — obraz kontenera (Podman/Docker)
#
# Zbuduj z katalogu mock_backend/ (kontekstem jest cały katalog backendu,
# a nie tunnel/, bo ścieżki COPY są względne wobec kontekstu):
#
#   cd mock_backend
#   podman build -t bukowy-dwor-backend -f tunnel/Dockerfile .
#   podman run -d --name bukowy-dwor-backend -p 8011:8011 localhost/bukowy-dwor-backend
#
# Nazwa obrazu (localhost/bukowy-dwor-backend) jest wymagana przez tunnel/podman_start.sh.
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# zależności (wersje przypięte — patrz requirements.txt)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# aplikacja — wszystkie moduły importowane przez main.py muszą trafić do obrazu
COPY main.py schemas.py catalog.py store.py telegram.py ./
COPY data/ ./data/

# port API
EXPOSE 8011

# uruchomienie (0.0.0.0 — dostęp z maszyny Podman i tunelu)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8011"]
