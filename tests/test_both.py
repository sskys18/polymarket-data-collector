"""Run both historical and realtime tests sequentially"""

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from test_historical_single import test_historical_single_market
from test_realtime_single import test_realtime_single_market

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    """Run all tests"""
    logger.info("=" * 70)
    logger.info("Running All Tests")
    logger.info("=" * 70)

    try:
        # Test 1: Historical data collection
        logger.info("\n\nTEST 1: Historical Data Collection")
        logger.info("=" * 70)
        await test_historical_single_market()

        # Wait a bit between tests
        logger.info("\nWaiting 5 seconds before next test...\n")
        await asyncio.sleep(5)

        # Test 2: Real-time data collection
        logger.info("\n\nTEST 2: Real-Time Data Collection")
        logger.info("=" * 70)
        await test_realtime_single_market()

        logger.info("\n\n" + "=" * 70)
        logger.info("✓ ALL TESTS PASSED")
        logger.info("=" * 70)

    except Exception as e:
        logger.error(f"\n\n✗ TESTS FAILED: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
