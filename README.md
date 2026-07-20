# Sezi - Personal Life Reflection System

**Sezi** is a personal data aggregation and reflection system that collects health, calendar, financial, and habit data to help you understand invisible patterns in your life.

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
- **Database:** PostgreSQL (Neon), schema managed via **Alembic**
- **Scheduling:** APScheduler (cron-based, Europe/Istanbul)
- **Data Collection:** Google Fit, Google Calendar, Health Connect (Android bridge), Spotify, Strava,
  Open-Meteo, Frankfurter, TCMB EVDS, altinapi.com, Yahoo Finance, TEFAS, EPİAŞ, Etkinlik.io, TMDB,
  ESHOT (İzmir transit) — see [Modules](#modules) below for the full list
- **Notifications:** Telegram bot (also used for manual data entry — `/sigara`, `/izledim`, `/context`), plus ntfy.sh fallback
- **Frontend:** Vanilla PWA served by FastAPI (`static/`)
- **Testing:** pytest + pytest-asyncio + respx (`requirements-dev.txt`), runs on every push/PR (`.github/workflows/test.yml`)
- **Deployment:** Self-hosted VPS, GitHub Actions SSH auto-deploy on push to `main` (see `DEPLOYMENT.md`)

---

## Quick Start

### Prerequisites

- Python 3.12 (see `.python-version` / `runtime.txt`)
- PostgreSQL (Neon recommended — the app strips `?sslmode=require` and adds `ssl=require` to
  `connect_args` automatically for `neon.tech` hosts)

### Installation

1. **Clone repository:**
   ```bash
   git clone https://github.com/ysferencakir/sezi.git
   cd sezi
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   # for local development (tests):
   pip install -r requirements-dev.txt
   ```

4. **Set up environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials — see Configuration below
   ```

5. **Run migrations:**

   ```bash
   alembic upgrade head
   ```

   On a brand-new empty database `python main.py` also auto-creates tables (`create_tables()`),
   but schema changes (new column/table) are tracked via Alembic migrations — when adding a new
   module/field, run `alembic revision --autogenerate -m "..."`, **review** the generated file in
   `alembic/versions/`, then commit it alongside your model change.

6. **Start development server:**
   ```bash
   python main.py
   ```

   Visit: `http://localhost:8000/docs` (Swagger UI) or `http://localhost:8000/` (dashboard)

7. **Run tests:**
   ```bash
   pytest -v
   ```

---

## Configuration

Every module degrades gracefully when its credentials are missing — it logs a warning and
skips its scheduled sync rather than crashing, so you don't need to configure everything at once.
Copy `.env.example` to `.env` and fill in only what you need. Grouped overview:

| Group | Variables | Notes |
| --- | --- | --- |
| Core | `DATABASE_URL`, `APP_ENV`, `LOG_LEVEL` | Required |
| Notifications | `NTFY_URL`, `NTFY_TOPIC`, `NTFY_TOKEN`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | Both optional but at least one recommended for job-failure alerts |
| Google OAuth | `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI` | Fit + Calendar |
| Spotify OAuth | `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, `SPOTIFY_REDIRECT_URI` | |
| Strava OAuth | `STRAVA_CLIENT_ID`, `STRAVA_CLIENT_SECRET`, `STRAVA_REDIRECT_URI` | Requires an active Strava subscription to create an app (2026) |
| Notion | `NOTION_TOKEN`, `NOTION_DATABASE_ID` | Internal integration token, not OAuth |
| Health Connect bridge | `HEALTH_INGEST_TOKEN` | Shared secret for `POST /api/health/ingest`; endpoint returns 503 if unset |
| Admin endpoints | `ADMIN_TOKEN` | Shared secret for `POST /modules/{name}/run` and `/trigger/{job_id}`; 503 if unset. **Not used by the dashboard UI** |
| Gold | `ALTINAPI_KEY` | altinapi.com, free tier |
| Stocks | `STOCKS_WATCHLIST` | Comma-separated `.IS`-suffixed Yahoo Finance symbols |
| TEFAS | `TEFAS_WATCHLIST` | Comma-separated fund codes, no auth needed |
| TCMB EVDS | `EVDS_API_KEY` | Free self-serve registration |
| Bank (Kobaküs) | `KOBAKUS_FIRM_CODE`, `KOBAKUS_PASSWORD`, `KOBAKUS_CHANNEL_CODE` | **Postponed** — see [Modules](#modules) |
| Barcode (camgoz.net) | `CAMGOZ_API_BASE`, `CAMGOZ_API_KEY` | Requires a JoJ API Marketplace gateway URL — see module note |
| Energy (EPİAŞ) | `EPIAS_USERNAME`, `EPIAS_PASSWORD`, `EPIAS_CITY_ID` | Individual-account access unverified |
| Events | `ETKINLIK_CITY` | Client-side keyword filter, no auth needed |
| Watchlog (TMDB) | `TMDB_API_KEY` | Free self-serve registration |
| ScraperAPI | `SCRAPERAPI_KEY` | Only needed if the transit scraper runs from a datacenter IP that eshot.gov.tr blocks |

See `.env.example` for the exact variable names, defaults, and inline notes on where to get each key.

### Getting Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project
3. Enable "Fitness API" and "Calendar API"
4. Create OAuth 2.0 Client ID (Web Application), add the redirect URI from `.env`
5. Copy Client ID and Secret to `.env`

---

## API Endpoints

### Health Check & Modules

- `GET /health` — system status
- `GET /modules` — list all registered modules (name, description, schedule count)
- `POST /modules/{name}/run` 🔒 — manually run a module's full `fetch()+process()` cycle
- `POST /modules/{name}/trigger/{job_id}` 🔒 — manually run one specific scheduled job

🔒 = requires `X-Admin-Token` header matching `ADMIN_TOKEN` (503 if `ADMIN_TOKEN` unset).

### OAuth

- `GET /auth/{google,spotify,strava}/authorize` — get the provider's authorization URL
- `GET /auth/{google,spotify,strava}/callback` — OAuth callback, stores the token

### Dashboard data (read-only, used by `static/index.html`)

- `GET /api/summary` — latest snapshot across every module
- `GET /api/history?days=N` — daily time series for trend charts
- `GET /api/health/heart-rate?hours=N` — raw heart rate samples
- `GET /api/health/records?days=N&category=&record_type=` — filterable Health Connect record browser
- `GET /api/spotify/recent?limit=N`
- `GET /api/calendar/categories?days=N`

### Writes

- `POST /api/context` — submit/update a weekly reflection note
- `GET /api/context?week_start=` — list reflection notes
- `POST /api/health/ingest` 🔒 (`X-Ingest-Token`) — Health Connect bridge app pushes raw records here

### Other

- `GET /api/barcode/{code}` — product/price lookup via camgoz.net (currently non-functional, see Modules)

---

## Modules

Sezi uses a **plugin-based module system** — every module extends `BaseModule` and is
auto-discovered from the `modules/` directory (`core/module_loader.py`). 18 modules are registered:

| Module | What it does | Status |
| --- | --- | --- |
| `health` | Google Fit: steps, calories, sleep, heart rate | ✅ |
| `calendar` | Google Calendar: meeting stats, categories, holidays | ✅ |
| `context` | Weekly reflection notes (web form + Telegram `/context`) | ✅ |
| `currency` | Frankfurter (ECB): USD/EUR/GBP/CHF → TRY | ✅ |
| `evds` | TCMB EVDS: official USD/EUR buy/sell rate | Needs `EVDS_API_KEY` |
| `gold` | altinapi.com: gram gold + sarrafiye (çeyrek/yarım/tam/ata) | Needs `ALTINAPI_KEY` |
| `stocks` | Yahoo Finance: BIST daily close for a watchlist | ✅ (no auth needed) |
| `tefas` | TEFAS: daily fund NAV for a watchlist | ✅ (no auth needed) |
| `bank` | Kobaküs Open Banking: multi-bank account balances | ⏸️ **Postponed** — real cost is ~₺6.240/mo (not free), and the free alternative (each bank's own developer portal) turned out to require a corporate/business registration, not available to individuals |
| `weather` | Open-Meteo: forecast, air quality, sunrise/sunset, from live Telegram location | ✅ (no auth needed) |
| `energy` | EPİAŞ: today's planned/unplanned power outages | Needs `EPIAS_USERNAME`/`PASSWORD` — individual-account access not yet verified |
| `events` | Etkinlik.io RSS: current events feed, optional city filter | ✅ (no auth needed) |
| `spotify` | Recently played tracks | Needs Spotify OAuth |
| `strava` | Activity history (runs, rides, ...) | Needs Strava OAuth |
| `watchlog` | Telegram `/izledim <text>`: manual watch log, enriched via TMDB (poster/overview) | Needs `TMDB_API_KEY` |
| `smoking` | Daily cigarette count via Telegram `/sigara` | ✅ (no external API) |
| `notion` | Writes a daily summary page to a Notion database | Needs `NOTION_TOKEN`/`NOTION_DATABASE_ID` |
| `digest` | Consolidated morning (08:40) / evening (22:45) Telegram summary of every other module | ✅ |

A `GET /api/barcode/{code}` endpoint also exists (camgoz.net product/price lookup) but isn't a
scheduled module — see `modules/barcode/camgoz_client.py` for why it currently 502s (the JoJ API
Marketplace gateway URL isn't known yet).

The İzmir ESHOT bus tracker (`modules/transit/`) is Telegram-only (`/otobus`, `/ofis`, `/yurt`,
`/yakindurak`) — no scheduled job, so it isn't in `GET /modules`.

### Module Architecture

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

Modules with no external API (`smoking`, `context`, `watchlog`) implement `fetch`/`process` as
no-ops and return `[]` from `schedules()` — their data arrives via Telegram commands or the web
form instead, handled in `core/telegram_bot.py` / `api/routers/context.py`.

---

## Database Schema

Every module owns its tables in its own `modules/<name>/models.py` — there's no central schema
file to keep in sync. `core/database.py` defines the shared `Base` and the generic `ModuleRecord`
log table (one row per module run: name, event, timestamp).

Schema changes go through **Alembic** (`alembic/`): `alembic revision --autogenerate -m "..."`,
review the diff (autogenerate reflects the live DB, so unrelated drift can show up — only commit
what your change actually touches), then `alembic upgrade head`.

---

## Scheduled Jobs

Jobs are defined in each module's `schedules()` method. APScheduler runs them based on cron
expressions, all evaluated in **Europe/Istanbul** time (explicitly pinned in `core/scheduler.py`
so behavior doesn't depend on the host machine's system timezone). On failure, a job logs the
exception and sends a notification via `core/notifier.py` (Telegram + ntfy.sh) instead of failing
silently.

```text
"0 7 * * *"    = Every day at 07:00 TR
"30 8 * * *"   = Every day at 08:30 TR
"45 22 * * *"  = Every day at 22:45 TR
```

---

## Local Development

### Running Tests

```bash
pytest -v
```

30+ tests covering: security dependency logic, request parsing/enrichment for the newer clients
(TEFAS, EVDS, Yahoo Finance, Etkinlik.io RSS, TMDB, watchlog text parser), and API-level smoke
tests (health check, module listing, admin-token gate). External HTTP calls are mocked with
`respx` — no test hits a real network or a real database. CI runs the same suite on every push/PR
(`.github/workflows/test.yml`).

### Debugging

Set `LOG_LEVEL=DEBUG` in `.env` for verbose SQLAlchemy/httpx output.

### Manual Module Trigger

```bash
curl -X POST http://localhost:8000/modules/health/run -H "X-Admin-Token: $ADMIN_TOKEN"
```

---

## Deployment

Sezi runs on a **self-hosted VPS**, not a PaaS — two components need a long-running process
(the Telegram bot's long-polling loop and APScheduler's cron jobs), which ruled out serverless/
Render-style platforms. `.github/workflows/deploy.yml` SSHes into the VPS and restarts a systemd
service on every push to `main`. Full rationale and step-by-step server setup: see `DEPLOYMENT.md`.

The database is Neon PostgreSQL (external to the VPS, no local Postgres to manage).

---

## Security

- `POST /modules/{name}/run` and `/trigger/{job_id}` require `ADMIN_TOKEN` — these aren't called
  by the dashboard, only for manual/curl-based operation.
- `POST /api/health/ingest` requires `HEALTH_INGEST_TOKEN` (used by the Health Connect bridge app).
- `POST /api/context` and all `GET /api/*` dashboard endpoints are **unauthenticated** — the
  dashboard is a single-page static app with no login system, so gating them would either break
  the UI or require embedding a secret in client-side JS (which defeats the purpose). This is a
  known, accepted residual risk for a single-user personal deployment; closing it properly would
  need a real login/session layer.

---

## Obsession Prevention

Sezi has built-in guardrails:

- **Long windows:** Minimum 7 days analysis (prevents noise)
- **No real-time alerts:** Only daily/weekly/monthly reviews
- **Weekly checkpoint:** Manual context logging (5 min/week)
- **Month 1 check:** Is this curiosity or obsession?

---

## Troubleshooting

### "OAuth token not found" (Google/Spotify/Strava)

- Run: `GET /auth/{provider}/authorize`, open the returned URL, authorize, wait for the callback.

### "No data appearing" for a module

- Check `GET /modules` — is the module listed?
- Trigger it manually: `POST /modules/{name}/run` (needs `ADMIN_TOKEN`) and read the response/logs.
- Most modules log a specific warning (e.g. `[gold] ALTINAPI_KEY ayarlanmamış — atlanıyor`) when a
  required credential is missing — check the server logs first.

### "Database connection failed"

- Verify `DATABASE_URL` in `.env`.
- For Neon: the app already strips `?sslmode=require` and sets `connect_args={"ssl": "require"}`
  automatically when the host contains `neon.tech` — don't add it manually.

### Alembic migration conflicts

- `alembic current` shows what the DB thinks its revision is; `alembic history` shows the chain.
- If autogenerate produces unrelated diffs (stale drift from before Alembic was introduced), only
  keep the lines relevant to your actual change and delete the rest from the generated file before
  applying it.

---

## Roadmap

**Status as of 2026-07-20** (see `HANDOFF.md` for the living day-to-day overview):

- [x] Core infra: scheduler, database (+ Alembic migrations), notifier (ntfy.sh + Telegram),
      dynamic module loader, admin-token-gated write endpoints, per-card dashboard error isolation
- [x] 18 registered modules — see [Modules](#modules) table above
- [x] Web dashboard (PWA, `static/`, installable on Android) with cards for every module
- [x] Test suite (pytest + respx) + CI workflow
- [x] Samsung Health / Health Connect bridge (`bridge-android/`)
- [ ] Bank/finance module — code written, **postponed** (see Modules table for why)
- [ ] Barcode module — code written, blocked on JoJ API Marketplace gateway URL
- [ ] EPİAŞ energy module — code written, individual-account access unverified
- [ ] TR barcode / nutrition (Türkomp) — evaluated, not started
- [ ] Stable APK signing + GitHub Releases + Obtainium update flow for the bridge app

### Later

- [ ] Correlation detection (the codebase already has enough daily/weekly data for this)
- [ ] Monthly/yearly retrospective reports
- [ ] Two-way Notion integration (currently write-only)

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

- Check the Troubleshooting section
- Review server logs
- Check `HANDOFF.md` for known issues and in-progress work

---

**Last Updated:** 2026-07-20
**Status:** Live in production (VPS) — 18 modules registered, core infra hardened (auth, tests, migrations, error isolation)
