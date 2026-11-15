# Mock backend (PMS for the Anna voice agent) — container image (Podman or Docker).
#
# Build context is the mock_backend/ directory (COPY paths are relative to it):
#
#   podman build -t bukowy-dwor-backend -f Dockerfile .      # from mock_backend/
#   docker build -t bukowy-dwor-backend -f mock_backend/Dockerfile mock_backend   # from repo root
#
# The image name (localhost/bukowy-dwor-backend) is what tunnel/podman_start.sh expects.
# Files excluded from the context (tests/, tunnel/, .env, caches) are listed in .dockerignore
# and .containerignore in this directory.
#
# Python is pinned to 3.12 (the same version CI runs). Change it here and in .github/workflows/ci.yml together.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=Europe/Warsaw

WORKDIR /app

# Time zone data: slim images have no tzdata, and without it TZ=Europe/Warsaw silently falls back to UTC.
RUN apt-get update \
    && apt-get install -y --no-install-recommends tzdata \
    && rm -rf /var/lib/apt/lists/*

# Dependencies first, so that code changes do not invalidate the pip layer. Versions are pinned in requirements.txt.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Application: everything in the build context except what .dockerignore excludes (tests/, tunnel/, .env, caches).
COPY . ./

# Directory for the SQLite database (ANNA_DB_PATH) when a volume is mounted there.
# Owned by the unprivileged user so that a fresh named volume inherits writable permissions.
RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app \
    && mkdir -p /var/lib/anna \
    && chown app:app /var/lib/anna
USER app

EXPOSE 8011

# Health check from the standard library (no curl in the image). urlopen raises on a non-2xx status.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import sys, urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8011/health', timeout=4).status == 200 else 1)"]

# 0.0.0.0 so that the port is reachable from the host and from the tunnel.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8011"]
