"""Main orchestration for Polymarket data collector"""

import asyncio
import logging
import time

from core.http.client import HttpClient
from exchanges.polymarket.clob.constants import BASE_URL
from exchanges.polymarket.clob.rest_client import PolymarketClobRestClient

from .collectors.discovery import MarketDiscoveryService
from .collectors.realtime import RealtimeCollector
from .config import settings
from .database import AsyncSessionLocal

logger = logging.getLogger(__name__)


async def main():
    """Main entry point for data collection"""
    # Configure logging
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger.info("Starting Polymarket Data Collector")
    logger.info(f"Collection interval: {settings.collection_interval_seconds}s")
    logger.info(f"Batch size: {settings.batch_size}")

    # Initialize Polymarket CLOB client (no auth for public endpoints)
    http = HttpClient(base_url=BASE_URL, signer=None)
    client = PolymarketClobRestClient(http)

    try:
        # Phase 1: Discover markets (run once at startup)
        logger.info("=" * 60)
        logger.info("PHASE 1: Market Discovery")
        logger.info("=" * 60)

        async with AsyncSessionLocal() as db:
            discovery = MarketDiscoveryService(client, db)
            token_ids = await discovery.discover_all_markets()
            logger.info(f"✓ Discovered {len(token_ids)} markets")

        # Phase 2: Start real-time collection loop (every 1 minute for active markets)
        logger.info("=" * 60)
        logger.info("PHASE 2: Real-Time Price Collection (ACTIVE markets only)")
        logger.info("=" * 60)
        logger.info(f"Collecting midpoint prices every {settings.collection_interval_seconds}s ({settings.collection_interval_seconds/60:.1f} minutes)...")

        iteration = 0
        while True:
            iteration += 1
            logger.info(f"--- Collection iteration {iteration} ---")

            try:
                start_time = time.time()
                async with AsyncSessionLocal() as db:
                    realtime = RealtimeCollector(client, db)
                    count = await realtime.collect_all_prices()
                    elapsed = time.time() - start_time
                    logger.info(f"✓ Collected {count} midpoint prices in {elapsed:.1f}s")

            except Exception as e:
                logger.error(f"✗ Collection failed: {e}", exc_info=True)

            # Wait for next interval
            logger.info(f"Next collection in {settings.collection_interval_seconds}s...")
            await asyncio.sleep(settings.collection_interval_seconds)

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise
    finally:
        await http.close()
        logger.info("Polymarket Data Collector stopped")


if __name__ == "__main__":
    asyncio.run(main())
