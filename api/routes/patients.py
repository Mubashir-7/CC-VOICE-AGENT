"""
routes/patients.py — All CRUD endpoints for /patients.

GET    /patients           — list with optional filters
GET    /patients/{id}      — single patient by UUID
POST   /patients           — create new patient (201)
PUT    /patients/{id}      — partial update (200)
DELETE /patients/{id}      — soft delete (200)
"""

from datetime import datetime, timezone


def utcnow() -> datetime:
    """Timezone-aware UTC now (replaces deprecated datetime.utcnow())."""
    return datetime.now(timezone.utc)
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from api.db import get_session
from api.models import Patient
from api.schemas import APIResponse, PatientCreate, PatientResponse, PatientUpdate

router = APIRouter()


# ── Helper: build consistent 200/404 error ───────────────────────────────────
def _not_found() -> HTTPException:
    return HTTPException(status_code=404, detail="Patient not found")


def _patient_to_response(patient: Patient) -> PatientResponse:
    return PatientResponse.model_validate(patient)


# ── POST /patients ────────────────────────────────────────────────────────────
@router.post("", status_code=201, response_model=APIResponse[PatientResponse])
def create_patient(
    payload: PatientCreate,
    session: Session = Depends(get_session),
):
    """
    Create a new patient record.
    Returns 201 on success, 422 on validation failure.
    Called by the Vapi voice agent's create_patient tool AFTER caller confirmation.
    """
    patient = Patient(**payload.model_dump())
    session.add(patient)
    session.commit()
    session.refresh(patient)
    return APIResponse(data=_patient_to_response(patient))


# ── GET /patients ─────────────────────────────────────────────────────────────
@router.get("", response_model=APIResponse[List[PatientResponse]])
def list_patients(
    last_name: Optional[str] = Query(default=None, description="Filter by last name (case-insensitive)"),
    date_of_birth: Optional[str] = Query(default=None, description="Filter by DOB (YYYY-MM-DD)"),
    phone_number: Optional[str] = Query(default=None, description="Filter by phone number (10 digits)"),
    session: Session = Depends(get_session),
):
    """
    List all active (non-deleted) patients.
    Supports optional query filters: last_name, date_of_birth, phone_number.
    Used by the Vapi voice agent's lookup_patient_by_phone tool.
    """
    statement = select(Patient).where(Patient.deleted_at == None)  # noqa: E711

    if last_name:
        statement = statement.where(
            Patient.last_name.ilike(f"%{last_name.strip()}%")
        )

    if date_of_birth:
        statement = statement.where(Patient.date_of_birth == date_of_birth)

    if phone_number:
        # Normalize: strip all non-digits, remove leading 1
        import re
        digits = re.sub(r"\D", "", phone_number)
        if len(digits) == 11 and digits.startswith("1"):
            digits = digits[1:]
        statement = statement.where(Patient.phone_number == digits)

    patients = session.exec(statement).all()
    return APIResponse(data=[_patient_to_response(p) for p in patients])


# ── GET /patients/{patient_id} ────────────────────────────────────────────────
@router.get("/{patient_id}", response_model=APIResponse[PatientResponse])
def get_patient(
    patient_id: str,
    session: Session = Depends(get_session),
):
    """Retrieve a single patient by UUID. Returns 404 if not found or soft-deleted."""
    patient = session.get(Patient, patient_id)
    if not patient or patient.deleted_at is not None:
        raise _not_found()
    return APIResponse(data=_patient_to_response(patient))


# ── PUT /patients/{patient_id} ────────────────────────────────────────────────
@router.put("/{patient_id}", response_model=APIResponse[PatientResponse])
def update_patient(
    patient_id: str,
    payload: PatientUpdate,
    session: Session = Depends(get_session),
):
    """
    Partial update — only fields included in the request body are updated.
    Returns 404 if not found, 422 on validation failure.
    """
    patient = session.get(Patient, patient_id)
    if not patient or patient.deleted_at is not None:
        raise _not_found()

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(patient, field, value)

    patient.updated_at = utcnow()
    session.add(patient)
    session.commit()
    session.refresh(patient)
    return APIResponse(data=_patient_to_response(patient))


# ── DELETE /patients/{patient_id} ─────────────────────────────────────────────
@router.delete("/{patient_id}", response_model=APIResponse[None])
def delete_patient(
    patient_id: str,
    session: Session = Depends(get_session),
):
    """
    Soft-delete a patient record by setting deleted_at timestamp.
    The record is preserved in the database but excluded from all GET queries.
    Returns 404 if not found or already deleted.
    """
    patient = session.get(Patient, patient_id)
    if not patient or patient.deleted_at is not None:
        raise _not_found()

    patient.deleted_at = utcnow()
    patient.updated_at = utcnow()
    session.add(patient)
    session.commit()
    return APIResponse(data=None)
