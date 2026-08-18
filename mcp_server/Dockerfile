FROM python:3.14-slim

RUN apt-get update && apt-get install -y

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml .
COPY uv.lock .
COPY config.py .
COPY config.json .
COPY mcp_server/main.py .
RUN uv sync --no-dev

CMD ["uv", "run", "python", "main.py", "--host", "0.0.0.0", "--port", "9000"]