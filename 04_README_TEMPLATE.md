# Voice AI Patient Registration Agent

**Live phone number:** `+1-XXX-XXX-XXXX`
**API base URL:** `https://your-app.up.railway.app`
**API docs:** `https://your-app.up.railway.app/docs`

## Overview
A voice AI agent that answers a real phone call, conversationally collects
US patient demographic information, persists it to a database, and exposes
it through a REST API. Calling the number a second time retrieves/recognizes
the previously registered patient.

## Architecture
```
Caller
  │  (PSTN)
  ▼
Vapi (Telephony + STT/TTS + LLM orchestration)
  │  (tool/function calls over HTTPS)
  ▼
FastAPI service  ──────►  SQLite (patients.db, persistent volume)
  │
  ▼
REST API (GET/POST/PUT/DELETE /patients)
```
- **Telephony/Voice layer:** Vapi — handles call answering, STT, TTS,
  interruption handling, and turn-taking. The LLM (system prompt below)
  drives the conversation and calls out to our API via defined tools.
- **API layer:** FastAPI, single service, responsible for all validation and
  persistence. The voice agent has no direct DB access — it only calls this
  API, so validation logic lives in exactly one place.
- **DB layer:** SQLite file on a persistent volume. Chosen over
  Postgres/Mongo deliberately — see Tech Stack Justification below.

## Tech stack justification
| Layer | Choice | Why |
|---|---|---|
| Telephony + Voice AI | Vapi | Abstracts STT/TTS/telephony so build time goes into prompt quality and integration, not infra glue |
| LLM | GPT-4o-mini | Fast, cheap, sufficient for structured slot-filling dialogue |
| Backend | FastAPI (Python) | Pydantic gives free server-side validation; auto docs |
| DB | SQLite | Zero-ops persistence appropriate for the scope and time box; explicitly suggested in the assessment brief |
| Hosting | Railway (free tier) | Simple deploy, persistent volume for SQLite |

## Setup instructions
```bash
git clone <repo>
cd <repo>/api
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in values below
uvicorn main:app --reload
```
Voice agent config is in `/agent` — import `agent/vapi_assistant_config.json`
into your Vapi account, or run `agent/setup.py` if a provisioning script is
included, and point its tool URLs at your deployed API base URL.

## Environment variables
```
VAPI_API_KEY=
VAPI_PHONE_NUMBER_ID=
OPENAI_API_KEY=
DATABASE_URL=sqlite:///./patients.db
API_BASE_URL=
```

## Data model
[Paste final schema / link to `api/models.py`]

## API endpoints
| Method | Endpoint | Description |
|---|---|---|
| GET | /patients | List patients, filterable by `last_name`, `date_of_birth`, `phone_number` |
| GET | /patients/:id | Retrieve one patient |
| POST | /patients | Create patient |
| PUT | /patients/:id | Partial update |
| DELETE | /patients/:id | Soft delete (`deleted_at` set) |

All responses: `{ "data": ..., "error": ... }`

## Voice agent system prompt
[Paste the final prompt here in full, or link to `agent/system_prompt.md` —
reviewers explicitly want to see this]

## How the agent talks to the database
The agent calls `create_patient` (→ `POST /patients`) once the caller
confirms their information after read-back. [Add `lookup_patient_by_phone`
description here if duplicate detection was implemented.]

## Edge cases handled
- [ ] Invalid/future date of birth → re-prompt
- [ ] Malformed phone number → re-prompt
- [ ] Mid-call correction ("actually, spelled...") → field updated in place
- [ ] Caller asks to start over → state reset
- [ ] DB write failure → spoken graceful error, not silence
- [ ] Repeat caller (same phone number) → [describe behavior]

## Known limitations / trade-offs
- SQLite instead of Postgres — appropriate for this scope, would move to
  Postgres for concurrent write safety in a real multi-instance deployment
- [Add anything you actually cut from `01_SCOPE.md`'s P1 list]
- No HIPAA-grade encryption/access controls — out of scope per assessment FAQ
- [Anything else you know is rough]

## Next steps (if given more time)
- [Pull unshipped P1/bonus items from `01_SCOPE.md` here]
- Automated test suite for the API layer
- Dashboard UI for registered patients
- Multi-language support

## Testing it yourself
1. Call `+1-XXX-XXX-XXXX`
2. Provide test demographic info when asked (do not use real personal data)
3. Confirm when the agent reads it back
4. Verify: `curl https://your-app.up.railway.app/patients`
5. Call again from the same number to test recognition/second-call persistence
