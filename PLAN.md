# SEZI Implementation Plan

**Status:** Planning Phase  
**Start Date:** May 14, 2026  
**Target Go-Live:** Week 4 (June 4, 2026)  
**Duration:** 4 weeks infrastructure, ongoing data collection  

---

## Executive Summary

Sezi is a personal life reflection system built on:
- **Data collection:** Health Connect, Google Calendar, Bank data (automated)
- **Backend:** FastAPI on Render.com (free)
- **Database:** PostgreSQL on Neon (free tier)
- **Frontend:** React on Vercel (free)
- **Scheduling:** GitHub Actions (free, 2000 min/month)
- **Domain:** ysferencakir.info.tr (existing)
- **Total Cost:** $0/month

Timeline: 4 weeks to MVP, then continuous data collection.

---

## Phase 1: Infrastructure Setup (Week 1)

### 1.1 GitHub Repository Setup

**Task:** Create private GitHub repo for Sezi project

```bash
# Local setup
mkdir ~/projects/sezi
cd ~/projects/sezi
git init
git remote add origin https://github.com/ysferencakir/sezi.git

# Create folder structure
mkdir backend frontend scripts database
mkdir -p backend/app backend/tests
mkdir -p frontend/src frontend/public
mkdir -p scripts/etl scripts/utils
mkdir -p database/migrations
```

**Files to create:**
- `README.md` - Project overview
- `.gitignore` - Standard Python + Node patterns
- `.env.example` - Template for secrets
- `LICENSE` - MIT or similar

**Checklist:**
- [ ] Repository created on GitHub
- [ ] Repository is PRIVATE
- [ ] Clone to local machine
- [ ] Folder structure created
- [ ] README written
- [ ] `.gitignore` added

---

### 1.2 Neon PostgreSQL Setup

**Task:** Create PostgreSQL database on Neon

**Steps:**
1. Go to https://neon.tech
2. Sign up with GitHub account
3. Create new project: `sezi-db`
4. Copy connection string: `postgres://[user]:[pass]@[host]/[db]`

**Database Schema:**

```sql
-- daily_health.sql
CREATE TABLE daily_health (
  id SERIAL PRIMARY KEY,
  date DATE NOT NULL UNIQUE,
  sleep_hours FLOAT,
  sleep_quality INT CHECK (sleep_quality >= 1 AND sleep_quality <= 10),
  avg_heart_rate INT,
  steps INT,
  workouts INT,
  recovery_score INT,
  notes TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_daily_health_date ON daily_health(date DESC);

-- daily_calendar.sql
CREATE TABLE daily_calendar (
  id SERIAL PRIMARY KEY,
  date DATE NOT NULL UNIQUE,
  meeting_count INT DEFAULT 0,
  meeting_minutes INT DEFAULT 0,
  free_consecutive_hours FLOAT,
  busiest_hour INT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_daily_calendar_date ON daily_calendar(date DESC);

-- weekly_context.sql
CREATE TABLE weekly_context (
  id SERIAL PRIMARY KEY,
  week_start DATE NOT NULL UNIQUE,
  notes TEXT,
  special_events TEXT,
  general_feeling INT CHECK (general_feeling >= 1 AND general_feeling <= 10),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_weekly_context_week_start ON weekly_context(week_start DESC);

-- daily_finance.sql
CREATE TABLE daily_finance (
  id SERIAL PRIMARY KEY,
  date DATE NOT NULL,
  amount FLOAT NOT NULL,
  category VARCHAR(100),
  description TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_daily_finance_date ON daily_finance(date DESC);
CREATE INDEX idx_daily_finance_category ON daily_finance(category);
```

**Checklist:**
- [ ] Neon account created
- [ ] Project `sezi-db` created
- [ ] Connection string saved (in `.env`)
- [ ] Schema tables created (run SQL above)
- [ ] Connections tested from local machine

---

### 1.3 Environment Variables Setup

**Task:** Create `.env` file with all credentials

```bash
# Create .env file (DO NOT commit to git)
cat > .env << EOF
# Database
DATABASE_URL=postgres://[user]:[pass]@[host]/sezi

# Health Connect (OAuth)
HEALTH_CONNECT_CLIENT_ID=xxxxx
HEALTH_CONNECT_CLIENT_SECRET=xxxxx
HEALTH_CONNECT_REDIRECT_URI=http://localhost:8000/auth/health-connect/callback

# Google Calendar (OAuth)
GOOGLE_CLIENT_ID=xxxxx
GOOGLE_CLIENT_SECRET=xxxxx
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback

# Google Form (Context Log)
GOOGLE_FORM_ID=xxxxx

# API Security
API_SECRET_KEY=xxxxx (generate with: openssl rand -hex 32)
FRONTEND_URL=https://ysferencakir.info.tr

# Environment
ENV=development
DEBUG=True
EOF
```

**Store in `.env.example` (without values):**
```bash
DATABASE_URL=
HEALTH_CONNECT_CLIENT_ID=
HEALTH_CONNECT_CLIENT_SECRET=
HEALTH_CONNECT_REDIRECT_URI=
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=
GOOGLE_FORM_ID=
API_SECRET_KEY=
FRONTEND_URL=
ENV=development
DEBUG=False
```

**Checklist:**
- [ ] `.env` file created locally
- [ ] `.env` added to `.gitignore`
- [ ] `.env.example` committed (without secrets)
- [ ] All credentials documented where to find them

---

## Phase 2: Backend Setup (Week 2)

### 2.1 FastAPI Project Setup

**Task:** Create FastAPI backend with basic structure

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install fastapi uvicorn psycopg2-binary python-dotenv pydantic
pip install google-auth-httplib2 google-auth-oauthlib google-api-python-client
pip freeze > requirements.txt
```

**Project Structure:**
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app
│   ├── config.py               # Settings from .env
│   ├── database.py             # DB connection
│   ├── models.py               # Pydantic models
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── health.py           # GET /health
│   │   ├── daily.py            # GET /api/daily
│   │   ├── weekly.py           # GET /api/week
│   │   ├── monthly.py          # GET /api/month
│   │   ├── context.py          # POST /api/context
│   │   └── auth.py             # OAuth callbacks
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── health.py
│   │   ├── calendar.py
│   │   └── context.py
│   └── utils/
│       ├── __init__.py
│       ├── db.py               # Query helpers
│       └── formatting.py       # Response formatting
├── tests/
│   ├── __init__.py
│   ├── test_routes.py
│   └── test_db.py
├── requirements.txt
└── .env (local only, not committed)
```

**Basic `app/main.py`:**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Sezi API",
    description="Personal life reflection system",
    version="0.1.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://ysferencakir.info.tr",
        "https://www.ysferencakir.info.tr"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "sezi-api",
        "version": "0.1.0"
    }

# Import routes
from app.routes import health, daily, weekly, monthly, context

app.include_router(health.router)
app.include_router(daily.router)
app.include_router(weekly.router)
app.include_router(monthly.router)
app.include_router(context.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
```

**Basic `app/database.py`:**

```python
import psycopg2
from psycopg2.extras import RealDictCursor
import os

def get_db_connection():
    """Get database connection"""
    try:
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        return conn
    except Exception as e:
        print(f"Database connection failed: {e}")
        raise

def query_db(sql, params=None):
    """Execute SELECT query"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute(sql, params or ())
        results = cur.fetchall()
        return [dict(row) for row in results]
    finally:
        cur.close()
        conn.close()

def execute_db(sql, params=None):
    """Execute INSERT/UPDATE/DELETE query"""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(sql, params or ())
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Database error: {e}")
        raise
    finally:
        cur.close()
        conn.close()
```

**Checklist:**
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] Basic FastAPI app runs locally
- [ ] `/health` endpoint responds
- [ ] Database connection works
- [ ] CORS configured for localhost + domain

---

### 2.2 API Routes Implementation

**Task:** Implement core API endpoints

**`app/routes/daily.py`:**

```python
from fastapi import APIRouter, Query
from datetime import datetime
from app.database import query_db

router = APIRouter(prefix="/api", tags=["daily"])

@router.get("/daily")
async def get_daily(date: str = Query(..., regex=r"\d{4}-\d{2}-\d{2}")):
    """
    Get daily metrics for specific date
    
    Example: /api/daily?date=2026-05-14
    """
    sql = """
    SELECT 
        h.date,
        h.sleep_hours,
        h.avg_heart_rate,
        h.steps,
        h.workouts,
        c.meeting_count,
        c.meeting_minutes,
        f.amount as total_spent
    FROM daily_health h
    LEFT JOIN daily_calendar c ON h.date = c.date
    LEFT JOIN (SELECT date, SUM(amount) as amount FROM daily_finance GROUP BY date) f ON h.date = f.date
    WHERE h.date = %s
    """
    
    result = query_db(sql, (date,))
    if not result:
        return {"date": date, "data": None, "message": "No data for this date"}
    
    return {"date": date, "data": result[0]}
```

**`app/routes/weekly.py`:**

```python
from fastapi import APIRouter
from datetime import datetime, timedelta
from app.database import query_db

router = APIRouter(prefix="/api", tags=["weekly"])

@router.get("/week")
async def get_week_summary():
    """Get last 7 days summary"""
    
    # Calculate date range (last 7 days including today)
    today = datetime.now().date()
    week_start = today - timedelta(days=6)
    
    sql = """
    SELECT 
        h.date,
        h.sleep_hours,
        h.avg_heart_rate,
        h.steps,
        c.meeting_count,
        f.total_spent
    FROM daily_health h
    LEFT JOIN daily_calendar c ON h.date = c.date
    LEFT JOIN (SELECT date, SUM(amount) as total_spent FROM daily_finance GROUP BY date) f ON h.date = f.date
    WHERE h.date >= %s AND h.date <= %s
    ORDER BY h.date DESC
    """
    
    daily_data = query_db(sql, (week_start, today))
    
    # Calculate aggregates (only from non-null values)
    sleep_values = [d['sleep_hours'] for d in daily_data if d['sleep_hours']]
    hr_values = [d['avg_heart_rate'] for d in daily_data if d['avg_heart_rate']]
    step_values = [d['steps'] for d in daily_data if d['steps']]
    meeting_values = [d['meeting_count'] for d in daily_data if d['meeting_count']]
    
    return {
        "period": f"{week_start} to {today}",
        "daily_metrics": daily_data,
        "summary": {
            "avg_sleep": round(sum(sleep_values) / len(sleep_values), 1) if sleep_values else None,
            "avg_heart_rate": round(sum(hr_values) / len(hr_values)) if hr_values else None,
            "total_steps": sum(step_values) if step_values else None,
            "total_meetings": sum(meeting_values) if meeting_values else None,
            "days_with_data": len(daily_data)
        }
    }
```

**`app/routes/monthly.py`:**

```python
from fastapi import APIRouter, Query
from datetime import datetime
from dateutil.relativedelta import relativedelta
from app.database import query_db

router = APIRouter(prefix="/api", tags=["monthly"])

@router.get("/month")
async def get_month_summary(month: str = Query(None, regex=r"\d{4}-\d{2}")):
    """
    Get monthly summary
    
    Example: /api/month?month=2026-05
    If month not provided, returns current month
    """
    
    if not month:
        month = datetime.now().strftime("%Y-%m")
    
    # Parse month
    month_date = datetime.strptime(month, "%Y-%m").date()
    month_start = month_date.replace(day=1)
    month_end = (month_date + relativedelta(months=1)) - timedelta(days=1)
    
    sql = """
    SELECT 
        h.date,
        h.sleep_hours,
        h.avg_heart_rate,
        h.steps,
        c.meeting_count,
        f.total_spent
    FROM daily_health h
    LEFT JOIN daily_calendar c ON h.date = c.date
    LEFT JOIN (SELECT date, SUM(amount) as total_spent FROM daily_finance GROUP BY date) f ON h.date = f.date
    WHERE h.date >= %s AND h.date <= %s
    ORDER BY h.date ASC
    """
    
    daily_data = query_db(sql, (month_start, month_end))
    
    # Get context notes for the month
    context_sql = """
    SELECT * FROM weekly_context
    WHERE week_start >= %s AND week_start <= %s
    ORDER BY week_start ASC
    """
    context_data = query_db(context_sql, (month_start, month_end))
    
    # Aggregates
    sleep_values = [d['sleep_hours'] for d in daily_data if d['sleep_hours']]
    hr_values = [d['avg_heart_rate'] for d in daily_data if d['avg_heart_rate']]
    
    return {
        "month": month,
        "period": f"{month_start} to {month_end}",
        "daily_metrics": daily_data,
        "weekly_context": context_data,
        "summary": {
            "avg_sleep": round(sum(sleep_values) / len(sleep_values), 1) if sleep_values else None,
            "avg_heart_rate": round(sum(hr_values) / len(hr_values)) if hr_values else None,
            "days_with_health_data": len([d for d in daily_data if d['sleep_hours']]),
            "total_days_in_month": len(daily_data)
        }
    }
```

**`app/routes/context.py`:**

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.database import query_db, execute_db
from datetime import datetime, timedelta, date

router = APIRouter(prefix="/api", tags=["context"])

class ContextEntry(BaseModel):
    week_start: str  # YYYY-MM-DD
    notes: str
    special_events: str = None
    general_feeling: int = None

@router.post("/context")
async def submit_context(entry: ContextEntry):
    """Submit weekly context notes"""
    
    try:
        sql = """
        INSERT INTO weekly_context (week_start, notes, special_events, general_feeling)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (week_start) DO UPDATE SET
            notes = EXCLUDED.notes,
            special_events = EXCLUDED.special_events,
            general_feeling = EXCLUDED.general_feeling,
            updated_at = CURRENT_TIMESTAMP
        """
        
        execute_db(sql, (
            entry.week_start,
            entry.notes,
            entry.special_events,
            entry.general_feeling
        ))
        
        return {
            "status": "success",
            "week_start": entry.week_start,
            "message": "Context saved successfully"
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/context")
async def get_context(week_start: str = None):
    """Get context notes for a week"""
    
    if not week_start:
        # Return last 4 weeks
        today = date.today()
        week_start = (today - timedelta(days=21)).isoformat()
    
    sql = """
    SELECT * FROM weekly_context
    WHERE week_start >= %s
    ORDER BY week_start DESC
    """
    
    results = query_db(sql, (week_start,))
    return {"context": results}
```

**Checklist:**
- [ ] All route files created
- [ ] Routes imported in `main.py`
- [ ] Local testing: `/api/week` returns data (or empty if no data)
- [ ] Local testing: `/api/daily?date=2026-05-14`
- [ ] Local testing: `/api/month?month=2026-05`
- [ ] Local testing: POST `/api/context`

---

### 2.3 Render.com Deployment

**Task:** Deploy FastAPI backend to Render.com

**Steps:**

1. **Create Render account:**
   - Go to https://render.com
   - Sign in with GitHub

2. **Create PostgreSQL connection (backup):**
   - (Skip if using Neon — Neon will provide connection string)

3. **Create Web Service:**
   - Go to Dashboard → New → Web Service
   - Connect GitHub repo (sezi)
   - Select repository
   - Set Build Command: `pip install -r backend/requirements.txt`
   - Set Start Command: `cd backend && uvicorn app.main:app --host 0.0.0.0`
   - Set Environment:
     ```
     DATABASE_URL = [from Neon]
     HEALTH_CONNECT_CLIENT_ID = [placeholder]
     HEALTH_CONNECT_CLIENT_SECRET = [placeholder]
     GOOGLE_CLIENT_ID = [placeholder]
     GOOGLE_CLIENT_SECRET = [placeholder]
     FRONTEND_URL = https://ysferencakir.info.tr
     ```
   - Deploy

4. **Verify deployment:**
   - Wait for build (2-3 minutes)
   - Visit https://sezi-api.onrender.com/health
   - Should see: `{"status":"ok","service":"sezi-api","version":"0.1.0"}`

**Checklist:**
- [ ] Render account created
- [ ] Web Service created and connected to GitHub
- [ ] Environment variables set
- [ ] Build successful
- [ ] `/health` endpoint responds
- [ ] Database connection works from Render
- [ ] Record API URL: `https://[your-service].onrender.com`

---

## Phase 3: Data Collection Setup (Week 2-3)

### 3.1 GitHub Actions Workflow

**Task:** Create automated daily data collection

**File:** `.github/workflows/daily-collect.yml`

```yaml
name: Daily Data Collection

on:
  schedule:
    # Run daily at 06:00 UTC (13:00 Turkey time)
    - cron: '0 6 * * *'
  workflow_dispatch:  # Manual trigger

jobs:
  collect:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd scripts
          pip install -r requirements.txt
      
      - name: Run data collection
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          HEALTH_CONNECT_CLIENT_ID: ${{ secrets.HEALTH_CONNECT_CLIENT_ID }}
          HEALTH_CONNECT_CLIENT_SECRET: ${{ secrets.HEALTH_CONNECT_CLIENT_SECRET }}
          GOOGLE_CLIENT_ID: ${{ secrets.GOOGLE_CLIENT_ID }}
          GOOGLE_CLIENT_SECRET: ${{ secrets.GOOGLE_CLIENT_SECRET }}
        run: |
          cd scripts
          python etl_main.py
      
      - name: Report results
        if: always()
        run: echo "Data collection completed at $(date)"
```

**GitHub Secrets Setup:**
1. Go to GitHub repo → Settings → Secrets and variables → Actions
2. Add secrets:
   - `DATABASE_URL`
   - `HEALTH_CONNECT_CLIENT_ID`
   - `HEALTH_CONNECT_CLIENT_SECRET`
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`

**Checklist:**
- [ ] Workflow file created
- [ ] GitHub secrets configured
- [ ] Workflow tested manually
- [ ] Logs show successful run

---

### 3.2 Health Connect API Setup

**Task:** Set up OAuth 2.0 for Health Connect

**Process:**
1. Register app with Google Cloud Project
2. Get OAuth credentials
3. Implement token refresh logic
4. Store refresh tokens securely

**File:** `scripts/integrations/health_connect.py`

```python
import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv()

class HealthConnectClient:
    def __init__(self):
        self.client_id = os.getenv('HEALTH_CONNECT_CLIENT_ID')
        self.client_secret = os.getenv('HEALTH_CONNECT_CLIENT_SECRET')
        self.redirect_uri = "http://localhost:8000/auth/health-connect/callback"
        self.token_file = "tokens/health_connect_token.json"
        
    def get_access_token(self):
        """Get fresh access token using refresh token"""
        if os.path.exists(self.token_file):
            with open(self.token_file, 'r') as f:
                token_data = json.load(f)
                if token_data['expires_at'] > datetime.now().timestamp():
                    return token_data['access_token']
                else:
                    return self.refresh_token(token_data['refresh_token'])
        else:
            raise Exception("No token found. Need to authenticate first.")
    
    def refresh_token(self, refresh_token):
        """Refresh access token"""
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        response = requests.post('https://oauth2.googleapis.com/token', data=data)
        token_data = response.json()
        
        # Save new token
        token_data['expires_at'] = datetime.now().timestamp() + token_data['expires_in']
        os.makedirs('tokens', exist_ok=True)
        with open(self.token_file, 'w') as f:
            json.dump(token_data, f)
        
        return token_data['access_token']
    
    def get_sleep_data(self, date):
        """Get sleep data for a specific date from Health Connect"""
        access_token = self.get_access_token()
        
        # Health Connect API endpoint (example)
        headers = {'Authorization': f'Bearer {access_token}'}
        params = {'date': date.isoformat()}
        
        # Call health connect API
        # (implementation depends on Health Connect API documentation)
        
        return {}  # Return formatted sleep data
    
    def get_heart_rate_data(self, date):
        """Get heart rate data for a specific date"""
        # Similar to above
        return {}
    
    def get_steps_data(self, date):
        """Get steps data for a specific date"""
        # Similar to above
        return {}
```

**Checklist:**
- [ ] OAuth credentials obtained from Google Cloud
- [ ] `health_connect.py` created
- [ ] Token refresh logic implemented
- [ ] Test data retrieval
- [ ] Tokens stored securely (not in git)

---

### 3.3 Google Calendar API Setup

**Task:** Set up OAuth 2.0 for Google Calendar

**File:** `scripts/integrations/google_calendar.py`

```python
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from google.auth.oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os
from datetime import datetime, timedelta

class GoogleCalendarClient:
    SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
    
    def __init__(self):
        self.service = self.build_service()
    
    def build_service(self):
        """Build Google Calendar service"""
        creds = None
        
        # Load from saved token
        if os.path.exists('tokens/google_calendar_token.json'):
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            creds = Credentials.from_authorized_user_file('tokens/google_calendar_token.json', self.SCOPES)
        
        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials
            os.makedirs('tokens', exist_ok=True)
            with open('tokens/google_calendar_token.json', 'w') as token:
                token.write(creds.to_json())
        
        return build('calendar', 'v3', credentials=creds)
    
    def get_daily_meetings(self, date):
        """Get all meetings for a specific date"""
        start_of_day = datetime.combine(date, datetime.min.time()).isoformat() + 'Z'
        end_of_day = datetime.combine(date + timedelta(days=1), datetime.min.time()).isoformat() + 'Z'
        
        events = self.service.events().list(
            calendarId='primary',
            timeMin=start_of_day,
            timeMax=end_of_day,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        meetings = events.get('items', [])
        
        # Calculate metrics
        meeting_count = len(meetings)
        meeting_minutes = 0
        free_blocks = []
        busiest_hour = None
        
        for event in meetings:
            start = datetime.fromisoformat(event['start']['dateTime'].replace('Z', '+00:00'))
            end = datetime.fromisoformat(event['end']['dateTime'].replace('Z', '+00:00'))
            meeting_minutes += int((end - start).total_seconds() / 60)
            
            if not busiest_hour:
                busiest_hour = start.hour
        
        return {
            'meeting_count': meeting_count,
            'meeting_minutes': meeting_minutes,
            'busiest_hour': busiest_hour
        }
```

**Checklist:**
- [ ] Google Calendar OAuth credentials obtained
- [ ] `google_calendar.py` created
- [ ] Token storage implemented
- [ ] Test meeting retrieval
- [ ] Verify meeting count calculation

---

### 3.4 ETL Main Script

**Task:** Create main orchestration script

**File:** `scripts/etl_main.py`

```python
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import psycopg2
from integrations.health_connect import HealthConnectClient
from integrations.google_calendar import GoogleCalendarClient

load_dotenv()

def log(message):
    """Print timestamped message"""
    print(f"[{datetime.now().isoformat()}] {message}")

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(os.getenv('DATABASE_URL'))

def collect_yesterday_data():
    """Collect data for yesterday (gives time for systems to sync)"""
    
    log("Starting data collection")
    
    yesterday = datetime.now().date() - timedelta(days=1)
    log(f"Collecting data for {yesterday}")
    
    try:
        # Initialize clients
        health = HealthConnectClient()
        calendar = GoogleCalendarClient()
        
        # Collect Health Connect data
        log("Fetching Health Connect data...")
        sleep_data = health.get_sleep_data(yesterday)
        hr_data = health.get_heart_rate_data(yesterday)
        steps_data = health.get_steps_data(yesterday)
        
        # Collect Google Calendar data
        log("Fetching Google Calendar data...")
        calendar_data = calendar.get_daily_meetings(yesterday)
        
        # Save to database
        log("Saving to database...")
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Insert health data
        if sleep_data or hr_data or steps_data:
            cur.execute("""
                INSERT INTO daily_health (date, sleep_hours, avg_heart_rate, steps)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (date) DO UPDATE SET
                    sleep_hours = EXCLUDED.sleep_hours,
                    avg_heart_rate = EXCLUDED.avg_heart_rate,
                    steps = EXCLUDED.steps
            """, (
                yesterday,
                sleep_data.get('sleep_hours'),
                hr_data.get('avg_heart_rate'),
                steps_data.get('steps')
            ))
        
        # Insert calendar data
        if calendar_data:
            cur.execute("""
                INSERT INTO daily_calendar (date, meeting_count, meeting_minutes, busiest_hour)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (date) DO UPDATE SET
                    meeting_count = EXCLUDED.meeting_count,
                    meeting_minutes = EXCLUDED.meeting_minutes,
                    busiest_hour = EXCLUDED.busiest_hour
            """, (
                yesterday,
                calendar_data['meeting_count'],
                calendar_data['meeting_minutes'],
                calendar_data['busiest_hour']
            ))
        
        conn.commit()
        cur.close()
        conn.close()
        
        log(f"Data collection successful for {yesterday}")
        return True
    
    except Exception as e:
        log(f"ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    success = collect_yesterday_data()
    exit(0 if success else 1)
```

**Checklist:**
- [ ] ETL script created
- [ ] All integrations imported
- [ ] Test run locally
- [ ] Verify data inserted to database
- [ ] Error handling implemented

---

## Phase 4: Frontend Setup (Week 3-4)

### 4.1 React Project Creation

**Task:** Create React frontend

```bash
# Create React app
npx create-react-app frontend

cd frontend

# Install dependencies
npm install react-router-dom recharts axios dotenv

# Create folder structure
mkdir src/pages src/components src/services src/utils
mkdir src/styles
```

**`.env.local` (local development):**
```
REACT_APP_API_URL=http://localhost:8000
REACT_APP_DOMAIN=ysferencakir.info.tr
```

**Checklist:**
- [ ] React app created
- [ ] Dependencies installed
- [ ] Folder structure created
- [ ] `.env.local` configured
- [ ] App runs on localhost:3000

---

### 4.2 API Service

**File:** `src/services/api.js`

```javascript
const API_URL = process.env.REACT_APP_API_URL || 'https://api.sezi.onrender.com';

export const apiService = {
  async getWeekSummary() {
    const response = await fetch(`${API_URL}/api/week`);
    return response.json();
  },

  async getDaily(date) {
    const response = await fetch(`${API_URL}/api/daily?date=${date}`);
    return response.json();
  },

  async getMonth(month) {
    const response = await fetch(`${API_URL}/api/month?month=${month}`);
    return response.json();
  },

  async submitContext(weekStart, notes, specialEvents, feeling) {
    const response = await fetch(`${API_URL}/api/context`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        week_start: weekStart,
        notes: notes,
        special_events: specialEvents,
        general_feeling: feeling
      })
    });
    return response.json();
  },

  async getContext(weekStart = null) {
    const url = weekStart 
      ? `${API_URL}/api/context?week_start=${weekStart}`
      : `${API_URL}/api/context`;
    const response = await fetch(url);
    return response.json();
  }
};
```

**Checklist:**
- [ ] API service created
- [ ] All endpoints have methods
- [ ] Error handling added
- [ ] CORS tested with local API

---

### 4.3 Dashboard Pages

**File:** `src/pages/Dashboard.jsx`

```javascript
import React, { useState, useEffect } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { apiService } from '../services/api';

export default function Dashboard() {
  const [weekData, setWeekData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchWeekData();
  }, []);

  const fetchWeekData = async () => {
    try {
      setLoading(true);
      const data = await apiService.getWeekSummary();
      setWeekData(data);
      setError(null);
    } catch (err) {
      setError('Failed to load weekly data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="loading">Loading...</div>;
  if (error) return <div className="error">{error}</div>;
  if (!weekData) return <div>No data available</div>;

  const { summary, daily_metrics } = weekData;

  return (
    <div className="dashboard">
      <h1>Sezi Weekly Summary</h1>
      
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-value">{summary.avg_sleep}</div>
          <div className="metric-label">Avg Sleep (hours)</div>
        </div>
        <div className="metric-card">
          <div className="metric-value">{summary.avg_heart_rate}</div>
          <div className="metric-label">Avg Heart Rate</div>
        </div>
        <div className="metric-card">
          <div className="metric-value">{(summary.total_steps / 1000).toFixed(1)}k</div>
          <div className="metric-label">Total Steps</div>
        </div>
        <div className="metric-card">
          <div className="metric-value">{summary.total_meetings}</div>
          <div className="metric-label">Total Meetings</div>
        </div>
      </div>

      <div className="charts">
        <div className="chart-container">
          <h3>Sleep & Heart Rate Trend</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={daily_metrics}>
              <CartesianGrid />
              <XAxis dataKey="date" />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
              <Tooltip />
              <Legend />
              <Line yAxisId="left" type="monotone" dataKey="sleep_hours" stroke="#8884d8" />
              <Line yAxisId="right" type="monotone" dataKey="avg_heart_rate" stroke="#82ca9d" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-container">
          <h3>Daily Activity</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={daily_metrics}>
              <CartesianGrid />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="steps" fill="#8884d8" />
              <Bar dataKey="meeting_count" fill="#82ca9d" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
```

**File:** `src/pages/Monthly.jsx`

```javascript
import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';

export default function Monthly() {
  const [monthData, setMonthData] = useState(null);
  const [month, setMonth] = useState(new Date().toISOString().slice(0, 7));

  useEffect(() => {
    fetchMonthData();
  }, [month]);

  const fetchMonthData = async () => {
    try {
      const data = await apiService.getMonth(month);
      setMonthData(data);
    } catch (err) {
      console.error('Failed to load monthly data:', err);
    }
  };

  if (!monthData) return <div>Loading...</div>;

  return (
    <div className="monthly">
      <h1>Monthly Summary: {month}</h1>
      
      <input 
        type="month" 
        value={month} 
        onChange={(e) => setMonth(e.target.value)}
      />

      <div className="summary">
        <p><strong>Avg Sleep:</strong> {monthData.summary.avg_sleep} hours</p>
        <p><strong>Avg Heart Rate:</strong> {monthData.summary.avg_heart_rate} bpm</p>
        <p><strong>Days with data:</strong> {monthData.summary.days_with_health_data}</p>
      </div>

      <h3>Weekly Context</h3>
      <div className="context-list">
        {monthData.weekly_context.map((week) => (
          <div key={week.id} className="context-card">
            <strong>{week.week_start}</strong>
            <p>{week.notes}</p>
            {week.special_events && <p><em>Events: {week.special_events}</em></p>}
            {week.general_feeling && <p>Feeling: {week.general_feeling}/10</p>}
          </div>
        ))}
      </div>
    </div>
  );
}
```

**File:** `src/pages/Context.jsx`

```javascript
import React, { useState } from 'react';
import { apiService } from '../services/api';

export default function Context() {
  const [formData, setFormData] = useState({
    week_start: new Date().toISOString().slice(0, 10),
    notes: '',
    special_events: '',
    general_feeling: 5
  });
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await apiService.submitContext(
        formData.week_start,
        formData.notes,
        formData.special_events,
        formData.general_feeling
      );
      setSubmitted(true);
      setTimeout(() => setSubmitted(false), 3000);
      setFormData({ week_start: new Date().toISOString().slice(0, 10), notes: '', special_events: '', general_feeling: 5 });
    } catch (err) {
      console.error('Failed to submit:', err);
    }
  };

  return (
    <div className="context-form">
      <h1>Weekly Context</h1>
      {submitted && <div className="success-message">Context saved!</div>}
      
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Week Start Date:</label>
          <input 
            type="date" 
            value={formData.week_start}
            onChange={(e) => setFormData({...formData, week_start: e.target.value})}
          />
        </div>

        <div className="form-group">
          <label>What happened this week?</label>
          <textarea
            value={formData.notes}
            onChange={(e) => setFormData({...formData, notes: e.target.value})}
            placeholder="Brief notes about this week..."
            rows="5"
          />
        </div>

        <div className="form-group">
          <label>Special Events:</label>
          <input
            type="text"
            value={formData.special_events}
            onChange={(e) => setFormData({...formData, special_events: e.target.value})}
            placeholder="Exam, illness, move, stress, etc."
          />
        </div>

        <div className="form-group">
          <label>General Feeling (1-10):</label>
          <input
            type="range"
            min="1"
            max="10"
            value={formData.general_feeling}
            onChange={(e) => setFormData({...formData, general_feeling: parseInt(e.target.value)})}
          />
          <span>{formData.general_feeling}/10</span>
        </div>

        <button type="submit">Save Context</button>
      </form>
    </div>
  );
}
```

**Checklist:**
- [ ] Dashboard page created and tested
- [ ] Monthly page created and tested
- [ ] Context form created and tested
- [ ] API calls working
- [ ] Charts rendering correctly

---

### 4.4 App Router & Styling

**File:** `src/App.jsx`

```javascript
import React from 'react';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Monthly from './pages/Monthly';
import Context from './pages/Context';
import './App.css';

function App() {
  return (
    <BrowserRouter>
      <div className="App">
        <nav className="navbar">
          <div className="nav-brand">Sezi</div>
          <ul className="nav-links">
            <li><Link to="/">Dashboard</Link></li>
            <li><Link to="/month">Monthly</Link></li>
            <li><Link to="/context">Context</Link></li>
          </ul>
        </nav>

        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/month" element={<Monthly />} />
            <Route path="/context" element={<Context />} />
          </Routes>
        </main>

        <footer className="footer">
          <p>Sezi v0.1.0 - Personal Life Reflection System</p>
        </footer>
      </div>
    </BrowserRouter>
  );
}

export default App;
```

**File:** `src/App.css` (minimal styling)

```css
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', sans-serif;
  background-color: #f5f5f5;
  color: #333;
}

.App {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.navbar {
  background-color: #fff;
  border-bottom: 1px solid #e0e0e0;
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.nav-brand {
  font-size: 1.5rem;
  font-weight: bold;
  color: #333;
}

.nav-links {
  display: flex;
  list-style: none;
  gap: 2rem;
}

.nav-links a {
  text-decoration: none;
  color: #666;
  transition: color 0.3s;
}

.nav-links a:hover {
  color: #333;
}

.main-content {
  flex: 1;
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin: 2rem 0;
}

.metric-card {
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  text-align: center;
}

.metric-value {
  font-size: 2rem;
  font-weight: bold;
  color: #2c3e50;
}

.metric-label {
  font-size: 0.9rem;
  color: #7f8c8d;
  margin-top: 0.5rem;
}

.charts {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 2rem;
  margin: 2rem 0;
}

.chart-container {
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.chart-container h3 {
  margin-bottom: 1rem;
  color: #2c3e50;
}

.context-form {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  max-width: 600px;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #2c3e50;
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  font-family: inherit;
  font-size: 1rem;
}

.form-group button {
  background-color: #2c3e50;
  color: white;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
}

.form-group button:hover {
  background-color: #34495e;
}

.success-message {
  background-color: #d4edda;
  color: #155724;
  padding: 1rem;
  border-radius: 4px;
  margin-bottom: 1rem;
}

.footer {
  background-color: #f5f5f5;
  padding: 2rem;
  text-align: center;
  color: #7f8c8d;
  border-top: 1px solid #e0e0e0;
}

.loading, .error {
  padding: 2rem;
  text-align: center;
}

.error {
  color: #c0392b;
}
```

**Checklist:**
- [ ] Router setup completed
- [ ] All pages integrated
- [ ] Navigation working
- [ ] Styling applied
- [ ] App runs locally on localhost:3000

---

### 4.5 Vercel Deployment

**Task:** Deploy React frontend to Vercel

**Steps:**

1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Initial frontend setup"
   git push origin main
   ```

2. **Deploy on Vercel:**
   - Go to https://vercel.com
   - Sign in with GitHub
   - Click "New Project"
   - Select `sezi` repository
   - Set root directory: `frontend`
   - Set build command: `npm run build`
   - Set output directory: `build`
   - Environment variables:
     ```
     REACT_APP_API_URL=https://api.sezi.onrender.com
     REACT_APP_DOMAIN=ysferencakir.info.tr
     ```
   - Deploy

3. **Add Custom Domain:**
   - In Vercel project settings → Domains
   - Add `ysferencakir.info.tr`
   - Follow DNS setup (Vercel will provide CNAME)

4. **Verify deployment:**
   - Visit https://ysferencakir.info.tr
   - Dashboard should load
   - Click through pages
   - Verify API calls work

**Checklist:**
- [ ] Frontend pushed to GitHub
- [ ] Vercel project created and deployed
- [ ] Custom domain configured
- [ ] DNS updated (may take 5-30 minutes)
- [ ] Site accessible at ysferencakir.info.tr
- [ ] All pages working
- [ ] API calls successful

---

## Phase 5: Data Accumulation & Testing (Week 4+)

### 5.1 Daily Operations

**What happens:**
1. GitHub Actions runs daily at 06:00 UTC
2. Python ETL script collects yesterday's data
3. Data inserted into Neon PostgreSQL
4. Dashboard updates automatically
5. You check dashboard weekly (not daily!)

**Manual Weekly Task (5 minutes):**
- Every Sunday evening: Submit context form
- What happened?
- Special events?
- General feeling?

---

### 5.2 Obsession Checkpoints

**Week 4 Checkpoint:**
- Question: How often are you checking the dashboard?
- Expected: 1-2 times per week
- Red flag: Multiple times per day
- Action: If too frequent, set a reminder to check only Sundays

**Week 8 Checkpoint:**
- Question: Does tracking feel like curiosity or obligation?
- Expected: "Interesting to see what patterns emerge"
- Red flag: "Feel anxious if I don't check"
- Action: Take 1-2 weeks off, see if you feel relief or missing something

**Week 12 Checkpoint:**
- Question: Have you learned anything meaningful?
- Expected: "I notice X correlates with Y", "Baseline is Z"
- Red flag: Only accumulating data, no insights
- Action: Review data manually, look for patterns, or consider next steps

---

### 5.3 First Month Expectations

**What should happen:**
- ✅ Data collecting smoothly
- ✅ No breaks in collection
- ✅ Dashboard loading data
- ✅ Context notes saved
- ✅ No obsession detected

**What should NOT happen:**
- ❌ Major optimizations based on data
- ❌ Checking dashboard daily
- ❌ Anxiety about missing a day
- ❌ Trying to "fix" patterns

**Goal:** Smooth operation, data accumulation, gentle reflection.

---

## Timeline Summary

```
Week 1 (May 14-20): Infrastructure
├─ GitHub repo setup
├─ Neon PostgreSQL setup
├─ Environment variables
└─ Render account created

Week 2 (May 21-27): Backend
├─ FastAPI app creation
├─ API routes implemented
├─ Render deployment
└─ Test endpoints

Week 2-3 (May 21-June 3): Data Collection Setup
├─ GitHub Actions workflow
├─ Health Connect API integration
├─ Google Calendar API integration
├─ ETL script creation
└─ First test run

Week 3-4 (May 28-June 10): Frontend
├─ React app creation
├─ API service
├─ Dashboard page
├─ Monthly & Context pages
├─ Routing & styling
└─ Vercel deployment

Week 4+ (June 4+): Operations
├─ Daily GitHub Actions runs
├─ Weekly context submissions
├─ Obsession checkpoints
└─ Data accumulation
```

---

## Cost Breakdown

```
Service             Tier       Monthly Cost
─────────────────────────────────────────
Neon PostgreSQL     Free       $0
GitHub Actions      Free       $0 (2000 min/mo)
Render API          Free       $0 (sleeps after 15min idle)
Vercel Frontend     Free       $0
Domain              Existing   $0 (already owned)
─────────────────────────────────────────
TOTAL                          $0/month
```

---

## Success Criteria (Go/No-Go)

### Phase 1 - Pass if:
- [ ] GitHub repo created and structure set up
- [ ] Neon database created with schema
- [ ] Environment variables documented

### Phase 2 - Pass if:
- [ ] FastAPI app runs locally
- [ ] All endpoints respond
- [ ] Deployed to Render without errors

### Phase 3 - Pass if:
- [ ] OAuth setup complete for Health Connect & Calendar
- [ ] GitHub Actions workflow executes without error
- [ ] Data successfully inserted into database

### Phase 4 - Pass if:
- [ ] React app runs locally
- [ ] All pages accessible and rendering
- [ ] Dashboard loads data from API
- [ ] Deployed to Vercel
- [ ] ysferencakir.info.tr accessible

### Phase 5 - Pass if:
- [ ] 4 weeks of continuous data collection
- [ ] No obsession detected
- [ ] At least 1-2 patterns noticed
- [ ] Dashboard useful for reflection

---

## Troubleshooting Reference

**"API returns CORS error"**
- Check CORS middleware in FastAPI includes your domain
- Verify `FRONTEND_URL` environment variable
- Test with `curl` from different origins

**"No data appearing in dashboard"**
- Check GitHub Actions logs for collection errors
- Verify API endpoint returns data: `curl https://api.sezi.onrender.com/api/week`
- Check database has records: Login to Neon console

**"Health Connect data not syncing"**
- Verify refresh token is valid
- Check token file exists and not expired
- Re-authorize if needed

**"Dashboard very slow"**
- Check if querying too much data (limit to 90 days)
- Verify API response time (should be <1 second)
- Check Render CPU/memory usage

---

## Next Steps After MVP

Once MVP is stable (4 weeks):

1. **Weekly email digest** (automated)
2. **Monthly PDF report** (generated)
3. **Bank CSV auto-upload** (S3 or manual)
4. **Advanced queries** (date range, filtering)
5. **Baseline calculations** (mean, std dev)
6. **Correlation detection** (automated weak hypothesis)

But not before 4 weeks. Be patient with data.

---

## Final Notes

- **This is personal.** Don't optimize prematurely.
- **Data quality > quantity.** 4 sources done right beats 20 sources half-done.
- **Reflection takes time.** Real insights emerge month 3-6.
- **Stay humble.** Correlations are not causations.
- **Watch yourself.** The obsession risk is real.

Let the system breathe. The data will tell you what's useful.

Good luck. Start Week 1 Monday.
