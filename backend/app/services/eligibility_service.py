"""
Eligibility Service — Sahayak AI
===================================
Orchestrates the eligibility evaluation workflow.
Calls repository for data, calls rule_engine for evaluation.
All business logic lives here — routes stay thin.
"""

import math
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    SchemeNotFoundException,
    ProfileIncompleteException,
    NoEligibilityRulesException,
    NotFoundException,
)
from app.core.logging import get_logger
from app.models.profile import Profile
from app.models.scheme import Scheme
from app.repositories.eligibility_repository import EligibilityRepository
from app.repositories.profile_repository import ProfileRepository
from app.repositories.scheme_repository import SchemeRepository
from app.schemas.eligibility import (
    EligibilityCheckResponse,
    EligibilitySummary,
    MySchemeEligibilityResponse,
    EligibilityRuleAdminRead,
    EligibilityRuleAdminResponse,
    EligibilityRuleListResponse,
    RuleResult,
)
from app.services.rule_engine import evaluate_rule
from app.services.scheme_service import SchemeService

logger = get_logger(__name__)

# Minimum profile fields for eligibility check
_REQUIRED_FIELDS = ["age", "gender", "state", "category", "occupation", "annual_income"]


def _profile_completion(profile: Profile) -> float:
    """Return 0–100 % of key profile fields that are filled."""
    all_fields = [
        "age", "gender", "state", "district", "category",
        "occupation", "education", "annual_income",
    ]
    filled = sum(1 for f in all_fields if getattr(profile, f, None) is not None)
    return round(filled / len(all_fields) * 100, 1)


def _build_response(
    scheme: Scheme,
    passed: list[RuleResult],
    failed: list[RuleResult],
    missing: list[str],
    status: str,
) -> EligibilityCheckResponse:
    total = len(passed) + len(failed) + len(missing)
    score = round(len(passed) / total * 100, 1) if total > 0 else 100.0
    eligible = status == "eligible"

    recommendations: list[str] = []
    for m in missing:
        recommendations.append(f"Add your {m.lower()} to your profile to check this criterion.")
    for f in failed:
        recommendations.append(f"Criterion not met: {f.criterion} — {f.reason}")

    return EligibilityCheckResponse(
        scheme_id=scheme.id,
        scheme_name=scheme.name,
        scheme_code=scheme.scheme_code,
        eligible=eligible,
        status=status,  # type: ignore[arg-type]
        score=score,
        total_rules=len(passed) + len(failed),
        passed_count=len(passed),
        failed_count=len(failed),
        missing_count=len(missing),
        passed_rules=passed,
        failed_rules=failed,
        missing_information=missing,
        recommendations=recommendations,
        evaluated_at=datetime.now(tz=timezone.utc),
    )


class EligibilityService:
    def __init__(self, db: AsyncSession) -> None:
        self._eligibility_repo = EligibilityRepository(db)
        self._profile_repo = ProfileRepository(db)
        self._scheme_repo = SchemeRepository(db)

    # ── Core evaluation ───────────────────────────────────────────────────

    async def _get_profile(self, user_id: uuid.UUID) -> Profile:
        profile = await self._profile_repo.get_by_user_id(user_id)
        if not profile:
            raise ProfileIncompleteException(
                "You have not created a profile yet. "
                "Please complete your profile before checking eligibility."
            )
        return profile

    async def evaluate_scheme(
        self, scheme_id: uuid.UUID, user_id: uuid.UUID, lang: str = "en"
    ) -> EligibilityCheckResponse:
        """Full evaluation of a single scheme for a user."""
        # 1. Load scheme
        scheme = await self._scheme_repo.get_by_id(scheme_id)
        if not scheme:
            raise SchemeNotFoundException()
            
        if lang != "en":
            scheme_svc = SchemeService(self._eligibility_repo._db)
            await scheme_svc._inject_translation(scheme, lang)

        # 2. Load user profile
        profile = await self._get_profile(user_id)

        # 3. Load rules
        rules = await self._eligibility_repo.get_rules_for_scheme(scheme_id)
        if not rules:
            return _build_response(scheme, [], [], [], "no_rules")

        # 4. Evaluate every rule (ALL must pass for eligible = True)
        all_passed: list[RuleResult] = []
        all_failed: list[RuleResult] = []
        all_missing_set: set[str] = set()

        for rule in rules:
            results = evaluate_rule(rule, profile)
            for r in results:
                if r.user_value == "Not provided":
                    all_missing_set.add(r.criterion)
                elif r.passed:
                    all_passed.append(r)
                else:
                    all_failed.append(r)

        # Deduplicate passed/failed by criterion (last write wins across multiple rules)
        passed_map: dict[str, RuleResult] = {}
        failed_map: dict[str, RuleResult] = {}
        for r in all_passed:
            passed_map[r.criterion] = r
        for r in all_failed:
            failed_map[r.criterion] = r

        # A criterion in failed_map overrides passed_map
        final_passed = [v for k, v in passed_map.items() if k not in failed_map]
        final_failed = list(failed_map.values())
        final_missing = sorted(all_missing_set - set(failed_map.keys()))

        if final_missing:
            status = "incomplete_profile"
        elif final_failed:
            status = "not_eligible"
        else:
            status = "eligible"

        return _build_response(scheme, final_passed, final_failed, final_missing, status)

    async def get_my_schemes(self, user_id: uuid.UUID, lang: str = "en") -> MySchemeEligibilityResponse:
        """Evaluate ALL active schemes and return summary for each."""
        profile = await self._get_profile(user_id)
        completion = _profile_completion(profile)

        schemes_with_rules = await self._eligibility_repo.get_active_schemes_with_rules()
        
        if lang != "en":
            scheme_svc = SchemeService(self._eligibility_repo._db)
            await scheme_svc._inject_translations_bulk(schemes_with_rules, lang)

        summaries: list[EligibilitySummary] = []
        eligible_count = not_eligible_count = incomplete_count = 0

        for scheme in schemes_with_rules:
            result = await self.evaluate_scheme(scheme.id, user_id)
            summaries.append(EligibilitySummary(
                scheme_id=scheme.id,
                scheme_name=scheme.name,
                scheme_code=scheme.scheme_code,
                scheme_type=scheme.scheme_type.value,
                category=scheme.category.value if scheme.category else None,
                ministry=scheme.ministry,
                state=scheme.state,
                eligible=result.eligible,
                status=result.status,
                score=result.score,
                total_rules=result.total_rules,
                passed_count=result.passed_count,
            ))
            if result.status == "eligible":
                eligible_count += 1
            elif result.status == "incomplete_profile":
                incomplete_count += 1
            else:
                not_eligible_count += 1

        return MySchemeEligibilityResponse(
            total_schemes=len(summaries),
            eligible_count=eligible_count,
            not_eligible_count=not_eligible_count,
            incomplete_count=incomplete_count,
            profile_completion=completion,
            data=summaries,
        )

    # ── Admin rule management ─────────────────────────────────────────────

    async def create_rule(self, data: dict) -> EligibilityRuleAdminResponse:
        scheme = await self._scheme_repo.get_by_id(data["scheme_id"])
        if not scheme:
            raise SchemeNotFoundException()
        rule = await self._eligibility_repo.create_rule(data)
        logger.info("EligibilityRule created for scheme %s", data["scheme_id"])
        return EligibilityRuleAdminResponse(
            message="Rule created successfully.",
            data=EligibilityRuleAdminRead.model_validate(rule),
        )

    async def update_rule(
        self, rule_id: uuid.UUID, data: dict
    ) -> EligibilityRuleAdminResponse:
        rule = await self._eligibility_repo.update_rule(rule_id, data)
        if not rule:
            raise NotFoundException("Eligibility rule not found.")
        return EligibilityRuleAdminResponse(
            message="Rule updated successfully.",
            data=EligibilityRuleAdminRead.model_validate(rule),
        )

    async def delete_rule(self, rule_id: uuid.UUID) -> dict:
        deleted = await self._eligibility_repo.delete_rule(rule_id)
        if not deleted:
            raise NotFoundException("Eligibility rule not found.")
        return {"success": True, "message": "Rule deleted successfully."}

    async def list_rules(
        self, scheme_id: uuid.UUID | None = None
    ) -> EligibilityRuleListResponse:
        rules = await self._eligibility_repo.get_all_rules(scheme_id=scheme_id)
        total = await self._eligibility_repo.count_rules(scheme_id=scheme_id)
        return EligibilityRuleListResponse(
            data=[EligibilityRuleAdminRead.model_validate(r) for r in rules],
            total=total,
        )
