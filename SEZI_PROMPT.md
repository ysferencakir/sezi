# SEZI Project - Comprehensive Prompt

## What is Sezi?

**Sezi** is a personal life reflection system that helps you understand invisible patterns in your life through data-driven insights, without judgment, optimization pressure, or medical claims.

**Core Mission:** Make your life visible to yourself through observation, not control.

**NOT:**
- ❌ A productivity app
- ❌ A fitness tracker
- ❌ An AI therapist
- ❌ A medical diagnostic tool
- ❌ An optimization engine

**IS:**
- ✅ A Reflective Signal System
- ✅ A pattern discovery tool
- ✅ A personal data archive
- ✅ A reflection facilitator

---

## Ethical & Psychological Constraints

### Core Principles:
1. **Weak Language Only**
   - Never use: "why", "cause", "problem", "stress"
   - Use: "concurrent change", "recurring pattern", "notable shift"

2. **Long Window Analysis**
   - Minimum: 7 days
   - Preferred: 14+ days
   - Some insights: 30 days
   - Reason: Noise reduction, signal clarity

3. **No Real-Time Alerts**
   - ❌ "Recovery dropped!"
   - ❌ "Stress detected!"
   - ✅ Daily calm summary
   - ✅ Weekly reflection
   - ✅ Monthly retrospective
   - Reason: Prevent anxiety loops

4. **User-Led Interpretation**
   - System shows correlations
   - User interprets meaning
   - System never explains "why"

5. **Context First Architecture**
   - Context > Metrics
   - Special events matter: exams, illness, moves, relationship stress
   - Baseline without context = meaningless

6. **Observable, Not Prescriptive**
   - Mission: "Make life visible"
   - Not: "Optimize life"
   - Philosophy: Variation is normal, not failure

### Obsession Prevention Checkpoints:
- **Week 4:** Is system becoming obsession or curiosity?
- **Week 8:** Is tracking mandatory feeling or optional interest?
- **Week 12:** Is system producing insight or just accumulating data?

---

## Data Sources & Collection

### Automatic (No Manual Entry Friction):
1. **Health Connect API** (Samsung Health)
   - Sleep (hours, quality)
   - Heart rate (daily average)
   - Steps
   - Workouts
   - Recovery score (if available)

2. **Google Calendar API**
   - Meeting count (daily)
   - Total meeting minutes
   - Free consecutive blocks
   - Busiest hours
   - Event categories (work/personal)

3. **Bank CSV (Monthly Upload)**
   - Transaction date
   - Amount
   - Category

### Manual (Low Friction):
4. **Weekly Context Log** (Google Form → auto Sheets)
   - What happened this week? (2-3 sentences)
   - Special events? (exam, illness, move, stress)
   - General feeling (1-10 scale)
   - Time: 5 minutes/week

### NOT Collecting (Too Noisy):
- ❌ Daily mood (retrospective bias, unreliable)
- ❌ Screen time (no context: work vs. scroll?)
- ❌ Focus score (undefined metric)

---

## Technical Stack

### Data Collection
- **Scheduling:** GitHub Actions (daily, 06:00 UTC)
- **Language:** Python 3.11+
- **Trigger:** Cron job (2000 min/month available)
- **Credentials:** OAuth 2.0 (secure token refresh)

### Database
- **Type:** PostgreSQL (Neon)
- **Backup:** Automatic (Neon)
- **Local Backup:** Weekly (encrypted, external drive)
- **Encryption:** SSL enabled (default)
- **Cost:** Free tier (3GB storage, more than enough for 1 year)

### API Layer
- **Framework:** FastAPI (Python)
- **Deployment:** Render.com (free tier)
- **Endpoints:** 
  - `GET /api/week` - last 7 days summary
  - `GET /api/daily?date=YYYY-MM-DD` - specific day
  - `GET /api/month?month=YYYY-MM` - monthly summary
  - `POST /api/context` - manual context entry
  - `GET /health` - health check

### Frontend
- **Framework:** React (or Next.js)
- **Deployment:** Vercel (free)
- **Domain:** ysferencakir.info.tr
- **Charts:** Recharts
- **Features:**
  - Dashboard: Week view (cards + charts)
  - Monthly: Overview & trends
  - Query: Ad-hoc metric lookups
  - Manual entry: Context log form

### Cost Analysis
```
Neon PostgreSQL:    $0 (free tier)
GitHub Actions:     $0 (2000 min/month)
Render.com API:     $0 (free tier)
Vercel Frontend:    $0 (free)
Domain:             Already owned (ysferencakir.info.tr)
─────────────────────────────────
TOTAL/MONTH:        $0
```

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│  DATA SOURCES (Automatic Collection)            │
├─────────────────────────────────────────────────┤
│ • Health Connect API (Samsung Health)           │
│ • Google Calendar API                           │
│ • Bank CSV (manual upload)                      │
│ • Google Form (weekly context)                  │
└─────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────┐
│  GITHUB ACTIONS (Scheduling)                    │
├─────────────────────────────────────────────────┤
│ Trigger: Daily 06:00 UTC                        │
│ Duration: ~5 min per run                        │
│ Action: Run Python ETL script                   │
└─────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────┐
│  PYTHON ETL SCRIPT                              │
├─────────────────────────────────────────────────┤
│ 1. Auth: Refresh OAuth tokens                   │
│ 2. Fetch: Health Connect API data               │
│ 3. Fetch: Google Calendar API data              │
│ 4. Parse: Bank CSV (if present)                 │
│ 5. Transform: Normalize & validate              │
│ 6. Load: Insert to Neon PostgreSQL              │
│ 7. Log: Error handling & monitoring             │
└─────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────┐
│  NEON POSTGRESQL (Database)                     │
├─────────────────────────────────────────────────┤
│ Tables:                                          │
│  • daily_health (sleep, hr, steps, workouts)   │
│  • daily_calendar (meetings, free time)        │
│  • weekly_context (notes, special events)      │
│  • daily_finance (spending, categories)        │
│                                                 │
│ Backup: Automatic (Neon handles)               │
│ SSL: Enabled (default)                         │
└─────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────┐
│  FASTAPI (Backend)                              │
├─────────────────────────────────────────────────┤
│ Deployment: Render.com (free tier)              │
│ URL: api.sezi.onrender.com                      │
│                                                 │
│ Endpoints:                                      │
│  GET  /api/week          - 7-day summary       │
│  GET  /api/daily?date=   - specific day        │
│  GET  /api/month?month=  - monthly report      │
│  POST /api/context       - context submission  │
│  GET  /health            - health check        │
│                                                 │
│ CORS: Configured for Vercel frontend           │
└─────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────┐
│  REACT FRONTEND (Dashboard)                     │
├─────────────────────────────────────────────────┤
│ Deployment: Vercel (free)                       │
│ Domain: ysferencakir.info.tr                    │
│                                                 │
│ Pages:                                          │
│  /dashboard  - Week view (metrics + charts)    │
│  /month      - Monthly summary & trends        │
│  /query      - Ad-hoc queries                  │
│  /context    - Manual context entry form       │
│                                                 │
│ Charts: Recharts (lightweight, clean)          │
│ Design: Minimal, calm, reflection-focused      │
└─────────────────────────────────────────────────┘
```

---

## Key Implementation Principles

### 1. Weak Hypothesis Generation
- System observes correlations
- System never claims causation
- User discovers meaning

### 2. Long Window Analysis
- Minimum 7 days for any pattern
- 14 days preferred
- 30 days for complex patterns
- Prevents noise detection as signal

### 3. No Predictive Claims
- ❌ "You should sleep more"
- ❌ "Your stress is high"
- ✅ "Over last 14 days, you've slept avg 6.5h when meeting count > 8/day"

### 4. Context Matters Most
- Baseline without context = noise
- With context = signal
- User provides context = system learns

### 5. Reflection Over Optimization
- Question: "What patterns am I noticing?"
- Not: "How do I fix this?"
- Philosophy: Understanding first, action optional

### 6. Obsession Prevention
- Checkpoints at weeks 4, 8, 12
- Break signals: "Must check", "Feel incomplete without it"
- Healthy signals: "Interesting observation", "Didn't notice last month"

---

## What This System Does

✅ **Shows you what you didn't notice before**
- Recurring patterns
- Correlations between life areas
- Baseline variations

✅ **Helps you reflect on your life**
- Weekly summaries
- Monthly retrospectives
- Context-aware insights

✅ **Lets you query your own data**
- "Show me weeks with >10 meetings"
- "Compare sleep when traveling vs home"
- "Find patterns in finance & energy"

---

## What This System Does NOT Do

❌ **Does not judge or prescribe**
- No "you should" statements
- No moral values attached
- No optimization pressure

❌ **Does not diagnose or treat**
- Not a medical tool
- Not a mental health app
- Not a therapist

❌ **Does not track everything**
- Not mood (too unreliable)
- Not focus (undefined)
- Not behavior scores

❌ **Does not create addiction**
- Long windows prevent compulsion
- Checkpoints detect obsession
- Optional, not required

---

## Success Metrics (Personal Use Only)

**After 3 months:**
- ✅ Data is accumulating cleanly
- ✅ No obsession detected
- ✅ 1-2 interesting patterns noticed

**After 6 months:**
- ✅ Can compare "before/after" periods
- ✅ Context log is helpful for understanding
- ✅ Still feel it's reflection, not compulsion

**After 12 months:**
- ✅ Full year of data available
- ✅ Seasonal patterns visible
- ✅ Understand own baseline & variations
- ✅ Can answer: "What affected my sleep/energy/spending?"

---

## Failure Modes to Watch

🔴 **Obsession Loop**
- Checking system compulsively
- Anxiety about missing data
- Metrics become performance targets
- **Fix:** 2-week breaks, week 8 checkpoint

🔴 **Noise Detection**
- Finding spurious correlations
- Overthinking single-day variations
- **Fix:** Long windows (7-14+ days), context requirements

🔴 **Scope Creep**
- Adding 20 more data sources
- Building complex ML models
- Becoming a startup product
- **Fix:** Keep it personal, keep it simple

🔴 **Siren Song of Optimization**
- "I should change based on this pattern"
- Turns reflective system into productivity app
- **Fix:** Remember mission = visibility, not control

---

## For Future Reference

This system is **intentionally minimal** because:
1. **Complexity kills adoption** - simple works, complex fails
2. **Personal project ≠ Product** - you'll learn what's useful before scaling
3. **Data quality > quantity** - 4 sources done well > 20 sources done poorly
4. **Reflection takes time** - insights emerge at month 3-6, not week 1
5. **Obsession risk is real** - keep guardrails simple, stick to them

---

## Implementation Approach

- **Phase 1 (Week 1):** Infrastructure setup (databases, APIs, repos)
- **Phase 2 (Week 2):** Data collection setup (OAuth, schedulers)
- **Phase 3 (Week 3):** API endpoints (basic endpoints, testing)
- **Phase 4 (Week 4):** Frontend (dashboard, forms)
- **Phase 5 (Weeks 5+):** Data accumulation & reflection

**No analysis until Month 2.**
**No big conclusions until Month 6.**
**Full value at Month 12.**

This is intentional. Be patient with the data.
