# TECH_STACK.md — Choices and Why (Free Tier Only)

## Summary table

| Layer | Choice | Free tier limit | Why this over alternatives |
|---|---|---|---|
| Telephony + Voice AI | **Vapi** | Free trial credits (~10–20 min of calls, no card required for a Vapi phone number in most regions; can also import a Twilio number) | Handles STT, TTS, turn-taking, interruption/barge-in, and tool-calling out of the box. Building this from raw Twilio + Deepgram + ElevenLabs is a 2nd/3rd-hour sink for STT/TTS glue code that adds zero grading value (FAQ explicitly says they don't care if you built STT/TTS yourself) |
| Backup telephony | **Twilio trial number** | Free trial, $15 credit, inbound calls to your own trial number work without restriction | Fallback if Vapi's number provisioning is slow/unavailable in your region — Vapi can also just use a Twilio number you provision, best of both |
| LLM | **GPT-4o-mini** (via Vapi's built-in model routing) or **Claude Haiku** if you want Anthropic | Vapi includes model cost in trial credits; OpenAI/Anthropic free/trial API credits otherwise | Fast + cheap + good enough for structured slot-filling conversation; a bigger model buys you little here versus prompt quality |
| Backend / API | **Python + FastAPI** | Free (self-hosted) | Async, built-in request validation via Pydantic (covers the "server-side validation" requirement for free), auto-generates OpenAPI docs which looks good to a reviewer with zero extra work |
| Database | **SQLite** | Free, file-based | Explicitly suggested in the brief as the "simplicity" choice. No separate DB server to provision or keep alive on a free host. Survives restarts as long as it's on a persistent disk/volume |
| ORM | **SQLModel** (or plain `sqlite3` if you want zero dependencies) | Free | SQLModel = Pydantic + SQLAlchemy in one, minimal boilerplate, matches FastAPI naturally |
| Hosting (API) | **Railway free tier** (or Render free web service) | Railway: free trial credit; Render: free tier sleeps after inactivity | Railway persists a volume more reliably for SQLite; Render's free tier works but the disk resets on redeploy unless you attach a paid disk — worth checking at build time |
| Hosting fallback | **ngrok** (local machine + tunnel) | Free tier gives a temporary public URL | FAQ explicitly says this is an acceptable, non-penalized fallback if cloud deploy is a blocker. Use as Plan B only — a real cloud URL looks more finished |
| Voice agent ↔ API integration | **Vapi Tool/Function calling** → hits your FastAPI endpoints directly | Free | Keeps a single source of truth for persistence logic (per requirement #5 in the brief: "the voice agent must use the REST API or directly invoke the same service layer") |
| Version control | **GitHub** (public repo) | Free | Required by submission instructions |

## Alternatives considered and rejected

- **Retell AI / Bland.ai instead of Vapi** — both are viable and roughly
  equivalent; Vapi is picked here for having the most permissive free trial
  and the most straightforward tool-calling docs. If you already have
  familiarity with Retell, swap freely — the architecture doesn't change.
- **Twilio + raw Deepgram/ElevenLabs** — more "impressive" on paper but is a
  significant time sink for STT/TTS/turn-taking glue in a 3-hour box, and the
  brief explicitly says this isn't what's being evaluated.
- **Postgres/Supabase** — Supabase free tier is fine functionally, but adds
  network latency and an extra external dependency/auth setup for zero
  grading benefit over SQLite in this scope.
- **Node/Express instead of FastAPI** — equally valid; FastAPI is preferred
  here because Pydantic gives you free server-side validation, which is an
  explicit requirement ("do not rely solely on the voice agent for
  validation").
- **MongoDB** — no relational constraints needed for this data model; adds
  schema-enforcement work FastAPI/SQLite give you for free.

## Environment variables you'll need
```
VAPI_API_KEY=
VAPI_PHONE_NUMBER_ID=
OPENAI_API_KEY=            # or ANTHROPIC_API_KEY, depending on model choice
DATABASE_URL=sqlite:///./patients.db
API_BASE_URL=              # your deployed FastAPI base URL, for Vapi tool config
```
Never commit these — `.env` + `.gitignore`, load via `python-dotenv` or the
host's env var panel.
