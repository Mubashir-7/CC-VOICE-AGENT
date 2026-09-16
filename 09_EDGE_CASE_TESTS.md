# Edge Case Test Script — Voice AI Patient Registration

## Purpose
This is the explicit test script for the 4 failure scenarios named in the challenge brief,
plus additional robustness tests. Run each before submitting.

These are highly likely to match the reviewer's actual test procedure.

---

## Test Environment Setup
```bash
# Export your deployed API URL
export API_URL="https://your-app.up.railway.app"

# Clear any test data before running the suite
# (optional — don't do this if you want to keep seed data)
```

---

## Test Suite

### TEST 1: Full Happy Path (P0 — Critical)
**Goal**: Complete registration end-to-end

**Call script (say these things)**:
```
Agent: "Thank you for calling! I'm here to help register..."
You: "Hi, my name is Alex Johnson, and my date of birth is March 12th, 1985"
Agent: [Acknowledges and continues]
You: "I'm male"
You: "My phone number is 555-867-5309"
You: "My address is 42 Elm Street, Springfield, Illinois, 62701"
Agent: [Reads back all information]
You: "Yes, that's correct"
```

**Expected outcomes**:
- [ ] Agent greets naturally (not a rigid IVR menu tone)
- [ ] Agent accepts name + DOB together without repeating the question
- [ ] Agent reads back all fields before asking for confirmation
- [ ] After "yes", agent says "You're all set, Alex! Have a great day"
- [ ] Call ends cleanly

**API verification**:
```bash
curl "$API_URL/patients?last_name=Johnson"
# Expected: {"data": [{...patient record...}], "error": null}
```

---

### TEST 2: Invalid Date of Birth — Future Date (P0 — Critical)
**Goal**: Agent re-prompts specifically for DOB, nothing else

**Call script**:
```
You: "My name is Sarah Williams, date of birth January 1st, 2035"
```

**Expected outcomes**:
- [ ] Agent immediately catches the future date
- [ ] Agent says something like "That date would be in the future..."
- [ ] Agent asks ONLY for the date of birth again (does not re-ask for name)
- [ ] After correct DOB provided, conversation continues normally

**If test fails**: Check the system prompt's inline validation section.

---

### TEST 3: Call Drops Mid-Registration (P0 — Critical)
**Goal**: No partial/corrupt record saved if caller hangs up before confirmation

**Call script**:
```
You: Give name, DOB, sex, phone number
[Hang up before the agent reads back / before saying "yes"]
```

**Expected outcomes**:
- [ ] `curl $API_URL/patients` does NOT show a record for this caller
- [ ] DB is clean (no partial record)

**Why this passes automatically**: Save happens via `create_patient` tool call, which only fires after confirmation. If the call drops before confirmation, the tool never fires.

**If test fails**: Check system prompt — `create_patient` must only fire after explicit caller confirmation.

---

### TEST 4: DB Write Failure (P0 — Critical)
**Goal**: Agent gives graceful spoken error instead of silence or crash

**Setup**:
1. Temporarily stop the API (Railway: pause service, OR locally kill uvicorn)
2. Make a call and get to the confirmation step

**Call script**:
```
[Complete full happy path conversation]
You: "Yes, that's correct"
[API is down — create_patient tool call will fail]
```

**Expected outcomes**:
- [ ] Agent says something graceful like "I'm sorry, I'm having trouble saving your information..."
- [ ] Agent does NOT crash, go silent, or say "undefined" or "error"
- [ ] Call ends cleanly with an apology

**If test fails**: Check system prompt's error handling section for `create_patient` failure.

---

### TEST 5: Mid-Call Correction (P1 — High Value)
**Goal**: Agent updates a specific field without restarting the flow

**Call script**:
```
You: "My name is John Doe, date of birth June 5th, 1992"
Agent: [Continues collecting other fields]
You: "Actually, I spelled my last name wrong. It's D-O-U-G-H"
```

**Expected outcomes**:
- [ ] Agent acknowledges: "Of course! So your last name is Dough?"
- [ ] Agent ONLY asks about the corrected field, not everything else
- [ ] Conversation continues from where it was (doesn't restart)
- [ ] Final read-back shows "Dough" not "Doe"

**If test fails**: Strengthen the correction handling section in the system prompt with more trigger words.

---

### TEST 6: "Start Over" Intent (P1)
**Goal**: Complete state reset, clean restart

**Call script**:
```
You: [Give name and DOB]
You: "Actually, start over please"
```

**Expected outcomes**:
- [ ] Agent says "Of course! Let's start fresh..."
- [ ] Agent returns to opening question
- [ ] No data from before the "start over" is retained

---

### TEST 7: Out-of-Order Data (P1)
**Goal**: Agent accepts volunteered information without repeating questions

**Call script**:
```
Agent: "Could I get your full name and date of birth?"
You: "Sure, I'm Mike Chen, born April 3rd, 1978, and my phone number is 617-555-0192"
```

**Expected outcomes**:
- [ ] Agent accepts all three pieces of info at once
- [ ] Agent does NOT later ask "What's your phone number?" (it was already given)
- [ ] Agent moves on to the next uncollected fields

---

### TEST 8: Second Call — Duplicate Detection (Bonus)
**Goal**: Agent recognizes a returning caller by phone number

**Setup**: Complete TEST 1 successfully first (creates a record for that phone number)

**Call script**:
```
[Call from same phone number as TEST 1]
You: "Hi, I'd like to register"
You: [Give same phone number when asked]
```

**Expected outcomes**:
- [ ] After `lookup_patient_by_phone` fires, agent says "I see you may already be registered..."
- [ ] Agent mentions the name on file
- [ ] Agent asks if they want to update their info

**API verification**:
```bash
curl "$API_URL/patients?phone_number=5558675309"
# Should return the original TEST 1 patient record
```

---

### TEST 9: Invalid Phone Number Format
**Call script**:
```
You: "My phone number is 555-12" [stops mid-number]
```

**Expected outcomes**:
- [ ] Agent asks: "I need a complete US phone number. Could you repeat that?"
- [ ] Does NOT accept partial phone number
- [ ] Does NOT move on to next field

---

### TEST 10: API Endpoint Smoke Tests
Run these curl commands to verify the API independent of the voice agent:

```bash
# Health check
curl $API_URL/
# Expected: {"status": "ok"}

# List patients (should have at least seed data)
curl $API_URL/patients
# Expected: {"data": [...], "error": null}

# Get specific patient (use an ID from list above)
curl $API_URL/patients/PATIENT_ID_HERE
# Expected: {"data": {...}, "error": null}

# Create patient (valid data)
curl -X POST $API_URL/patients \
  -H "Content-Type: application/json" \
  -d '{"first_name":"Test","last_name":"User","date_of_birth":"1990-01-01","sex":"male","phone_number":"5550000001","address_line_1":"1 Test Ave","city":"Boston","state":"MA","zip_code":"02101"}'
# Expected: 201 with patient object

# Create patient (future DOB — should fail)
curl -X POST $API_URL/patients \
  -H "Content-Type: application/json" \
  -d '{"first_name":"Test","last_name":"User","date_of_birth":"2099-01-01","sex":"male","phone_number":"5550000002","address_line_1":"1 Test Ave","city":"Boston","state":"MA","zip_code":"02101"}'
# Expected: 422 with error message

# Soft delete
curl -X DELETE $API_URL/patients/PATIENT_ID_HERE
# Expected: {"data": null, "error": null}

# Verify soft-deleted patient no longer in list
curl $API_URL/patients
# Patient should be gone from list

# Partial update
curl -X PUT $API_URL/patients/ANOTHER_PATIENT_ID \
  -H "Content-Type: application/json" \
  -d '{"city": "Cambridge"}'
# Expected: {"data": {...updated patient...}, "error": null}
```

---

## Pass/Fail Summary Table

| Test | Status | Notes |
|------|--------|-------|
| 1: Happy path | ☐ Pass / ☐ Fail | |
| 2: Future DOB | ☐ Pass / ☐ Fail | |
| 3: Drop before confirm | ☐ Pass / ☐ Fail | |
| 4: DB write fails | ☐ Pass / ☐ Fail | |
| 5: Mid-call correction | ☐ Pass / ☐ Fail | |
| 6: Start over | ☐ Pass / ☐ Fail | |
| 7: Out-of-order data | ☐ Pass / ☐ Fail | |
| 8: Duplicate detection | ☐ Pass / ☐ Fail | |
| 9: Invalid phone | ☐ Pass / ☐ Fail | |
| 10: API smoke tests | ☐ Pass / ☐ Fail | |

Fill this in before submitting. Include in README's "Edge Cases Handled" section.
