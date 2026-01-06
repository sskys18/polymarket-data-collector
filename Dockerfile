FROM python:3.11-slim

WORKDIR /app

# Install git for installing exchange-adapters from GitHub
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml ./
COPY requirements.txt* ./

# Install dependencies
RUN pip install --no-cache-dir -e .

# Copy application code
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Run migrations and start the collector
CMD ["sh", "-c", "alembic upgrade head && python -m src.main"]
