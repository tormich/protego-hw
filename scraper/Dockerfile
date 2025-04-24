FROM python:3.13-slim-bullseye
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
RUN apt-get update && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml /app/
COPY uv.lock /app/
RUN uv sync --frozen --compile-bytecode

COPY ../scraper /app/scraper
COPY ../models /app/models
COPY scrape.py /app/
COPY settings.py /app/

CMD ["uv", "run", "scrape.py"]
