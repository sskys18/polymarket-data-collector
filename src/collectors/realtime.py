"""Real-time price collector for active markets"""

import asyncio
import logging
import time
from typing import List

from exchanges.polymarket.clob.models.rest import BookRequest
from exchanges.polymarket.clob.rest_client import PolymarketClobRestClient
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..models import MarketPrice

logger = logging.getLogger(__name__)


def _chunk(items, size):
    """Split list into chunks"""
    for i in range(0, len(items), size):
        yield items[i : i + size]


class RealtimeCollector:
    """Collector for real-time midpoint prices of active markets"""

    def __init__(self, polymarket_client: PolymarketClobRestClient, db_session: AsyncSession):
        self.client = polymarket_client
        self.db = db_session
        self.batch_size = settings.batch_size
        self.semaphore = asyncio.Semaphore(settings.max_concurrent_requests)

    async def _get_active_token_ids(self) -> List[str]:
        """Get token IDs for active markets only"""
        response = await self.client.get_sampling_markets()
        markets = response.get("data", []) if isinstance(response, dict) else []

        token_ids = []
        for market in markets:
            # Skip closed or inactive markets
            if not market.get("active") or market.get("closed"):
                continue

            for token in market.get("tokens", []):
                token_id = token.get("token_id") or token.get("tokenId")
                if token_id:
                    token_ids.append(token_id)

        logger.debug(f"Found {len(token_ids)} active token IDs")
        return token_ids

    async def _fetch_batch_midpoints(self, chunk: List[BookRequest]) -> List[dict]:
        """Fetch midpoints for one batch with semaphore control"""
        async with self.semaphore:
            try:
                return await self.client.get_midpoints(chunk)
            except Exception as e:
                logger.error(f"Failed to fetch midpoints for batch: {e}")
                return []

    async def collect_all_prices(self) -> int:
        """Fetch and store midpoint prices for all active markets"""
        token_ids = await self._get_active_token_ids()

        if not token_ids:
            logger.warning("No active token IDs found")
            return 0

        # Build requests for all tokens (no side needed for midpoint)
        requests = [BookRequest(token_id=tid) for tid in token_ids]
        chunks = list(_chunk(requests, self.batch_size))

        # Fetch all batches concurrently
        timestamp = int(time.time())
        logger.info(f"Fetching midpoints for {len(token_ids)} tokens in {len(chunks)} batches")

        tasks = [self._fetch_batch_midpoints(chunk) for chunk in chunks]
        batch_results = await asyncio.gather(*tasks)

        # Flatten results and build records
        records = []
        for prices in batch_results:
            for p in prices:
                token_id = p.get("token_id")
                price_value = p.get("mid")  # API returns 'mid' field

                if token_id and price_value is not None:
                    records.append({
                        "token_id": token_id,
                        "price": float(price_value),  # Store 'mid' as 'price' in DB
                        "timestamp": timestamp,
                    })

        # Batch insert with conflict handling
        if records:
            stmt = pg_insert(MarketPrice).values(records)
            stmt = stmt.on_conflict_do_nothing(
                index_elements=["token_id", "timestamp"]
            )
            await self.db.execute(stmt)
            await self.db.commit()
            logger.info(f"Inserted {len(records)} midpoint price records")

        return len(records)
