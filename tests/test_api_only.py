"""Test Polymarket API connectivity without database"""

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

END_CURSOR = "LTE="


async def test_api_connectivity():
    """Test basic API connectivity and data fetching"""

    logger.info("=" * 70)
    logger.info("Testing Polymarket API Connectivity")
    logger.info("=" * 70)

    http = None
    try:
        # Initialize client
        logger.info("\n1. Initializing Polymarket CLOB client...")
        http = HttpClient(base_url=BASE_URL, signer=None)
        client = PolymarketClobRestClient(http)
        logger.info("✓ Client initialized successfully")

        # Test fetching ALL markets with pagination
        logger.info("\n2. Fetching ALL markets using cursor pagination...")

        all_markets = []
        all_tokens = []
        next_cursor = "MA=="
        page_count = 0
        max_pages = 20  # Increase to find active markets

        while next_cursor and next_cursor != END_CURSOR and page_count < max_pages:
            page_count += 1
            logger.info(f"  Fetching page {page_count} (cursor: {next_cursor})...")

            response = await client.get_markets(next_cursor=next_cursor)

            if isinstance(response, dict):
                markets = response.get("data", [])
                all_markets.extend(markets)

                # Extract all tokens
                for market in markets:
                    for token in market.get("tokens", []):
                        token_id = token.get("token_id") or token.get("tokenId")
                        if token_id:
                            all_tokens.append({
                                "token_id": token_id,
                                "outcome": token.get("outcome", "N/A"),
                                "question": market.get("question", "N/A"),
                                "active": market.get("active", True),
                                "closed": market.get("closed", False),
                            })

                logger.info(f"    ✓ Page {page_count}: {len(markets)} markets, {len(all_tokens)} total tokens")

                next_cursor = response.get("next_cursor")
            else:
                logger.error(f"Unexpected response type: {type(response)}")
                break

        logger.info(f"\n✓ Successfully fetched {len(all_markets)} markets across {page_count} pages")
        logger.info(f"✓ Total tokens collected: {len(all_tokens)}")

        if next_cursor and next_cursor != END_CURSOR:
            logger.info(f"  Note: More pages available (stopped at {max_pages} pages for testing)")
        else:
            logger.info(f"  Reached end of pagination")

        # Test historical data - try multiple tokens until we find one with data
        if all_tokens:
            logger.info("\n3. Testing historical data collection...")

            # Prioritize active, non-closed markets for better chance of historical data
            active_tokens = [t for t in all_tokens if t["active"] and not t["closed"]]
            closed_tokens = [t for t in all_tokens if t["closed"]]

            logger.info(f"  Active tokens: {len(active_tokens)}")
            logger.info(f"  Closed tokens: {len(closed_tokens)}")
            logger.info(f"  Trying active tokens first to find historical data...")

            tokens_tried = 0
            tokens_with_data = 0
            max_tries = 50  # Try up to 50 tokens

            # Try active tokens first, then closed if needed
            tokens_to_try = active_tokens[:max_tries] if active_tokens else all_tokens[:max_tries]

            for token_info in tokens_to_try:
                tokens_tried += 1
                token_id = token_info["token_id"]

                # Try different intervals: all, 1h, 1d
                for interval in ["all", "1h", "1d"]:
                    # Fetch historical data
                    history = await client.get_price_history(
                        market=token_id,
                        interval=interval
                    )

                    if history and len(history) > 0:
                        break  # Found data with this interval
                else:
                    # No data with any interval
                    history = None

                if history and len(history) > 0:
                    tokens_with_data += 1
                    logger.info(f"\n  ✓ Token #{tokens_tried} has historical data:")
                    logger.info(f"    Question: {token_info['question'][:80]}...")
                    logger.info(f"    Outcome: {token_info['outcome']}")
                    logger.info(f"    Token ID: {token_id}")
                    logger.info(f"    Active: {token_info['active']}, Closed: {token_info['closed']}")
                    logger.info(f"    Interval used: {interval}")
                    logger.info(f"    Historical points: {len(history)}")

                    # Show sample data points
                    if len(history) >= 3:
                        logger.info(f"\n    Sample price points:")
                        for i, point in enumerate(history[:3], 1):
                            price = point.get("p", "N/A")
                            timestamp = point.get("t", "N/A")
                            logger.info(f"      {i}. Price: {price}, Timestamp: {timestamp}")

                    # Stop after finding first token with data for quick test
                    if tokens_with_data >= 3:
                        logger.info(f"\n  ✓ Found {tokens_with_data} tokens with historical data")
                        break
                else:
                    logger.debug(f"  Token #{tokens_tried} has no historical data (skipping)")

            logger.info(f"\n  Summary:")
            logger.info(f"    Tokens tried: {tokens_tried}")
            logger.info(f"    Tokens with historical data: {tokens_with_data}")

            if tokens_with_data == 0:
                logger.warning("  ⚠ No tokens with historical data found in sample")

        else:
            logger.warning("  No tokens found to test historical data")

        logger.info("\n" + "=" * 70)
        logger.info("✓ API CONNECTIVITY TEST PASSED")
        logger.info("=" * 70)
        logger.info(f"\nResults:")
        logger.info(f"  - Markets fetched: {len(all_markets)}")
        logger.info(f"  - Total tokens: {len(all_tokens)}")
        logger.info(f"  - Pages fetched: {page_count}")
        logger.info("=" * 70)
        return True

    except Exception as e:
        logger.error("\n" + "=" * 70)
        logger.error(f"✗ API TEST FAILED: {e}")
        logger.error("=" * 70)
        import traceback
        traceback.print_exc()
        return False
    finally:
        if http:
            await http.close()


async def main():
    success = await test_api_connectivity()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
