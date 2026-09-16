# Deployment Guide — Railway (Primary) + Render/ngrok (Fallback)

## Overview
Deploy the FastAPI backend to a public URL before wiring Vapi tool calls.
This must be done early (Phase 2, ~45 min mark) so you can test the full
end-to-end call before spending time polishing the prompt.

---

## Option A: Railway (Recommended — Best SQLite persistence)

### Prerequisites
- GitHub repo pushed and public
- Railway account at https://railway.app (free, no card required for trial)

### Step-by-Step

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "initial commit: FastAPI patient registration API"
   git remote add origin https://github.com/YOUR_USERNAME/care-cloud-voice-agent.git
   git push -u origin main
   ```

2. **Create Railway project**
   - Go to https://railway.app/dashboard
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your `care-cloud-voice-agent` repo
   - Railway will auto-detect Python and start deploying

3. **Set environment variables**
   - In Railway dashboard: Settings → Variables
   - Add each var from `.env.example`:
     ```
     OPENAI_API_KEY=sk-...
     VAPI_API_KEY=...
     DATABASE_URL=sqlite:///./data/patients.db
     API_BASE_URL=https://YOUR-APP.up.railway.app  (set after first deploy)
     ```

4. **Add a persistent volume for SQLite**
   > [!IMPORTANT]
   > Without a volume, the SQLite file resets on every deploy. This is a CRITICAL step.
   - Railway dashboard: Volumes → New Volume
   - Mount path: `/app/data`
   - Update `DATABASE_URL` to: `sqlite:////app/data/patients.db`

5. **Set the start command**
   Add a `Procfile` in project root:
   ```
   web: uvicorn api.main:app --host 0.0.0.0 --port $PORT
   ```
   Or add to `railway.json`:
   ```json
   {
     "build": { "builder": "NIXPACKS" },
     "deploy": {
       "startCommand": "uvicorn api.main:app --host 0.0.0.0 --port $PORT",
       "restartPolicyType": "ON_FAILURE"
     }
   }
   ```

6. **Verify deployment**
   ```bash
   curl https://YOUR-APP.up.railway.app/
   # Should return: {"status": "ok"}
   
   curl https://YOUR-APP.up.railway.app/patients
   # Should return: {"data": [], "error": null}
   ```

7. **Test SQLite persistence**
   ```bash
   # Create a test patient
   curl -X POST https://YOUR-APP.up.railway.app/patients \
     -H "Content-Type: application/json" \
     -d '{"first_name":"Test","last_name":"Patient","date_of_birth":"1990-01-01","sex":"male","phone_number":"5551234567","address_line_1":"123 Test St","city":"Boston","state":"MA","zip_code":"02101"}'
   
   # Trigger a redeploy in Railway dashboard
   
   # Verify record still exists
   curl https://YOUR-APP.up.railway.app/patients
   # Should still show the test patient
   ```

8. **Copy the URL** → set as `API_BASE_URL` env var → redeploy

---

## Option B: Render (Fallback if Railway volume doesn't work)

1. Go to https://render.com/dashboard
2. New → Web Service → Connect GitHub repo
3. Build Command: `pip install -r api/requirements.txt`
4. Start Command: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
5. Add a Disk:
   - Name: `patients-db`
   - Mount Path: `/data`
   - Size: 1 GB (free)
6. Set env vars (same as Railway)
7. Update `DATABASE_URL=sqlite:////data/patients.db`

> [!WARNING]
> Render's free tier **sleeps after 15 minutes of inactivity**. The first call after sleep will be slow (30-60 second cold start). This may cause Vapi's tool call to time out on the first call.
> **Fix**: Use Render's UptimeRobot integration to ping `/` every 10 minutes and prevent sleep.

---

## Option C: ngrok (Last Resort — Explicitly Acceptable per Brief)

If both Railway and Render have issues, run locally with ngrok:

1. **Install ngrok**: https://ngrok.com/download
2. **Start FastAPI locally**:
   ```bash
   cd api
   uvicorn main:app --reload --port 8000
   ```
3. **Start ngrok tunnel**:
   ```bash
   ngrok http 8000
   ```
4. **Copy the HTTPS URL** (e.g., `https://abc123.ngrok.io`)
5. Set this as `API_BASE_URL` in your Vapi assistant tool URLs
6. **Document in README** that this requires your local machine to be running

> [!NOTE]
> The brief explicitly states: "if a cloud deploy is a blocker, fall back to ngrok and document it clearly — this will not be penalized."

---

## Post-Deploy Checklist

After whichever deploy method works:

- [ ] `GET /` returns `{"status": "ok"}` 
- [ ] `GET /patients` returns `{"data": [], "error": null}`
- [ ] `POST /patients` with valid body returns 201 with patient object
- [ ] `POST /patients` with future DOB returns 422 with error message
- [ ] After redeploy, previously created patient still appears in `GET /patients`
- [ ] API_BASE_URL env var updated to point to live URL
- [ ] Vapi tool URLs updated to use deployed URL
- [ ] README updated with live URL

---

## Railway railway.json Reference

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn api.main:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10,
    "healthcheckPath": "/",
    "healthcheckTimeout": 300
  }
}
```

## requirements.txt Reference

```
fastapi==0.111.0
uvicorn[standard]==0.30.1
sqlmodel==0.0.19
pydantic[email]==2.7.4
python-dotenv==1.0.1
httpx==0.27.0
```

## Common Deploy Errors and Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `ModuleNotFoundError: No module named 'api'` | Start command path issue | Change to `uvicorn api.main:app` from project root |
| SQLite file not persisting | No volume attached | Attach volume at `/app/data`, update DATABASE_URL |
| `PORT not found` | Not using `$PORT` env var | Ensure start command uses `--port $PORT` |
| 502 Bad Gateway | App crashed on startup | Check Railway logs → likely missing env var |
| Tool call timeout from Vapi | Render sleep or Railway cold start | Add health check ping, or use ngrok locally |
