FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files first for layer caching
COPY pyproject.toml uv.lock /app/

# Install dependencies (no project, just deps — faster cache hit on code changes)
RUN uv sync --frozen --no-install-project

# Copy source and install project
COPY src /app/src
RUN uv sync --frozen

CMD ["uv", "run", "python", "-m", "sem.run"]
