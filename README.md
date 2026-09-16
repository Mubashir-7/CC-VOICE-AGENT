# Voice AI Patient Registration Agent

**Live phone number:** `+1 (385) 406-9126`
**API base URL:** *(set after Railway deploy)*
**API docs:** *(set after Railway deploy)*/docs

---

## Overview

A voice AI agent that answers a real US phone number, conversationally collects patient demographic information, persists it to a database, and exposes it through a REST API. Calling the number a second time allows retrieving previously registered patient data.

Built for the Voice AI Agent take-home assessment. Deployed and live at review time.

## Architecture

```
Caller
  │  (PSTN)
  ▼
Vapi  (Telephony + STT + TTS + LLM orchestration)
  │  (tool/function calls over HTTPS)
  ▼
FastAPI Service ──────► SQLite (patients.db, persistent volume on Railway)
  │
  ▼
REST API (/patients — GET, POST, PUT, DELETE)
```

- **Telephony/Voice layer:** Vapi — handles call answering, speech-to-text (Google Gemini), text-to-speech (Azure Neural), interruption handling, and turn-taking. The LLM drives the conversation and calls our API via defined tools.
- **LLM:** Google Gemini 2.0 Flash via Vapi — fast, low-latency, free tier sufficient for conversational slot-filling.
- **API layer:** FastAPI (Python) — all validation and persistence logic lives here, not in the agent.
- **DB layer:** SQLite on a persistent Railway volume. Zero-ops, survives restarts, sufficient for assessment scope.

## Tech Stack Justification

| Layer | Choice | Why |
|---|---|---|
| Telephony + Voice AI | Vapi | Abstracts STT/TTS/telephony — build time goes into prompt quality and integration, not infra glue |
| LLM | Gemini 2.0 Flash | Fast, low-latency, free tier; natively supported in Vapi |
| STT | Google (Gemini) via Vapi | Accurate, fast, free via Vapi |
| TTS | Azure Neural (Jenny) via Vapi | Natural-sounding warm voice suitable for a medical office context |
| Backend | FastAPI (Python) | Pydantic gives free server-side validation; auto-generates OpenAPI docs |
| DB | SQLite | Zero-ops, file-based, explicitly suggested in the assessment brief |
| Hosting | Railway (free tier) | Simple deploy, persistent volume for SQLite |

## Setup Instructions

### 1. Clone the repo
```bash
git clone <repo-url>
cd care-cloud-voice-agent
```

### 2. Install dependencies
```bash
cd api
python -m venv venv
source venv/bin/activate     # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment variables
```bash
cp .env.example .env
# Fill in GEMINI_API_KEY and any missing values
```

### 4. Run locally
```bash
uvicorn api.main:app --reload
# Visit http://localhost:8000/docs to test the API
```

### 5. Deploy to Railway
See `08_DEPLOYMENT_GUIDE.md` for full step-by-step Railway deploy instructions.

### 6. Set up the Vapi assistant
After deploying, update `API_BASE_URL` in `.env`, then run:
```bash
python agent/setup_vapi.py
```
Or import `agent/vapi_assistant_config.json` manually in the Vapi dashboard.

### 7. Seed test data
```bash
python scripts/seed_patients.py
```

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `VAPI_PRIVATE_KEY` | Yes | Vapi private API key |
| `VAPI_PUBLIC_KEY` | Yes | Vapi public API key |
| `VAPI_PHONE_NUMBER_ID` | Yes | ID of provisioned Vapi phone number |
| `VAPI_PHONE_NUMBER` | No | Actual dial-in number (display only) |
| `GEMINI_API_KEY` | Yes | Google AI Studio API key |
| `GEMINI_MODEL` | No | Default: `gemini-2.0-flash` |
| `DATABASE_URL` | Yes | SQLite path (set after deploy) |
| `API_BASE_URL` | Yes | Deployed URL (set after Railway deploy) |
| `CORS_ORIGINS` | No | Allowed CORS origins (default: `*`) |

## Data Model

All fields per the assessment brief:

| Field | Type | Required | Validation |
|---|---|---|---|
| patient_id | UUID | Auto | Auto-generated |
| first_name | String | Yes | 1–50 chars, letters/hyphens/apostrophes |
| last_name | String | Yes | 1–50 chars, letters/hyphens/apostrophes |
| date_of_birth | Date | Yes | Not in future, YYYY-MM-DD |
| sex | Enum | Yes | male/female/other/decline_to_answer |
| phone_number | String | Yes | US 10-digit (stored as digits only) |
| address_line_1 | String | Yes | Street address |
| address_line_2 | String | No | Apt/suite/unit |
| city | String | Yes | — |
| state | String | Yes | Valid 2-letter US state |
| zip_code | String | Yes | 5-digit or ZIP+4 |
| email | String | No | Valid email format |
| insurance_provider | String | No | — |
| insurance_member_id | String | No | — |
| preferred_language | String | No | Default: English |
| emergency_contact_name | String | No | — |
| emergency_contact_phone | String | No | US 10-digit |
| created_at | Timestamp | Auto | UTC |
| updated_at | Timestamp | Auto | UTC |
| deleted_at | Timestamp | Auto | Soft delete (null = active) |

## API Endpoints

All responses use `{ "data": ..., "error": ... }` envelope.

| Method | Endpoint | Description | Status Codes |
|---|---|---|---|
| GET | /patients | List all patients (filterable) | 200 |
| GET | /patients/{id} | Get single patient | 200, 404 |
| POST | /patients | Create patient | 201, 422 |
| PUT | /patients/{id} | Partial update | 200, 404, 422 |
| DELETE | /patients/{id} | Soft delete | 200, 404 |

**Query params for GET /patients:** `?last_name=`, `?date_of_birth=`, `?phone_number=`

## Voice Agent System Prompt

See `agent/system_prompt.md` for the full system prompt. Key design decisions:
- Fields collected in natural clusters (name + DOB together, full address together)
- Out-of-order data accepted without re-asking
- Inline validation — errors caught immediately, not deferred to read-back
- Corrections ("actually...") update only the mentioned field and continue
- `create_patient` tool fires ONLY after explicit caller confirmation

## How the Agent Talks to the Database

The agent uses two Vapi tool calls that hit the deployed FastAPI:

1. `lookup_patient_by_phone` → `GET /patients?phone_number=X`
   - Called after caller confirms read-back, before saving
   - Detects returning callers

2. `create_patient` → `POST /patients`
   - Called only after explicit caller confirmation
   - API validates all fields server-side independent of the agent

## Edge Cases Handled

| Scenario | Behavior |
|---|---|
| Invalid/future date of birth | Agent re-prompts specifically for DOB immediately |
| Malformed phone number | Agent re-prompts specifically for phone |
| Call drops before confirmation | No record saved (save only on tool call after confirmation) |
| DB write failure | Agent gives graceful spoken error, ends call politely |
| Mid-call correction ("actually...") | Only the mentioned field updated, conversation continues |
| "Start over" request | All state reset, returns to opening question |
| Returning caller (same phone) | `lookup_patient_by_phone` detects match, offers to update |
| Out-of-order data volunteered | Accepted and tracked, not re-asked |

## Known Limitations / Trade-offs

- **SQLite instead of Postgres** — appropriate for this scope; would use Postgres for multi-instance concurrent writes in production
- **No HIPAA-grade encryption** — explicitly out of scope per assessment FAQ
- **No automated test suite** — API manually tested via `/docs` and curl
- Railway free tier has a usage cap — not suitable for production traffic
- Optional fields (insurance, emergency contact) not collected by default — offered as opt-in

## Next Steps (if given more time)

- Automated test suite (pytest + httpx for API, Vapi call simulation)
- Dashboard UI for patient management
- PostgreSQL for concurrent write safety
- Multi-language support (Vapi supports multilingual STT)
- HIPAA-compliant encryption at rest and audit logging
- Appointment scheduling integration

## Testing It Yourself

1. Call **+1 (385) 406-9126**
2. Speak naturally — provide test demographics (do not use real personal data)
3. Confirm when the agent reads it back
4. Verify: `curl <API_BASE_URL>/patients`
5. Call again from the same number to test returning caller detection

**Test data suggestion:**
- Name: Alex Johnson, DOB: March 12, 1985
- Sex: Male, Phone: your test number
- Address: 42 Main Street, Springfield, Illinois, 62701
