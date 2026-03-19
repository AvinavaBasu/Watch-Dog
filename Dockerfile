FROM python:3.12-slim

LABEL maintainer="Watch Dog"
LABEL description="Amazon product availability monitor"

# Create non-root user
RUN groupadd -r watchdog --gid=1001 && \
    useradd -r -g watchdog --uid=1001 --shell=/bin/false watchdog

WORKDIR /app

# Install dependencies first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Create data directory for non-root user
RUN mkdir -p /app/data && chown -R watchdog:watchdog /app

USER watchdog

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; print('ok')" || exit 1

CMD ["python", "run.py", "run"]
