FROM python:3.13-slim-bullseye
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
RUN apt-get update && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml /app/
COPY uv.lock /app/
RUN uv sync --frozen --compile-bytecode

COPY ../api /app/api
COPY ../models /app/models
COPY settings.py /app/

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]
