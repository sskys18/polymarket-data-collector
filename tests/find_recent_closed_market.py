"""Find the most recently closed market"""

import asyncio
import logging
from datetime import datetime

from core.http.client import HttpClient
from exchanges.polymarket.clob.constants import BASE_URL
from exchanges.polymarket.clob.rest_client import PolymarketClobRestClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def find_recent_closed_market():
    """Find the most recently closed market"""

    http = None
    try:
        http = HttpClient(base_url=BASE_URL, signer=None)
        client = PolymarketClobRestClient(http)

        logger.info("=" * 80)
        logger.info("Finding Most Recently Closed Markets")
        logger.info("=" * 80)

        closed_markets = []
        next_cursor = "MA=="

        # Search through multiple pages to find recent closed markets
        for page in range(20):
            response = await client.get_markets(next_cursor=next_cursor)
            markets = response.get("data", []) if isinstance(response, dict) else []

            for market in markets:
                if market.get("closed"):
                    end_date_str = market.get("end_date_iso")

                    try:
                        if end_date_str:
                            # Parse the end date
                            end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))

                            closed_markets.append({
                                "question": market.get("question", "N/A"),
                                "end_date_str": end_date_str,
                                "end_date": end_date,
                                "tokens": market.get("tokens", []),
                                "active": market.get("active"),
                                "closed": market.get("closed")
                            })
                    except:
                        continue

            next_cursor = response.get("next_cursor") if isinstance(response, dict) else None
            if not next_cursor or next_cursor == "LTE=":
                break

        # Sort by end date (most recent first)
        closed_markets.sort(key=lambda x: x["end_date"], reverse=True)

        logger.info(f"\nFound {len(closed_markets)} closed markets with valid end dates")
        logger.info("\n" + "=" * 80)
        logger.info("TOP 10 MOST RECENTLY CLOSED MARKETS")
        logger.info("=" * 80)

        for i, market in enumerate(closed_markets[:10], 1):
            logger.info(f"\n{i}. Market: {market['question']}")
            logger.info(f"   End Date: {market['end_date_str']}")
            logger.info(f"   Closed: {market['closed']}")
            logger.info(f"   Active: {market['active']}")

            tokens = market['tokens']
            for j, token in enumerate(tokens, 1):
                token_id = token.get("token_id") or token.get("tokenId")
                outcome = token.get("outcome", "N/A")
                logger.info(f"   Token {j}: {outcome}")
                logger.info(f"   Token ID: {token_id}")

        # Test historical data for the most recent closed market
        if closed_markets:
            logger.info("\n" + "=" * 80)
            logger.info("TESTING HISTORICAL DATA FOR MOST RECENT CLOSED MARKET")
            logger.info("=" * 80)

            most_recent = closed_markets[0]
            logger.info(f"\nMarket: {most_recent['question']}")
            logger.info(f"End Date: {most_recent['end_date_str']}")

            if most_recent['tokens']:
                token = most_recent['tokens'][0]
                token_id = token.get("token_id") or token.get("tokenId")
                outcome = token.get("outcome", "N/A")

                logger.info(f"Testing Token: {outcome}")
                logger.info(f"Token ID: {token_id}")

                for interval in ["max", "1h", "1d"]:
                    history = await client.get_price_history(
                        market=token_id,
                        interval=interval
                    )

                    logger.info(f"\n  interval='{interval}': {len(history)} price points")
                    if history and len(history) > 0:
                        logger.info(f"    ✓ First: {history[0]}")
                        logger.info(f"    ✓ Last: {history[-1]}")

        logger.info("\n" + "=" * 80)

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
    finally:
        if http:
            await http.close()


if __name__ == "__main__":
    asyncio.run(find_recent_closed_market())
