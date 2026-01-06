"""Test to see the raw API response"""

import asyncio
import logging
import time

from core.http.client import HttpClient
from exchanges.polymarket.clob.constants import BASE_URL

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_raw_response():
    """Check raw API response format"""

    http = None
    try:
        http = HttpClient(base_url=BASE_URL, signer=None)

        # Test with a sample token and time range
        end_ts = int(time.time())
        start_ts = end_ts - (7 * 24 * 60 * 60)  # 7 days ago

        # Pick a known active token (from previous test)
        token_id = "350977769852917329387037893294763093471844346281449484439085576212613048126"

        params = {
            "market": token_id,
            "startTs": start_ts,
            "endTs": end_ts,
            "interval": "1h"
        }

        logger.info("Making request to /prices-history with params:")
        logger.info(f"  market: {token_id[:20]}...")
        logger.info(f"  startTs: {start_ts}")
        logger.info(f"  endTs: {end_ts}")
        logger.info(f"  interval: 1h")

        response = await http.get("/prices-history", params=params)

        logger.info(f"\nRaw response type: {type(response)}")
        logger.info(f"Raw response: {response}")

        # Check if it has a 'history' key
        if isinstance(response, dict):
            history = response.get("history")
            logger.info(f"\nFound 'history' key: {history is not None}")
            if history:
                logger.info(f"History type: {type(history)}")
                logger.info(f"History length: {len(history)}")
                if len(history) > 0:
                    logger.info(f"First item: {history[0]}")

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
    finally:
        if http:
            await http.close()


if __name__ == "__main__":
    asyncio.run(test_raw_response())
