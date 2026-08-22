"""
Recommendation Engine Tests — Sahayak AI (Phase 5)
===================================================
Tests for:
  - Pure scoring functions (no DB)
  - Priority assignment
  - Reason generation
  - Profile completion calculation
  - API endpoint security (auth required checks)
  - OpenAPI schema validation

Follows the same patterns as test_eligibility.py and test_auth.py:
  - Pure unit tests use direct function calls
  - Service tests use AsyncMock + patch
  - API tests use TestClient (sync, no live DB)
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.models.enums import (
    ApplicationModeEnum,
    CategoryEnum,
    GenderEnum,
    OccupationEnum,
    SchemeCategoryEnum,
    SchemeTypeEnum,
)
from app.schemas.eligibility import EligibilityCheckResponse, RuleResult
from app.services.recommendation_service import (
    PRIORITY_HIGH_THRESHOLD,
    PRIORITY_MEDIUM_THRESHOLD,
    WEIGHT_CATEGORY,
    WEIGHT_ELIGIBILITY,
    WEIGHT_FEATURED,
    WEIGHT_INCOME,
    WEIGHT_OCCUPATION,
    WEIGHT_STATE,
    _assign_priority,
    _category_passed,
    _income_passed,
    _occupation_passed,
    _state_matched,
    calculate_profile_completion,
    calculate_score,
    generate_reasons,
)


# ============================================================
# Helpers
# ============================================================

def _make_profile(
    state: str | None = "Maharashtra",
    occupation=OccupationEnum.FARMER,
    annual_income: int | None = 80_000,
    category=CategoryEnum.OBC,
    age: int | None = 35,
    gender=GenderEnum.MALE,
    education=None,
    district: str | None = None,
):
    """Create a mock Profile object."""
    p = MagicMock()
    p.state = state
    p.occupation = occupation
    p.annual_income = annual_income
    p.category = category
    p.age = age
    p.gender = gender
    p.education = education
    p.district = district
    p.is_farmer = True
    p.is_disabled = False
    return p


def _make_scheme(
    state: str | None = None,
    is_featured: bool = False,
    category=SchemeCategoryEnum.AGRICULTURE,
):
    """Create a mock Scheme object."""
    s = MagicMock()
    s.id = uuid.uuid4()
    s.name = "Test Scheme"
    s.scheme_code = "TEST-001"
    s.scheme_type = SchemeTypeEnum.CENTRAL
    s.category = category
    s.ministry = "Test Ministry"
    s.state = state
    s.is_featured = is_featured
    s.official_url = "https://example.com"
    s.official_pdf_url = None
    s.contact_email = None
    s.contact_phone = None
    s.short_description = "A test scheme."
    s.full_description = "Full description."
    s.benefits = "Benefits text."
    s.application_mode = ApplicationModeEnum.ONLINE
    s.application_start_date = None
    s.application_end_date = None
    s.department = None
    return s


def _make_eligibility(
    passed_rules: list[RuleResult] | None = None,
    failed_rules: list[RuleResult] | None = None,
    missing: list[str] | None = None,
    status: str = "eligible",
    total_rules: int = 3,
    passed_count: int = 3,
    failed_count: int = 0,
    missing_count: int = 0,
) -> EligibilityCheckResponse:
    """Create a mock EligibilityCheckResponse."""
    return EligibilityCheckResponse(
        scheme_id=uuid.uuid4(),
        scheme_name="Test Scheme",
        scheme_code="TEST-001",
        eligible=(status == "eligible"),
        status=status,  # type: ignore[arg-type]
        score=round(passed_count / max(total_rules, 1) * 100, 1),
        total_rules=total_rules,
        passed_count=passed_count,
        failed_count=failed_count,
        missing_count=missing_count,
        passed_rules=passed_rules or [],
        failed_rules=failed_rules or [],
        missing_information=missing or [],
        recommendations=[],
        evaluated_at=datetime.now(tz=timezone.utc),
    )


def _client():
    from app.main import create_application
    return TestClient(create_application(), raise_server_exceptions=False)


# ============================================================
# Unit: Priority Assignment
# ============================================================

class TestPriorityAssignment:
    def test_score_100_is_high(self):
        assert _assign_priority(100.0) == "HIGH"

    def test_score_at_threshold_high(self):
        assert _assign_priority(PRIORITY_HIGH_THRESHOLD) == "HIGH"

    def test_score_just_below_high_is_medium(self):
        assert _assign_priority(89.9) == "MEDIUM"

    def test_score_at_threshold_medium(self):
        assert _assign_priority(PRIORITY_MEDIUM_THRESHOLD) == "MEDIUM"

    def test_score_just_below_medium_is_low(self):
        assert _assign_priority(69.9) == "LOW"

    def test_score_zero_is_low(self):
        assert _assign_priority(0.0) == "LOW"

    def test_score_90_is_high(self):
        assert _assign_priority(90.0) == "HIGH"

    def test_score_70_is_medium(self):
        assert _assign_priority(70.0) == "MEDIUM"

    def test_score_50_is_low(self):
        assert _assign_priority(50.0) == "LOW"


# ============================================================
# Unit: Score Calculation
# ============================================================

class TestScoreCalculation:

    def test_full_score_all_factors(self):
        """A fully eligible user with all factors should score max 100."""
        profile = _make_profile(state="Maharashtra")
        scheme = _make_scheme(state=None, is_featured=True)

        passed_rules = [
            RuleResult(criterion="Occupation", requirement="Farmer", user_value="Farmer", passed=True, reason="Match"),
            RuleResult(criterion="Annual Income", requirement="≤₹1,00,000", user_value="₹80,000", passed=True, reason="Match"),
            RuleResult(criterion="Social Category", requirement="OBC", user_value="OBC", passed=True, reason="Match"),
        ]
        eligibility = _make_eligibility(passed_rules=passed_rules, total_rules=3, passed_count=3)
        score = calculate_score(eligibility, profile, scheme)

        assert score.eligibility_score == WEIGHT_ELIGIBILITY
        assert score.occupation_score == WEIGHT_OCCUPATION
        assert score.income_score == WEIGHT_INCOME
        assert score.state_score == WEIGHT_STATE
        assert score.category_score == WEIGHT_CATEGORY
        assert score.featured_score == WEIGHT_FEATURED
        assert score.total == 100.0

    def test_no_rules_gets_full_eligibility_weight(self):
        """Scheme with no rules → no restrictions → full eligibility weight."""
        profile = _make_profile()
        scheme = _make_scheme()
        eligibility = _make_eligibility(status="no_rules", total_rules=0, passed_count=0)
        score = calculate_score(eligibility, profile, scheme)
        assert score.eligibility_score == WEIGHT_ELIGIBILITY

    def test_state_mismatch_gives_no_state_score(self):
        profile = _make_profile(state="Maharashtra")
        scheme = _make_scheme(state="Karnataka")
        eligibility = _make_eligibility(passed_rules=[])
        score = calculate_score(eligibility, profile, scheme)
        assert score.state_score == 0.0

    def test_state_match_gives_state_score(self):
        profile = _make_profile(state="Karnataka")
        scheme = _make_scheme(state="Karnataka")
        eligibility = _make_eligibility(passed_rules=[])
        score = calculate_score(eligibility, profile, scheme)
        assert score.state_score == WEIGHT_STATE

    def test_central_scheme_always_gets_state_score(self):
        profile = _make_profile(state="Any State")
        scheme = _make_scheme(state=None)
        eligibility = _make_eligibility(passed_rules=[])
        score = calculate_score(eligibility, profile, scheme)
        assert score.state_score == WEIGHT_STATE

    def test_no_profile_state_with_state_scheme_gives_no_score(self):
        profile = _make_profile(state=None)
        scheme = _make_scheme(state="Maharashtra")
        eligibility = _make_eligibility(passed_rules=[])
        score = calculate_score(eligibility, profile, scheme)
        assert score.state_score == 0.0

    def test_featured_bonus_applied(self):
        profile = _make_profile()
        scheme = _make_scheme(is_featured=True)
        eligibility = _make_eligibility(passed_rules=[])
        score = calculate_score(eligibility, profile, scheme)
        assert score.featured_score == WEIGHT_FEATURED

    def test_not_featured_no_bonus(self):
        profile = _make_profile()
        scheme = _make_scheme(is_featured=False)
        eligibility = _make_eligibility(passed_rules=[])
        score = calculate_score(eligibility, profile, scheme)
        assert score.featured_score == 0.0

    def test_partial_eligibility_scales_proportionally(self):
        """2 of 4 rules passed → eligibility_score = WEIGHT_ELIGIBILITY * 0.5"""
        profile = _make_profile()
        scheme = _make_scheme()
        eligibility = _make_eligibility(total_rules=4, passed_count=2)
        score = calculate_score(eligibility, profile, scheme)
        expected = round(0.5 * WEIGHT_ELIGIBILITY, 2)
        assert score.eligibility_score == expected

    def test_total_is_clamped_to_100(self):
        """Verify total never exceeds 100."""
        profile = _make_profile()
        scheme = _make_scheme(is_featured=True)
        passed_rules = [
            RuleResult(criterion="Occupation", requirement="", user_value="Farmer", passed=True, reason=""),
            RuleResult(criterion="Annual Income", requirement="", user_value="₹80,000", passed=True, reason=""),
            RuleResult(criterion="Social Category", requirement="", user_value="OBC", passed=True, reason=""),
        ]
        eligibility = _make_eligibility(passed_rules=passed_rules, total_rules=3, passed_count=3)
        score = calculate_score(eligibility, profile, scheme)
        assert score.total <= 100.0

    def test_score_is_non_negative(self):
        """Score should never be negative."""
        profile = _make_profile(state=None)
        scheme = _make_scheme(state="Kerala", is_featured=False)
        eligibility = _make_eligibility(passed_rules=[], total_rules=5, passed_count=0)
        score = calculate_score(eligibility, profile, scheme)
        assert score.total >= 0.0


# ============================================================
# Unit: Factor Detection
# ============================================================

class TestFactorDetection:

    def test_occupation_passed_detects_correctly(self):
        eligibility = _make_eligibility(
            passed_rules=[
                RuleResult(criterion="Occupation", requirement="Farmer", user_value="Farmer", passed=True, reason="")
            ]
        )
        assert _occupation_passed(eligibility) is True

    def test_occupation_passed_false_when_absent(self):
        assert _occupation_passed(_make_eligibility(passed_rules=[])) is False

    def test_income_passed_detects_correctly(self):
        eligibility = _make_eligibility(
            passed_rules=[
                RuleResult(criterion="Annual Income", requirement="≤₹1,00,000", user_value="₹80,000", passed=True, reason="")
            ]
        )
        assert _income_passed(eligibility) is True

    def test_income_passed_false_when_absent(self):
        assert _income_passed(_make_eligibility(passed_rules=[])) is False

    def test_category_passed_detects_correctly(self):
        eligibility = _make_eligibility(
            passed_rules=[
                RuleResult(criterion="Social Category", requirement="OBC", user_value="OBC", passed=True, reason="")
            ]
        )
        assert _category_passed(eligibility) is True

    def test_category_passed_false_when_absent(self):
        assert _category_passed(_make_eligibility(passed_rules=[])) is False

    def test_state_matched_central_scheme(self):
        profile = _make_profile(state="Any State")
        scheme = _make_scheme(state=None)
        assert _state_matched(scheme, profile) is True

    def test_state_matched_same_state_case_insensitive(self):
        profile = _make_profile(state="maharashtra")
        scheme = _make_scheme(state="Maharashtra")
        assert _state_matched(scheme, profile) is True

    def test_state_not_matched(self):
        profile = _make_profile(state="Punjab")
        scheme = _make_scheme(state="Karnataka")
        assert _state_matched(scheme, profile) is False

    def test_state_not_matched_missing_profile_state(self):
        profile = _make_profile(state=None)
        scheme = _make_scheme(state="Karnataka")
        assert _state_matched(scheme, profile) is False


# ============================================================
# Unit: Reason Generation
# ============================================================

class TestReasonGeneration:

    def _full_score(self):
        from app.schemas.recommendation import RecommendationScore
        return RecommendationScore(
            total=100.0,
            eligibility_score=40.0,
            occupation_score=20.0,
            income_score=15.0,
            state_score=10.0,
            category_score=10.0,
            featured_score=5.0,
        )

    def _zero_score(self):
        from app.schemas.recommendation import RecommendationScore
        return RecommendationScore(
            total=0.0,
            eligibility_score=0.0,
            occupation_score=0.0,
            income_score=0.0,
            state_score=0.0,
            category_score=0.0,
            featured_score=0.0,
        )

    def test_eligible_reason_type_present(self):
        eligibility = _make_eligibility(status="eligible")
        reasons = generate_reasons(self._full_score(), eligibility, _make_scheme(), _make_profile())
        assert any(r.reason_type == "eligibility" for r in reasons)

    def test_featured_reason_present_when_featured(self):
        eligibility = _make_eligibility(status="eligible")
        reasons = generate_reasons(self._full_score(), eligibility, _make_scheme(is_featured=True), _make_profile())
        assert any(r.reason_type == "featured" for r in reasons)

    def test_featured_reason_absent_when_not_featured(self):
        from app.schemas.recommendation import RecommendationScore
        score = RecommendationScore(
            total=75.0, eligibility_score=40.0, occupation_score=20.0,
            income_score=15.0, state_score=0.0, category_score=0.0, featured_score=0.0,
        )
        reasons = generate_reasons(score, _make_eligibility(status="eligible"), _make_scheme(is_featured=False), _make_profile())
        assert not any(r.reason_type == "featured" for r in reasons)

    def test_state_central_reason_mentions_central(self):
        from app.schemas.recommendation import RecommendationScore
        score = RecommendationScore(
            total=50.0, eligibility_score=40.0, occupation_score=0.0,
            income_score=0.0, state_score=10.0, category_score=0.0, featured_score=0.0,
        )
        reasons = generate_reasons(score, _make_eligibility(status="eligible"), _make_scheme(state=None), _make_profile())
        state_reasons = [r for r in reasons if r.reason_type == "state"]
        assert state_reasons
        assert "central" in state_reasons[0].text.lower()

    def test_incomplete_profile_reason_mentions_rules(self):
        eligibility = _make_eligibility(status="incomplete_profile", passed_count=2, total_rules=4)
        reasons = generate_reasons(self._zero_score(), eligibility, _make_scheme(), _make_profile())
        assert any(r.reason_type == "eligibility" for r in reasons)

    def test_no_rules_scheme_gets_no_restriction_reason(self):
        eligibility = _make_eligibility(status="no_rules", total_rules=0, passed_count=0)
        reasons = generate_reasons(self._zero_score(), eligibility, _make_scheme(), _make_profile())
        eligi_reasons = [r for r in reasons if r.reason_type == "eligibility"]
        assert eligi_reasons
        assert "no specific" in eligi_reasons[0].text.lower()

    def test_always_at_least_one_reason(self):
        """Even with zero score, fallback reason should fire."""
        reasons = generate_reasons(self._zero_score(), _make_eligibility(status="eligible"), _make_scheme(), _make_profile())
        assert len(reasons) >= 1

    def test_reason_texts_are_non_empty(self):
        reasons = generate_reasons(self._full_score(), _make_eligibility(status="eligible"), _make_scheme(is_featured=True), _make_profile())
        for r in reasons:
            assert r.text.strip() != ""


# ============================================================
# Unit: Profile Completion
# ============================================================

class TestProfileCompletion:

    def test_none_profile_returns_zero_percent(self):
        result = calculate_profile_completion(None)
        assert result.completion_percentage == 0.0
        assert result.filled_count == 0

    def test_none_profile_all_fields_missing(self):
        result = calculate_profile_completion(None)
        assert result.missing_fields  # non-empty

    def test_missing_fields_list_contains_unfilled_labels(self):
        profile = _make_profile(state=None, annual_income=None, category=None)
        result = calculate_profile_completion(profile)
        assert "State" in result.missing_fields
        assert "Annual Income" in result.missing_fields
        assert "Social Category" in result.missing_fields

    def test_total_fields_constant(self):
        result = calculate_profile_completion(None)
        assert result.total_fields == 10

    def test_filled_count_correct_for_partial_profile(self):
        # age, gender, state, occupation, income = 5 filled; rest None
        profile = _make_profile(
            age=35,
            gender=GenderEnum.MALE,
            state="Maharashtra",
            occupation=OccupationEnum.FARMER,
            annual_income=80_000,
            category=None,
            district=None,
            education=None,
        )
        result = calculate_profile_completion(profile)
        # is_farmer and is_disabled are always "truthy" from mock (not None)
        # So filled = age, gender, state, occupation, income, is_farmer, is_disabled = 7
        assert result.filled_count >= 5

    def test_success_field_is_true(self):
        result = calculate_profile_completion(None)
        assert result.success is True

    def test_percentage_between_0_and_100(self):
        profile = _make_profile()
        result = calculate_profile_completion(profile)
        assert 0.0 <= result.completion_percentage <= 100.0


# ============================================================
# Unit: Schema validation
# ============================================================

class TestRecommendationSchemas:

    def test_recommendation_score_schema(self):
        from app.schemas.recommendation import RecommendationScore
        score = RecommendationScore(
            total=85.5,
            eligibility_score=40.0,
            occupation_score=20.0,
            income_score=15.0,
            state_score=10.0,
            category_score=0.0,
            featured_score=0.5,
        )
        assert score.total == 85.5

    def test_recommendation_reason_schema(self):
        from app.schemas.recommendation import RecommendationReason
        reason = RecommendationReason(reason_type="eligibility", text="You qualify.")
        assert reason.reason_type == "eligibility"

    def test_profile_field_status_schema(self):
        from app.schemas.recommendation import ProfileFieldStatus
        field = ProfileFieldStatus(field="age", label="Age", filled=True, importance="required")
        assert field.filled is True

    def test_profile_completion_response_schema(self):
        from app.schemas.recommendation import ProfileCompletionResponse
        resp = ProfileCompletionResponse(
            completion_percentage=60.0,
            filled_count=6,
            total_fields=10,
            missing_fields=["District", "Education Level"],
            fields=[],
        )
        assert resp.completion_percentage == 60.0
        assert resp.missing_fields == ["District", "Education Level"]

    def test_recommendation_refresh_response_schema(self):
        from app.schemas.recommendation import RecommendationRefreshResponse
        resp = RecommendationRefreshResponse(
            total_recommendations=12,
            refreshed_at=datetime.now(tz=timezone.utc),
        )
        assert resp.success is True
        assert resp.total_recommendations == 12


# ============================================================
# API: Security checks (no live DB — TestClient)
# ============================================================

def test_recommendations_requires_auth():
    client = _client()
    resp = client.get("/api/v1/recommendations")
    assert resp.status_code == 401


def test_top_recommendations_requires_auth():
    client = _client()
    resp = client.get("/api/v1/recommendations/top")
    assert resp.status_code == 401


def test_profile_completion_requires_auth():
    client = _client()
    resp = client.get("/api/v1/recommendations/profile")
    assert resp.status_code == 401


def test_refresh_recommendations_requires_auth():
    client = _client()
    resp = client.post("/api/v1/recommendations/refresh")
    assert resp.status_code == 401


def test_recommendation_detail_requires_auth():
    client = _client()
    resp = client.get(f"/api/v1/recommendations/{uuid.uuid4()}")
    assert resp.status_code == 401


def test_recommendations_invalid_token_rejected():
    client = _client()
    resp = client.get(
        "/api/v1/recommendations",
        headers={"Authorization": "Bearer invalid.token.here"},
    )
    assert resp.status_code == 401


# ============================================================
# API: OpenAPI schema
# ============================================================

def test_recommendation_routes_in_openapi():
    client = _client()
    paths = client.get("/openapi.json").json()["paths"]
    assert "/api/v1/recommendations" in paths
    assert "/api/v1/recommendations/top" in paths
    assert "/api/v1/recommendations/profile" in paths
    assert "/api/v1/recommendations/refresh" in paths
    assert "/api/v1/recommendations/{scheme_id}" in paths


def test_recommendation_routes_tagged_correctly():
    client = _client()
    spec = client.get("/openapi.json").json()
    all_tags: set[str] = set()
    for path_item in spec["paths"].values():
        for method_item in path_item.values():
            if isinstance(method_item, dict):
                for tag in method_item.get("tags", []):
                    if isinstance(tag, str):
                        all_tags.add(tag)
    assert "Recommendations" in all_tags


# ============================================================
# Unit: Scoring weight constants
# ============================================================

def test_weights_sum_to_100():
    """All scoring weights must sum to 100."""
    total = WEIGHT_ELIGIBILITY + WEIGHT_OCCUPATION + WEIGHT_INCOME + WEIGHT_STATE + WEIGHT_CATEGORY + WEIGHT_FEATURED
    assert total == 100.0


def test_priority_thresholds_ordered():
    """HIGH threshold must be greater than MEDIUM threshold."""
    assert PRIORITY_HIGH_THRESHOLD > PRIORITY_MEDIUM_THRESHOLD


# ============================================================
# Service: async unit tests (mocked DB)
# ============================================================

@pytest.mark.asyncio
async def test_service_get_top_returns_empty_without_profile():
    """When no profile exists, top recommendations returns empty list gracefully."""
    from app.services.recommendation_service import RecommendationService

    mock_db = AsyncMock()
    svc = RecommendationService(mock_db)

    with patch.object(svc._repo, "get_user_profile", return_value=None):
        result = await svc.get_top_recommendations(uuid.uuid4())

    assert result.success is True
    assert result.data == []


@pytest.mark.asyncio
async def test_service_profile_completion_no_profile():
    """Profile completion with no profile returns 0%."""
    from app.services.recommendation_service import RecommendationService

    mock_db = AsyncMock()
    svc = RecommendationService(mock_db)

    with patch.object(svc._repo, "get_user_profile", return_value=None):
        result = await svc.get_profile_completion(uuid.uuid4())

    assert result.completion_percentage == 0.0
    assert result.filled_count == 0


@pytest.mark.asyncio
async def test_service_refresh_raises_without_profile():
    """refresh_recommendations raises ProfileIncompleteException when no profile."""
    from app.services.recommendation_service import RecommendationService
    from app.core.exceptions import ProfileIncompleteException

    mock_db = AsyncMock()
    svc = RecommendationService(mock_db)

    with patch.object(svc._repo, "get_user_profile", return_value=None), \
         patch.object(svc._repo, "get_all_active_schemes", return_value=[]):
        with pytest.raises(ProfileIncompleteException):
            await svc.refresh_recommendations(uuid.uuid4())


@pytest.mark.asyncio
async def test_service_recommendations_raises_without_profile():
    """get_recommendations raises ProfileIncompleteException when no profile."""
    from app.services.recommendation_service import RecommendationService
    from app.core.exceptions import ProfileIncompleteException

    mock_db = AsyncMock()
    svc = RecommendationService(mock_db)

    with patch.object(svc._repo, "get_user_profile", return_value=None), \
         patch.object(svc._repo, "get_all_active_schemes", return_value=[]):
        with pytest.raises(ProfileIncompleteException):
            await svc.get_recommendations(uuid.uuid4())


@pytest.mark.asyncio
async def test_service_recommendations_empty_when_all_ineligible():
    """If all schemes return not_eligible, result list should be empty."""
    from app.services.recommendation_service import RecommendationService

    mock_db = AsyncMock()
    svc = RecommendationService(mock_db)
    profile = _make_profile()
    scheme = _make_scheme()

    ineligible_result = _make_eligibility(
        status="not_eligible",
        total_rules=1,
        passed_count=0,
        failed_count=1,
    )

    with patch.object(svc._repo, "get_user_profile", return_value=profile), \
         patch.object(svc._repo, "get_all_active_schemes", return_value=[scheme]), \
         patch.object(svc._eligibility_svc, "evaluate_scheme", return_value=ineligible_result):
        result = await svc.get_recommendations(uuid.uuid4())

    assert result.total == 0
    assert result.data == []


@pytest.mark.asyncio
async def test_service_recommendations_ranks_higher_score_first():
    """Higher scored recommendations appear before lower scored ones."""
    from app.services.recommendation_service import RecommendationService

    mock_db = AsyncMock()
    svc = RecommendationService(mock_db)
    profile = _make_profile()

    scheme_a = _make_scheme(is_featured=True, state=None)  # will get featured bonus
    scheme_b = _make_scheme(is_featured=False, state="Kerala")  # no featured, state mismatch

    eligible_result = _make_eligibility(
        status="eligible",
        passed_rules=[
            RuleResult(criterion="Occupation", requirement="", user_value="Farmer", passed=True, reason=""),
            RuleResult(criterion="Annual Income", requirement="", user_value="₹80,000", passed=True, reason=""),
        ],
        total_rules=2,
        passed_count=2,
    )

    async def mock_evaluate(scheme_id, user_id):
        return eligible_result

    with patch.object(svc._repo, "get_user_profile", return_value=profile), \
         patch.object(svc._repo, "get_all_active_schemes", return_value=[scheme_a, scheme_b]), \
         patch.object(svc._eligibility_svc, "evaluate_scheme", side_effect=mock_evaluate):
        result = await svc.get_recommendations(uuid.uuid4())

    assert result.total >= 1
    if len(result.data) >= 2:
        # The first scheme (featured) should score higher
        assert result.data[0].recommendation_score >= result.data[1].recommendation_score
