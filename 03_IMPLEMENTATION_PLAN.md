# IMPLEMENTATION_PLAN.md — 3-Hour Build Sequence

Principle: get a *thin, ugly, end-to-end call working in the first 45
minutes*, before writing a single line of "polish." Everything after that is
additive, and you can stop at any checkpoint with a gradeable artifact.

---

## Phase 0 — Setup (0:00–0:15)
- [ ] Create GitHub repo, basic folder structure (see below)
- [ ] Create Vapi account, generate API key
- [ ] Create OpenAI (or Anthropic) API key
- [ ] Scaffold FastAPI project with `uvicorn` running locally
- [ ] Confirm you can hit `localhost:8000/docs`

**Repo structure:**
```
/agent          -> Vapi assistant config / system prompt (JSON or config script)
/api            -> FastAPI app
  main.py
  models.py     -> SQLModel table definitions
  schemas.py    -> Pydantic request/response models
  db.py         -> engine/session setup
  routes/
    patients.py
/README.md
/SCOPE.md       (this planning doc, optional to include)
.env.example
.gitignore
```

## Phase 1 — Data layer (0:15–0:45)
- [ ] Define `Patient` model with all fields from the brief (required +
      optional), UUID `patient_id`, `created_at`/`updated_at`, `deleted_at`
      nullable (for soft delete)
- [ ] Wire SQLite file, auto-create tables on startup
- [ ] Implement `POST /patients` with Pydantic validation matching the
      validation rules table (regex for phone, 2-letter state, 5/ZIP+4 zip,
      DOB not in future, enum for sex)
- [ ] Implement `GET /patients` (with `last_name`/`date_of_birth`/
      `phone_number` query filters) and `GET /patients/:id`
- [ ] Return the `{data, error}` envelope consistently; correct status codes
      (201 on create, 404 on missing, 422 on validation failure)
- [ ] Manually test all three with `curl` or the FastAPI `/docs` UI — do not
      move on until this works in isolation

**Checkpoint (0:45):** API is fully testable via curl/Postman without the
voice agent involved. This isolates bugs later — if something breaks
end-to-end, you'll know it's the agent/tool-call layer, not the DB.

## Phase 2 — Deploy the API early (0:45–1:05)
Deploy now, not at the end. You want your public URL locked in before you
wire Vapi's tool calls to it.
- [ ] Push to GitHub
- [ ] Deploy to Railway/Render free tier
- [ ] Confirm persistent volume/disk actually persists the SQLite file across
      a redeploy (test this explicitly — it's a common silent failure)
- [ ] Hit the deployed `/patients` endpoint from your local machine to confirm
      it's live

**Checkpoint (1:05):** You have a public API URL that works. This de-risks
the single biggest failure mode (system not reachable at review time) early,
while you still have time to fall back to ngrok if the host is being difficult.

## Phase 3 — Voice agent (1:05–2:00)
This is where most of your grading value is. Budget the most time here.
- [ ] Write the system prompt (see `agent/system_prompt.md` — draft this as
      its own file, not inline in code, so it's easy to iterate on and easy
      for a reviewer to read)
- [ ] Define the prompt's conversational strategy explicitly:
  - Ask for fields in natural clusters, not one-by-one robotically
    ("Can I get your full name and date of birth to start?")
  - Accept corrections at any point, not just when asked
  - Validate as you go (reject a DOB in the future immediately, ask again)
  - After required fields, offer the optional bundle as one yes/no question
  - Read back the full record before saving, explicitly ask for confirmation
  - Handle "start over" as a recognized intent at any point
- [ ] Define Vapi tools (function calls) matching your API:
  - `create_patient` → POST /patients
  - `lookup_patient_by_phone` → GET /patients?phone_number= (for duplicate
    detection / bonus)
- [ ] Wire the tools' endpoint URLs to your deployed API base URL
- [ ] Assign the number (Vapi-provisioned or imported Twilio number)
- [ ] **Call it yourself.** Multiple times. Try: a clean flow, a mid-call
      correction, an invalid DOB, hanging up and calling back with the same
      number

**Checkpoint (2:00):** You've personally completed a full successful call and
can see the record land in the DB via the API.

## Phase 4 — Edge cases pass (2:00–2:30)
Go down the brief's explicit list, test each, fix what breaks:
- [ ] Invalid DOB → re-prompts specifically for DOB
- [ ] Malformed phone number → re-prompts specifically for phone
- [ ] Mid-call "actually, it's spelled..." correction → agent updates the
      field, doesn't restart the whole flow
- [ ] Caller says "start over" → agent resets collected state cleanly
- [ ] Simulate a DB write failure (e.g., stop the API briefly) → agent gives
      a graceful spoken error, not silence or a crash
- [ ] Second call, same number → duplicate detection or at minimum: data from
      call 1 is confirmed retrievable via API

## Phase 5 — Documentation (2:30–2:55)
- [ ] Fill in README from `04_README_TEMPLATE.md` — setup, architecture
      diagram (even ASCII is fine), tech stack + why, env vars, known
      limitations, "Next Steps" section
- [ ] Include the live phone number and API base URL directly in the README,
      not just in the submission email
- [ ] Add 1–2 seed patients via a small script or manual POST, note it in
      README
- [ ] Copy the final system prompt into the README or a linked file so
      reviewers can read your prompt engineering without calling the agent

## Phase 6 — Final buffer (2:55–3:00)
- [ ] One last live call to confirm nothing broke during doc-writing
- [ ] Push final commit
- [ ] Send repo URL, phone number, API base URL, any test notes

---

## If things go wrong mid-build
| Symptom | Fast fix |
|---|---|
| Vapi number provisioning stuck/unavailable | Provision a Twilio trial number instead and import it into Vapi |
| Railway/Render deploy fails or disk doesn't persist | Fall back to ngrok + local server, document it clearly (FAQ says this won't be penalized) |
| Running low on time at 2h mark with agent still flaky | Cut all P1 items from `01_SCOPE.md`, get one clean happy-path call working, document known gaps honestly in README |
| LLM tool calls not firing reliably | Simplify tool schema (fewer required params per call), test tool call in isolation via Vapi's test console before blaming the prompt |
