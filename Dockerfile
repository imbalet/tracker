FROM ghcr.io/astral-sh/uv:debian-slim AS base

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_TOOL_BIN_DIR=/usr/local/bin

COPY .python-version pyproject.toml uv.lock alembic.ini ./


# Test

FROM base AS test
RUN uv sync --locked --no-install-project --group test

COPY . .
RUN uv pip install .
ENV PATH="/app/.venv/bin:$PATH"

ENTRYPOINT []
CMD ["pytest", "tests"]


# Production

FROM base AS prod
RUN uv sync --frozen --no-install-project --no-dev

COPY alembic ./alembic
COPY src ./src
RUN uv sync --frozen --no-dev --no-editable
ENV PATH="/app/.venv/bin:$PATH"

ENTRYPOINT []
CMD ["uv", "run", "-m", "--no-sync", "tracker.main"]