# --------- STAGE 1: Build Dependencies ---------
FROM python:3.12.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create a virtual environment to isolate python dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .

# Use BuildKit cache for pip to speed up repeated builds
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && \
    pip install -r requirements.txt

# --------- STAGE 2: Runtime Stage ---------
FROM python:3.12.11-slim AS runner

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/opt/venv/bin:$PATH"

# Install only the runtime dependencies (libmariadb3) and gosu for dropping root privileges
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmariadb3 \
    gosu \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create a secure non-root user
RUN adduser --disabled-password --gecos "" appuser

# Copy virtual environment from builder stage
COPY --from=builder --chown=appuser:appuser /opt/venv /opt/venv

# Copy application files
COPY --chown=appuser:appuser . .

# Ensure staticfiles and media directories exist and have correct permissions
RUN mkdir -p /app/staticfiles /app/media && \
    chown -R appuser:appuser /app/staticfiles /app/media && \
    chmod +x entrypoint.sh

# Collect static files during the build phase (prevents slow startup times)
# Pass dummy credentials to satisfy settings check without exposing real database/secrets
RUN SECRET_KEY=dummy_secret_key_for_collectstatic \
    DB_NAME=dummy_db \
    DB_USER=dummy_user \
    DB_PASSWORD=dummy_pass \
    DB_HOST=localhost \
    GOOGLE_CLIENT_ID=dummy_g \
    python manage.py collectstatic --noinput

# Switch to the non-root user
# USER appuser

EXPOSE 8000

# Native health check checking Django health view, avoiding curl installation
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

ENTRYPOINT ["./entrypoint.sh"]