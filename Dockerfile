FROM python:3.14-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

COPY . .
RUN uv sync --frozen

EXPOSE 5000

CMD ["uv", "run", "gunicorn", "--workers", "4", "--bind", "0.0.0.0:5000", "run:app"]
