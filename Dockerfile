FROM ghcr.io/astral-sh/uv:debian-slim

WORKDIR /app

COPY .python-version pyproject.toml uv.lock ./
RUN uv venv .venv
ENV VIRTUAL_ENV="/app/.venv"
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN uv sync

COPY . .
ENV PYTHONPATH=/app

CMD .venv/bin/python3 src/main.py