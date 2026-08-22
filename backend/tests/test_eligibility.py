"""
Eligibility Engine Tests — Sahayak AI Phase 5
=============================================
Tests: rule engine evaluators, service logic (mocked DB),
       schemas, exception hierarchy, API security.
All 123 previous tests must still pass.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.models.enums import (
    GenderEnum, OccupationEnum, CategoryEnum, EducationEnum,
)


# ─── Helpers ──────────────────────────────────────────────────────────────

def _rule(**kwargs):
    """Build a mock EligibilityRule with all fields defaulting to None."""
    r = MagicMock()
    for field in [
        "minimum_age", "maximum_age", "minimum_income", "maximum_income",
        "gender", "occupation", "state", "district", "category",
        "education", "require_farmer", "require_disabled",
    ]:
        setattr(r, field, kwargs.get(field, None))
    return r


def _profile(**kwargs):
    """Build a mock Profile with sensible defaults."""
    p = MagicMock()
    p.age = kwargs.get("age", 30)
    p.annual_income = kwargs.get("annual_income", 120000)
    p.gender = kwargs.get("gender", GenderEnum.MALE)
    p.occupation = kwargs.get("occupation", OccupationEnum.FARMER)
    p.state = kwargs.get("state", "Maharashtra")
    p.district = kwargs.get("district", None)
    p.category = kwargs.get("category", CategoryEnum.SC)
    p.education = kwargs.get("education", EducationEnum.SECONDARY)
    p.is_farmer = kwargs.get("is_farmer", True)
    p.is_disabled = kwargs.get("is_disabled", False)
    return p


# ─── Age evaluator ────────────────────────────────────────────────────────

def test_age_pass_within_range():
    from app.services.rule_engine import _age_evaluator
    r = _rule(minimum_age=18, maximum_age=60)
    result = _age_evaluator(r, _profile(age=35))
    assert result is not None
    assert result.passed is True
    assert "35" in result.user_value


def test_age_fail_below_minimum():
    from app.services.rule_engine import _age_evaluator
    r = _rule(minimum_age=18)
    result = _age_evaluator(r, _profile(age=15))
    assert result.passed is False


def test_age_fail_above_maximum():
    from app.services.rule_engine import _age_evaluator
    r = _rule(maximum_age=40)
    result = _age_evaluator(r, _profile(age=45))
    assert result.passed is False


def test_age_missing_from_profile():
    from app.services.rule_engine import _age_evaluator
    r = _rule(minimum_age=18)
    p = _profile()
    p.age = None
    result = _age_evaluator(r, p)
    assert result.passed is False
    assert result.user_value == "Not provided"


def test_age_no_restriction_returns_none():
    from app.services.rule_engine import _age_evaluator
    result = _age_evaluator(_rule(), _profile())
    assert result is None


# ─── Income evaluator ─────────────────────────────────────────────────────

def test_income_pass_below_maximum():
    from app.services.rule_engine import _income_evaluator
    r = _rule(maximum_income=200000)
    result = _income_evaluator(r, _profile(annual_income=100000))
    assert result.passed is True


def test_income_fail_above_maximum():
    from app.services.rule_engine import _income_evaluator
    r = _rule(maximum_income=100000)
    result = _income_evaluator(r, _profile(annual_income=250000))
    assert result.passed is False


def test_income_missing():
    from app.services.rule_engine import _income_evaluator
    r = _rule(maximum_income=100000)
    p = _profile()
    p.annual_income = None
    result = _income_evaluator(r, p)
    assert result.passed is False
    assert "Not provided" in result.user_value


def test_income_no_restriction():
    from app.services.rule_engine import _income_evaluator
    assert _income_evaluator(_rule(), _profile()) is None


# ─── Gender evaluator ─────────────────────────────────────────────────────

def test_gender_pass():
    from app.services.rule_engine import _gender_evaluator
    r = _rule(gender=GenderEnum.FEMALE)
    result = _gender_evaluator(r, _profile(gender=GenderEnum.FEMALE))
    assert result.passed is True


def test_gender_fail():
    from app.services.rule_engine import _gender_evaluator
    r = _rule(gender=GenderEnum.FEMALE)
    result = _gender_evaluator(r, _profile(gender=GenderEnum.MALE))
    assert result.passed is False


def test_gender_no_restriction():
    from app.services.rule_engine import _gender_evaluator
    assert _gender_evaluator(_rule(), _profile()) is None


# ─── Occupation evaluator ─────────────────────────────────────────────────

def test_occupation_pass():
    from app.services.rule_engine import _occupation_evaluator
    r = _rule(occupation=OccupationEnum.FARMER)
    result = _occupation_evaluator(r, _profile(occupation=OccupationEnum.FARMER))
    assert result.passed is True


def test_occupation_fail():
    from app.services.rule_engine import _occupation_evaluator
    r = _rule(occupation=OccupationEnum.STUDENT)
    result = _occupation_evaluator(r, _profile(occupation=OccupationEnum.FARMER))
    assert result.passed is False


# ─── State evaluator ──────────────────────────────────────────────────────

def test_state_pass():
    from app.services.rule_engine import _state_evaluator
    r = _rule(state="Maharashtra")
    result = _state_evaluator(r, _profile(state="Maharashtra"))
    assert result.passed is True


def test_state_fail():
    from app.services.rule_engine import _state_evaluator
    r = _rule(state="Kerala")
    result = _state_evaluator(r, _profile(state="Maharashtra"))
    assert result.passed is False


def test_state_case_insensitive():
    from app.services.rule_engine import _state_evaluator
    r = _rule(state="maharashtra")
    result = _state_evaluator(r, _profile(state="Maharashtra"))
    assert result.passed is True


def test_state_no_restriction():
    from app.services.rule_engine import _state_evaluator
    assert _state_evaluator(_rule(), _profile()) is None


# ─── Category evaluator ───────────────────────────────────────────────────

def test_category_pass():
    from app.services.rule_engine import _category_evaluator
    r = _rule(category=CategoryEnum.SC)
    result = _category_evaluator(r, _profile(category=CategoryEnum.SC))
    assert result.passed is True


def test_category_fail():
    from app.services.rule_engine import _category_evaluator
    r = _rule(category=CategoryEnum.ST)
    result = _category_evaluator(r, _profile(category=CategoryEnum.SC))
    assert result.passed is False


# ─── Education evaluator ──────────────────────────────────────────────────

def test_education_pass_exact():
    from app.services.rule_engine import _education_evaluator
    r = _rule(education=EducationEnum.SECONDARY)
    result = _education_evaluator(r, _profile(education=EducationEnum.SECONDARY))
    assert result.passed is True


def test_education_pass_higher():
    from app.services.rule_engine import _education_evaluator
    r = _rule(education=EducationEnum.PRIMARY)
    result = _education_evaluator(r, _profile(education=EducationEnum.GRADUATE))
    assert result.passed is True


def test_education_fail_lower():
    from app.services.rule_engine import _education_evaluator
    r = _rule(education=EducationEnum.GRADUATE)
    result = _education_evaluator(r, _profile(education=EducationEnum.PRIMARY))
    assert result.passed is False


# ─── Farmer evaluator ─────────────────────────────────────────────────────

def test_farmer_pass():
    from app.services.rule_engine import _farmer_evaluator
    r = _rule(require_farmer=True)
    result = _farmer_evaluator(r, _profile(is_farmer=True))
    assert result.passed is True


def test_farmer_fail():
    from app.services.rule_engine import _farmer_evaluator
    r = _rule(require_farmer=True)
    result = _farmer_evaluator(r, _profile(is_farmer=False))
    assert result.passed is False


def test_farmer_no_restriction():
    from app.services.rule_engine import _farmer_evaluator
    assert _farmer_evaluator(_rule(), _profile()) is None


# ─── Disabled evaluator ───────────────────────────────────────────────────

def test_disabled_pass():
    from app.services.rule_engine import _disabled_evaluator
    r = _rule(require_disabled=True)
    result = _disabled_evaluator(r, _profile(is_disabled=True))
    assert result.passed is True


def test_disabled_no_restriction():
    from app.services.rule_engine import _disabled_evaluator
    assert _disabled_evaluator(_rule(), _profile()) is None


# ─── Full evaluate_rule ───────────────────────────────────────────────────

def test_evaluate_rule_multiple_criteria():
    from app.services.rule_engine import evaluate_rule
    r = _rule(minimum_age=18, maximum_age=60, maximum_income=200000)
    p = _profile(age=30, annual_income=100000)
    results = evaluate_rule(r, p)
    # age = 1 result, income = 1 result → total 2
    assert len(results) == 2
    assert all(res.passed for res in results)


def test_evaluate_rule_partial_failure():
    from app.services.rule_engine import evaluate_rule
    r = _rule(minimum_age=18, maximum_age=60, state="Kerala")
    p = _profile(age=30, state="Maharashtra")
    results = evaluate_rule(r, p)
    passed = [res for res in results if res.passed]
    failed = [res for res in results if not res.passed]
    # age passes (1), state fails (1)
    assert len(passed) == 1
    assert len(failed) == 1


def test_evaluate_rule_no_criteria_returns_empty():
    from app.services.rule_engine import evaluate_rule
    r = _rule()  # all None
    p = _profile()
    results = evaluate_rule(r, p)
    assert results == []


# ─── Score calculation ────────────────────────────────────────────────────

def test_score_all_pass():
    """100% score when all rules pass."""
    from app.services.rule_engine import evaluate_rule
    r = _rule(minimum_age=18, state="Maharashtra")
    p = _profile(age=25, state="Maharashtra")
    results = evaluate_rule(r, p)
    passed = [res for res in results if res.passed]
    total = len(results)
    score = round(len(passed) / total * 100, 1) if total > 0 else 100.0
    assert score == 100.0


def test_score_partial():
    from app.services.rule_engine import evaluate_rule
    r = _rule(minimum_age=18, state="Kerala", category=CategoryEnum.SC)
    p = _profile(age=25, state="Maharashtra", category=CategoryEnum.SC)
    results = evaluate_rule(r, p)
    passed_count = sum(1 for res in results if res.passed)
    score = round(passed_count / len(results) * 100, 1)
    assert 0 < score < 100


# ─── Schema tests ─────────────────────────────────────────────────────────

def test_eligibility_check_request_valid():
    from app.schemas.eligibility import EligibilityCheckRequest
    req = EligibilityCheckRequest(scheme_id=uuid.uuid4())
    assert req.scheme_id is not None


def test_rule_result_schema():
    from app.schemas.eligibility import RuleResult
    r = RuleResult(
        criterion="Age",
        requirement="18–60 years",
        user_value="35 years",
        passed=True,
        reason="Age 35 is within range.",
    )
    assert r.passed is True


def test_eligibility_check_response_schema():
    from app.schemas.eligibility import EligibilityCheckResponse, RuleResult
    resp = EligibilityCheckResponse(
        scheme_id=uuid.uuid4(),
        scheme_name="PM Kisan",
        scheme_code="PM-KISAN-2024",
        eligible=True,
        status="eligible",
        score=100.0,
        total_rules=2,
        passed_count=2,
        failed_count=0,
        missing_count=0,
        passed_rules=[],
        failed_rules=[],
        missing_information=[],
        recommendations=[],
        evaluated_at=datetime.now(tz=timezone.utc),
    )
    assert resp.eligible is True
    assert resp.score == 100.0


def test_eligibility_admin_create_schema():
    from app.schemas.eligibility import EligibilityRuleAdminCreate
    r = EligibilityRuleAdminCreate(
        scheme_id=uuid.uuid4(),
        minimum_age=18,
        maximum_age=60,
        maximum_income=200000,
        state="Maharashtra",
    )
    assert r.minimum_age == 18


# ─── Exception hierarchy ──────────────────────────────────────────────────

def test_eligibility_exceptions():
    from app.core.exceptions import ProfileIncompleteException, NoEligibilityRulesException
    assert ProfileIncompleteException.status_code == 422
    assert NoEligibilityRulesException.status_code == 404


# ─── Service tests (mocked DB) ────────────────────────────────────────────

def _mock_scheme(name="PM Kisan", code="PM-KISAN-2024"):
    from app.models.enums import SchemeTypeEnum, ApplicationModeEnum, SchemeCategoryEnum
    s = MagicMock()
    s.id = uuid.uuid4()
    s.name = name
    s.scheme_code = code
    s.scheme_type = SchemeTypeEnum.CENTRAL
    s.category = SchemeCategoryEnum.AGRICULTURE
    s.ministry = "Ministry of Agriculture"
    s.state = None
    s.is_active = True
    return s


@pytest.mark.asyncio
async def test_service_evaluate_no_rules_returns_no_rules_status():
    from app.services.eligibility_service import EligibilityService
    mock_db = AsyncMock()
    svc = EligibilityService(mock_db)
    scheme = _mock_scheme()
    profile = _profile()

    with patch.object(svc._scheme_repo, "get_by_id", return_value=scheme), \
         patch.object(svc._profile_repo, "get_by_user_id", return_value=profile), \
         patch.object(svc._eligibility_repo, "get_rules_for_scheme", return_value=[]):
        result = await svc.evaluate_scheme(scheme.id, uuid.uuid4())

    assert result.status == "no_rules"
    assert result.eligible is False


@pytest.mark.asyncio
async def test_service_evaluate_scheme_not_found():
    from app.services.eligibility_service import EligibilityService
    from app.core.exceptions import SchemeNotFoundException
    mock_db = AsyncMock()
    svc = EligibilityService(mock_db)

    with patch.object(svc._scheme_repo, "get_by_id", return_value=None):
        with pytest.raises(SchemeNotFoundException):
            await svc.evaluate_scheme(uuid.uuid4(), uuid.uuid4())


@pytest.mark.asyncio
async def test_service_evaluate_no_profile():
    from app.services.eligibility_service import EligibilityService
    from app.core.exceptions import ProfileIncompleteException
    mock_db = AsyncMock()
    svc = EligibilityService(mock_db)
    scheme = _mock_scheme()

    with patch.object(svc._scheme_repo, "get_by_id", return_value=scheme), \
         patch.object(svc._profile_repo, "get_by_user_id", return_value=None):
        with pytest.raises(ProfileIncompleteException):
            await svc.evaluate_scheme(scheme.id, uuid.uuid4())


@pytest.mark.asyncio
async def test_service_evaluate_eligible_user():
    from app.services.eligibility_service import EligibilityService
    mock_db = AsyncMock()
    svc = EligibilityService(mock_db)
    scheme = _mock_scheme()
    profile = _profile(age=30, state="Maharashtra")
    rule = _rule(minimum_age=18, maximum_age=60, state="Maharashtra")

    with patch.object(svc._scheme_repo, "get_by_id", return_value=scheme), \
         patch.object(svc._profile_repo, "get_by_user_id", return_value=profile), \
         patch.object(svc._eligibility_repo, "get_rules_for_scheme", return_value=[rule]):
        result = await svc.evaluate_scheme(scheme.id, uuid.uuid4())

    assert result.eligible is True
    assert result.status == "eligible"
    assert result.score == 100.0


@pytest.mark.asyncio
async def test_service_evaluate_ineligible_user():
    from app.services.eligibility_service import EligibilityService
    mock_db = AsyncMock()
    svc = EligibilityService(mock_db)
    scheme = _mock_scheme()
    profile = _profile(age=30, state="Maharashtra")
    rule = _rule(state="Kerala")   # user is in Maharashtra — will fail

    with patch.object(svc._scheme_repo, "get_by_id", return_value=scheme), \
         patch.object(svc._profile_repo, "get_by_user_id", return_value=profile), \
         patch.object(svc._eligibility_repo, "get_rules_for_scheme", return_value=[rule]):
        result = await svc.evaluate_scheme(scheme.id, uuid.uuid4())

    assert result.eligible is False
    assert result.status == "not_eligible"
    assert result.failed_count > 0


@pytest.mark.asyncio
async def test_service_evaluate_incomplete_profile():
    from app.services.eligibility_service import EligibilityService
    mock_db = AsyncMock()
    svc = EligibilityService(mock_db)
    scheme = _mock_scheme()
    profile = _profile()
    profile.age = None   # missing age
    rule = _rule(minimum_age=18)

    with patch.object(svc._scheme_repo, "get_by_id", return_value=scheme), \
         patch.object(svc._profile_repo, "get_by_user_id", return_value=profile), \
         patch.object(svc._eligibility_repo, "get_rules_for_scheme", return_value=[rule]):
        result = await svc.evaluate_scheme(scheme.id, uuid.uuid4())

    assert result.status == "incomplete_profile"
    assert "Age" in result.missing_information


# ─── API endpoint security tests ─────────────────────────────────────────

def _client():
    from app.main import create_application
    return TestClient(create_application(), raise_server_exceptions=False)


def test_check_eligibility_requires_auth():
    client = _client()
    resp = client.post("/api/v1/eligibility/check", json={"scheme_id": str(uuid.uuid4())})
    assert resp.status_code == 401


def test_my_schemes_requires_auth():
    client = _client()
    resp = client.get("/api/v1/eligibility/my-schemes")
    assert resp.status_code == 401


def test_admin_rules_requires_admin():
    client = _client()
    resp = client.get("/api/v1/eligibility/admin/rules")
    assert resp.status_code == 401


def test_create_rule_requires_admin():
    client = _client()
    resp = client.post("/api/v1/eligibility/admin/rules", json={
        "scheme_id": str(uuid.uuid4())
    })
    assert resp.status_code == 401


def test_eligibility_routes_in_openapi():
    client = _client()
    paths = client.get("/openapi.json").json()["paths"]
    assert "/api/v1/eligibility/check" in paths
    assert "/api/v1/eligibility/my-schemes" in paths
    assert "/api/v1/eligibility/admin/rules" in paths
