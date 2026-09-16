"""
schemas.py — Pydantic request/response models with full server-side validation.

The voice agent is NOT the only validation layer.
All business rules are enforced here too.
"""

import re
from datetime import date, datetime
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, EmailStr, field_validator, model_validator

# ── US state abbreviations ────────────────────────────────────────────────────
US_STATES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
    "DC", "PR", "VI", "GU", "AS", "MP",
}

SEX_VALUES = {"male", "female", "other", "decline_to_answer"}

PHONE_REGEX = re.compile(r"^\+?1?[\s\-.]?\(?\d{3}\)?[\s\-.]?\d{3}[\s\-.]?\d{4}$")
ZIP_REGEX = re.compile(r"^\d{5}(-\d{4})?$")
NAME_REGEX = re.compile(r"^[A-Za-z\-\'\s]{1,50}$")


def normalize_phone(phone: str) -> str:
    """Strip everything except digits, remove leading country code 1."""
    digits = re.sub(r"\D", "", phone)
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    return digits


# ── Generic API response envelope ────────────────────────────────────────────
T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """
    Consistent JSON envelope for all API responses.
    Shape: { "data": <T | null>, "error": <string | null> }
    """

    data: Optional[T] = None
    error: Optional[str] = None


# ── Patient schemas ───────────────────────────────────────────────────────────

class PatientCreate(BaseModel):
    """Payload for POST /patients — all required fields enforced here."""

    # Required
    first_name: str
    last_name: str
    date_of_birth: date
    sex: str
    phone_number: str
    address_line_1: str
    city: str
    state: str
    zip_code: str

    # Optional
    address_line_2: Optional[str] = None
    email: Optional[str] = None
    insurance_provider: Optional[str] = None
    insurance_member_id: Optional[str] = None
    preferred_language: Optional[str] = "English"
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None

    # ── Validators ────────────────────────────────────────────────────────────

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Name cannot be empty")
        if len(v) > 50:
            raise ValueError("Name must be 50 characters or fewer")
        if not NAME_REGEX.match(v):
            raise ValueError("Name must contain only letters, hyphens, or apostrophes")
        return v

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, v: date) -> date:
        today = date.today()
        if v > today:
            raise ValueError("date_of_birth must not be in the future")
        if (today - v).days > 150 * 365:
            raise ValueError("date_of_birth is implausibly far in the past")
        return v

    @field_validator("sex")
    @classmethod
    def validate_sex(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in SEX_VALUES:
            raise ValueError(
                f"sex must be one of: {', '.join(sorted(SEX_VALUES))}"
            )
        return v

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        normalized = normalize_phone(v)
        if len(normalized) != 10:
            raise ValueError(
                "phone_number must be a valid US 10-digit number"
            )
        return normalized  # Store as 10 digits, no formatting

    @field_validator("state")
    @classmethod
    def validate_state(cls, v: str) -> str:
        v = v.strip().upper()
        if v not in US_STATES:
            raise ValueError(
                "state must be a valid 2-letter US state abbreviation"
            )
        return v

    @field_validator("zip_code")
    @classmethod
    def validate_zip(cls, v: str) -> str:
        v = v.strip()
        if not ZIP_REGEX.match(v):
            raise ValueError(
                "zip_code must be a 5-digit or ZIP+4 format (e.g., 02101 or 02101-4567)"
            )
        return v

    @field_validator("emergency_contact_phone")
    @classmethod
    def validate_emergency_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        normalized = normalize_phone(v)
        if len(normalized) != 10:
            raise ValueError(
                "emergency_contact_phone must be a valid US 10-digit number"
            )
        return normalized

    @field_validator("address_line_1", "city")
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Field cannot be empty")
        return v


class PatientUpdate(BaseModel):
    """Payload for PUT /patients/:id — all fields optional (partial update)."""

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    sex: Optional[str] = None
    phone_number: Optional[str] = None
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    email: Optional[str] = None
    insurance_provider: Optional[str] = None
    insurance_member_id: Optional[str] = None
    preferred_language: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not v or not NAME_REGEX.match(v):
            raise ValueError("Name must contain only letters, hyphens, or apostrophes (max 50 chars)")
        return v

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, v: Optional[date]) -> Optional[date]:
        if v is None:
            return v
        if v > date.today():
            raise ValueError("date_of_birth must not be in the future")
        return v

    @field_validator("sex")
    @classmethod
    def validate_sex(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip().lower()
        if v not in SEX_VALUES:
            raise ValueError(f"sex must be one of: {', '.join(sorted(SEX_VALUES))}")
        return v

    @field_validator("phone_number", "emergency_contact_phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        normalized = normalize_phone(v)
        if len(normalized) != 10:
            raise ValueError("Must be a valid US 10-digit phone number")
        return normalized

    @field_validator("state")
    @classmethod
    def validate_state(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip().upper()
        if v not in US_STATES:
            raise ValueError("state must be a valid 2-letter US state abbreviation")
        return v

    @field_validator("zip_code")
    @classmethod
    def validate_zip(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not ZIP_REGEX.match(v):
            raise ValueError("zip_code must be a 5-digit or ZIP+4 format")
        return v


class PatientResponse(BaseModel):
    """Full patient object returned in API responses."""

    patient_id: str
    first_name: str
    last_name: str
    date_of_birth: date
    sex: str
    phone_number: str
    address_line_1: str
    address_line_2: Optional[str]
    city: str
    state: str
    zip_code: str
    email: Optional[str]
    insurance_provider: Optional[str]
    insurance_member_id: Optional[str]
    preferred_language: Optional[str]
    emergency_contact_name: Optional[str]
    emergency_contact_phone: Optional[str]
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]

    model_config = {"from_attributes": True}
