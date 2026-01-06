"""Test all available price methods on Polymarket API"""

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


async def test_all_price_methods():
    """Test all available price endpoints"""

    http = None
    try:
        # Initialize client
        http = HttpClient(base_url=BASE_URL, signer=None)
        client = PolymarketClobRestClient(http)

        # Get some active tokens
        logger.info("Fetching active markets...")
        sampling_response = await client.get_sampling_markets()
        sampling_markets = sampling_response.get("data", []) if isinstance(sampling_response, dict) else []

        # Extract first few active tokens
        active_tokens = []
        for market in sampling_markets[:10]:
            if market.get("active") and not market.get("closed"):
                for token in market.get("tokens", []):
                    token_id = token.get("token_id") or token.get("tokenId")
                    if token_id:
                        active_tokens.append({
                            "token_id": token_id,
                            "outcome": token.get("outcome", "N/A"),
                            "question": market.get("question", "N/A"),
                        })
                        if len(active_tokens) >= 3:
                            break
            if len(active_tokens) >= 3:
                break

        logger.info(f"Selected {len(active_tokens)} tokens for testing\n")

        for i, token in enumerate(active_tokens, 1):
            logger.info(f"Token {i}: {token['question'][:60]}")
            logger.info(f"  Outcome: {token['outcome']}, ID: {token['token_id'][:30]}...\n")

        if not active_tokens:
            logger.error("No active tokens found!")
            return False

        test_token = active_tokens[0]["token_id"]

        # Test each price method
        logger.info("=" * 80)
        logger.info("TESTING ALL PRICE METHODS")
        logger.info("=" * 80)

        # 1. get_order_book
        logger.info("\n1. get_order_book(token_id)")
        try:
            result = await client.get_order_book(test_token)
            logger.info(f"   ✓ Result type: {type(result)}")
            if isinstance(result, dict):
                logger.info(f"   ✓ Keys: {list(result.keys())}")
                if 'bids' in result and result['bids']:
                    logger.info(f"   ✓ First bid: {result['bids'][0]}")
                if 'asks' in result and result['asks']:
                    logger.info(f"   ✓ First ask: {result['asks'][0]}")
            else:
                logger.info(f"   ✓ Result: {result}")
        except Exception as e:
            logger.error(f"   ✗ Error: {e}")

        # 2. get_midpoint
        logger.info("\n2. get_midpoint(token_id)")
        try:
            result = await client.get_midpoint(test_token)
            logger.info(f"   ✓ Result: {result}")
        except Exception as e:
            logger.error(f"   ✗ Error: {e}")

        # 3. get_market_price
        logger.info("\n3. get_market_price(token_id)")
        try:
            result = await client.get_market_price(test_token)
            logger.info(f"   ✓ Result: {result}")
        except Exception as e:
            logger.error(f"   ✗ Error: {e}")

        # 4. get_last_trade_price
        logger.info("\n4. get_last_trade_price(token_id)")
        try:
            result = await client.get_last_trade_price(test_token)
            logger.info(f"   ✓ Result: {result}")
        except Exception as e:
            logger.error(f"   ✗ Error: {e}")

        # 5. get_spread
        logger.info("\n5. get_spread(token_id)")
        try:
            result = await client.get_spread(test_token)
            logger.info(f"   ✓ Result: {result}")
        except Exception as e:
            logger.error(f"   ✗ Error: {e}")

        # 6. get_price (singular)
        logger.info("\n6. get_price(token_id, side='BUY')")
        try:
            result = await client.get_price(test_token, side="BUY")
            logger.info(f"   ✓ Result: {result}")
        except Exception as e:
            logger.error(f"   ✗ Error: {e}")

        # 7. get_midpoints (multiple)
        logger.info("\n7. get_midpoints([token_ids])")
        try:
            token_ids = [t["token_id"] for t in active_tokens]
            result = await client.get_midpoints(token_ids)
            logger.info(f"   ✓ Result type: {type(result)}")
            logger.info(f"   ✓ Length: {len(result) if isinstance(result, (list, dict)) else 'N/A'}")
            if isinstance(result, list) and result:
                logger.info(f"   ✓ First item: {result[0]}")
            elif isinstance(result, dict):
                logger.info(f"   ✓ Keys: {list(result.keys())[:5]}")
        except Exception as e:
            logger.error(f"   ✗ Error: {e}")

        # 8. get_spreads (multiple)
        logger.info("\n8. get_spreads([token_ids])")
        try:
            token_ids = [t["token_id"] for t in active_tokens]
            result = await client.get_spreads(token_ids)
            logger.info(f"   ✓ Result type: {type(result)}")
            logger.info(f"   ✓ Length: {len(result) if isinstance(result, (list, dict)) else 'N/A'}")
            if isinstance(result, list) and result:
                logger.info(f"   ✓ First item: {result[0]}")
            elif isinstance(result, dict):
                logger.info(f"   ✓ Keys: {list(result.keys())[:5]}")
        except Exception as e:
            logger.error(f"   ✗ Error: {e}")

        # 9. get_last_trades_prices (multiple)
        logger.info("\n9. get_last_trades_prices([token_ids])")
        try:
            token_ids = [t["token_id"] for t in active_tokens]
            result = await client.get_last_trades_prices(token_ids)
            logger.info(f"   ✓ Result type: {type(result)}")
            logger.info(f"   ✓ Length: {len(result) if isinstance(result, (list, dict)) else 'N/A'}")
            if isinstance(result, list) and result:
                logger.info(f"   ✓ First item: {result[0]}")
            elif isinstance(result, dict):
                logger.info(f"   ✓ Keys: {list(result.keys())[:5]}")
        except Exception as e:
            logger.error(f"   ✗ Error: {e}")

        logger.info("\n" + "=" * 80)
        logger.info("SUMMARY")
        logger.info("=" * 80)
        logger.info("Test different price methods to find which ones return actual data")
        logger.info("=" * 80)

        return True

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        return False
    finally:
        if http:
            await http.close()


async def main():
    success = await test_all_price_methods()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
