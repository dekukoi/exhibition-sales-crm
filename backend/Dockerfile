FROM ghcr.io/astral-sh/uv:0.12.13 AS uv

FROM python:3.13.7-slim-trixie AS base
COPY --from=uv /uv /uvx /usr/local/bin/
WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    PATH="/app/.venv/bin:${PATH}" \
    PYTHONUNBUFFERED=1

COPY pyproject.toml uv.lock ./

FROM base AS runtime
RUN uv sync --frozen --no-install-project --no-dev
COPY app ./app
COPY migrations ./migrations
COPY alembic.ini ./
RUN uv sync --frozen --no-dev

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM base AS test
RUN uv sync --frozen --no-install-project
COPY app ./app
COPY migrations ./migrations
COPY alembic.ini ./
COPY tests ./tests
RUN uv sync --frozen

CMD ["pytest"]
