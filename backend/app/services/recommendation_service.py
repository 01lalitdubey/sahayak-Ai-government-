"""
Recommendation Service — Sahayak AI (Phase 5)
==============================================
Deterministic recommendation engine. Not AI, not ML, not RAG.
Pure weighted scoring based on eligibility results and user profile.

Architecture:
    RecommendationService
        ↓ loads profile via RecommendationRepository
        ↓ evaluates each scheme via EligibilityService
        ↓ calculates weighted score per scheme
        ↓ generates human-readable reasons
        ↓ assigns priority level
        ↓ sorts, paginates, returns recommendations

Scoring weights (configurable — add new factors by adding a new weight
and updating _calculate_score):
    WEIGHT_ELIGIBILITY  40   — % of eligibility rules passed (0–40)
    WEIGHT_OCCUPATION   20   — occupation matches scheme rule
    WEIGHT_INCOME       15   — income falls within scheme income rule
    WEIGHT_STATE        10   — user state matches scheme state (or central)
    WEIGHT_CATEGORY     10   — social category matches scheme category rule
    WEIGHT_FEATURED      5   — scheme is marked as featured

Priority thresholds:
    score >= 90  →  HIGH
    score >= 70  →  MEDIUM
    score <  70  →  LOW
"""

import math
import uuid
from datetime import datetime, timezone
from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ProfileIncompleteException, SchemeNotFoundException
from app.core.logging import get_logger
from app.models.profile import Profile
from app.models.scheme import Scheme
from app.repositories.recommendation_repository import RecommendationRepository
from app.schemas.eligibility import EligibilityCheckResponse
from app.schemas.recommendation import (
    ProfileCompletionResponse,
    ProfileFieldStatus,
    RecommendationDetail,
    RecommendationPriority,
    RecommendationReason,
    RecommendationRefreshResponse,
    RecommendationResponse,
    RecommendationScore,
    RecommendationSummary,
    TopRecommendationsResponse,
)
from app.services.eligibility_service import EligibilityService
from app.services.scheme_service import SchemeService

logger = get_logger(__name__)

# ── Configurable scoring weights ──────────────────────────────────────────
# Total of all max weights must equal 100.
WEIGHT_ELIGIBILITY: float = 40.0
WEIGHT_OCCUPATION: float = 20.0
WEIGHT_INCOME: float = 15.0
WEIGHT_STATE: float = 10.0
WEIGHT_CATEGORY: float = 10.0
WEIGHT_FEATURED: float = 5.0

# ── Priority thresholds ───────────────────────────────────────────────────
PRIORITY_HIGH_THRESHOLD: float = 90.0
PRIORITY_MEDIUM_THRESHOLD: float = 70.0

# ── Profile field definitions ─────────────────────────────────────────────
_PROFILE_FIELDS: list[tuple[str, str, Literal["required", "important", "optional"]]] = [
    ("age",            "Age",              "required"),
    ("gender",         "Gender",           "required"),
    ("state",          "State",            "required"),
    ("category",       "Social Category",  "important"),
    ("occupation",     "Occupation",       "important"),
    ("annual_income",  "Annual Income",    "important"),
    ("district",       "District",         "optional"),
    ("education",      "Education Level",  "optional"),
    ("is_farmer",      "Farmer Status",    "optional"),
    ("is_disabled",    "Disability Status","optional"),
]


# ── Pure scoring functions (stateless, testable without DB) ───────────────

def _assign_priority(score: float) -> RecommendationPriority:
    """Convert numeric score to priority level."""
    if score >= PRIORITY_HIGH_THRESHOLD:
        return "HIGH"
    if score >= PRIORITY_MEDIUM_THRESHOLD:
        return "MEDIUM"
    return "LOW"


def _calculate_eligibility_score(eligibility: EligibilityCheckResponse) -> float:
    """
    Eligibility sub-score (0–WEIGHT_ELIGIBILITY).
    Scales the passed_count / total_rules ratio over the eligibility weight.
    Schemes with no rules get full eligibility weight (open access).
    """
    if eligibility.status == "no_rules":
        return WEIGHT_ELIGIBILITY   # no restrictions → full weight
    if eligibility.total_rules == 0:
        return WEIGHT_ELIGIBILITY
    ratio = eligibility.passed_count / eligibility.total_rules
    return round(ratio * WEIGHT_ELIGIBILITY, 2)


def _occupation_passed(eligibility: EligibilityCheckResponse) -> bool:
    """Return True if the Occupation criterion was in passed_rules."""
    return any(r.criterion == "Occupation" for r in eligibility.passed_rules)


def _income_passed(eligibility: EligibilityCheckResponse) -> bool:
    """Return True if the Annual Income criterion was in passed_rules."""
    return any(r.criterion == "Annual Income" for r in eligibility.passed_rules)


def _state_matched(scheme: Scheme, profile: Profile) -> bool:
    """
    Return True if:
     - scheme is central (scheme.state is None) — available nationwide, OR
     - profile.state matches scheme.state
    """
    if scheme.state is None:
        return True   # central scheme
    if profile.state is None:
        return False  # user hasn't provided state
    return profile.state.lower() == scheme.state.lower()


def _category_passed(eligibility: EligibilityCheckResponse) -> bool:
    """Return True if Social Category criterion was in passed_rules."""
    return any(r.criterion == "Social Category" for r in eligibility.passed_rules)


def calculate_score(
    eligibility: EligibilityCheckResponse,
    profile: Profile,
    scheme: Scheme,
) -> RecommendationScore:
    """
    Calculate the full weighted recommendation score for one scheme.

    This is a pure function — no DB access, easily unit-testable.
    Each factor contributes its weight only if the match is confirmed.

    Returns a RecommendationScore with all component values and the total.
    """
    eligibility_score = _calculate_eligibility_score(eligibility)

    occupation_score = WEIGHT_OCCUPATION if _occupation_passed(eligibility) else 0.0
    income_score = WEIGHT_INCOME if _income_passed(eligibility) else 0.0
    state_score = WEIGHT_STATE if _state_matched(scheme, profile) else 0.0
    category_score = WEIGHT_CATEGORY if _category_passed(eligibility) else 0.0
    featured_score = WEIGHT_FEATURED if scheme.is_featured else 0.0

    total = round(
        eligibility_score
        + occupation_score
        + income_score
        + state_score
        + category_score
        + featured_score,
        2,
    )
    # Clamp to [0, 100]
    total = max(0.0, min(100.0, total))

    return RecommendationScore(
        total=total,
        eligibility_score=eligibility_score,
        occupation_score=occupation_score,
        income_score=income_score,
        state_score=state_score,
        category_score=category_score,
        featured_score=featured_score,
    )


def generate_reasons(
    score: RecommendationScore,
    eligibility: EligibilityCheckResponse,
    scheme: Scheme,
    profile: Profile,
) -> list[RecommendationReason]:
    """
    Generate human-readable recommendation reasons.
    Only adds a reason for factors that positively contributed to the score.
    """
    reasons: list[RecommendationReason] = []

    # Eligibility
    if eligibility.status == "eligible":
        reasons.append(RecommendationReason(
            reason_type="eligibility",
            text="You satisfy all eligibility rules for this scheme.",
        ))
    elif eligibility.status == "incomplete_profile":
        reasons.append(RecommendationReason(
            reason_type="eligibility",
            text=(
                f"You meet {eligibility.passed_count} of {eligibility.total_rules} "
                "eligibility rules. Complete your profile to see full eligibility."
            ),
        ))
    elif eligibility.status == "no_rules":
        reasons.append(RecommendationReason(
            reason_type="eligibility",
            text="This scheme has no specific eligibility restrictions — anyone can apply.",
        ))

    # Occupation
    if score.occupation_score > 0:
        occ_rule = next(
            (r for r in eligibility.passed_rules if r.criterion == "Occupation"),
            None,
        )
        text = (
            f"Your occupation ({occ_rule.user_value}) matches the target audience."
            if occ_rule
            else "Your occupation matches the target audience of this scheme."
        )
        reasons.append(RecommendationReason(reason_type="occupation", text=text))

    # Income
    if score.income_score > 0:
        income_rule = next(
            (r for r in eligibility.passed_rules if r.criterion == "Annual Income"),
            None,
        )
        text = (
            f"Your income ({income_rule.user_value}) falls within the required limit."
            if income_rule
            else "Your annual income falls within the required income limit."
        )
        reasons.append(RecommendationReason(reason_type="income", text=text))

    # State
    if score.state_score > 0:
        if scheme.state is None:
            reasons.append(RecommendationReason(
                reason_type="state",
                text="This is a central government scheme available across all states.",
            ))
        else:
            reasons.append(RecommendationReason(
                reason_type="state",
                text=f"The scheme is available in your state ({scheme.state}).",
            ))

    # Category
    if score.category_score > 0:
        cat_rule = next(
            (r for r in eligibility.passed_rules if r.criterion == "Social Category"),
            None,
        )
        text = (
            f"Your social category ({cat_rule.user_value}) matches the scheme's target group."
            if cat_rule
            else "Your social category matches the scheme's target beneficiary group."
        )
        reasons.append(RecommendationReason(reason_type="category", text=text))

    # Featured
    if score.featured_score > 0:
        reasons.append(RecommendationReason(
            reason_type="featured",
            text="This scheme is highlighted as a featured priority scheme.",
        ))

    # Fallback — always have at least one reason
    if not reasons:
        reasons.append(RecommendationReason(
            reason_type="general",
            text="This scheme may be relevant based on your profile.",
        ))

    return reasons


def calculate_profile_completion(profile: Profile | None) -> ProfileCompletionResponse:
    """
    Calculate how complete a user's profile is.
    Returns percentage, missing field list, and per-field detail.
    """
    if profile is None:
        all_labels = [f[1] for f in _PROFILE_FIELDS]
        return ProfileCompletionResponse(
            completion_percentage=0.0,
            filled_count=0,
            total_fields=len(_PROFILE_FIELDS),
            missing_fields=all_labels,
            fields=[
                ProfileFieldStatus(field=f, label=l, filled=False, importance=i)
                for f, l, i in _PROFILE_FIELDS
            ],
        )

    field_statuses: list[ProfileFieldStatus] = []
    filled_count = 0
    missing_labels: list[str] = []

    for field_name, label, importance in _PROFILE_FIELDS:
        val = getattr(profile, field_name, None)
        # Boolean fields: is_farmer and is_disabled are always set (default False)
        # so they count as filled, but we infer from model defaults
        is_filled = val is not None
        if is_filled:
            filled_count += 1
        else:
            missing_labels.append(label)
        field_statuses.append(ProfileFieldStatus(
            field=field_name,
            label=label,
            filled=is_filled,
            importance=importance,
        ))

    pct = round(filled_count / len(_PROFILE_FIELDS) * 100, 1)
    return ProfileCompletionResponse(
        completion_percentage=pct,
        filled_count=filled_count,
        total_fields=len(_PROFILE_FIELDS),
        missing_fields=missing_labels,
        fields=field_statuses,
    )


# ── Service class ─────────────────────────────────────────────────────────

class RecommendationService:
    """
    Orchestrates the full recommendation pipeline.

    Follows the same pattern as EligibilityService:
      - Constructor receives AsyncSession
      - Composes repositories and other services
      - Exposes async public methods
    """

    def __init__(self, db: AsyncSession) -> None:
        self._repo = RecommendationRepository(db)
        self._eligibility_svc = EligibilityService(db)

    # ── Internal helpers ───────────────────────────────────────────────────

    async def _build_recommendations(
        self,
        user_id: uuid.UUID,
        lang: str = "en",
    ) -> tuple[list[tuple[RecommendationSummary, RecommendationScore]], Profile | None]:
        """
        Core pipeline: load profile, evaluate each scheme, score, sort.
        Returns (sorted_recommendations, profile).
        """
        profile = await self._repo.get_user_profile(user_id)
        if profile is None:
            return [], None

        schemes = await self._repo.get_all_active_schemes()
        
        # Inject translations
        if lang != "en":
            scheme_svc = SchemeService(self._repo._db)
            await scheme_svc._inject_translations_bulk(schemes, lang)

        logger.info(
            "Scoring %d schemes for user %s", len(schemes), str(user_id)[:8]
        )

        results: list[tuple[RecommendationSummary, RecommendationScore]] = []

        for scheme in schemes:
            try:
                eligibility = await self._eligibility_svc.evaluate_scheme(
                    scheme.id, user_id
                )
            except Exception as exc:
                logger.warning(
                    "Eligibility evaluation failed for scheme %s: %s",
                    scheme.scheme_code, exc,
                )
                continue

            # Exclude definitively not-eligible schemes
            if eligibility.status == "not_eligible":
                continue

            score = calculate_score(eligibility, profile, scheme)
            reasons = generate_reasons(score, eligibility, scheme, profile)
            priority = _assign_priority(score.total)

            summary = RecommendationSummary(
                scheme_id=scheme.id,
                scheme_name=scheme.name,
                scheme_code=scheme.scheme_code,
                scheme_type=scheme.scheme_type.value,
                category=scheme.category.value if scheme.category else None,
                ministry=scheme.ministry,
                state=scheme.state,
                is_featured=scheme.is_featured,
                official_url=scheme.official_url,
                short_description=scheme.short_description,
                recommendation_score=score.total,
                priority=priority,
                eligibility_status=eligibility.status,
                eligible=eligibility.eligible,
                reasons=reasons,
                missing_information=eligibility.missing_information,
            )
            results.append((summary, score))

        # Sort by recommendation_score descending
        results.sort(key=lambda t: t[0].recommendation_score, reverse=True)
        return results, profile

    # ── Public API ─────────────────────────────────────────────────────────

    async def get_recommendations(
        self,
        user_id: uuid.UUID,
        *,
        page: int = 1,
        page_size: int = 10,
        priority_filter: str | None = None,
        category_filter: str | None = None,
        sort: str = "score_desc",
        lang: str = "en",
    ) -> RecommendationResponse:
        """
        Return paginated, filtered, sorted recommendations for user.
        Raises ProfileIncompleteException if no profile exists.
        """
        all_results, profile = await self._build_recommendations(user_id, lang=lang)

        if profile is None:
            raise ProfileIncompleteException(
                "Please create your profile to get personalised recommendations."
            )

        summaries = [s for s, _ in all_results]

        # ── Apply filters ──────────────────────────────────────────────────
        if priority_filter:
            summaries = [s for s in summaries if s.priority == priority_filter.upper()]

        if category_filter:
            summaries = [
                s for s in summaries
                if s.category and s.category.lower() == category_filter.lower()
            ]

        # ── Apply sort ─────────────────────────────────────────────────────
        if sort == "score_asc":
            summaries.sort(key=lambda s: s.recommendation_score)
        elif sort == "alphabetical":
            summaries.sort(key=lambda s: s.scheme_name)
        elif sort == "priority":
            _pri_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
            summaries.sort(key=lambda s: _pri_order.get(s.priority, 9))
        # default: score_desc (already sorted)

        total = len(summaries)
        total_pages = max(1, math.ceil(total / page_size))
        page = max(1, min(page, total_pages))
        offset = (page - 1) * page_size
        page_data = summaries[offset: offset + page_size]

        return RecommendationResponse(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            data=page_data,
        )

    async def get_top_recommendations(
        self,
        user_id: uuid.UUID,
        *,
        limit: int = 5,
        lang: str = "en",
    ) -> TopRecommendationsResponse:
        """
        Return top N recommendations for the dashboard widget.
        Returns empty list (not an error) if profile is missing.
        """
        try:
            all_results, profile = await self._build_recommendations(user_id, lang=lang)
        except Exception as exc:
            logger.warning("Top recommendations failed for %s: %s", user_id, exc)
            return TopRecommendationsResponse(data=[])

        if profile is None:
            return TopRecommendationsResponse(data=[])

        top = [s for s, _ in all_results[:limit]]
        return TopRecommendationsResponse(data=top)

    async def get_recommendation(
        self,
        user_id: uuid.UUID,
        scheme_id: uuid.UUID,
        lang: str = "en",
    ) -> RecommendationDetail:
        """
        Return full recommendation detail for a single scheme.
        Raises SchemeNotFoundException if scheme doesn't exist.
        Raises ProfileIncompleteException if no profile.
        """
        profile = await self._repo.get_user_profile(user_id)
        if profile is None:
            raise ProfileIncompleteException(
                "Please create your profile to view recommendation details."
            )

        # Evaluate eligibility — this will raise SchemeNotFoundException internally
        try:
            eligibility = await self._eligibility_svc.evaluate_scheme(scheme_id, user_id)
        except Exception:
            raise SchemeNotFoundException()

        # Load scheme object for metadata
        schemes = await self._repo.get_all_active_schemes()
        scheme = next((s for s in schemes if s.id == scheme_id), None)
        if scheme is None:
            raise SchemeNotFoundException()
            
        if lang != "en":
            scheme_svc = SchemeService(self._repo._db)
            await scheme_svc._inject_translation(scheme, lang)

        score = calculate_score(eligibility, profile, scheme)
        reasons = generate_reasons(score, eligibility, scheme, profile)
        priority = _assign_priority(score.total)

        return RecommendationDetail(
            scheme_id=scheme.id,
            scheme_name=scheme.name,
            scheme_code=scheme.scheme_code,
            scheme_type=scheme.scheme_type.value,
            category=scheme.category.value if scheme.category else None,
            ministry=scheme.ministry,
            department=scheme.department,
            state=scheme.state,
            is_featured=scheme.is_featured,
            official_url=scheme.official_url,
            official_pdf_url=scheme.official_pdf_url,
            contact_email=scheme.contact_email,
            contact_phone=scheme.contact_phone,
            short_description=scheme.short_description,
            full_description=scheme.full_description,
            benefits=scheme.benefits,
            application_mode=scheme.application_mode.value,
            application_start_date=(
                scheme.application_start_date.isoformat()
                if scheme.application_start_date else None
            ),
            application_end_date=(
                scheme.application_end_date.isoformat()
                if scheme.application_end_date else None
            ),
            recommendation_score=score.total,
            score_breakdown=score,
            priority=priority,
            eligibility_status=eligibility.status,
            eligible=eligibility.eligible,
            reasons=reasons,
            missing_information=eligibility.missing_information,
            passed_rules=[r.model_dump() for r in eligibility.passed_rules],
            failed_rules=[r.model_dump() for r in eligibility.failed_rules],
            evaluated_at=eligibility.evaluated_at,
        )

    async def refresh_recommendations(
        self,
        user_id: uuid.UUID,
    ) -> RecommendationRefreshResponse:
        """
        Force re-evaluation of all schemes for a user.
        Since recommendations are not persisted, this simply re-runs scoring.
        Returns the count of fresh recommendations.
        """
        all_results, profile = await self._build_recommendations(user_id)

        if profile is None:
            raise ProfileIncompleteException(
                "Please create your profile to get personalised recommendations."
            )

        logger.info(
            "Recommendations refreshed for user %s: %d results",
            str(user_id)[:8],
            len(all_results),
        )

        return RecommendationRefreshResponse(
            total_recommendations=len(all_results),
            refreshed_at=datetime.now(tz=timezone.utc),
        )

    async def get_profile_completion(
        self,
        user_id: uuid.UUID,
    ) -> ProfileCompletionResponse:
        """Return profile completion details for the dashboard card."""
        profile = await self._repo.get_user_profile(user_id)
        return calculate_profile_completion(profile)
