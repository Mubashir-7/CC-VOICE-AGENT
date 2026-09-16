# SCOPE.md — Voice AI Patient Registration Agent

## Objective
Ship a phone number that, when called, has a natural conversation to collect
patient demographics, persists them, exposes them via a REST API, and
recognizes the same caller on a second call. Deployed and live at review time.

## Hard constraints
- 3-hour time box (real, not aspirational)
- Free-tier tools only — no paid infra
- Must be reachable by a real phone call at review time, not just "runs locally"

## MVP — must ship (P0)
These are non-negotiable; the whole grade depends on these existing and working.

| # | Item | Notes |
|---|------|-------|
| 1 | Real dialable US number | Vapi-provisioned or Twilio trial number |
| 2 | Conversational collection of all **required** fields | first_name, last_name, dob, sex, phone_number, address_line_1, city, state, zip_code |
| 3 | Read-back + confirmation before save | Agent must literally repeat the values and ask "did I get that right?" |
| 4 | Re-prompt on invalid data | At minimum: future DOB, malformed phone number |
| 5 | Persist to DB (survives restart) | SQLite file on disk (or Railway/Render persistent volume) |
| 6 | REST API: GET /patients, GET /patients/:id, POST /patients | With `{data, error}` envelope |
| 7 | Voice agent calls the API to save (not a separate write path) | Single source of truth for persistence logic |
| 8 | Second-call test passes | Call once, register; call again, data is retrievable |
| 9 | README with setup, architecture, tech stack, env vars, limitations | Written last, from what you actually built |
| 10 | Graceful call ending | Confirms name, says goodbye, hangs up cleanly |

## Should ship if time allows (P1)
| # | Item | Cut if behind schedule |
|---|------|------|
| 11 | PUT /patients/:id (partial update) | Yes — implement stub, document as "not wired to agent" |
| 12 | DELETE /patients/:id (soft delete) | Yes |
| 13 | Optional field opt-in flow (insurance, emergency contact, language) | Yes — collect required only |
| 14 | Duplicate detection by phone number (bonus) | Yes, but high value if time remains — cheap to add as one more tool call |
| 15 | Mid-call correction handling ("actually my name is...") | **Try not to cut** — this is graded directly under Conversational Quality |
| 16 | Basic input validation on API (server-side, not just agent-side) | Try not to cut — explicitly required, cheap to add with Pydantic/Zod |

## Explicitly out of scope (do not attempt)
- HIPAA compliance / encryption at rest (FAQ says explicitly not required)
- Real patient data (use only test data)
- Multi-language support (bonus only — skip unless everything else is done with >30 min left)
- Appointment scheduling (bonus only)
- Call recording/transcript storage (bonus only)
- A dashboard UI (bonus only)
- Automated test suite (bonus only — a single manual test script is enough)
- Hand-rolled STT/TTS — use a platform (Vapi/Retell), explicitly encouraged in FAQ
- Postgres/MySQL — SQLite is explicitly suggested and sufficient
- CI/CD pipelines, Docker, Kubernetes — no time value in a 3-hour box

## Cut line (if you're running out of time at each checkpoint)
- **At 1h30 mark**: if the agent isn't yet making a successful end-to-end test
  call, drop ALL P1 items immediately and focus only on P0 #1–8.
- **At 2h15 mark**: if deployment isn't live, stop building features. Get
  *something* callable, even a local ngrok tunnel with clear instructions
  (explicitly acceptable per FAQ).
- **At 2h45 mark**: stop coding. Write the README. A working system with a
  rushed README beats a half-documented ambitious one.

## Definition of done
- [ ] I can call the number from my own phone right now and it works
- [ ] I called it twice and the second call recognized/retrieved prior data
- [ ] `curl GET /patients` returns the record I just created
- [ ] I intentionally gave a bad DOB and the agent re-asked
- [ ] README has the live phone number and API base URL written in it
