# Evaluation Analysis — Reading Between the Lines

## What the document says vs. what actually gets scored

The brief states 5 categories at 20% each. In practice, take-home reviewers don't
score that mechanically — they form an impression in the first 2 minutes and then
look for evidence to confirm it. Here's how it actually plays out:

### The gate: "Working System" (20% on paper, ~50% in practice)
If the reviewer calls your number and it doesn't pick up, times out, or crashes
mid-conversation, **nothing else matters**. A perfect README with a broken demo
scores lower than a rough README with a working demo. This is explicitly stated:
> "a working but incomplete system scores higher than a non-functional but
> ambitious one."

Treat this as a hard gate, not a category. Build the thinnest possible working
slice first (call → collect 3 fields → save → read back), get it deployed and
callable, THEN go back and add breadth.

### The tell: "Conversational Quality"
This is the category that actually differentiates candidates, because most
people get the CRUD/API part right (it's boilerplate) but ship a robotic,
brittle voice agent. Reviewers are specifically going to try to break it:
- Give a correction mid-flow ("actually, my last name is spelled...")
- Say something out of order (give phone number before being asked)
- Say "hold on" or trail off
- Give an invalid DOB or a fake phone number

If your system prompt is a rigid script with no tolerance for these, you lose
points here even if the API and DB are flawless. **This is where most
candidates fail, and where you should spend disproportionate prompt-engineering
time.**

### The hidden signal: trade-off communication
Look at this line: "Make smart trade-offs — knowing when to use a shortcut
(SQLite over Postgres, ngrok over cloud deploy) and when to invest (clean
prompt engineering, proper error handling)." They are explicitly telling you
they want to see you SKIP infrastructure polish and INVEST in the agent logic.
Don't burn an hour setting up Postgres + Docker + CI. Use SQLite. Use a
platform (Vapi/Retell) instead of hand-rolling STT/TTS/telephony. The FAQ
confirms this is encouraged, not a shortcut you need to apologize for.

### What "Technical Architecture" really checks
Not cleverness — separation of concerns. They will open your repo and expect
to immediately see: telephony/agent config in one place, business logic in
another, DB schema in another, API routes in another. A single 400-line
`server.js` doing everything reads as "didn't plan," even if it works.

### What "Edge Cases" really checks
They list 4 specific failure scenarios in the doc itself. That's not
decoration — that's very likely close to their actual test script:
1. Invalid DOB (future date)
2. Call drops mid-registration
3. DB write fails
4. Caller wants to restart mid-conversation

Treat these four as acceptance criteria, not "nice to have edge cases."

## Net conclusion — where to spend your 3 hours
1. **~40%** — Vapi/Retell setup + system prompt + tool-calling to your API
   (this is the differentiator)
2. **~25%** — API + DB (keep boring and correct, don't over-engineer)
3. **~15%** — deploy + verify the real call end-to-end, twice
4. **~15%** — README + edge case pass
5. **~5%** — buffer

See `03_IMPLEMENTATION_PLAN.md` for the minute-by-minute breakdown.
