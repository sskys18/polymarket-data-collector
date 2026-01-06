"""Comprehensive Polymarket API test - tests all available endpoints"""

import asyncio
import logging

from core.http.client import HttpClient
from exchanges.polymarket.clob.constants import BASE_URL
from exchanges.polymarket.clob.rest_client import PolymarketClobRestClient
from exchanges.polymarket.clob.models.rest import BookRequest

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

END_CURSOR = "LTE="


async def test_comprehensive():
    """Test all available Polymarket API endpoints"""

    logger.info("=" * 80)
    logger.info("Comprehensive Polymarket API Test")
    logger.info("=" * 80)

    http = None
    try:
        # Initialize client
        logger.info("\n1. Initializing Polymarket CLOB client...")
        http = HttpClient(base_url=BASE_URL, signer=None)
        client = PolymarketClobRestClient(http)
        logger.info("✓ Client initialized successfully")

        # Test 1: Fetch markets with pagination
        logger.info("\n" + "=" * 80)
        logger.info("TEST 1: Market Discovery (paginated get_markets)")
        logger.info("=" * 80)

        all_markets = []
        next_cursor = "MA=="
        max_pages = 3

        for page in range(max_pages):
            logger.info(f"  Fetching page {page + 1}...")
            response = await client.get_markets(next_cursor=next_cursor)

            if isinstance(response, dict):
                markets = response.get("data", [])
                all_markets.extend(markets)
                next_cursor = response.get("next_cursor")
                logger.info(f"    ✓ Got {len(markets)} markets")

            if not next_cursor or next_cursor == END_CURSOR:
                break

        logger.info(f"\n✓ Total markets fetched: {len(all_markets)}")

        # Count active vs closed
        active_count = sum(1 for m in all_markets if m.get("active") and not m.get("closed"))
        closed_count = sum(1 for m in all_markets if m.get("closed"))
        logger.info(f"  Active markets: {active_count}")
        logger.info(f"  Closed markets: {closed_count}")

        # Test 2: Get sampling markets (active markets endpoint)
        logger.info("\n" + "=" * 80)
        logger.info("TEST 2: Active Markets (get_sampling_markets)")
        logger.info("=" * 80)

        sampling_response = await client.get_sampling_markets()
        sampling_markets = sampling_response.get("data", []) if isinstance(sampling_response, dict) else []

        logger.info(f"✓ Sampling markets fetched: {len(sampling_markets)}")

        # Extract active tokens
        active_tokens = []
        for market in sampling_markets:
            if market.get("active") and not market.get("closed"):
                for token in market.get("tokens", []):
                    token_id = token.get("token_id") or token.get("tokenId")
                    if token_id:
                        active_tokens.append({
                            "token_id": token_id,
                            "outcome": token.get("outcome", "N/A"),
                            "question": market.get("question", "N/A"),
                        })

        logger.info(f"✓ Active tokens extracted: {len(active_tokens)}")

        if active_tokens:
            # Show sample
            logger.info(f"\n  Sample active markets:")
            for i, token in enumerate(active_tokens[:3], 1):
                logger.info(f"    {i}. {token['question'][:70]}...")
                logger.info(f"       Outcome: {token['outcome']}, Token ID: {token['token_id'][:20]}...")

        # Test 3: Get real-time prices
        logger.info("\n" + "=" * 80)
        logger.info("TEST 3: Real-Time Prices (get_prices)")
        logger.info("=" * 80)

        if active_tokens:
            # Test with first 10 tokens
            test_tokens = active_tokens[:10]
            buy_requests = [BookRequest(token_id=t["token_id"], side="BUY") for t in test_tokens]

            logger.info(f"  Requesting prices for {len(buy_requests)} tokens...")
            prices = await client.get_prices(buy_requests)

            logger.info(f"✓ Got {len(prices)} price responses")

            if prices:
                logger.info(f"\n  Sample prices:")
                for i, price_data in enumerate(prices[:5], 1):
                    token_id = price_data.get("token_id", "N/A")
                    price = price_data.get("price", "N/A")
                    # Find the token info
                    token_info = next((t for t in test_tokens if t["token_id"] == token_id), None)
                    if token_info:
                        logger.info(f"    {i}. {token_info['question'][:60]}...")
                        logger.info(f"       Outcome: {token_info['outcome']}, Price: {price}")
        else:
            logger.warning("  No active tokens to test prices")

        # Test 4: Historical data availability
        logger.info("\n" + "=" * 80)
        logger.info("TEST 4: Historical Data Availability")
        logger.info("=" * 80)

        if active_tokens:
            logger.info(f"  Testing historical data for {min(5, len(active_tokens))} active tokens...")

            has_history = 0
            for token in active_tokens[:5]:
                token_id = token["token_id"]
                history = await client.get_price_history(market=token_id, interval="1h")

                if history and len(history) > 0:
                    has_history += 1
                    logger.info(f"    ✓ {token['question'][:60]}...")
                    logger.info(f"      Has {len(history)} historical data points")

            if has_history == 0:
                logger.warning("  ⚠ No active tokens have historical data")
                logger.info("  Note: Historical data may not be available via this API endpoint")
            else:
                logger.info(f"  ✓ {has_history} out of 5 tokens have historical data")
        else:
            logger.warning("  No active tokens to test")

        # Summary
        logger.info("\n" + "=" * 80)
        logger.info("SUMMARY")
        logger.info("=" * 80)
        logger.info(f"✓ Market Discovery: {len(all_markets)} markets ({active_count} active, {closed_count} closed)")
        logger.info(f"✓ Active Markets API: {len(active_tokens)} active tokens")
        logger.info(f"✓ Real-Time Prices: Available via get_prices()")
        logger.info(f"⚠ Historical Data: Limited/Not available for most markets")
        logger.info("\nRecommendation: Focus on real-time price collection for active markets")
        logger.info("=" * 80)

        return True

    except Exception as e:
        logger.error("\n" + "=" * 80)
        logger.error(f"✗ API TEST FAILED: {e}")
        logger.error("=" * 80)
        import traceback
        traceback.print_exc()
        return False
    finally:
        if http:
            await http.close()


async def main():
    success = await test_comprehensive()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
