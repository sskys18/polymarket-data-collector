"""Show token IDs for closed markets"""

import asyncio
import logging

from core.http.client import HttpClient
from exchanges.polymarket.clob.constants import BASE_URL
from exchanges.polymarket.clob.rest_client import PolymarketClobRestClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def show_closed_market_tokens():
    """Display token IDs for closed markets"""

    http = None
    try:
        http = HttpClient(base_url=BASE_URL, signer=None)
        client = PolymarketClobRestClient(http)

        logger.info("Fetching closed markets...")

        response = await client.get_markets(next_cursor="MA==")
        markets = response.get("data", []) if isinstance(response, dict) else []

        closed_count = 0
        logger.info("\n" + "=" * 100)
        logger.info("CLOSED MARKETS - Token IDs")
        logger.info("=" * 100)

        for market in markets:
            if market.get("closed") and closed_count < 10:
                closed_count += 1

                question = market.get("question", "N/A")
                end_date = market.get("end_date_iso", "N/A")
                tokens = market.get("tokens", [])

                logger.info(f"\n{closed_count}. Market: {question}")
                logger.info(f"   End Date: {end_date}")
                logger.info(f"   Closed: {market.get('closed')}")
                logger.info(f"   Active: {market.get('active')}")

                for i, token in enumerate(tokens, 1):
                    token_id = token.get("token_id") or token.get("tokenId")
                    outcome = token.get("outcome", "N/A")
                    logger.info(f"   Token {i}: {outcome}")
                    logger.info(f"   Token ID: {token_id}")

        logger.info("\n" + "=" * 100)

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
    finally:
        if http:
            await http.close()


if __name__ == "__main__":
    asyncio.run(show_closed_market_tokens())
