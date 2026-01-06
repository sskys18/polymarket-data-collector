"""Simple test for historical data without time ranges"""

import asyncio
import logging

from core.http.client import HttpClient
from exchanges.polymarket.clob.constants import BASE_URL
from exchanges.polymarket.clob.rest_client import PolymarketClobRestClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_simple_history():
    """Test historical data with just interval parameter"""

    http = None
    try:
        http = HttpClient(base_url=BASE_URL, signer=None)
        client = PolymarketClobRestClient(http)

        # Get an active market
        logger.info("Finding an active market...")
        sampling_response = await client.get_sampling_markets()
        markets = sampling_response.get("data", []) if isinstance(sampling_response, dict) else []

        if not markets:
            logger.error("No markets found")
            return

        market = markets[0]
        tokens = market.get("tokens", [])
        if not tokens:
            logger.error("No tokens found")
            return

        token_id = tokens[0].get("token_id") or tokens[0].get("tokenId")
        question = market.get("question", "N/A")

        logger.info(f"Testing market: {question}")
        logger.info(f"Token ID: {token_id[:20]}...")

        # Try different intervals
        for interval in ["1h", "max"]:
            logger.info(f"\nTrying interval='{interval}'...")
            history = await client.get_price_history(market=token_id, interval=interval)

            logger.info(f"  Returned {len(history)} price points")
            if history and len(history) > 0:
                logger.info(f"  First: {history[0]}")
                logger.info(f"  Last: {history[-1]}")

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
    finally:
        if http:
            await http.close()


if __name__ == "__main__":
    asyncio.run(test_simple_history())
