# Polymarket Data Collector

A Python application that collects and stores Polymarket market data in PostgreSQL.

## Features

- **Market Discovery**: Fetches all available markets from Polymarket CLOB API
- **Real-Time Collection**: Collects midpoint prices every 1 minute (60s) for ACTIVE markets only
- **Time-Series Storage**: Optimized PostgreSQL schema with proper indexing for time-series queries
- **Concurrent Processing**: Batch API calls with semaphore-controlled concurrency

## Project Structure

```
polymarket-data-collector/
├── terraform/          # Infrastructure as code (PostgreSQL in Docker)
├── src/
│   ├── config.py       # Settings management
│   ├── database.py     # Async SQLAlchemy setup
│   ├── models.py       # Database models
│   ├── collectors/     # Data collection modules
│   └── main.py         # Application entry point
├── alembic/            # Database migrations
└── pyproject.toml      # Dependencies
```

## Prerequisites

- Python 3.9+
- Docker
- Terraform
- SSH access to GitHub (for installing exchange-adapters)

## Quick Start with Docker

The easiest way to run the collector is using Docker:

```bash
# Clone the repository
git clone https://github.com/sskys18/polymarket-data-collector.git
cd polymarket-data-collector

# Create .env file (optional - uses defaults if not provided)
cp .env.example .env
# Edit .env if you want to change the database password or other settings

# Start everything (PostgreSQL + Collector)
docker-compose up -d

# View logs
docker-compose logs -f collector

# Stop everything
docker-compose down
```

This will:
- Start PostgreSQL database on port 5432
- Run database migrations automatically
- Start the price collector (collects every 1 minute)
- Persist data in a Docker volume

## Installation (Manual)

### 1. Provision Database

```bash
cd terraform
terraform init
terraform apply -var="database_password=YOUR_SECURE_PASSWORD"
```

This will create:
- PostgreSQL 16 container on port 5433
- Persistent volume for data storage

### 2. Install Dependencies

```bash
cd ..
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

pip install -e .
```

This will install:
- `exchange-adapters` from GitHub
- SQLAlchemy with async support
- Pydantic for settings
- Alembic for migrations
- asyncpg for PostgreSQL"

### 3. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your database password:

```bash
DATABASE_URL=postgresql://polymarket:YOUR_PASSWORD@localhost:5433/polymarket_data
COLLECTION_INTERVAL_SECONDS=60  # 1 minute
BATCH_SIZE=100
MAX_CONCURRENT_REQUESTS=10
LOG_LEVEL=INFO
```

### 4. Run Database Migrations

```bash
alembic upgrade head
```

This creates the following tables:
- `markets` - Market metadata (active status, questions, etc.)
- `market_prices` - Unified time-series table for all midpoint prices

## Usage

### Start the Collector

```bash
python -m src.main
```

The application will:

1. **Discover Markets** - Fetch all markets from Polymarket CLOB API (once at startup)
2. **Real-Time Collection** - Collect midpoint prices for ACTIVE markets every 1 minute (continuous loop)

### Stop the Collector

Press `Ctrl+C` to gracefully shutdown.

## Database Schema

### `markets` Table

Stores market metadata:
- `token_id` (PK) - Unique token identifier
- `question` - Market question text
- `outcome` - Specific outcome for this token
- `active` / `closed` - Market status
- Indexes on `active` and `closed`

### `market_prices` Table

Unified time-series table for all midpoint prices:
- `id` (PK) - Auto-incrementing primary key
- `token_id` (FK) - Reference to market
- `price` - Midpoint price (DECIMAL 18,16) in range [0, 1]
- `timestamp` - Unix timestamp (seconds)
- `collected_at` - Database timestamp of collection
- Unique constraint on `(token_id, timestamp)`
- Composite indexes for time-series queries: `(timestamp, token_id)` and `(token_id, timestamp)`

## Query Examples

```sql
-- Get latest prices for all active markets
SELECT m.question, m.outcome, p.price, p.timestamp
FROM market_prices p
JOIN markets m ON p.token_id = m.token_id
WHERE m.active = true
ORDER BY p.timestamp DESC
LIMIT 100;

-- Get price history for a specific market
SELECT timestamp, price, collected_at
FROM market_prices
WHERE token_id = 'YOUR_TOKEN_ID'
ORDER BY timestamp ASC;

-- Get price changes over time (hourly snapshots)
SELECT
    token_id,
    MIN(price) as min_price,
    MAX(price) as max_price,
    AVG(price) as avg_price,
    COUNT(*) as data_points
FROM market_prices
WHERE timestamp >= EXTRACT(EPOCH FROM NOW() - INTERVAL '24 hours')
GROUP BY token_id;

-- Count total markets
SELECT COUNT(*) FROM markets;

-- Count active markets
SELECT COUNT(*) FROM markets WHERE active = true;

-- Count total price records
SELECT COUNT(*) FROM market_prices;
```

## Configuration

All settings are configured via environment variables in `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | - | PostgreSQL connection string (required) |
| `COLLECTION_INTERVAL_SECONDS` | 3600 | Seconds between price collections (1 hour) |
| `BATCH_SIZE` | 100 | API request batch size for midpoint fetching |
| `MAX_CONCURRENT_REQUESTS` | 10 | Max concurrent batch requests |
| `LOG_LEVEL` | INFO | Logging level (DEBUG, INFO, WARN, ERROR) |

## Troubleshooting

### Database Connection Errors

```bash
# Check if PostgreSQL is running
docker ps | grep polymarket_postgres

# Check logs
docker logs polymarket_postgres
```

### Missing Dependencies

```bash
# Reinstall with SSH key
pip install -e . --force-reinstall
```

### Migration Issues

```bash
# Generate new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1
```

## Testing

### Test API Methods

Before running the full collector, you can test API connectivity:

**Test Working Price Methods:**
```bash
python tests/test_working_prices.py
```

This will:
- Fetch active markets
- Test `get_midpoint()` API on sample tokens
- Display success rates and timing metrics
- Estimate full collection time

**Test API Connectivity:**
```bash
python tests/test_api_only.py
```

This will:
- Test cursor-based pagination
- Fetch all markets without database
- Verify API responses

### Prerequisites for Tests

Make sure you have:
1. Dependencies installed (`pip install -e .`)
2. Active internet connection for API calls

Database tests will require:
1. Database running (`terraform apply`)
2. Environment configured (`.env` file)
3. Migrations applied (`alembic upgrade head`)

## Development

### Create New Migration

```bash
alembic revision --autogenerate -m "Add new column"
alembic upgrade head
```

### Reset Database

```bash
# WARNING: This deletes all data
terraform destroy
terraform apply -var="database_password=YOUR_PASSWORD"
alembic upgrade head
```

## Architecture

- **Async I/O**: Uses asyncio and async SQLAlchemy for efficient concurrent operations
- **Batch API Processing**: Uses `get_midpoints()` batch API to fetch 100 tokens per request
- **Concurrent Execution**: `asyncio.gather()` processes multiple batches in parallel
- **Rate Limiting**: Semaphore limits to 10 concurrent requests to prevent API throttling
- **Time-Series Optimization**: Composite indexes on (timestamp, token_id) for fast queries
- **Error Handling**: Continues on individual failures, logs errors without stopping collection
- **Upsert Logic**: Prevents duplicates using PostgreSQL `ON CONFLICT DO NOTHING`
- **Two-Phase Strategy**:
  - Phase 2: Initial snapshot of ALL markets (~35,770 tokens) takes ~10-20 seconds
  - Phase 3: Hourly updates of ACTIVE markets (~2,000 tokens) takes ~1-2 seconds

## License

MIT

## References

- [Polymarket CLOB API Docs](https://docs.polymarket.com/)
- [Exchange Adapters GitHub](https://github.com/sskys18/exchange-adapter)
