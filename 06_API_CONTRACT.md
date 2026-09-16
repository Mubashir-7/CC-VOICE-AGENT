# API Contract — Voice AI Patient Registration Agent

## Base URL
- **Local**: `http://localhost:8000`
- **Deployed**: `https://<your-app>.up.railway.app` (set after deploy)

## Response Envelope
ALL endpoints return this JSON structure:
```json
{
  "data": <object | array | null>,
  "error": <string | null>
}
```

---

## Endpoints

### POST /patients
Create a new patient record.

**Request Body:**
```json
{
  "first_name": "Jane",
  "last_name": "Smith",
  "date_of_birth": "1990-05-15",
  "sex": "female",
  "phone_number": "5551234567",
  "address_line_1": "123 Main St",
  "address_line_2": "Apt 4B",
  "city": "Boston",
  "state": "MA",
  "zip_code": "02101",
  "email": "jane.smith@example.com",
  "insurance_provider": "BlueCross",
  "insurance_member_id": "BC123456",
  "preferred_language": "English",
  "emergency_contact_name": "John Smith",
  "emergency_contact_phone": "5559876543"
}
```

**Required fields:** `first_name`, `last_name`, `date_of_birth`, `sex`, `phone_number`, `address_line_1`, `city`, `state`, `zip_code`

**Response 201:**
```json
{
  "data": {
    "patient_id": "550e8400-e29b-41d4-a716-446655440000",
    "first_name": "Jane",
    "last_name": "Smith",
    "date_of_birth": "1990-05-15",
    "sex": "female",
    "phone_number": "5551234567",
    "address_line_1": "123 Main St",
    "address_line_2": "Apt 4B",
    "city": "Boston",
    "state": "MA",
    "zip_code": "02101",
    "email": "jane.smith@example.com",
    "insurance_provider": "BlueCross",
    "insurance_member_id": "BC123456",
    "preferred_language": "English",
    "emergency_contact_name": "John Smith",
    "emergency_contact_phone": "5559876543",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z",
    "deleted_at": null
  },
  "error": null
}
```

**Response 422 (validation error):**
```json
{
  "data": null,
  "error": "date_of_birth must not be in the future"
}
```

---

### GET /patients
List all active (not soft-deleted) patients. Supports optional filters.

**Query Parameters:**
| Param | Type | Example |
|-------|------|---------|
| `last_name` | string | `?last_name=Smith` |
| `date_of_birth` | date (YYYY-MM-DD) | `?date_of_birth=1990-05-15` |
| `phone_number` | string | `?phone_number=5551234567` |

**Response 200:**
```json
{
  "data": [
    { ...patient object... },
    { ...patient object... }
  ],
  "error": null
}
```

---

### GET /patients/{patient_id}
Retrieve a single patient by UUID.

**Response 200:**
```json
{
  "data": { ...patient object... },
  "error": null
}
```

**Response 404:**
```json
{
  "data": null,
  "error": "Patient not found"
}
```

---

### PUT /patients/{patient_id}
Partial update. All fields optional — only provided fields are updated.

**Request Body (partial):**
```json
{
  "address_line_1": "456 Oak Avenue",
  "city": "Cambridge"
}
```

**Response 200:** Updated patient object in `data`.

**Response 404:** Patient not found.

**Response 422:** Validation error (e.g., invalid state code).

---

### DELETE /patients/{patient_id}
Soft delete — sets `deleted_at` timestamp. Record is excluded from all GET queries but preserved in the database.

**Response 200:**
```json
{
  "data": null,
  "error": null
}
```

**Response 404:**
```json
{
  "data": null,
  "error": "Patient not found"
}
```

---

## Validation Rules Reference

| Field | Rule | Error message |
|-------|------|---------------|
| `first_name` | 1–50 chars, letters/hyphens/apostrophes only | "first_name must be 1–50 alphabetic characters" |
| `last_name` | 1–50 chars, letters/hyphens/apostrophes only | "last_name must be 1–50 alphabetic characters" |
| `date_of_birth` | Valid date, not in future, not >150 years ago | "date_of_birth must not be in the future" |
| `sex` | One of: `male`, `female`, `other`, `decline_to_answer` | "sex must be one of: male, female, other, decline_to_answer" |
| `phone_number` | US 10-digit (allows formatting) | "phone_number must be a valid US 10-digit number" |
| `state` | Valid 2-letter US state code | "state must be a valid 2-letter US state abbreviation" |
| `zip_code` | `^\d{5}(-\d{4})?$` | "zip_code must be a 5-digit or ZIP+4 format" |
| `email` | Valid email format (when provided) | "email must be a valid email address" |

---

## HTTP Status Code Reference

| Code | Meaning | When Used |
|------|---------|-----------|
| 200 | OK | Successful GET, PUT, DELETE |
| 201 | Created | Successful POST /patients |
| 400 | Bad Request | Malformed JSON |
| 404 | Not Found | Patient ID doesn't exist |
| 422 | Unprocessable Entity | Validation failure |
| 500 | Internal Server Error | Unexpected DB or server error |

---

## Vapi Tool Call Mapping

| Vapi Tool | Maps to | Notes |
|-----------|---------|-------|
| `lookup_patient_by_phone` | `GET /patients?phone_number=X` | Returns list; if `data.length > 0`, patient exists |
| `create_patient` | `POST /patients` | Called ONLY after caller confirms read-back |

Vapi sends tool results as JSON back to the LLM. The system prompt instructs the LLM how to interpret the response.
