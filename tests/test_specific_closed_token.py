"""Test historical data for a specific closed market token"""

import asyncio
import logging

from core.http.client import HttpClient
from exchanges.polymarket.clob.constants import BASE_URL
from exchanges.polymarket.clob.rest_client import PolymarketClobRestClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_specific_token():
    """Test fetching historical data for a specific closed market token"""

    http = None
    try:
        http = HttpClient(base_url=BASE_URL, signer=None)
        client = PolymarketClobRestClient(http)

        # Use the Arizona State token from a closed market (March 2023)
        token_id = "73470541315377973562501025254719659796416871135081220986683321361000395461644"

        logger.info("=" * 80)
        logger.info("Testing Historical Data for Specific Closed Market Token")
        logger.info("=" * 80)
        logger.info(f"\nMarket: NCAAB: Arizona State vs. Nevada (March 15, 2023)")
        logger.info(f"Outcome: Arizona State")
        logger.info(f"Token ID: {token_id}")
        logger.info(f"Status: CLOSED")

        # Try different intervals
        intervals = ["max", "1d", "1h", "1w"]

        for interval in intervals:
            logger.info(f"\n--- Testing interval='{interval}' ---")

            history = await client.get_price_history(
                market=token_id,
                interval=interval
            )

            logger.info(f"Response: {len(history)} price points")

            if history and len(history) > 0:
                logger.info(f"✓ SUCCESS! Found historical data")
                logger.info(f"  First point: {history[0]}")
                logger.info(f"  Last point: {history[-1]}")

                # Show a few sample points
                if len(history) > 5:
                    logger.info(f"  Sample points (first 3):")
                    for i, point in enumerate(history[:3], 1):
                        logger.info(f"    {i}. Timestamp: {point.get('t')}, Price: {point.get('p')}")
            else:
                logger.info(f"✗ No data returned")

        logger.info("\n" + "=" * 80)

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
    finally:
        if http:
            await http.close()


if __name__ == "__main__":
    asyncio.run(test_specific_token())
