"""Test historical price data for closed markets"""

import asyncio
import logging
from datetime import datetime

from core.http.client import HttpClient
from exchanges.polymarket.clob.constants import BASE_URL
from exchanges.polymarket.clob.rest_client import PolymarketClobRestClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_closed_market_history():
    """Test fetching historical data for closed markets"""

    http = None
    try:
        logger.info("=" * 80)
        logger.info("Testing Historical Data for Closed Markets")
        logger.info("=" * 80)

        http = HttpClient(base_url=BASE_URL, signer=None)
        client = PolymarketClobRestClient(http)

        # Find closed markets
        logger.info("\n1. Finding and testing closed markets...")
        next_cursor = "MA=="
        closed_markets_tested = 0
        markets_with_history = []
        tested_markets_info = []

        for page in range(10):  # Check first 10 pages
            response = await client.get_markets(next_cursor=next_cursor)
            markets = response.get("data", []) if isinstance(response, dict) else []

            for market in markets:
                if market.get("closed"):
                    closed_markets_tested += 1

                    question = market.get("question", "N/A")
                    end_date = market.get("end_date_iso", "N/A")
                    tokens = market.get("tokens", [])

                    if not tokens:
                        continue

                    token_id = tokens[0].get("token_id") or tokens[0].get("tokenId")
                    outcome = tokens[0].get("outcome", "N/A")

                    logger.info(f"  Testing #{closed_markets_tested}: {question[:60]}... (ended: {end_date})")

                    # Track tested market
                    tested_markets_info.append({
                        "question": question[:80],
                        "end_date": end_date,
                        "has_data": False
                    })

                    # Test with different intervals
                    for interval in ["max", "1h", "1d"]:
                        history = await client.get_price_history(
                            market=token_id,
                            interval=interval
                        )

                        if history and len(history) > 0:
                            tested_markets_info[-1]["has_data"] = True
                            markets_with_history.append({
                                "question": question,
                                "outcome": outcome,
                                "token_id": token_id,
                                "end_date": end_date,
                                "interval": interval,
                                "data_points": len(history),
                                "first": history[0],
                                "last": history[-1]
                            })
                            logger.info(f"    ✓ Found {len(history)} price points with interval '{interval}'")
                            logger.info(f"      First: {history[0]}, Last: {history[-1]}")
                            break  # Found data for this market, move to next

                    # Test first 30 closed markets
                    if closed_markets_tested >= 30:
                        break

            if closed_markets_tested >= 30:
                break

            next_cursor = response.get("next_cursor") if isinstance(response, dict) else None
            if not next_cursor or next_cursor == "LTE=":
                break

        # Summary
        logger.info("\n" + "=" * 80)
        logger.info("SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Closed markets tested: {closed_markets_tested}")
        logger.info(f"Markets with historical data: {len(markets_with_history)}")

        # Show sample of tested markets
        logger.info(f"\nSample of tested closed markets:")
        for i, m in enumerate(tested_markets_info[:5], 1):
            status = "✓ HAS DATA" if m['has_data'] else "✗ No data"
            logger.info(f"  {i}. {m['question']} ({status})")
            logger.info(f"     End date: {m['end_date']}")

        if markets_with_history:
            logger.info(f"\n✓ Historical data IS available for closed markets!")
            logger.info(f"\nDetails of markets with data:")
            for i, m in enumerate(markets_with_history, 1):
                logger.info(f"\n  {i}. {m['question'][:60]}...")
                logger.info(f"     Outcome: {m['outcome']}")
                logger.info(f"     End date: {m['end_date']}")
                logger.info(f"     Interval: {m['interval']}, Data points: {m['data_points']}")
        else:
            logger.info(f"\n✗ No historical data found for the {closed_markets_tested} closed markets tested")
            logger.info(f"   Note: Closed markets may not retain historical price data")

        logger.info("=" * 80)

        return len(markets_with_history) > 0

    except Exception as e:
        logger.error(f"\n✗ Test failed: {e}", exc_info=True)
        return False
    finally:
        if http:
            await http.close()


if __name__ == "__main__":
    success = asyncio.run(test_closed_market_history())
    exit(0 if success else 1)
