FROM ghcr.io/astral-sh/uv:debian-slim

WORKDIR /app

COPY .python-version pyproject.toml uv.lock ./
RUN uv venv .venv
ENV VIRTUAL_ENV="/app/.venv"

RUN uv sync

COPY . .
RUN uv pip install .


CMD [".venv/bin/python3", "-m", "tracker.main"]