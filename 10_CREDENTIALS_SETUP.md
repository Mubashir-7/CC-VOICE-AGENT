# Credentials & Environment Variables — Setup Guide

## Overview
This document lists every credential and environment variable needed, where to get it,
and the exact variable name to use in `.env`.

**NEVER commit `.env` to GitHub.** It is in `.gitignore`.

---

## Required Credentials

### 1. Vapi API Key
**Where**: https://dashboard.vapi.ai → Settings → API Keys → Create new key
**Format**: `vapi_xxxxxxxxxxxxxxxx`
**Variable**:
```
VAPI_API_KEY=vapi_xxxxxxxxxxxxxxxx
```
**Notes**: Free trial includes enough credits for testing (~10–20 min of calls). No credit card required for the free tier.

---

### 2. Vapi Phone Number ID
**Where**: After provisioning a phone number in Vapi Dashboard → Phone Numbers
**Format**: UUID string like `f47ac10b-58cc-4372-a567-0e02b2c3d479`
**Variable**:
```
VAPI_PHONE_NUMBER_ID=f47ac10b-58cc-4372-a567-0e02b2c3d479
```
**Notes**: This is the ID of the provisioned number (not the number itself). 
The actual dial-in number (e.g., `+1-555-XXX-XXXX`) goes in the README, not in env vars.

**If Vapi number unavailable in your region**: 
- Go to Twilio → Provision a trial number → Import it into Vapi
- The PHONE_NUMBER_ID will then be from Vapi after import

---

### 3. OpenAI API Key
**Where**: https://platform.openai.com/api-keys → Create new secret key
**Format**: `sk-proj-xxxxxxxxxxxxxxxx`
**Variable**:
```
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxx
```
**Notes**: 
- Model used: `gpt-4o-mini` (configured in Vapi assistant, not here directly)
- Vapi charges against its own credits for the LLM if using Vapi's model routing
- If using OpenAI directly through Vapi, Vapi will use this key
- New OpenAI accounts get $5 free credit — more than enough for testing

**Fallback**: Anthropic Claude Haiku
```
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxx
```

---

### 4. Database URL
**Variable**:
```
# Local development
DATABASE_URL=sqlite:///./patients.db

# Railway with persistent volume
DATABASE_URL=sqlite:////app/data/patients.db

# Render with attached disk  
DATABASE_URL=sqlite:////data/patients.db
```
**Notes**: No account or credential needed — SQLite is file-based.

---

### 5. API Base URL
**Variable**:
```
# Set after deploy — leave blank until Railway/Render gives you a URL
API_BASE_URL=https://care-cloud-production.up.railway.app
```
**Notes**:
- Do NOT set this until after first deploy
- After setting it, redeploy so the app knows its own URL (used in any self-referential logging)
- **Most importantly**: update Vapi tool `serverUrl` fields to this value

---

## .env.example Template
Copy this file to `.env` and fill in values:

```bash
# ============================================================
# Vapi (Telephony + Voice AI)
# Get from: https://dashboard.vapi.ai
# ============================================================
VAPI_API_KEY=

# The ID of your provisioned phone number in Vapi
# Get from: Vapi Dashboard > Phone Numbers
VAPI_PHONE_NUMBER_ID=

# ============================================================
# LLM Provider
# Get from: https://platform.openai.com/api-keys
# ============================================================
OPENAI_API_KEY=

# (Optional fallback) Get from: https://console.anthropic.com
# ANTHROPIC_API_KEY=

# ============================================================
# Database
# SQLite file path — change after deploy to match volume mount
# ============================================================
DATABASE_URL=sqlite:///./patients.db

# ============================================================
# API
# Set to your deployed URL after Railway/Render deploy
# Used in Vapi tool serverUrl configuration
# ============================================================
API_BASE_URL=
```

---

## Twilio (Only if using Twilio number imported into Vapi)

If Vapi number provisioning is unavailable in your region, provision a Twilio trial number
and import it into Vapi. You do NOT need Twilio credentials in your `.env` if you're just 
importing the number — Vapi handles the Twilio integration.

**If needed**:
1. https://twilio.com → Create free account
2. Get a US trial number (free, no card for trial)
3. In Vapi Dashboard → Phone Numbers → Import Twilio Number
4. Enter your Twilio Account SID + Auth Token + the number
5. Vapi will generate a `PHONE_NUMBER_ID` — use that in your `.env`

---

## Railway (Deployment)

No API key needed in `.env`. Railway deployment is managed through:
1. GitHub → Railway connection (OAuth)
2. Env vars set directly in Railway dashboard UI

---

## Credential Handoff Checklist

Before starting the build, confirm you have:
- [ ] Vapi account created and API key copied
- [ ] Vapi phone number provisioned (or Twilio trial number ready to import)
- [ ] OpenAI account and API key copied (or Anthropic key)
- [ ] Railway account created (linked to GitHub)
- [ ] All values pasted into `.env` locally

Once these are confirmed, coding can begin immediately.
