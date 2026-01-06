# Changes Made - Real-Time Only Collection

## Summary
Removed historical snapshot collection and changed to 1-minute interval real-time collection only.

## What Changed

### 1. `src/main.py`
**Removed:**
- Phase 2: Historical snapshot collection for all markets
- Import of `HistoricalCollector`

**Changed:**
- Phase 2 → Real-time collection (was Phase 3)
- Collection runs every 1 minute instead of 1 hour

**Before:**
```python
# Phase 1: Market Discovery
# Phase 2: Snapshot Collection (ALL markets)
# Phase 3: Real-Time Collection (ACTIVE markets) - every 1 hour
```

**After:**
```python
# Phase 1: Market Discovery
# Phase 2: Real-Time Collection (ACTIVE markets) - every 1 minute
```

### 2. `src/config.py`
**Changed:**
```python
collection_interval_seconds: int = 60  # 1 minute (was 3600)
```

### 3. `README.md`
**Updated:**
- Removed "Initial Snapshot" feature
- Changed interval from "1 hour" to "1 minute"
- Updated workflow description

### 4. `.env.example`
**Updated:**
```bash
COLLECTION_INTERVAL_SECONDS=60  # 1 minute (was 3600)
```

## Why These Changes?

Based on testing, we found that:
1. **Historical data is NOT available** from Polymarket API for closed markets
2. Historical data is only available for **currently active markets**
3. To build historical data, we need to collect prices **while markets are active**

## New Behavior

The collector now:
1. **Discovers all markets** at startup (one-time)
2. **Collects prices every 1 minute** for active markets only (continuous loop)
3. Builds historical time-series data by storing each collection in the database

## Data Collection Pattern

With 1-minute intervals:
- **60 data points per hour** per active market
- **1,440 data points per day** per active market
- **~10,080 data points per week** per active market

This creates a high-resolution time-series dataset for all active markets!

## Files Not Changed

The following remain unchanged:
- `src/collectors/realtime.py` - Still collects midpoint prices for active markets
- `src/collectors/discovery.py` - Still discovers all markets
- `src/collectors/historical.py` - Remains in codebase but not used
- `src/models.py` - Database schema unchanged
- `src/database.py` - Database setup unchanged

## Migration Notes

If you have existing data from the historical snapshot:
- No migration needed
- Old snapshot data will remain in the database
- New collections will add to the same `market_prices` table
- No schema changes required
