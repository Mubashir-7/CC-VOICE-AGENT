# File Structure Reference

## Final Repository Layout

```
care-cloud-voice-agent/
│
├── api/                            # FastAPI backend service
│   ├── main.py                     # App entrypoint: FastAPI init, CORS, startup events
│   ├── db.py                       # SQLite engine + session dependency (get_session)
│   ├── models.py                   # SQLModel ORM table definitions (Patient)
│   ├── schemas.py                  # Pydantic request/response shapes + validators
│   ├── routes/
│   │   └── patients.py             # All 5 CRUD endpoints for /patients
│   └── requirements.txt            # Python dependencies
│
├── agent/                          # Voice agent configuration
│   ├── system_prompt.md            # The full Vapi system prompt (reviewers read this)
│   ├── vapi_assistant_config.json  # Full Vapi assistant JSON (drag-drop importable)
│   └── setup_vapi.py               # Script: creates/updates Vapi assistant via REST API
│
├── scripts/
│   └── seed_patients.py            # Inserts 2 test patients into deployed API
│
├── railway.json                    # Railway deployment config (optional)
├── Procfile                        # Fallback: "web: uvicorn api.main:app --host 0.0.0.0 --port $PORT"
├── .env.example                    # All required env vars documented (no values)
├── .gitignore                      # node_modules, __pycache__, .env, patients.db
└── README.md                       # Setup + architecture + live phone/API URL
```

## What Goes in Each File

### api/main.py
```python
# Responsibilities:
# - Create FastAPI() app instance
# - Add CORSMiddleware (allow all origins for free-tier demo)
# - Register router: app.include_router(patients_router, prefix="/patients")
# - @app.on_event("startup"): create_all_tables()
# - GET / healthcheck endpoint: returns {"status": "ok"}
```

### api/db.py
```python
# Responsibilities:
# - Create SQLite engine from DATABASE_URL env var
# - Define create_all_tables() function called on startup
# - Define get_session() generator dependency (yields SQLModel Session)
```

### api/models.py
```python
# Responsibilities:
# - Define Patient(SQLModel, table=True) with all fields
# - patient_id: UUID (auto-generated primary key)
# - All required fields: first_name, last_name, date_of_birth, sex,
#   phone_number, address_line_1, city, state, zip_code
# - All optional fields: address_line_2, email, insurance_provider,
#   insurance_member_id, preferred_language, emergency_contact_name,
#   emergency_contact_phone
# - Metadata: created_at, updated_at (auto), deleted_at (nullable, soft delete)
```

### api/schemas.py
```python
# Responsibilities:
# - PatientCreate: Pydantic model for POST /patients body
#   - Validators: DOB not in future, phone regex, state 2-letter, zip regex
# - PatientUpdate: Optional[...] version of PatientCreate for PATCH semantics
# - PatientResponse: What we return (includes patient_id, created_at, etc.)
# - APIResponse: Generic envelope {"data": T | None, "error": str | None}
```

### api/routes/patients.py
```python
# Responsibilities:
# - POST   /          → create_patient() → 201
# - GET    /          → list_patients(last_name, date_of_birth, phone_number) → 200
# - GET    /{id}      → get_patient() → 200 | 404
# - PUT    /{id}      → update_patient() → 200 | 404 | 422
# - DELETE /{id}      → soft_delete_patient() → 200 | 404
# All routes filter out deleted_at IS NOT NULL records (soft delete)
```

### agent/system_prompt.md
```
# Responsibilities:
# - Full natural-language instructions for the Vapi LLM
# - Personality + tone guidelines
# - Field collection strategy (clusters, not one-by-one)
# - Inline validation rules (what to say when DOB is wrong, etc.)
# - Correction handling ("actually..." intent)
# - Start-over handling
# - Confirmation read-back script
# - Tool invocation logic (when to call lookup vs. create)
# - Graceful error + goodbye scripts
```

### agent/vapi_assistant_config.json
```json
// Responsibilities:
// - Full Vapi assistant config JSON
// - Includes: model (GPT-4o-mini), voice (ElevenLabs/Azure preset), 
//   firstMessage, systemPrompt, tools (lookup_patient_by_phone, create_patient)
// - Tool schemas match the POST /patients Pydantic schema exactly
// - serverUrl fields use the deployed API_BASE_URL
```

### agent/setup_vapi.py
```python
# Responsibilities:
# - Load VAPI_API_KEY and API_BASE_URL from .env
# - Read vapi_assistant_config.json
# - Replace {{API_BASE_URL}} placeholders with real URL
# - POST to Vapi API to create/update assistant
# - Print assistant ID for use in phone number assignment
```

### scripts/seed_patients.py
```python
# Responsibilities:
# - POST two test patients to API_BASE_URL/patients
# - Patient 1: John Doe, test demographics
# - Patient 2: Jane Smith, test demographics
# - Print confirmation + patient_ids
```
