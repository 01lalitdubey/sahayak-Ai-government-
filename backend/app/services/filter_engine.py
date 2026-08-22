"""
Filter Engine — Sahayak AI / CraftNCode (Implemented by Person A)
==================================================================
Performs strict boolean eligibility filtering of government schemes
against a citizen user profile.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Mapping, Optional, Sequence, Union

try:
    from app.services.ranker import UserProfile, _clean_str, _extract_criterion, _is_wildcard, _parse_numeric, _safe_get
except ImportError:
    try:
        from ranker import UserProfile, _clean_str, _extract_criterion, _is_wildcard, _parse_numeric, _safe_get
    except ImportError:
        from dataclasses import dataclass

        @dataclass
        class UserProfile:  # type: ignore[no-redef]
            age: Optional[int] = None
            gender: Optional[str] = None
            occupation: Optional[str] = None
            annual_income: Optional[Union[int, float]] = None
            state: Optional[str] = None
            district: Optional[str] = None
            category: Optional[str] = None
            education: Optional[str] = None
            is_farmer: Optional[bool] = None
            farmer_category: Optional[str] = None
            is_disabled: Optional[bool] = None
            disability_percentage: Optional[float] = None
            is_bpl: Optional[bool] = None
            is_minority: Optional[bool] = None

        def _safe_get(obj: Any, key: str, default: Any = None) -> Any:
            if obj is None:
                return default
            if isinstance(obj, Mapping):
                return obj.get(key, default)
            return getattr(obj, key, default)

        def _clean_str(val: Any) -> Optional[str]:
            if val is None:
                return None
            if hasattr(val, "value"):
                val = val.value
            s = str(val).strip()
            return s if s else None

        def _is_wildcard(val: Any) -> bool:
            if val is None:
                return True
            if hasattr(val, "value"):
                val = val.value
            if isinstance(val, str):
                return val.strip().lower() in {"", "*", "all", "any", "na", "n/a", "none", "null", "pan-india", "central"}
            if isinstance(val, (list, tuple, set)):
                return len(val) == 0 or all(_is_wildcard(x) for x in val)
            return False

        def _extract_criterion(scheme: Mapping[str, Any], *candidate_keys: str, default: Any = None) -> Any:
            for k in candidate_keys:
                if k in scheme and scheme[k] is not None:
                    return scheme[k]
            for container_key in ("criteria", "rules", "eligibility_rules", "eligibility_criteria"):
                container = scheme.get(container_key)
                if isinstance(container, Mapping):
                    for k in candidate_keys:
                        if k in container and container[k] is not None:
                            return container[k]
            return default

        def _parse_numeric(val: Any) -> Optional[float]:
            if val is None or _is_wildcard(val):
                return None
            try:
                return float(str(val).replace(",", "").strip())
            except (ValueError, TypeError):
                return None

logger = logging.getLogger(__name__)


def is_eligible(profile: Union[UserProfile, Any], scheme: Mapping[str, Any]) -> bool:
    """Evaluate whether a user profile strictly meets all non-wildcard criteria of a scheme."""
    # 1. State
    target_state = _extract_criterion(scheme, "state", "applicable_state", "target_state", "states")
    if not _is_wildcard(target_state):
        user_state = _clean_str(_safe_get(profile, "state"))
        if not user_state:
            return False
        user_state_lower = user_state.lower()
        if isinstance(target_state, (list, tuple, set)):
            if not any(str(s).strip().lower() == user_state_lower for s in target_state):
                return False
        else:
            if str(target_state).strip().lower() != user_state_lower:
                return False

    # 2. Gender
    target_gender = _extract_criterion(scheme, "gender", "target_gender", "eligible_gender", "for_gender")
    if not _is_wildcard(target_gender):
        user_gender = _clean_str(_safe_get(profile, "gender"))
        if not user_gender:
            return False
        user_g_lower = user_gender.lower()
        target_g_lower = str(target_gender).strip().lower()
        female_syns = {"female", "woman", "women", "girl", "girls"}
        male_syns = {"male", "man", "men", "boy", "boys"}
        if target_g_lower in female_syns and user_g_lower not in female_syns:
            return False
        elif target_g_lower in male_syns and user_g_lower not in male_syns:
            return False
        elif target_g_lower not in female_syns and target_g_lower not in male_syns and target_g_lower != user_g_lower:
            return False

    # 3. Age
    min_age_val = _extract_criterion(scheme, "minimum_age", "min_age", "age_min")
    max_age_val = _extract_criterion(scheme, "maximum_age", "max_age", "age_max")
    min_age = _parse_numeric(min_age_val)
    max_age = _parse_numeric(max_age_val)
    if min_age is not None or max_age is not None:
        user_age = _parse_numeric(_safe_get(profile, "age"))
        if user_age is None:
            return False
        if min_age is not None and user_age < min_age:
            return False
        if max_age is not None and user_age > max_age:
            return False

    # 4. Income
    max_income_val = _extract_criterion(scheme, "maximum_income", "max_income", "income_limit", "income_ceiling", "income_threshold")
    max_income = _parse_numeric(max_income_val)
    if max_income is not None and max_income > 0:
        user_income = _parse_numeric(_safe_get(profile, "annual_income", _safe_get(profile, "income")))
        if user_income is None or user_income > max_income:
            return False

    # 5. Farmer
    require_farmer = _extract_criterion(scheme, "require_farmer", "is_farmer", "farmer_only", "farmer_status")
    if require_farmer is True or (isinstance(require_farmer, str) and require_farmer.lower() in {"true", "yes", "farmer"}):
        user_farmer = bool(_safe_get(profile, "is_farmer", False))
        user_occ = _clean_str(_safe_get(profile, "occupation", "")) or ""
        if not user_farmer and not any(k in user_occ.lower() for k in ["farmer", "agriculture", "kisan"]):
            return False

    # 6. Disability
    require_disabled = _extract_criterion(scheme, "require_disabled", "is_disabled", "disability_required", "target_disability", "pwd_only")
    if require_disabled is True or (isinstance(require_disabled, str) and require_disabled.lower() in {"true", "yes", "pwd", "disabled"}):
        user_disabled = bool(_safe_get(profile, "is_disabled", False))
        if not user_disabled:
            return False

    # 7. Occupation
    target_occ = _extract_criterion(scheme, "target_occupation", "targeted_occupation", "occupation", "occupations", "eligible_occupations")
    if not _is_wildcard(target_occ):
        user_occ = _clean_str(_safe_get(profile, "occupation"))
        if not user_occ or _is_wildcard(user_occ):
            return False
        user_occ_lower = user_occ.lower().replace("_", " ").strip()
        if isinstance(target_occ, (list, tuple, set)):
            if not any(_clean_str(o) and (_clean_str(o).lower().replace("_", " ") in user_occ_lower or user_occ_lower in _clean_str(o).lower().replace("_", " ")) for o in target_occ):
                return False
        else:
            t_occ_str = _clean_str(target_occ)
            if not t_occ_str:
                return False
            t_occ_lower = t_occ_str.lower().replace("_", " ")
            if t_occ_lower not in user_occ_lower and user_occ_lower not in t_occ_lower:
                return False

    # 8. Category
    target_cat = _extract_criterion(scheme, "category", "social_category", "caste", "target_category", "eligible_categories")
    if not _is_wildcard(target_cat):
        user_cat = _clean_str(_safe_get(profile, "category"))
        if not user_cat or _is_wildcard(user_cat):
            return False
        user_cat_clean = user_cat.strip().upper()
        if isinstance(target_cat, (list, tuple, set)):
            if not any(str(c).strip().upper() == user_cat_clean for c in target_cat):
                return False
        else:
            if str(target_cat).strip().upper() != user_cat_clean:
                return False

    return True


def filter_eligible(
    profile: Union[UserProfile, Any],
    schemes: Sequence[Mapping[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Filter schemes to only those where the user profile satisfies all strict criteria.
    Returns list of eligible scheme dicts.
    """
    if not schemes:
        return []

    eligible: List[Dict[str, Any]] = []
    for s in schemes:
        if isinstance(s, Mapping) and is_eligible(profile, s):
            eligible.append(dict(s))
    return eligible


__all__ = ["is_eligible", "filter_eligible"]
