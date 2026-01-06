"""Debug test for get_prices endpoint"""

import asyncio
import logging

from core.http.client import HttpClient
from exchanges.polymarket.clob.constants import BASE_URL
from exchanges.polymarket.clob.rest_client import PolymarketClobRestClient
from exchanges.polymarket.clob.models.rest import BookRequest

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_prices_debug():
    """Debug the get_prices endpoint"""

    http = None
    try:
        # Initialize client
        http = HttpClient(base_url=BASE_URL, signer=None)
        client = PolymarketClobRestClient(http)

        # Get active markets
        logger.info("Fetching active markets...")
        sampling_response = await client.get_sampling_markets()
        sampling_markets = sampling_response.get("data", []) if isinstance(sampling_response, dict) else []

        logger.info(f"Got {len(sampling_markets)} sampling markets")

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
                        if len(active_tokens) >= 5:  # Just get 5 for testing
                            break
            if len(active_tokens) >= 5:
                break

        logger.info(f"Selected {len(active_tokens)} active tokens for testing")

        for i, token in enumerate(active_tokens, 1):
            logger.info(f"  {i}. Question: {token['question'][:60]}")
            logger.info(f"     Outcome: {token['outcome']}")
            logger.info(f"     Token ID: {token['token_id']}")

        # Test 1: Single token price request
        logger.info("\n" + "=" * 80)
        logger.info("TEST 1: Single token price request")
        logger.info("=" * 80)

        if active_tokens:
            token_id = active_tokens[0]["token_id"]
            logger.info(f"Requesting BUY price for token: {token_id}")

            buy_request = BookRequest(token_id=token_id, side="BUY")
            prices = await client.get_prices([buy_request])

            logger.info(f"Response type: {type(prices)}")
            logger.info(f"Response length: {len(prices) if isinstance(prices, list) else 'N/A'}")
            logger.info(f"Response: {prices}")

        # Test 2: Multiple token price request
        logger.info("\n" + "=" * 80)
        logger.info("TEST 2: Multiple token price request")
        logger.info("=" * 80)

        if active_tokens:
            logger.info(f"Requesting prices for {len(active_tokens)} tokens...")

            buy_requests = [BookRequest(token_id=t["token_id"], side="BUY") for t in active_tokens]
            prices = await client.get_prices(buy_requests)

            logger.info(f"Response type: {type(prices)}")
            logger.info(f"Response length: {len(prices) if isinstance(prices, list) else 'N/A'}")
            logger.info(f"Response: {prices}")

        # Test 3: Try SELL side as well
        logger.info("\n" + "=" * 80)
        logger.info("TEST 3: SELL side price request")
        logger.info("=" * 80)

        if active_tokens:
            token_id = active_tokens[0]["token_id"]
            logger.info(f"Requesting SELL price for token: {token_id}")

            sell_request = BookRequest(token_id=token_id, side="SELL")
            prices = await client.get_prices([sell_request])

            logger.info(f"Response: {prices}")

        return True

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        return False
    finally:
        if http:
            await http.close()


async def main():
    success = await test_prices_debug()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
