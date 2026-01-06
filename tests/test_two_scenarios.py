"""Test two specific scenarios:
1. Fetch one closed market and get all historical 1h interval prices
2. Fetch one active market and get real-time price once
"""

import asyncio
import logging
import time

from core.http.client import HttpClient
from exchanges.polymarket.clob.constants import BASE_URL
from exchanges.polymarket.clob.rest_client import PolymarketClobRestClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_two_scenarios():
    """Test both scenarios"""

    http = None
    try:
        # Initialize client
        logger.info("=" * 80)
        logger.info("Testing Two Scenarios")
        logger.info("=" * 80)

        http = HttpClient(base_url=BASE_URL, signer=None)
        client = PolymarketClobRestClient(http)

        # SCENARIO 1: Get a market and fetch all historical 1h interval prices
        logger.info("\n" + "=" * 80)
        logger.info("SCENARIO 1: Fetch All Historical 1h Interval Prices")
        logger.info("=" * 80)

        # Find a market with historical data (try both active and closed)
        logger.info("\n1. Finding a market with historical data...")

        # First try active markets
        sampling_response = await client.get_sampling_markets()
        sampling_markets = sampling_response.get("data", []) if isinstance(sampling_response, dict) else []

        market_with_history = None
        token_with_history = None
        history = None

        # Check first 10 active markets
        # Use a time range - last 7 days
        end_ts = int(time.time())
        start_ts = end_ts - (7 * 24 * 60 * 60)  # 7 days ago

        for market in sampling_markets[:10]:
            tokens = market.get("tokens", [])
            if tokens:
                test_token_id = tokens[0].get("token_id") or tokens[0].get("tokenId")
                # Try to fetch historical data with time range
                test_history = await client.get_price_history(
                    market=test_token_id,
                    interval="1h",
                    start_ts=start_ts,
                    end_ts=end_ts
                )

                # Check first market in detail
                if market == sampling_markets[0]:
                    logger.info(f"    Testing: {market.get('question', 'N/A')[:60]}...")
                    logger.info(f"    API returned: {len(test_history) if test_history else 0} price points")

                if test_history and len(test_history) > 0:
                    # Found a market with historical data!
                    market_with_history = market
                    token_with_history = test_token_id
                    history = test_history
                    logger.info(f"  Found active market with historical data")
                    break

        # If no active market has history, try closed markets
        if not market_with_history:
            logger.info("  No active markets have historical data, checking closed markets...")
            next_cursor = "MA=="
            markets_checked = 0

            for page in range(5):
                response = await client.get_markets(next_cursor=next_cursor)
                markets = response.get("data", []) if isinstance(response, dict) else []

                for market in markets:
                    if market.get("closed"):
                        markets_checked += 1
                        tokens = market.get("tokens", [])
                        if tokens:
                            test_token_id = tokens[0].get("token_id") or tokens[0].get("tokenId")

                            # For closed markets, try to get data from when they were active
                            # Use the end_date if available, otherwise go back 30 days from now
                            market_end_ts = market.get("end_date_iso")
                            if market_end_ts:
                                # If we have end date, get last 7 days before close
                                try:
                                    from datetime import datetime
                                    end_dt = datetime.fromisoformat(market_end_ts.replace('Z', '+00:00'))
                                    end_ts = int(end_dt.timestamp())
                                    start_ts = end_ts - (7 * 24 * 60 * 60)
                                except:
                                    # Fallback to last 30 days
                                    end_ts = int(time.time())
                                    start_ts = end_ts - (30 * 24 * 60 * 60)
                            else:
                                # No end date, try last 30 days
                                end_ts = int(time.time())
                                start_ts = end_ts - (30 * 24 * 60 * 60)

                            test_history = await client.get_price_history(
                                market=test_token_id,
                                interval="1h",
                                start_ts=start_ts,
                                end_ts=end_ts
                            )

                            if test_history and len(test_history) > 0:
                                market_with_history = market
                                token_with_history = test_token_id
                                history = test_history
                                logger.info(f"  Found closed market with historical data (checked {markets_checked} closed markets)")
                                break

                        if markets_checked >= 10:
                            break

                if market_with_history:
                    break

                next_cursor = response.get("next_cursor") if isinstance(response, dict) else None
                if not next_cursor or next_cursor == "LTE=":
                    break

        if not market_with_history or not token_with_history:
            logger.error("✗ Could not find any market with historical data")
            logger.info("  Note: Polymarket API may not provide historical price data for most markets")
        else:
            question = market_with_history.get("question", "N/A")
            outcome = market_with_history.get("tokens", [{}])[0].get("outcome", "N/A")
            is_closed = market_with_history.get("closed", False)
            status = "Closed" if is_closed else "Active"

            logger.info(f"✓ Found {status.lower()} market with historical data:")
            logger.info(f"  Question: {question}")
            logger.info(f"  Outcome: {outcome}")
            logger.info(f"  Token ID: {token_with_history}")
            logger.info(f"  Status: {status}")

            # Display historical prices
            logger.info(f"\n2. All historical 1h interval prices:")

            if history and len(history) > 0:
                logger.info(f"✓ Retrieved {len(history)} historical price data points")

                # Show first few and last few entries
                logger.info(f"\n  First 5 price points:")
                for i, point in enumerate(history[:5], 1):
                    t = point.get("t", "N/A")
                    p = point.get("p", "N/A")
                    logger.info(f"    {i}. Timestamp: {t}, Price: ${p}")

                if len(history) > 5:
                    logger.info(f"\n  Last 5 price points:")
                    for i, point in enumerate(history[-5:], len(history) - 4):
                        t = point.get("t", "N/A")
                        p = point.get("p", "N/A")
                        logger.info(f"    {i}. Timestamp: {t}, Price: ${p}")
            else:
                logger.warning("⚠ No historical data available")

        # SCENARIO 2: Get one active market and fetch real-time price once
        logger.info("\n" + "=" * 80)
        logger.info("SCENARIO 2: Active Market - Real-Time Price (One Time)")
        logger.info("=" * 80)

        # Find an active market
        logger.info("\n1. Finding an active market...")
        sampling_response = await client.get_sampling_markets()
        sampling_markets = sampling_response.get("data", []) if isinstance(sampling_response, dict) else []

        active_market = None
        active_token_id = None

        for market in sampling_markets:
            if market.get("active") and not market.get("closed"):
                active_market = market
                tokens = market.get("tokens", [])
                if tokens:
                    active_token_id = tokens[0].get("token_id") or tokens[0].get("tokenId")
                    break

        if not active_market or not active_token_id:
            logger.error("✗ Could not find an active market")
        else:
            question = active_market.get("question", "N/A")
            outcome = active_market.get("tokens", [{}])[0].get("outcome", "N/A")

            logger.info(f"✓ Found active market:")
            logger.info(f"  Question: {question}")
            logger.info(f"  Outcome: {outcome}")
            logger.info(f"  Token ID: {active_token_id}")

            # Fetch real-time price once
            logger.info(f"\n2. Fetching real-time price (one time)...")
            result = await client.get_midpoint(active_token_id)
            price = result.get("mid") if isinstance(result, dict) else None

            if price is not None:
                logger.info(f"✓ Current midpoint price: ${price}")
            else:
                logger.warning("⚠ Could not fetch price for this market")

        # Summary
        logger.info("\n" + "=" * 80)
        logger.info("SUMMARY")
        logger.info("=" * 80)

        if market_with_history and history and len(history) > 0:
            logger.info(f"✓ Scenario 1: Successfully fetched {len(history)} historical price data points")
        else:
            logger.info(f"✗ Scenario 1: Failed to fetch historical prices (API may not provide historical data)")

        if active_market and active_token_id and price is not None:
            logger.info(f"✓ Scenario 2: Successfully fetched real-time price (${price}) for active market")
        else:
            logger.info(f"✗ Scenario 2: Failed to fetch real-time price")

        logger.info("=" * 80)

        return True

    except Exception as e:
        logger.error(f"\n✗ Test failed: {e}", exc_info=True)
        return False
    finally:
        if http:
            await http.close()


async def main():
    success = await test_two_scenarios()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
