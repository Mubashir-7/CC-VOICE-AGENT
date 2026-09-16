"""
models.py — SQLModel ORM table definitions.

Defines the Patient table with all required and optional fields
from the assessment brief's data model.
"""

import uuid
from datetime import date, datetime, timezone
from typing import Optional


def _utcnow() -> datetime:
    """Timezone-aware UTC now for use as a SQLModel field default_factory."""
    return datetime.now(timezone.utc)

from sqlmodel import Field, SQLModel


class Patient(SQLModel, table=True):
    """
    Persistent patient record.

    Required fields: first_name, last_name, date_of_birth, sex,
                     phone_number, address_line_1, city, state, zip_code
    Optional fields: address_line_2, email, insurance_provider,
                     insurance_member_id, preferred_language,
                     emergency_contact_name, emergency_contact_phone
    Auto fields:     patient_id, created_at, updated_at, deleted_at
    """

    # Primary key — auto-generated UUID
    patient_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True,
        description="Auto-generated unique patient identifier (UUID)",
    )

    # ── Required fields ─────────────────────────────────────────────────────
    first_name: str = Field(
        max_length=50,
        description="Patient's legal first name",
    )
    last_name: str = Field(
        max_length=50,
        description="Patient's legal last name",
    )
    date_of_birth: date = Field(
        description="Date of birth — must not be in the future (YYYY-MM-DD)",
    )
    sex: str = Field(
        description="One of: male, female, other, decline_to_answer",
    )
    phone_number: str = Field(
        max_length=15,
        description="Valid US 10-digit phone number (digits only)",
    )
    address_line_1: str = Field(
        max_length=200,
        description="Street address",
    )
    city: str = Field(
        max_length=100,
        description="City name",
    )
    state: str = Field(
        max_length=2,
        description="2-letter US state abbreviation (e.g., CA, TX, NY)",
    )
    zip_code: str = Field(
        max_length=10,
        description="5-digit or ZIP+4 US zip code",
    )

    # ── Optional fields ──────────────────────────────────────────────────────
    address_line_2: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Apartment, suite, or unit number",
    )
    email: Optional[str] = Field(
        default=None,
        max_length=254,
        description="Valid email address",
    )
    insurance_provider: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Name of insurance company",
    )
    insurance_member_id: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Insurance member or subscriber ID",
    )
    preferred_language: Optional[str] = Field(
        default="English",
        max_length=50,
        description="Patient's preferred language",
    )
    emergency_contact_name: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Emergency contact's full name",
    )
    emergency_contact_phone: Optional[str] = Field(
        default=None,
        max_length=15,
        description="Emergency contact's US 10-digit phone number",
    )

    # ── Auto-managed timestamps ──────────────────────────────────────────────
    created_at: datetime = Field(
        default_factory=_utcnow,
        description="UTC timestamp when the record was created",
    )
    updated_at: datetime = Field(
        default_factory=_utcnow,
        description="UTC timestamp of the last update",
    )
    deleted_at: Optional[datetime] = Field(
        default=None,
        description="Soft-delete timestamp. Non-null means the record is deleted.",
    )
