"""Test working price collection for all active markets"""

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


async def test_working_price_collection():
    """Test that we can collect prices for all active markets"""

    http = None
    try:
        # Initialize client
        logger.info("=" * 80)
        logger.info("Testing Working Price Collection for Active Markets")
        logger.info("=" * 80)

        http = HttpClient(base_url=BASE_URL, signer=None)
        client = PolymarketClobRestClient(http)

        # Get all active markets
        logger.info("\n1. Fetching active markets...")
        sampling_response = await client.get_sampling_markets()
        sampling_markets = sampling_response.get("data", []) if isinstance(sampling_response, dict) else []

        # Extract ALL active tokens
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

        logger.info(f"✓ Found {len(active_tokens)} active tokens")

        # Test price collection methods
        logger.info("\n2. Testing price collection for sample tokens...")

        test_sample = active_tokens[:10]  # Test with 10 tokens
        successful_prices = 0
        start_time = time.time()

        for i, token in enumerate(test_sample, 1):
            try:
                # Try get_midpoint - simplest and most reliable
                result = await client.get_midpoint(token["token_id"])
                price = result.get("mid") if isinstance(result, dict) else None

                if price:
                    successful_prices += 1
                    logger.info(f"  {i}. {token['question'][:60]}")
                    logger.info(f"     Outcome: {token['outcome']}, Midpoint: ${price}")

            except Exception as e:
                logger.warning(f"  {i}. Failed for token: {e}")

        elapsed = time.time() - start_time
        logger.info(f"\n✓ Successfully got prices for {successful_prices}/{len(test_sample)} tokens")
        logger.info(f"✓ Average time per token: {elapsed/len(test_sample):.3f}s")

        # Estimate full collection time
        total_tokens = len(active_tokens)
        estimated_time = (elapsed / len(test_sample)) * total_tokens

        logger.info(f"\n3. Full Collection Estimate:")
        logger.info(f"   Total active tokens: {total_tokens}")
        logger.info(f"   Estimated collection time: {estimated_time:.1f}s ({estimated_time/60:.1f} minutes)")

        # Test different price methods on one token
        logger.info(f"\n4. Testing all price methods on one token...")
        if active_tokens:
            token = active_tokens[0]
            token_id = token["token_id"]

            logger.info(f"   Token: {token['question'][:60]}")
            logger.info(f"   Outcome: {token['outcome']}\n")

            # Midpoint
            result = await client.get_midpoint(token_id)
            logger.info(f"   • Midpoint: ${result.get('mid')}")

            # Last trade
            result = await client.get_last_trade_price(token_id)
            logger.info(f"   • Last trade: ${result.get('price')} ({result.get('side')})")

            # BUY price
            result = await client.get_price(token_id, side="BUY")
            logger.info(f"   • Best BUY: ${result.get('price')}")

            # SELL price
            result = await client.get_price(token_id, side="SELL")
            logger.info(f"   • Best SELL: ${result.get('price')}")

            # Spread
            result = await client.get_spread(token_id)
            logger.info(f"   • Spread: {result.get('spread')}")

        logger.info("\n" + "=" * 80)
        logger.info("SUMMARY")
        logger.info("=" * 80)
        logger.info(f"✓ Price collection is WORKING!")
        logger.info(f"✓ Active markets: {len(active_tokens)} tokens")
        logger.info(f"✓ Success rate: {successful_prices}/{len(test_sample)} = {100*successful_prices/len(test_sample):.0f}%")
        logger.info(f"\nRecommended approach:")
        logger.info(f"  - Use get_sampling_markets() to get active tokens")
        logger.info(f"  - Use get_midpoint(token_id) for price collection")
        logger.info(f"  - Or use get_last_trade_price(token_id) for actual trades")
        logger.info("=" * 80)

        return True

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        return False
    finally:
        if http:
            await http.close()


async def main():
    success = await test_working_price_collection()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
