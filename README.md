# Sezi - Personal Life Reflection System

**Sezi** is a personal data aggregation and reflection system that collects health, calendar, and financial data to help you understand invisible patterns in your life.

> **Core Mission:** Make your life visible to yourself through observation, not control.

---

## What is Sezi?

Sezi collects data from multiple sources and stores it in a personal database, enabling you to:

- ✅ **Observe patterns** - See recurring behaviors across health, calendar, and spending
- ✅ **Reflect without judgment** - Weekly context logs help you understand what matters
- ✅ **Query your own data** - "Show me weeks with >10 meetings", "Compare sleep when traveling"
- ✅ **Stay accountable** - Collect automatically, reflect manually

**NOT a:**
- Fitness tracker (no optimization pressure)
- Productivity app (no gamification)
- Medical tool (no diagnosis claims)
- AI therapist (no interpretation)

---

## Technical Stack

- **Backend:** FastAPI (Python async)
- **Database:** PostgreSQL on Neon
- **Scheduling:** APScheduler (cron-based)
- **Data Collection:** Google Fit API
- **Notifications:** ntfy.sh
- **Deployment:** Render.com (free tier)
- **Cost:** $0/month

---

## Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL (local or Neon)
- Google Cloud project with Fit API enabled

### Installation

1. **Clone repository:**
   ```bash
   git clone https://github.com/ysferencakir/sezi.git
   cd sezi
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

5. **Run migrations (if needed):**
   ```bash
   # SQLAlchemy will auto-create tables on first run
   ```

6. **Start development server:**
   ```bash
   python main.py
   ```

   Visit: http://localhost:8000/docs (Swagger UI)

---

## Configuration

### .env Variables

```env
# Database (Neon or local PostgreSQL)
DATABASE_URL=postgresql+asyncpg://user:password@localhost/sezi

# Google OAuth (from console.cloud.google.com)
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback

# Notifications (optional)
NTFY_URL=https://ntfy.sh
NTFY_TOPIC=your_topic_name
NTFY_TOKEN=           # optional, for private topics

# App
APP_ENV=development
LOG_LEVEL=INFO
```

### Getting Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project
3. Enable "Fitness API"
4. Create OAuth 2.0 Client ID (Desktop Application)
5. Copy Client ID and Secret to .env

---

## API Endpoints

### Health Check
- `GET /health` - System health status

### Module Management
- `GET /modules` - List all registered modules
- `POST /modules/{name}/run` - Manually trigger a module

### Authentication
- `GET /auth/google/authorize` - Get OAuth authorization URL
- `GET /auth/google/callback` - OAuth callback handler

### Modules

#### Health Module
Collects daily health data from Google Fit:
- Steps, calories, active minutes, distance
- Heart rate readings
- Sleep sessions

**Schedule:**
- Daily sync: 07:00 UTC (yesterday's data)
- Morning report: 08:30 UTC (optional notification)

---

## Module Architecture

Sezi uses a **plugin-based module system**. Each module extends `BaseModule`:

```python
from core.base_module import BaseModule, Schedule

class MyModule(BaseModule):
    name = "my_module"
    description = "What this module does"
    
    def schedules(self) -> list[Schedule]:
        return [
            Schedule("job_id", "0 8 * * *", "run", "Description"),
        ]
    
    async def fetch(self) -> Any:
        """Fetch raw data from external source."""
        return {...}
    
    async def process(self, data: Any) -> Any:
        """Transform and store data."""
        return {...}
```

Modules are auto-discovered from `modules/` directory.

---

## Database Schema

### oauth_tokens
Stores OAuth refresh tokens for external APIs.

### health_days
Daily health aggregate from Google Fit:
- `day` (DATE, unique)
- `steps`, `calories`, `active_minutes`, `distance_meters`

### heart_rates
Raw heart rate data points.

### sleep_sessions
Sleep periods with duration and stage.

---

## Scheduled Jobs

Jobs are defined in each module's `schedules()` method. APScheduler runs them based on cron expressions:

```
"0 7 * * *"    = Every day at 07:00 UTC
"30 8 * * *"   = Every day at 08:30 UTC
"0 0 * * 0"    = Every Sunday at 00:00 UTC (cron format)
```

---

## Local Development

### Running Tests

```bash
# Unit tests (if added)
pytest tests/
```

### Debugging

Set `LOG_LEVEL=DEBUG` in .env for verbose output.

Watch logs:
```bash
tail -f logs/sezi.log  # if logging to file
```

### Manual Module Trigger

```bash
curl -X POST http://localhost:8000/modules/health/run
```

---

## Deployment

### Render.com (Recommended)

1. Connect GitHub repo to Render
2. Set build command: `pip install -r requirements.txt`
3. Set start command: `python main.py`
4. Set environment variables (DATABASE_URL, GOOGLE_CLIENT_ID, etc.)
5. Deploy

### Neon PostgreSQL

1. Create account at https://neon.tech
2. Create project "sezi-db"
3. Copy connection string to `DATABASE_URL`
4. Tables auto-create on first run

### GitHub Actions (Optional Backup)

Schedule daily data collection:

```yaml
name: Daily Health Sync
on:
  schedule:
    - cron: '0 6 * * *'
jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: python main.py
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          GOOGLE_CLIENT_ID: ${{ secrets.GOOGLE_CLIENT_ID }}
          GOOGLE_CLIENT_SECRET: ${{ secrets.GOOGLE_CLIENT_SECRET }}
```

---

## Obsession Prevention

Sezi has built-in guardrails:

- **Long windows:** Minimum 7 days analysis (prevents noise)
- **No real-time alerts:** Only daily/weekly/monthly reviews
- **Weekly checkpoint:** Manual context logging (5 min/week)
- **Month 1 check:** Is this curiosity or obsession?

---

## Troubleshooting

### "Google OAuth token not found"
- Run: `GET /auth/google/authorize`
- Authorize the app
- Wait for callback

### "No data appearing"
- Check: `GET /modules/health/run` response
- Verify Google credentials in .env
- Check database: `SELECT * FROM health_days;`

### "Database connection failed"
- Verify DATABASE_URL in .env
- Test connection: `psql $DATABASE_URL`
- For Neon: ensure IP is whitelisted

### "Scheduler not starting"
- Check logs for error messages
- Verify APScheduler dependencies
- Try restarting application

---

## Future Roadmap

### Phase 2 (Month 2+)
- [ ] Calendar module (Google Calendar API)
- [ ] Finance module (CSV upload)
- [ ] Context module (weekly reflection form)
- [ ] Query/filter endpoints
- [ ] React dashboard
- [ ] Email digest

### Phase 3 (Month 3+)
- [ ] Correlation detection
- [ ] Baseline calculations
- [ ] Monthly PDF reports
- [ ] Health Connect API integration (replace Google Fit)

---

## Ethical Principles

1. **Weak language only:** Never claim causation, only correlation
2. **User-led interpretation:** System shows data, user finds meaning
3. **No optimization pressure:** Variation is normal
4. **Observable, not prescriptive:** Mission is visibility, not control
5. **Long windows:** Prevent noise detection as signal

---

## License

MIT - See LICENSE file

---

## Contributing

This is a personal project. If you fork it:
1. Keep the ethical principles
2. Don't turn it into a commercial fitness tracker
3. Prioritize data privacy
4. Watch for obsession patterns

---

## Support

Issues? Questions?
- Check troubleshooting section
- Review logs
- Check Google Cloud credentials setup

---

**Last Updated:** May 2026  
**Status:** MVP - Data collection working, reflection features in development
