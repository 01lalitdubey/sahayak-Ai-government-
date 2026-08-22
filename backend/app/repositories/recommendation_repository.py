"""
Recommendation Repository — Sahayak AI (Phase 5)
=================================================
Data access layer for the recommendation engine.

Responsibilities:
  - Load user profile (delegates to ProfileRepository)
  - Load active schemes with eligibility rules (delegates to EligibilityRepository)
  - Provide scheme detail objects needed for scoring

All heavy scoring/ranking logic lives in RecommendationService,
not here. This layer only fetches data.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.profile import Profile
from app.models.scheme import Scheme
from app.repositories.eligibility_repository import EligibilityRepository
from app.repositories.profile_repository import ProfileRepository

logger = get_logger(__name__)


class RecommendationRepository:
    """
    Data access for the recommendation engine.

    Pattern: thin data-fetching layer. No scoring logic here.
    Composes existing repositories rather than duplicating DB queries.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._profile_repo = ProfileRepository(db)
        self._eligibility_repo = EligibilityRepository(db)

    # ── Profile ───────────────────────────────────────────────────────────

    async def get_user_profile(self, user_id: uuid.UUID) -> Profile | None:
        """
        Load the user's demographic profile.
        Returns None if the user hasn't created a profile yet.
        Caller (service) decides how to handle missing profile.
        """
        return await self._profile_repo.get_by_user_id(user_id)

    # ── Schemes ──────────────────────────────────────────────────────────

    async def get_active_schemes_with_rules(self) -> list[Scheme]:
        """
        Return all active schemes that have at least one eligibility rule.
        These are the candidates for recommendation.
        Delegates to the existing eligibility repository query.
        """
        schemes = await self._eligibility_repo.get_active_schemes_with_rules()
        logger.debug("Loaded %d active schemes with rules for recommendation", len(schemes))
        return schemes

    async def get_all_active_schemes(self) -> list[Scheme]:
        """
        Return ALL active schemes, including those without rules.
        Used to include rule-less schemes in recommendations (score = eligibility weight only).
        """
        from sqlalchemy import select
        from app.models.scheme import Scheme as SchemeModel
        from sqlalchemy.orm import selectinload

        result = await self._db.execute(
            select(SchemeModel)
            .options(selectinload(SchemeModel.eligibility_rules))
            .where(SchemeModel.is_active == True)  # noqa: E712
            .order_by(SchemeModel.name)
        )
        schemes = list(result.scalars().unique().all())
        logger.debug("Loaded %d active schemes for recommendation", len(schemes))
        return schemes
