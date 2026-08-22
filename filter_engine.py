"""
Filter Engine Module — Sahayak AI
==================================
Deterministic rule evaluation engine for filtering welfare schemes against
citizen demographic and socio-economic profiles.

Evaluation Philosophy:
- Criteria pass if the rule constraint is unconstrained (None or 'any').
- Criteria pass if the citizen profile field is missing/null (non-disqualifying / plausible eligibility).
- Criteria pass if the citizen's concrete profile value satisfies the rule requirement.
- A scheme is eligible if ALL criteria evaluate to true.
"""

from __future__ import annotations

import enum
from typing import Any, List, Optional, Set, Tuple, Union

from schemas import (
    Education,
    FarmerStatus,
    Gender,
    MaritalStatus,
    Occupation,
    SchemeEligibilityRules,
    SchemeRecord,
    SocialCategory,
    UserProfile,
)


WILDCARD_TOKENS: Set[str] = {"any", "all", "*", "none", "n/a", "na", "", "null", "all-india", "central"}


# ============================================================================
# Helper Normalizers
# ============================================================================

def _normalize_to_set(val: Any) -> Optional[Set[str]]:
    """
    Extracts a set of canonical lowercase string values from a scalar, list, or enum.
    Returns None if val is None, empty, or contains a wildcard token.
    """
    if val is None:
        return None

    if isinstance(val, str):
        cleaned = val.strip().lower()
        if cleaned in WILDCARD_TOKENS:
            return None
        return {cleaned}

    if isinstance(val, enum.Enum):
        name_val = val.value.lower() if isinstance(val.value, str) else str(val.value).lower()
        if name_val in WILDCARD_TOKENS:
            return None
        return {name_val}

    if isinstance(val, (list, tuple, set)):
        result: Set[str] = set()
        for item in val:
            if item is None:
                continue
            item_str = item.value.lower() if isinstance(item, enum.Enum) else str(item).strip().lower()
            if item_str in WILDCARD_TOKENS:
                return None  # Wildcard in list matches everything
            if item_str:
                result.add(item_str)
        return result if result else None

    s = str(val).strip().lower()
    return None if s in WILDCARD_TOKENS else {s}


def _get_enum_str(val: Any) -> Optional[str]:
    """Extracts lowercase string from enum or string."""
    if val is None:
        return None
    if isinstance(val, enum.Enum):
        return val.value.lower() if isinstance(val.value, str) else str(val.value).lower()
    return str(val).strip().lower()


# ============================================================================
# Criterion Evaluators
# ============================================================================

def evaluate_age_criterion(
    profile_age: Optional[int],
    min_age: Optional[int],
    max_age: Optional[int],
) -> Tuple[bool, Optional[str]]:
    """Evaluates age boundary conditions."""
    if profile_age is None:
        return True, None

    if min_age is not None and profile_age < min_age:
        return False, f"Citizen age ({profile_age}) is below minimum required age ({min_age})."

    if max_age is not None and profile_age > max_age:
        return False, f"Citizen age ({profile_age}) exceeds maximum allowed age ({max_age})."

    return True, None


def evaluate_income_criterion(
    profile_income: Optional[float],
    max_annual_income: Optional[float],
) -> Tuple[bool, Optional[str]]:
    """Evaluates annual income ceiling."""
    if profile_income is None or max_annual_income is None:
        return True, None

    if profile_income > max_annual_income:
        return False, (
            f"Citizen annual income (INR {profile_income:,.0f}) exceeds "
            f"income ceiling of INR {max_annual_income:,.0f}."
        )

    return True, None


def evaluate_set_membership_criterion(
    profile_val: Any,
    rule_val: Any,
    criterion_name: str,
) -> Tuple[bool, Optional[str]]:
    """
    Generic set membership evaluation for categorical fields
    (occupation, farmer_status, social_category, gender, state, education, marital_status).
    """
    allowed_set = _normalize_to_set(rule_val)
    if allowed_set is None:
        return True, None  # Unconstrained rule

    if profile_val is None:
        return True, None  # Missing profile value is non-disqualifying

    user_val_str = _get_enum_str(profile_val)
    if not user_val_str or user_val_str in WILDCARD_TOKENS:
        return True, None

    if user_val_str not in allowed_set:
        return False, (
            f"Citizen {criterion_name} '{user_val_str}' does not match "
            f"allowed criteria: {sorted(list(allowed_set))}."
        )

    return True, None


def evaluate_disability_criterion(
    profile: UserProfile,
    disability_required: Optional[bool],
    min_disability_percentage: Optional[float],
) -> Tuple[bool, Optional[str]]:
    """Evaluates disability prerequisites and percentage thresholds."""
    if disability_required is None:
        return True, None

    if disability_required is True:
        # Scheme is exclusively for disabled citizens
        if profile.is_disabled is False and not profile.disability_type:
            return False, "Scheme requires certified disability status."

        if min_disability_percentage is not None and profile.disability_percentage is not None:
            if profile.disability_percentage < min_disability_percentage:
                return False, (
                    f"Disability percentage ({profile.disability_percentage}%) is below "
                    f"minimum requirement of {min_disability_percentage}%."
                )

    elif disability_required is False:
        # Scheme is strictly for non-disabled applicants
        if profile.is_disabled is True:
            return False, "Scheme is restricted to non-disabled applicants."

    return True, None


# ============================================================================
# Scheme & Rule Evaluation Functions
# ============================================================================

def is_scheme_eligible(
    profile: UserProfile,
    rules: SchemeEligibilityRules,
) -> Tuple[bool, List[str]]:
    """
    Evaluates a single UserProfile against SchemeEligibilityRules.
    Returns:
        (is_eligible: bool, failure_reasons: list[str])
    """
    disqualifications: List[str] = []

    # 1. Age check
    passed, reason = evaluate_age_criterion(profile.age, rules.min_age, rules.max_age)
    if not passed and reason:
        disqualifications.append(reason)

    # 2. Income check
    passed, reason = evaluate_income_criterion(profile.annual_income, rules.max_annual_income)
    if not passed and reason:
        disqualifications.append(reason)

    # 3. Occupation check
    passed, reason = evaluate_set_membership_criterion(profile.occupation, rules.occupation, "occupation")
    if not passed and reason:
        disqualifications.append(reason)

    # 4. Farmer Status check
    passed, reason = evaluate_set_membership_criterion(profile.farmer_status, rules.farmer_status, "farmer status")
    if not passed and reason:
        disqualifications.append(reason)

    # 5. Social Category check
    passed, reason = evaluate_set_membership_criterion(profile.social_category, rules.social_category, "social category")
    if not passed and reason:
        disqualifications.append(reason)

    # 6. Gender check
    passed, reason = evaluate_set_membership_criterion(profile.gender, rules.gender, "gender")
    if not passed and reason:
        disqualifications.append(reason)

    # 7. State check
    passed, reason = evaluate_set_membership_criterion(profile.state, rules.state, "state")
    if not passed and reason:
        disqualifications.append(reason)

    # 8. Education check
    passed, reason = evaluate_set_membership_criterion(profile.education, rules.education, "education")
    if not passed and reason:
        disqualifications.append(reason)

    # 9. Marital Status check
    passed, reason = evaluate_set_membership_criterion(profile.marital_status, rules.marital_status, "marital status")
    if not passed and reason:
        disqualifications.append(reason)

    # 10. Disability check
    passed, reason = evaluate_disability_criterion(profile, rules.disability_required, rules.min_disability_percentage)
    if not passed and reason:
        disqualifications.append(reason)

    is_eligible = len(disqualifications) == 0
    return is_eligible, disqualifications


def filter_eligible(
    profile: UserProfile,
    schemes: List[SchemeRecord],
) -> List[SchemeRecord]:
    """
    Filters a list of SchemeRecord instances against the provided UserProfile.

    Rules:
    - Executes deterministic boolean comparisons across all rule keys.
    - An unconstrained rule (None or 'any') matches all citizens.
    - A missing/null field on the UserProfile is non-disqualifying (treated as plausibly eligible).
    - Returns only the schemes where all specified constraints evaluate to true.

    Args:
        profile: The citizen demographic and economic profile.
        schemes: List of candidate scheme records to evaluate.

    Returns:
        List of SchemeRecord objects for which the citizen is eligible.
    """
    eligible_schemes: List[SchemeRecord] = []

    for scheme in schemes:
        if not scheme.is_active:
            continue

        rules = scheme.eligibility_rules
        is_match, _ = is_scheme_eligible(profile, rules)
        if is_match:
            eligible_schemes.append(scheme)

    return eligible_schemes


def filter_eligible_with_details(
    profile: UserProfile,
    schemes: List[SchemeRecord],
) -> List[dict[str, Any]]:
    """
    Evaluates schemes and returns structured audit details including pass/fail status
    and specific failure reasons for explainability.
    """
    results: List[dict[str, Any]] = []

    for scheme in schemes:
        rules = scheme.eligibility_rules
        is_match, reasons = is_scheme_eligible(profile, rules)
        results.append({
            "scheme_code": scheme.scheme_code,
            "scheme_name": scheme.name,
            "is_eligible": is_match,
            "is_active": scheme.is_active,
            "failure_reasons": reasons,
            "scheme": scheme,
        })

    return results


# ============================================================================
# Self-test block
# ============================================================================
if __name__ == "__main__":
    print("--- Running filter_engine.py Tests ---")

    # Sample Schemes
    s1 = SchemeRecord(
        scheme_code="PM-KISAN",
        name="PM Kisan Samman Nidhi",
        category="agriculture",
        eligibility_rules=SchemeEligibilityRules(
            min_age=18,
            max_age=75,
            occupation=[Occupation.FARMER],
            farmer_status=[FarmerStatus.MARGINAL_FARMER, FarmerStatus.SMALL_FARMER],
            state="any",
            gender=None,
            max_annual_income=200000.0,
        ),
    )

    s2 = SchemeRecord(
        scheme_code="WOMEN-SCHOLARSHIP-MH",
        name="Maharashtra Savitribai Phule Scholarship",
        category="education",
        eligibility_rules=SchemeEligibilityRules(
            min_age=14,
            max_age=25,
            gender=Gender.FEMALE,
            state="Maharashtra",
            max_annual_income=150000.0,
            occupation=["student", "unemployed"],
        ),
    )

    s3 = SchemeRecord(
        scheme_code="DIVYANG-PENSION",
        name="National Divyang Disability Pension",
        category="social_welfare",
        eligibility_rules=SchemeEligibilityRules(
            min_age=18,
            max_age=65,
            disability_required=True,
            min_disability_percentage=40.0,
        ),
    )

    s4 = SchemeRecord(
        scheme_code="ALL-CITIZEN-INSURANCE",
        name="Pradhan Mantri Suraksha Bima Yojana",
        category="insurance",
        eligibility_rules=SchemeEligibilityRules(
            min_age=18,
            max_age=70,
            # All other fields None / unconstrained
        ),
    )

    schemes_catalog = [s1, s2, s3, s4]

    # Test Case 1: Complete profile of a small female farmer from Maharashtra
    farmer_profile = UserProfile(
        age=32,
        gender=Gender.FEMALE,
        social_category=SocialCategory.OBC,
        occupation=Occupation.FARMER,
        farmer_status=FarmerStatus.SMALL_FARMER,
        annual_income=80000.0,
        state="Maharashtra",
        is_disabled=False,
    )

    matched = filter_eligible(farmer_profile, schemes_catalog)
    matched_codes = [s.scheme_code for s in matched]
    print(f"\n1. Female Farmer Eligible Schemes: {matched_codes}")
    assert "PM-KISAN" in matched_codes
    assert "ALL-CITIZEN-INSURANCE" in matched_codes
    assert "WOMEN-SCHOLARSHIP-MH" not in matched_codes  # Disqualified: age 32 > 25, occupation farmer != student
    assert "DIVYANG-PENSION" not in matched_codes      # Disqualified: disability_required

    # Test Case 2: Incomplete profile with missing/null fields (should NOT disqualify)
    partial_profile = UserProfile(
        age=20,
        gender=Gender.FEMALE,
        state="Maharashtra",
        # occupation, annual_income, farmer_status, is_disabled are missing/null
    )

    matched_partial = filter_eligible(partial_profile, schemes_catalog)
    matched_partial_codes = [s.scheme_code for s in matched_partial]
    print(f"\n2. Partial Profile Eligible Schemes: {matched_partial_codes}")
    # PM-KISAN, WOMEN-SCHOLARSHIP-MH, DIVYANG-PENSION, and ALL-CITIZEN-INSURANCE are all plausibly eligible!
    assert "PM-KISAN" in matched_partial_codes
    assert "WOMEN-SCHOLARSHIP-MH" in matched_partial_codes
    assert "ALL-CITIZEN-INSURANCE" in matched_partial_codes
    assert "DIVYANG-PENSION" in matched_partial_codes

    # Test Case 2b: Explicit non-disabled citizen excludes disability-required schemes
    non_disabled_profile = UserProfile(
        age=20,
        gender=Gender.FEMALE,
        state="Maharashtra",
        is_disabled=False,
    )
    matched_non_disabled = filter_eligible(non_disabled_profile, schemes_catalog)
    matched_non_disabled_codes = [s.scheme_code for s in matched_non_disabled]
    print(f"\n2b. Non-Disabled Profile Eligible Schemes: {matched_non_disabled_codes}")
    assert "DIVYANG-PENSION" not in matched_non_disabled_codes

    # Test Case 3: Disabled student citizen
    disabled_profile = UserProfile(
        age=22,
        gender=Gender.MALE,
        occupation=Occupation.STUDENT,
        is_disabled=True,
        disability_percentage=50.0,
        annual_income=40000.0,
    )
    matched_disabled = filter_eligible(disabled_profile, schemes_catalog)
    matched_disabled_codes = [s.scheme_code for s in matched_disabled]
    print(f"\n3. Disabled Student Eligible Schemes: {matched_disabled_codes}")
    assert "DIVYANG-PENSION" in matched_disabled_codes
    assert "ALL-CITIZEN-INSURANCE" in matched_disabled_codes
    assert "PM-KISAN" not in matched_disabled_codes  # Disqualified: occupation student != farmer

    print("\nAll filter engine tests executed and passed successfully!")
