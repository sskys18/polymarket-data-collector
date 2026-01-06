"""Historical price data backfill collector - collects current price snapshots for ALL markets"""

import asyncio
import logging
import time
from typing import Tuple

from exchanges.polymarket.clob.rest_client import PolymarketClobRestClient
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..models import MarketPrice

logger = logging.getLogger(__name__)

END_CURSOR = "LTE="


class HistoricalCollector:
    """Collector for current price snapshots of ALL markets (active + closed)"""

    def __init__(self, polymarket_client: PolymarketClobRestClient, db_session: AsyncSession):
        self.client = polymarket_client
        self.db = db_session
        self.semaphore = asyncio.Semaphore(settings.max_concurrent_requests)
        self.batch_size = 50
        self.snapshot_timestamp = int(time.time())  # Single timestamp for all snapshots

    async def _fetch_snapshot_for_token(self, token_id: str) -> bool:
        """Fetch and store current midpoint price snapshot for one token"""
        async with self.semaphore:
            try:
                result = await self.client.get_midpoint(token_id)
                price_value = result.get("mid") if isinstance(result, dict) else None

                if price_value is None:
                    logger.debug(f"No midpoint price for token: {token_id}")
                    return False

                # Store current price as snapshot in MarketPrice table
                record = {
                    "token_id": token_id,
                    "price": float(price_value),  # API 'mid' -> DB 'price'
                    "timestamp": self.snapshot_timestamp,
                }

                # Insert with conflict handling
                stmt = pg_insert(MarketPrice).values([record])
                stmt = stmt.on_conflict_do_nothing(
                    index_elements=["token_id", "timestamp"]
                )
                await self.db.execute(stmt)
                await self.db.commit()
                logger.debug(f"Stored snapshot for {token_id}: {price_value}")

                return True

            except Exception as e:
                logger.error(f"Failed to snapshot {token_id}: {e}")
                return False

    async def backfill_all_markets(self, max_tokens: int = 0) -> Tuple[int, int]:
        """Collect current price snapshots for ALL markets (active + closed)"""
        total = 0
        success = 0
        pending = []

        # Iterate through all markets with pagination
        next_cursor = "MA=="
        page_count = 0

        logger.info(f"Starting snapshot collection for ALL markets at timestamp {self.snapshot_timestamp}")

        while True:
            page_count += 1
            logger.info(f"Fetching markets for snapshot (page {page_count})")

            response = await self.client.get_markets(next_cursor=next_cursor)
            markets = response.get("data", []) if isinstance(response, dict) else []

            if not markets:
                break

            for market in markets:
                for token in market.get("tokens", []):
                    token_id = token.get("token_id") or token.get("tokenId")
                    if not token_id:
                        continue

                    total += 1
                    pending.append(
                        asyncio.create_task(self._fetch_snapshot_for_token(token_id))
                    )

                    # Process in batches for memory efficiency
                    if len(pending) >= self.batch_size:
                        results = await asyncio.gather(*pending)
                        success += sum(1 for r in results if r)
                        pending.clear()
                        logger.info(f"Snapshot progress: {success}/{total}")

                    if max_tokens and total >= max_tokens:
                        break

                if max_tokens and total >= max_tokens:
                    break

            next_cursor = response.get("next_cursor") if isinstance(response, dict) else None
            if not next_cursor or next_cursor == END_CURSOR:
                break

        # Process remaining
        if pending:
            results = await asyncio.gather(*pending)
            success += sum(1 for r in results if r)

        logger.info(f"Snapshot collection complete: {success}/{total} tokens")
        return success, total
