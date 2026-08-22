"""
Deterministic Rule Engine — Sahayak AI
========================================
Each criterion is a separate evaluator implementing RuleEvaluator protocol.
Adding a new criterion = add one new class, register in EVALUATORS list.
No AI, no ML — pure deterministic logic.

Evaluation result has 3 states:
  PASS    — user satisfies this criterion
  FAIL    — user does NOT satisfy this criterion
  MISSING — user hasn't provided this profile field; can't evaluate
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol

from app.models.eligibility_rule import EligibilityRule
from app.models.profile import Profile
from app.schemas.eligibility import RuleResult

# Education hierarchy for minimum-education checks
_EDUCATION_ORDER = [
    "no_formal_education", "primary", "middle", "secondary",
    "higher_secondary", "graduate", "post_graduate", "doctorate", "other",
]


@dataclass
class EvalState:
    PASS = "pass"
    FAIL = "fail"
    MISSING = "missing"


class RuleEvaluator(Protocol):
    """
    Every evaluator must implement __call__(rule, profile) -> RuleResult | None.
    Return None if this evaluator has no applicable criterion in the rule
    (i.e., the rule field is NULL → no restriction).
    """
    def __call__(self, rule: EligibilityRule, profile: Profile) -> RuleResult | None: ...


# ── Individual Evaluators ─────────────────────────────────────────────────

def _age_evaluator(rule: EligibilityRule, profile: Profile) -> RuleResult | None:
    if rule.minimum_age is None and rule.maximum_age is None:
        return None  # no age restriction

    if profile.age is None:
        parts = []
        if rule.minimum_age is not None:
            parts.append(f"≥{rule.minimum_age}")
        if rule.maximum_age is not None:
            parts.append(f"≤{rule.maximum_age}")
        return RuleResult(
            criterion="Age",
            requirement=" and ".join(parts) + " years",
            user_value="Not provided",
            passed=False,
            reason="Age is missing from your profile.",
        )

    req_parts = []
    if rule.minimum_age is not None:
        req_parts.append(f"≥{rule.minimum_age}")
    if rule.maximum_age is not None:
        req_parts.append(f"≤{rule.maximum_age}")

    min_ok = rule.minimum_age is None or profile.age >= rule.minimum_age
    max_ok = rule.maximum_age is None or profile.age <= rule.maximum_age
    passed = min_ok and max_ok

    reason = (
        f"Age {profile.age} is within {rule.minimum_age or '∞'}–{rule.maximum_age or '∞'} years."
        if passed
        else f"Age {profile.age} does not meet requirement ({' and '.join(req_parts)} years)."
    )
    return RuleResult(
        criterion="Age",
        requirement=" and ".join(req_parts) + " years",
        user_value=f"{profile.age} years",
        passed=passed,
        reason=reason,
    )


def _income_evaluator(rule: EligibilityRule, profile: Profile) -> RuleResult | None:
    if rule.minimum_income is None and rule.maximum_income is None:
        return None

    req_parts = []
    if rule.minimum_income is not None:
        req_parts.append(f"≥₹{rule.minimum_income:,}")
    if rule.maximum_income is not None:
        req_parts.append(f"≤₹{rule.maximum_income:,}")
    requirement = " and ".join(req_parts)

    if profile.annual_income is None:
        return RuleResult(
            criterion="Annual Income",
            requirement=requirement,
            user_value="Not provided",
            passed=False,
            reason="Annual income is missing from your profile.",
        )

    min_ok = rule.minimum_income is None or profile.annual_income >= rule.minimum_income
    max_ok = rule.maximum_income is None or profile.annual_income <= rule.maximum_income
    passed = min_ok and max_ok

    reason = (
        f"Income ₹{profile.annual_income:,} meets requirement ({requirement})."
        if passed
        else f"Income ₹{profile.annual_income:,} does not meet requirement ({requirement})."
    )
    return RuleResult(
        criterion="Annual Income",
        requirement=requirement,
        user_value=f"₹{profile.annual_income:,}",
        passed=passed,
        reason=reason,
    )


def _gender_evaluator(rule: EligibilityRule, profile: Profile) -> RuleResult | None:
    if rule.gender is None:
        return None

    requirement = rule.gender.value.replace("_", " ").title()

    if profile.gender is None:
        return RuleResult(
            criterion="Gender",
            requirement=requirement,
            user_value="Not provided",
            passed=False,
            reason="Gender is missing from your profile.",
        )

    passed = profile.gender == rule.gender
    return RuleResult(
        criterion="Gender",
        requirement=requirement,
        user_value=profile.gender.value.replace("_", " ").title(),
        passed=passed,
        reason=(
            f"Gender matches requirement ({requirement})."
            if passed
            else f"Gender '{profile.gender.value}' does not match required '{rule.gender.value}'."
        ),
    )


def _occupation_evaluator(rule: EligibilityRule, profile: Profile) -> RuleResult | None:
    if rule.occupation is None:
        return None

    requirement = rule.occupation.value.replace("_", " ").title()

    if profile.occupation is None:
        return RuleResult(
            criterion="Occupation",
            requirement=requirement,
            user_value="Not provided",
            passed=False,
            reason="Occupation is missing from your profile.",
        )

    passed = profile.occupation == rule.occupation
    return RuleResult(
        criterion="Occupation",
        requirement=requirement,
        user_value=profile.occupation.value.replace("_", " ").title(),
        passed=passed,
        reason=(
            f"Occupation matches requirement ({requirement})."
            if passed
            else f"Occupation '{profile.occupation.value}' does not match required '{rule.occupation.value}'."
        ),
    )


def _state_evaluator(rule: EligibilityRule, profile: Profile) -> RuleResult | None:
    if rule.state is None:
        return None  # pan-India scheme — no state restriction

    if profile.state is None:
        return RuleResult(
            criterion="State of Residence",
            requirement=rule.state,
            user_value="Not provided",
            passed=False,
            reason="State is missing from your profile.",
        )

    passed = profile.state.lower() == rule.state.lower()
    return RuleResult(
        criterion="State of Residence",
        requirement=rule.state,
        user_value=profile.state,
        passed=passed,
        reason=(
            f"State '{profile.state}' matches requirement."
            if passed
            else f"This scheme is only for residents of {rule.state}. Your state: {profile.state}."
        ),
    )


def _district_evaluator(rule: EligibilityRule, profile: Profile) -> RuleResult | None:
    if rule.district is None:
        return None

    if profile.district is None:
        return RuleResult(
            criterion="District",
            requirement=rule.district,
            user_value="Not provided",
            passed=False,
            reason="District is missing from your profile.",
        )

    passed = profile.district.lower() == rule.district.lower()
    return RuleResult(
        criterion="District",
        requirement=rule.district,
        user_value=profile.district,
        passed=passed,
        reason=(
            f"District '{profile.district}' matches requirement."
            if passed
            else f"Scheme is restricted to {rule.district}. Your district: {profile.district}."
        ),
    )


def _category_evaluator(rule: EligibilityRule, profile: Profile) -> RuleResult | None:
    if rule.category is None:
        return None

    requirement = rule.category.value.upper()

    if profile.category is None:
        return RuleResult(
            criterion="Social Category",
            requirement=requirement,
            user_value="Not provided",
            passed=False,
            reason="Social category (SC/ST/OBC/General) is missing from your profile.",
        )

    passed = profile.category == rule.category
    return RuleResult(
        criterion="Social Category",
        requirement=requirement,
        user_value=profile.category.value.upper(),
        passed=passed,
        reason=(
            f"Category '{profile.category.value.upper()}' matches requirement."
            if passed
            else f"Category '{profile.category.value.upper()}' does not match required '{requirement}'."
        ),
    )


def _education_evaluator(rule: EligibilityRule, profile: Profile) -> RuleResult | None:
    if rule.education is None:
        return None

    requirement = rule.education.value.replace("_", " ").title()

    if profile.education is None:
        return RuleResult(
            criterion="Education",
            requirement=f"At least {requirement}",
            user_value="Not provided",
            passed=False,
            reason="Education level is missing from your profile.",
        )

    rule_level = _EDUCATION_ORDER.index(rule.education.value) if rule.education.value in _EDUCATION_ORDER else -1
    user_level = _EDUCATION_ORDER.index(profile.education.value) if profile.education.value in _EDUCATION_ORDER else -1
    passed = user_level >= rule_level

    user_label = profile.education.value.replace("_", " ").title()
    return RuleResult(
        criterion="Education",
        requirement=f"At least {requirement}",
        user_value=user_label,
        passed=passed,
        reason=(
            f"Education '{user_label}' meets minimum requirement of '{requirement}'."
            if passed
            else f"Education '{user_label}' is below required minimum '{requirement}'."
        ),
    )


def _farmer_evaluator(rule: EligibilityRule, profile: Profile) -> RuleResult | None:
    if rule.require_farmer is None:
        return None

    passed = profile.is_farmer == rule.require_farmer
    requirement = "Must be a farmer" if rule.require_farmer else "Must not be a farmer"
    user_value = "Farmer" if profile.is_farmer else "Not a farmer"

    return RuleResult(
        criterion="Farmer Status",
        requirement=requirement,
        user_value=user_value,
        passed=passed,
        reason=(
            f"Farmer status matches requirement."
            if passed
            else f"{requirement} — your profile shows: {user_value}."
        ),
    )


def _disabled_evaluator(rule: EligibilityRule, profile: Profile) -> RuleResult | None:
    if rule.require_disabled is None:
        return None

    passed = profile.is_disabled == rule.require_disabled
    requirement = "Must have a disability" if rule.require_disabled else "Disability not required"
    user_value = "Has disability" if profile.is_disabled else "No disability"

    return RuleResult(
        criterion="Disability Status",
        requirement=requirement,
        user_value=user_value,
        passed=passed,
        reason=(
            "Disability status matches requirement."
            if passed
            else f"{requirement} — your profile shows: {user_value}."
        ),
    )


# ── Registry — add new evaluators here ───────────────────────────────────
EVALUATORS: list[RuleEvaluator] = [
    _age_evaluator,       # type: ignore[list-item]
    _income_evaluator,    # type: ignore[list-item]
    _gender_evaluator,    # type: ignore[list-item]
    _occupation_evaluator,# type: ignore[list-item]
    _state_evaluator,     # type: ignore[list-item]
    _district_evaluator,  # type: ignore[list-item]
    _category_evaluator,  # type: ignore[list-item]
    _education_evaluator, # type: ignore[list-item]
    _farmer_evaluator,    # type: ignore[list-item]
    _disabled_evaluator,  # type: ignore[list-item]
]


# ── Main evaluation entry point ───────────────────────────────────────────

def evaluate_rule(rule: EligibilityRule, profile: Profile) -> list[RuleResult]:
    """
    Run all evaluators against one rule + profile pair.
    Returns only results where a criterion was applicable (non-None).
    """
    results: list[RuleResult] = []
    for evaluator in EVALUATORS:
        result = evaluator(rule, profile)
        if result is not None:
            results.append(result)
    return results
