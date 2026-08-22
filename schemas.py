"""
Standalone Schemas Module — Pydantic v2
=========================================
Defines domain enums, citizen profile schema with validations,
eligibility rule constraints, and external API scheme payload models.
"""

from __future__ import annotations

import enum
from typing import Any, List, Optional, Set, Union
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


# ============================================================================
# 1. Domain Enums
# ============================================================================

class Gender(str, enum.Enum):
    """Gender identities for citizen profiles and scheme criteria."""
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    TRANSGENDER = "transgender"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"
    ANY = "any"


class SocialCategory(str, enum.Enum):
    """Social categories / castes as recognized by Government of India."""
    GENERAL = "general"
    OBC = "obc"  # Other Backward Class
    SC = "sc"    # Scheduled Caste
    ST = "st"    # Scheduled Tribe
    EWS = "ews"  # Economically Weaker Section
    OTHER = "other"
    ANY = "any"


class Occupation(str, enum.Enum):
    """Primary livelihood and occupational classifications."""
    FARMER = "farmer"
    DAILY_WAGE_LABORER = "daily_wage_laborer"
    STUDENT = "student"
    UNEMPLOYED = "unemployed"
    SELF_EMPLOYED = "self_employed"
    SALARIED = "salaried"
    HOMEMAKER = "homemaker"
    RETIRED = "retired"
    OTHER = "other"
    ANY = "any"


class Education(str, enum.Enum):
    """Highest educational qualification achieved."""
    NO_FORMAL_EDUCATION = "no_formal_education"
    PRIMARY = "primary"                   # Up to Class 5
    MIDDLE = "middle"                     # Class 6 to 8
    SECONDARY = "secondary"               # Class 9 to 10 (Matriculation)
    HIGHER_SECONDARY = "higher_secondary" # Class 11 to 12 (Intermediate)
    DIPLOMA = "diploma"                   # Vocational / Polytechnic diploma
    GRADUATE = "graduate"                 # Bachelor's Degree
    POST_GRADUATE = "post_graduate"       # Master's Degree
    DOCTORATE = "doctorate"               # Ph.D. / Equivalent
    OTHER = "other"
    ANY = "any"


class FarmerStatus(str, enum.Enum):
    """Landholding-based farmer classification under agricultural schemes."""
    NOT_FARMER = "not_farmer"
    MARGINAL_FARMER = "marginal_farmer"  # Land holding up to 1 hectare (~2.5 acres)
    SMALL_FARMER = "small_farmer"        # Land holding 1 to 2 hectares (2.5 to 5 acres)
    LARGE_FARMER = "large_farmer"        # Land holding over 2 hectares (> 5 acres)
    ANY = "any"


class MaritalStatus(str, enum.Enum):
    """Marital status of citizen."""
    SINGLE = "single"
    MARRIED = "married"
    WIDOWED = "widowed"
    DIVORCED = "divorced"
    SEPARATED = "separated"
    OTHER = "other"
    ANY = "any"


# ============================================================================
# 2. User Profile Model
# ============================================================================

class UserProfile(BaseModel):
    """
    Citizen demographic & socio-economic profile.
    Enforces strict boundary validations across age (0-120), income (>= 0),
    and optional fields like disability details.
    """
    model_config = ConfigDict(
        use_enum_values=True,
        validate_assignment=True,
        str_strip_whitespace=True,
        extra="ignore",
    )

    # Core demographic attributes with boundary constraints
    age: Optional[int] = Field(
        default=None,
        ge=0,
        le=120,
        description="Age of the citizen in years (must be between 0 and 120)",
        examples=[32],
    )
    gender: Optional[Gender] = Field(
        default=None,
        description="Gender identity of the citizen",
    )
    social_category: Optional[SocialCategory] = Field(
        default=None,
        description="Social category (general, obc, sc, st, ews)",
    )
    marital_status: Optional[MaritalStatus] = Field(
        default=None,
        description="Marital status",
    )

    # Socio-economic & occupational attributes
    occupation: Optional[Occupation] = Field(
        default=None,
        description="Primary occupation",
    )
    farmer_status: Optional[FarmerStatus] = Field(
        default=None,
        description="Farmer classification based on landholding",
    )
    education: Optional[Education] = Field(
        default=None,
        description="Highest completed education level",
    )
    annual_income: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Annual household income in INR (must be >= 0)",
        examples=[120000.0],
    )

    # Location attributes
    state: Optional[str] = Field(
        default=None,
        max_length=100,
        description="State or Union Territory of residence",
        examples=["Maharashtra"],
    )
    district: Optional[str] = Field(
        default=None,
        max_length=100,
        description="District of residence",
        examples=["Pune"],
    )

    # Disability attributes
    is_disabled: Optional[bool] = Field(
        default=None,
        description="Whether the citizen has a certified disability",
    )
    disability_type: Optional[str] = Field(
        default=None,
        max_length=150,
        description="Type of disability if applicable (e.g., visual, locomotor, hearing)",
    )
    disability_percentage: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Disability percentage (0.0 to 100.0%)",
    )

    @field_validator("disability_type", mode="after")
    @classmethod
    def sanitize_disability_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            return None
        return v

    @model_validator(mode="after")
    def validate_disability_consistency(self) -> UserProfile:
        """Ensure consistency between disability fields and is_disabled flag."""
        if (self.disability_type or self.disability_percentage) and not self.is_disabled:
            object.__setattr__(self, "is_disabled", True)
        return self


# ============================================================================
# 3. Scheme Eligibility Rules Model
# ============================================================================

def _normalize_criterion(val: Any) -> Optional[Set[str]]:
    """Helper to convert None, 'any', lists, or scalar enums/strings into a normalized match set."""
    if val is None:
        return None
    if isinstance(val, str):
        cleaned = val.strip().lower()
        if cleaned in ("", "any", "all", "*"):
            return None
        return {cleaned}
    if isinstance(val, enum.Enum):
        if val.value.lower() in ("any", "all"):
            return None
        return {val.value.lower()}
    if isinstance(val, (list, set, tuple)):
        result = set()
        for item in val:
            normalized = item.value.lower() if isinstance(item, enum.Enum) else str(item).strip().lower()
            if normalized in ("any", "all", "*"):
                return None  # Any wildcard matches everything
            if normalized:
                result.add(normalized)
        return result if result else None
    return {str(val).strip().lower()}


class SchemeEligibilityRules(BaseModel):
    """
    Pydantic v2 model defining scheme eligibility criteria.
    Accepts string, list of strings, enum, list of enums, or nulls/'any' for unconstrained criteria.
    """
    model_config = ConfigDict(
        use_enum_values=True,
        validate_assignment=True,
        str_strip_whitespace=True,
        extra="ignore",
    )

    # Age criteria (in years)
    min_age: Optional[int] = Field(
        default=None,
        ge=0,
        le=120,
        description="Minimum age required (inclusive). None means no lower bound.",
    )
    max_age: Optional[int] = Field(
        default=None,
        ge=0,
        le=120,
        description="Maximum age allowed (inclusive). None means no upper bound.",
    )

    # Financial criteria
    max_annual_income: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Maximum annual income threshold in INR. None means no income ceiling.",
    )

    # Demographic & Occupational criteria (flexible: list[str] | str | enum | None)
    occupation: Optional[Union[List[str], str, Occupation, List[Occupation]]] = Field(
        default=None,
        description="Eligible occupation(s). None or 'any' matches all occupations.",
    )
    farmer_status: Optional[Union[List[str], str, FarmerStatus, List[FarmerStatus]]] = Field(
        default=None,
        description="Eligible farmer landholding status(es). None or 'any' matches all.",
    )
    social_category: Optional[Union[List[str], str, SocialCategory, List[SocialCategory]]] = Field(
        default=None,
        description="Eligible social category/categories. None or 'any' matches all.",
    )
    gender: Optional[Union[List[str], str, Gender, List[Gender]]] = Field(
        default=None,
        description="Target gender(s). None or 'any' matches all genders.",
    )
    state: Optional[Union[List[str], str]] = Field(
        default=None,
        description="Applicable state(s) / UTs. None or 'any' indicates nationwide (Central) scheme.",
    )
    education: Optional[Union[List[str], str, Education, List[Education]]] = Field(
        default=None,
        description="Eligible education level(s). None or 'any' indicates no restriction.",
    )
    marital_status: Optional[Union[List[str], str, MaritalStatus, List[MaritalStatus]]] = Field(
        default=None,
        description="Eligible marital status(es). None or 'any' indicates no restriction.",
    )

    # Disability requirement
    disability_required: Optional[bool] = Field(
        default=None,
        description="None means unconstrained. True requires disability. False requires non-disabled.",
    )
    min_disability_percentage: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Minimum certified disability percentage required if disability_required is True.",
    )

    @model_validator(mode="after")
    def validate_age_range(self) -> SchemeEligibilityRules:
        """Ensure min_age does not exceed max_age."""
        if self.min_age is not None and self.max_age is not None:
            if self.min_age > self.max_age:
                raise ValueError(f"min_age ({self.min_age}) cannot be greater than max_age ({self.max_age}).")
        return self

    def is_eligible(self, profile: UserProfile) -> tuple[bool, list[str]]:
        """
        Evaluates a UserProfile against this scheme's eligibility rules.
        Returns a tuple: (is_eligible: bool, failure_reasons: list[str]).
        """
        reasons: list[str] = []

        # 1. Age check
        if profile.age is not None:
            if self.min_age is not None and profile.age < self.min_age:
                reasons.append(f"Age {profile.age} is below minimum requirement of {self.min_age}")
            if self.max_age is not None and profile.age > self.max_age:
                reasons.append(f"Age {profile.age} exceeds maximum limit of {self.max_age}")

        # 2. Income check
        if self.max_annual_income is not None and profile.annual_income is not None:
            if profile.annual_income > self.max_annual_income:
                reasons.append(
                    f"Annual income INR {profile.annual_income:,.0f} exceeds maximum ceiling of INR {self.max_annual_income:,.0f}"
                )

        # 3. Gender check
        allowed_genders = _normalize_criterion(self.gender)
        if allowed_genders and profile.gender is not None:
            user_gender = profile.gender.value.lower() if isinstance(profile.gender, enum.Enum) else str(profile.gender).lower()
            if user_gender not in allowed_genders and user_gender != "any":
                reasons.append(f"Gender '{user_gender}' is not in allowed list: {sorted(list(allowed_genders))}")

        # 4. Social Category check
        allowed_categories = _normalize_criterion(self.social_category)
        if allowed_categories and profile.social_category is not None:
            user_cat = profile.social_category.value.lower() if isinstance(profile.social_category, enum.Enum) else str(profile.social_category).lower()
            if user_cat not in allowed_categories and user_cat != "any":
                reasons.append(f"Category '{user_cat}' is not in allowed categories: {sorted(list(allowed_categories))}")

        # 5. Occupation check
        allowed_occupations = _normalize_criterion(self.occupation)
        if allowed_occupations and profile.occupation is not None:
            user_occ = profile.occupation.value.lower() if isinstance(profile.occupation, enum.Enum) else str(profile.occupation).lower()
            if user_occ not in allowed_occupations and user_occ != "any":
                reasons.append(f"Occupation '{user_occ}' is not in eligible occupations: {sorted(list(allowed_occupations))}")

        # 6. Farmer Status check
        allowed_farmer_statuses = _normalize_criterion(self.farmer_status)
        if allowed_farmer_statuses and profile.farmer_status is not None:
            user_farmer = profile.farmer_status.value.lower() if isinstance(profile.farmer_status, enum.Enum) else str(profile.farmer_status).lower()
            if user_farmer not in allowed_farmer_statuses and user_farmer != "any":
                reasons.append(f"Farmer status '{user_farmer}' is not in allowed list: {sorted(list(allowed_farmer_statuses))}")

        # 7. State check
        allowed_states = _normalize_criterion(self.state)
        if allowed_states and profile.state is not None:
            user_state = profile.state.strip().lower()
            if user_state not in allowed_states and user_state != "all-india" and user_state != "central":
                reasons.append(f"State '{profile.state}' is not eligible for this state-specific scheme ({sorted(list(allowed_states))})")

        # 8. Education check
        allowed_education = _normalize_criterion(self.education)
        if allowed_education and profile.education is not None:
            user_edu = profile.education.value.lower() if isinstance(profile.education, enum.Enum) else str(profile.education).lower()
            if user_edu not in allowed_education and user_edu != "any":
                reasons.append(f"Education '{user_edu}' does not match required qualification: {sorted(list(allowed_education))}")

        # 9. Marital Status check
        allowed_marital = _normalize_criterion(self.marital_status)
        if allowed_marital and profile.marital_status is not None:
            user_mar = profile.marital_status.value.lower() if isinstance(profile.marital_status, enum.Enum) else str(profile.marital_status).lower()
            if user_mar not in allowed_marital and user_mar != "any":
                reasons.append(f"Marital status '{user_mar}' is not in allowed statuses: {sorted(list(allowed_marital))}")

        # 10. Disability requirement check
        if self.disability_required is not None:
            if self.disability_required and not profile.is_disabled:
                reasons.append("Scheme requires certified disability status")
            elif not self.disability_required and profile.is_disabled:
                reasons.append("Scheme is reserved for non-disabled applicants")

        if self.min_disability_percentage is not None and profile.is_disabled:
            if profile.disability_percentage is not None and profile.disability_percentage < self.min_disability_percentage:
                reasons.append(
                    f"Disability percentage ({profile.disability_percentage}%) is below minimum required ({self.min_disability_percentage}%)"
                )

        return (len(reasons) == 0, reasons)


# ============================================================================
# 4. Scheme Record Model (for External API Payload Parsing)
# ============================================================================

class SchemeRecord(BaseModel):
    """
    Validates and parses incoming scheme JSON payloads from external government
    and portal API services (e.g. data.gov.in, myScheme, State Portals).
    Supports nested or flat eligibility rule definitions seamlessly.
    """
    model_config = ConfigDict(
        use_enum_values=True,
        validate_assignment=True,
        str_strip_whitespace=True,
        populate_by_name=True,
        extra="ignore",
    )

    scheme_code: str = Field(
        min_length=1,
        max_length=100,
        description="Unique scheme identifier code",
        examples=["PM-KISAN-2024"],
    )
    name: str = Field(
        min_length=1,
        max_length=500,
        description="Official title of the scheme",
        examples=["Pradhan Mantri Kisan Samman Nidhi"],
    )
    short_description: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Brief scheme summary",
    )
    full_description: Optional[str] = Field(
        default=None,
        description="Complete details and background of the welfare scheme",
    )
    benefits: Optional[str] = Field(
        default=None,
        description="Summary of financial or non-financial benefits provided",
    )
    category: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Scheme domain / category (e.g. agriculture, education, healthcare)",
    )
    ministry: Optional[str] = Field(
        default=None,
        max_length=300,
        description="Parent Ministry or Department",
    )
    state: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Target State/UT or None for Central/All-India schemes",
    )
    scheme_type: str = Field(
        default="central",
        description="Type of scheme: 'central' or 'state'",
    )
    official_url: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Official portal or application URL",
    )
    required_documents: Optional[Union[List[str], str]] = Field(
        default=None,
        description="List of mandatory documents (e.g., Aadhaar, Land Record, Income Certificate)",
    )
    eligibility_rules: SchemeEligibilityRules = Field(
        default_factory=SchemeEligibilityRules,
        description="Structured eligibility criteria evaluated by the rule engine",
    )
    is_active: bool = Field(
        default=True,
        description="Whether the scheme is currently open and accepting applications",
    )

    @model_validator(mode="before")
    @classmethod
    def extract_and_normalize_payload(cls, data: Any) -> Any:
        """
        Pre-processes external payload:
        1. Handles aliases (scheme_name -> name, code -> scheme_code, description -> short_description).
        2. Merges top-level flat eligibility fields into eligibility_rules if not already nested.
        """
        if not isinstance(data, dict):
            return data

        payload = data.copy()

        # Handle common external API aliases
        if "scheme_name" in payload and "name" not in payload:
            payload["name"] = payload["scheme_name"]
        if "code" in payload and "scheme_code" not in payload:
            payload["scheme_code"] = payload["code"]
        if "description" in payload and "short_description" not in payload:
            payload["short_description"] = payload["description"]

        # Extract eligibility rules if nested under 'eligibility_rules', 'eligibility', or 'rules'
        raw_rules = payload.get("eligibility_rules") or payload.get("eligibility") or payload.get("rules") or {}
        if isinstance(raw_rules, SchemeEligibilityRules):
            rules_dict = raw_rules.model_dump()
        elif isinstance(raw_rules, dict):
            rules_dict = raw_rules.copy()
        elif hasattr(raw_rules, "model_dump"):
            rules_dict = raw_rules.model_dump()
        else:
            rules_dict = {}

        # Merge flat top-level eligibility fields into rules_dict if present
        rule_keys = [
            "min_age",
            "max_age",
            "max_annual_income",
            "occupation",
            "farmer_status",
            "social_category",
            "gender",
            "education",
            "marital_status",
            "disability_required",
            "min_disability_percentage",
        ]
        for key in rule_keys:
            if key in payload and key not in rules_dict:
                rules_dict[key] = payload[key]

        # Propagate state to eligibility rules if not explicitly overridden
        if "state" in payload and "state" not in rules_dict:
            rules_dict["state"] = payload["state"]

        payload["eligibility_rules"] = rules_dict
        return payload


# ============================================================================
# Self-test execution block
# ============================================================================
if __name__ == "__main__":
    print("--- Testing Standalone Schemas ---")

    # 1. Test UserProfile Boundary Validations
    try:
        UserProfile(age=-5)
        raise AssertionError("Should have failed on negative age")
    except Exception:
        print("[PASS] Age < 0 rejected")

    try:
        UserProfile(age=125)
        raise AssertionError("Should have failed on age > 120")
    except Exception:
        print("[PASS] Age > 120 rejected")

    try:
        UserProfile(annual_income=-100.0)
        raise AssertionError("Should have failed on negative income")
    except Exception:
        print("[PASS] Income < 0 rejected")

    valid_user = UserProfile(
        age=34,
        gender=Gender.FEMALE,
        social_category=SocialCategory.OBC,
        occupation=Occupation.FARMER,
        farmer_status=FarmerStatus.MARGINAL_FARMER,
        education=Education.SECONDARY,
        annual_income=65000.0,
        state="Maharashtra",
        district="Satara",
        is_disabled=True,
        disability_type="Locomotor",
        disability_percentage=45.0,
    )
    print(f"[PASS] Created UserProfile: {valid_user.gender}, Income=INR {valid_user.annual_income}")

    # 2. Test SchemeEligibilityRules with list & scalar constraints
    rules = SchemeEligibilityRules(
        min_age=18,
        max_age=60,
        max_annual_income=100000.0,
        occupation=["farmer", "daily_wage_laborer"],
        farmer_status=["marginal_farmer", "small_farmer"],
        state="Maharashtra",
        gender="any",
        disability_required=None,
    )
    is_eligible, reasons = rules.is_eligible(valid_user)
    assert is_eligible is True, f"Expected eligible, got: {reasons}"
    print(f"[PASS] Evaluated Eligibility: {is_eligible} (Reasons: {reasons})")

    # 3. Test SchemeRecord parsing from External API JSON payload (flat/nested format)
    external_api_json = {
        "scheme_code": "MHA-AGRI-2024",
        "name": "Maharashtra Shetkari Sanman Yojana",
        "short_description": "Financial support for marginal and small farmers in Maharashtra",
        "category": "agriculture",
        "state": "Maharashtra",
        "min_age": 18,
        "max_age": 65,
        "max_annual_income": 120000.0,
        "occupation": ["farmer"],
        "farmer_status": ["marginal_farmer", "small_farmer"],
        "disability_required": None,
    }

    scheme_record = SchemeRecord.model_validate(external_api_json)
    print(f"[PASS] Parsed SchemeRecord: {scheme_record.scheme_code} - {scheme_record.name}")
    print(f"       Nested Rules: Min Age={scheme_record.eligibility_rules.min_age}, Occupations={scheme_record.eligibility_rules.occupation}")

    assert scheme_record.eligibility_rules.min_age == 18
    assert scheme_record.eligibility_rules.state == "Maharashtra"
    assert scheme_record.eligibility_rules.is_eligible(valid_user)[0] is True

    print("\nAll unit validations and tests passed successfully!")
