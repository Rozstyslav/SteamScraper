FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_NO_CACHE=1 \
    DATABASE_PATH=/data/steam_scraper.sqlite3 \
    BROWSER_BINARY=/usr/bin/chromium \
    BROWSER_HEADLESS=true

WORKDIR /app

RUN apt-get update \
    && apt-get install --no-install-recommends -y chromium chromium-driver xauth xvfb \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv==0.8.18

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY app ./app
COPY main.py ./main.py

RUN useradd --create-home --shell /usr/sbin/nologin appuser \
    && mkdir -p /data \
    && chown -R appuser:appuser /app /data

USER appuser

EXPOSE 8000

CMD ["xvfb-run", "--auto-servernum", ".venv/bin/uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
