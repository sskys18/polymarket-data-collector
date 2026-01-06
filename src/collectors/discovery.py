"""Market discovery service to fetch all markets from Polymarket CLOB API"""

import logging
from typing import List

from exchanges.polymarket.clob.rest_client import PolymarketClobRestClient
from sqlalchemy import insert
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Market

logger = logging.getLogger(__name__)

END_CURSOR = "LTE="


class MarketDiscoveryService:
    """Service to discover and store all Polymarket markets"""

    def __init__(self, polymarket_client: PolymarketClobRestClient, db_session: AsyncSession):
        self.client = polymarket_client
        self.db = db_session

    async def discover_all_markets(self) -> List[str]:
        """Fetch all markets and return list of token_ids"""
        token_ids = []
        next_cursor = "MA=="
        page_count = 0

        while True:
            page_count += 1
            logger.info(f"Fetching markets page {page_count} with cursor: {next_cursor}")

            response = await self.client.get_markets(next_cursor=next_cursor)
            markets = response.get("data", []) if isinstance(response, dict) else []

            if not markets:
                logger.warning(f"No markets returned for cursor: {next_cursor}")
                break

            for market in markets:
                question = market.get("question", "")
                closed = market.get("closed", False)
                active = market.get("active", True)
                condition_id = market.get("conditionId") or market.get("condition_id")

                for token in market.get("tokens", []):
                    token_id = token.get("token_id") or token.get("tokenId")
                    outcome = token.get("outcome", "")

                    if token_id:
                        token_ids.append(token_id)
                        # Upsert market metadata
                        await self._upsert_market(
                            token_id=token_id,
                            condition_id=condition_id,
                            question=question,
                            outcome=outcome,
                            active=active,
                            closed=closed,
                        )

            logger.info(f"Page {page_count}: Found {len(markets)} markets, {len(token_ids)} tokens so far")

            next_cursor = response.get("next_cursor") if isinstance(response, dict) else None
            if not next_cursor or next_cursor == END_CURSOR:
                logger.info("Reached end of market pagination")
                break

        logger.info(f"Discovery complete: {len(token_ids)} total tokens from {page_count} pages")
        await self.db.commit()
        return token_ids

    async def _upsert_market(
        self,
        token_id: str,
        condition_id: str,
        question: str,
        outcome: str,
        active: bool,
        closed: bool,
    ):
        """Insert or update market metadata"""
        stmt = pg_insert(Market).values(
            token_id=token_id,
            condition_id=condition_id,
            question=question,
            outcome=outcome,
            active=active,
            closed=closed,
        )

        # On conflict, update active and closed status
        stmt = stmt.on_conflict_do_update(
            index_elements=["token_id"],
            set_={
                "active": stmt.excluded.active,
                "closed": stmt.excluded.closed,
                "question": stmt.excluded.question,
                "outcome": stmt.excluded.outcome,
            },
        )

        await self.db.execute(stmt)
