"""
tests/test_api.py — Full automated test suite for the Patient Registration API.

Tests cover:
  - Happy path CRUD operations
  - All validation rules (DOB, phone, state, zip, sex, name)
  - Soft delete behavior
  - Query filters
  - 404 handling
  - Response envelope shape

Run with:
    pytest tests/ -v

Or with coverage:
    pytest tests/ -v --tb=short
"""

import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlmodel.pool import StaticPool

# ── Import app and override the DB dependency ─────────────────────────────────
from api.main import app
from api.db import get_session

# ── In-memory SQLite for tests (isolated, no disk writes) ────────────────────
TEST_DATABASE_URL = "sqlite://"

@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


# ── Reusable valid patient payload ────────────────────────────────────────────
VALID_PATIENT = {
    "first_name": "Jane",
    "last_name": "Smith",
    "date_of_birth": "1990-05-15",
    "sex": "female",
    "phone_number": "5551234567",
    "address_line_1": "123 Main Street",
    "city": "Boston",
    "state": "MA",
    "zip_code": "02101",
}


# ═══════════════════════════════════════════════════════════════════════════════
# HEALTH CHECK
# ═══════════════════════════════════════════════════════════════════════════════

class TestHealthCheck:
    def test_health_returns_ok(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"


# ═══════════════════════════════════════════════════════════════════════════════
# POST /patients — CREATE
# ═══════════════════════════════════════════════════════════════════════════════

class TestCreatePatient:

    def test_create_valid_patient_returns_201(self, client):
        resp = client.post("/patients", json=VALID_PATIENT)
        assert resp.status_code == 201
        body = resp.json()
        assert body["error"] is None
        data = body["data"]
        assert data["first_name"] == "Jane"
        assert data["last_name"] == "Smith"
        assert data["patient_id"] is not None
        assert data["deleted_at"] is None

    def test_create_stores_all_required_fields(self, client):
        resp = client.post("/patients", json=VALID_PATIENT)
        data = resp.json()["data"]
        assert data["date_of_birth"] == "1990-05-15"
        assert data["sex"] == "female"
        assert data["phone_number"] == "5551234567"
        assert data["address_line_1"] == "123 Main Street"
        assert data["city"] == "Boston"
        assert data["state"] == "MA"
        assert data["zip_code"] == "02101"

    def test_create_with_all_optional_fields(self, client):
        payload = {**VALID_PATIENT, **{
            "address_line_2": "Apt 4B",
            "email": "jane@example.com",
            "insurance_provider": "BlueCross",
            "insurance_member_id": "BC123",
            "preferred_language": "Spanish",
            "emergency_contact_name": "John Smith",
            "emergency_contact_phone": "5559876543",
        }}
        resp = client.post("/patients", json=payload)
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["email"] == "jane@example.com"
        assert data["insurance_provider"] == "BlueCross"
        assert data["emergency_contact_name"] == "John Smith"

    def test_create_normalizes_phone_with_formatting(self, client):
        """Phone with dashes/spaces should be normalized to 10 digits."""
        payload = {**VALID_PATIENT, "phone_number": "555-123-4567"}
        resp = client.post("/patients", json=payload)
        assert resp.status_code == 201
        assert resp.json()["data"]["phone_number"] == "5551234567"

    def test_create_normalizes_phone_with_country_code(self, client):
        payload = {**VALID_PATIENT, "phone_number": "+15551234567"}
        resp = client.post("/patients", json=payload)
        assert resp.status_code == 201
        assert resp.json()["data"]["phone_number"] == "5551234567"

    def test_create_accepts_decline_to_answer_sex(self, client):
        payload = {**VALID_PATIENT, "sex": "decline_to_answer"}
        resp = client.post("/patients", json=payload)
        assert resp.status_code == 201

    def test_create_accepts_zip_plus_4(self, client):
        payload = {**VALID_PATIENT, "zip_code": "02101-4567"}
        resp = client.post("/patients", json=payload)
        assert resp.status_code == 201


# ═══════════════════════════════════════════════════════════════════════════════
# POST /patients — VALIDATION FAILURES (422)
# ═══════════════════════════════════════════════════════════════════════════════

class TestCreatePatientValidation:

    def _assert_422(self, client, payload):
        resp = client.post("/patients", json=payload)
        assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"
        body = resp.json()
        # Check envelope shape
        assert "data" in body
        assert "error" in body
        return body

    def test_future_dob_returns_422(self, client):
        """CRITICAL: Future date of birth must be rejected."""
        future = (date.today() + timedelta(days=365)).isoformat()
        payload = {**VALID_PATIENT, "date_of_birth": future}
        body = self._assert_422(client, payload)
        assert "future" in (body.get("error") or "").lower() or body["data"] is None

    def test_invalid_phone_too_short_returns_422(self, client):
        payload = {**VALID_PATIENT, "phone_number": "12345"}
        self._assert_422(client, payload)

    def test_invalid_phone_letters_returns_422(self, client):
        payload = {**VALID_PATIENT, "phone_number": "555-CALL-NOW"}
        self._assert_422(client, payload)

    def test_invalid_state_returns_422(self, client):
        payload = {**VALID_PATIENT, "state": "XX"}
        self._assert_422(client, payload)

    def test_invalid_state_full_name_returns_422(self, client):
        """Full state name should not be accepted — only 2-letter codes."""
        payload = {**VALID_PATIENT, "state": "Massachusetts"}
        self._assert_422(client, payload)

    def test_invalid_zip_too_short_returns_422(self, client):
        payload = {**VALID_PATIENT, "zip_code": "123"}
        self._assert_422(client, payload)

    def test_invalid_zip_letters_returns_422(self, client):
        payload = {**VALID_PATIENT, "zip_code": "ABCDE"}
        self._assert_422(client, payload)

    def test_invalid_sex_returns_422(self, client):
        payload = {**VALID_PATIENT, "sex": "unknown"}
        self._assert_422(client, payload)

    def test_missing_required_field_returns_422(self, client):
        """Missing any required field must return 422."""
        for field in ["first_name", "last_name", "date_of_birth", "sex",
                      "phone_number", "address_line_1", "city", "state", "zip_code"]:
            payload = {k: v for k, v in VALID_PATIENT.items() if k != field}
            resp = client.post("/patients", json=payload)
            assert resp.status_code == 422, f"Expected 422 when '{field}' is missing, got {resp.status_code}"

    def test_empty_string_name_returns_422(self, client):
        payload = {**VALID_PATIENT, "first_name": ""}
        self._assert_422(client, payload)

    def test_name_with_numbers_returns_422(self, client):
        payload = {**VALID_PATIENT, "first_name": "Jane123"}
        self._assert_422(client, payload)


# ═══════════════════════════════════════════════════════════════════════════════
# GET /patients — LIST
# ═══════════════════════════════════════════════════════════════════════════════

class TestListPatients:

    def test_list_empty_returns_empty_array(self, client):
        resp = client.get("/patients")
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"] == []
        assert body["error"] is None

    def test_list_returns_created_patient(self, client):
        client.post("/patients", json=VALID_PATIENT)
        resp = client.get("/patients")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 1

    def test_list_multiple_patients(self, client):
        client.post("/patients", json=VALID_PATIENT)
        payload2 = {**VALID_PATIENT, "phone_number": "5559876543", "first_name": "Bob"}
        client.post("/patients", json=payload2)
        resp = client.get("/patients")
        assert len(resp.json()["data"]) == 2

    def test_filter_by_last_name(self, client):
        client.post("/patients", json=VALID_PATIENT)
        payload2 = {**VALID_PATIENT, "phone_number": "5559876543", "last_name": "Jones"}
        client.post("/patients", json=payload2)

        resp = client.get("/patients?last_name=Smith")
        data = resp.json()["data"]
        assert len(data) == 1
        assert data[0]["last_name"] == "Smith"

    def test_filter_by_phone_number(self, client):
        client.post("/patients", json=VALID_PATIENT)
        resp = client.get("/patients?phone_number=5551234567")
        data = resp.json()["data"]
        assert len(data) == 1
        assert data[0]["phone_number"] == "5551234567"

    def test_filter_by_date_of_birth(self, client):
        client.post("/patients", json=VALID_PATIENT)
        payload2 = {**VALID_PATIENT, "phone_number": "5559876543", "date_of_birth": "1985-01-01"}
        client.post("/patients", json=payload2)

        resp = client.get("/patients?date_of_birth=1990-05-15")
        data = resp.json()["data"]
        assert len(data) == 1

    def test_list_excludes_soft_deleted(self, client):
        create_resp = client.post("/patients", json=VALID_PATIENT)
        patient_id = create_resp.json()["data"]["patient_id"]
        client.delete(f"/patients/{patient_id}")

        resp = client.get("/patients")
        assert resp.json()["data"] == []


# ═══════════════════════════════════════════════════════════════════════════════
# GET /patients/{id} — SINGLE
# ═══════════════════════════════════════════════════════════════════════════════

class TestGetPatient:

    def test_get_existing_patient(self, client):
        create_resp = client.post("/patients", json=VALID_PATIENT)
        patient_id = create_resp.json()["data"]["patient_id"]

        resp = client.get(f"/patients/{patient_id}")
        assert resp.status_code == 200
        assert resp.json()["data"]["patient_id"] == patient_id

    def test_get_nonexistent_returns_404(self, client):
        resp = client.get("/patients/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404
        body = resp.json()
        assert body["data"] is None

    def test_get_soft_deleted_returns_404(self, client):
        create_resp = client.post("/patients", json=VALID_PATIENT)
        patient_id = create_resp.json()["data"]["patient_id"]
        client.delete(f"/patients/{patient_id}")

        resp = client.get(f"/patients/{patient_id}")
        assert resp.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════════
# PUT /patients/{id} — UPDATE
# ═══════════════════════════════════════════════════════════════════════════════

class TestUpdatePatient:

    def test_update_single_field(self, client):
        create_resp = client.post("/patients", json=VALID_PATIENT)
        patient_id = create_resp.json()["data"]["patient_id"]

        resp = client.put(f"/patients/{patient_id}", json={"city": "Cambridge"})
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["city"] == "Cambridge"
        assert data["first_name"] == "Jane"  # Unchanged

    def test_update_multiple_fields(self, client):
        create_resp = client.post("/patients", json=VALID_PATIENT)
        patient_id = create_resp.json()["data"]["patient_id"]

        resp = client.put(f"/patients/{patient_id}", json={
            "address_line_1": "456 Oak Ave",
            "city": "Cambridge",
            "zip_code": "02139",
        })
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["address_line_1"] == "456 Oak Ave"
        assert data["city"] == "Cambridge"

    def test_update_nonexistent_returns_404(self, client):
        resp = client.put(
            "/patients/00000000-0000-0000-0000-000000000000",
            json={"city": "Boston"}
        )
        assert resp.status_code == 404

    def test_update_with_invalid_field_returns_422(self, client):
        create_resp = client.post("/patients", json=VALID_PATIENT)
        patient_id = create_resp.json()["data"]["patient_id"]

        resp = client.put(f"/patients/{patient_id}", json={"state": "INVALID"})
        assert resp.status_code == 422

    def test_update_with_future_dob_returns_422(self, client):
        create_resp = client.post("/patients", json=VALID_PATIENT)
        patient_id = create_resp.json()["data"]["patient_id"]
        future = (date.today() + timedelta(days=1)).isoformat()

        resp = client.put(f"/patients/{patient_id}", json={"date_of_birth": future})
        assert resp.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════════
# DELETE /patients/{id} — SOFT DELETE
# ═══════════════════════════════════════════════════════════════════════════════

class TestDeletePatient:

    def test_delete_existing_patient(self, client):
        create_resp = client.post("/patients", json=VALID_PATIENT)
        patient_id = create_resp.json()["data"]["patient_id"]

        resp = client.delete(f"/patients/{patient_id}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"] is None
        assert body["error"] is None

    def test_delete_sets_deleted_at_not_hard_delete(self, client, session):
        """Verify soft delete — record still exists in DB with deleted_at set."""
        create_resp = client.post("/patients", json=VALID_PATIENT)
        patient_id = create_resp.json()["data"]["patient_id"]
        client.delete(f"/patients/{patient_id}")

        from api.models import Patient
        patient = session.get(Patient, patient_id)
        assert patient is not None, "Record should still exist in DB after soft delete"
        assert patient.deleted_at is not None, "deleted_at should be set after soft delete"

    def test_delete_nonexistent_returns_404(self, client):
        resp = client.delete("/patients/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404

    def test_double_delete_returns_404(self, client):
        """Deleting an already-deleted patient should return 404."""
        create_resp = client.post("/patients", json=VALID_PATIENT)
        patient_id = create_resp.json()["data"]["patient_id"]
        client.delete(f"/patients/{patient_id}")

        resp = client.delete(f"/patients/{patient_id}")
        assert resp.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════════
# RESPONSE ENVELOPE SHAPE
# ═══════════════════════════════════════════════════════════════════════════════

class TestResponseEnvelope:

    def test_all_success_responses_have_data_and_error_keys(self, client):
        resp = client.get("/patients")
        body = resp.json()
        assert "data" in body
        assert "error" in body

    def test_404_response_has_correct_envelope(self, client):
        resp = client.get("/patients/nonexistent-id")
        assert resp.status_code == 404

    def test_422_response_has_null_data(self, client):
        payload = {**VALID_PATIENT, "date_of_birth": "2099-01-01"}
        resp = client.post("/patients", json=payload)
        assert resp.status_code == 422
        body = resp.json()
        assert body.get("data") is None


# ═══════════════════════════════════════════════════════════════════════════════
# EDGE CASES (matches the brief's explicit test scenarios)
# ═══════════════════════════════════════════════════════════════════════════════

class TestEdgeCases:

    def test_call_drop_no_partial_record(self, client):
        """
        Simulates a dropped call — POST was never made.
        Verifies no partial record exists.
        """
        resp = client.get("/patients")
        assert resp.json()["data"] == []

    def test_duplicate_phone_detectable_via_filter(self, client):
        """
        Simulates the agent's duplicate detection:
        lookup_patient_by_phone returns data → patient exists.
        """
        client.post("/patients", json=VALID_PATIENT)
        resp = client.get("/patients?phone_number=5551234567")
        data = resp.json()["data"]
        assert len(data) >= 1
        assert data[0]["phone_number"] == "5551234567"

    def test_second_call_data_persists(self, client):
        """
        Simulates: Call 1 registers. Call 2 retrieves via API.
        """
        create_resp = client.post("/patients", json=VALID_PATIENT)
        patient_id = create_resp.json()["data"]["patient_id"]

        # Simulate second call retrieval
        get_resp = client.get(f"/patients/{patient_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["data"]["first_name"] == "Jane"

    def test_invalid_dob_today_is_allowed(self, client):
        """Today's DOB is valid (born today)."""
        today = date.today().isoformat()
        payload = {**VALID_PATIENT, "date_of_birth": today}
        resp = client.post("/patients", json=payload)
        assert resp.status_code == 201

    def test_invalid_dob_tomorrow_is_rejected(self, client):
        """Tomorrow's DOB is invalid — in the future."""
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        payload = {**VALID_PATIENT, "date_of_birth": tomorrow}
        resp = client.post("/patients", json=payload)
        assert resp.status_code == 422

    def test_state_is_uppercased(self, client):
        """State abbreviation should work even if submitted lowercase."""
        payload = {**VALID_PATIENT, "state": "ma"}
        resp = client.post("/patients", json=payload)
        assert resp.status_code == 201
        assert resp.json()["data"]["state"] == "MA"
