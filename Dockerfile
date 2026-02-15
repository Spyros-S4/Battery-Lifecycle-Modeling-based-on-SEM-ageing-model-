FROM python:3.11-slim

# Prevent Python from buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Copy metadata first (better Docker caching)
COPY pyproject.toml /app/
COPY src /app/src

# Install project + dev dependencies
RUN pip install --no-cache-dir -U pip \
    && pip install --no-cache-dir -e ".[dev]"

# Default command
CMD ["python", "-m", "sem.run"]
