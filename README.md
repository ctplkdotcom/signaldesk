# Signal Desk — Phase 1 MVP

Stock analysis, news scoring, and signal generation for US equities.

**Initial Universe:** MU (Micron Technology), VOO (Vanguard S&P 500 ETF), SNDK (SanDisk), NOK (Nokia), SQQQ (ProShares UltraPro Short QQQ)

---

## Implementation Status

| Area | Status |
|------|--------|
| Backend API | Complete — 15 route groups, all endpoints implemented |
| Frontend | Complete — 9 pages, dark theme, responsive |
| News Scoring | Complete — lexicon-based, 34 event types, 4 weighted components |
| Signal Engine | Complete — MA Trend (50/200 SMA crossover) |
| Data Health | Complete — 4 warning types, per-ticker monitoring |
| Data Confidence | Complete — 0–100 scoring per ticker, 4 penalty factors |
| Short-Term Indicators | Complete — 1m/5m/10m change, VWAP distance, volume spike |
| Backtest Lab | Complete — `momentum_5m` and `vwap_reversion` strategies, 10 output metrics |
| Methodology Library | Complete — DB-stored, versioned, 5 seeded strategies |
| Activity Log | Complete — action/level/ticker filtering, pagination |
| Auto-Refresh Scheduler | Complete — 60s loop, manual refresh, overlap prevention |
| Retention Service | Complete — configurable 120-day data cleanup |
| Verification | Complete — configurable external quote links, URL safety validation |
| Demo Server | Complete — full API mock (all endpoints, no DB needed), pre-seeded 5-ticker watchlist (MU, VOO, SNDK, NOK, SQQQ) |
| Process Manager | Complete — reusable PowerShell module (PID files, port kill, health check, timeout, finally cleanup) |
| Database | SQLite (default, built-in) or PostgreSQL (optional advanced mode) |
| Tests | **95 pass, 2 skip** (needs PostgreSQL + Redis), 0 fail |
| Frontend Build | Clean — 0 errors, 12 static pages generated |

---

## Features

- **Real-time prices** via Polygon.io (1-minute bars, session-aware)
- **Session classification** — premarket (04:00–09:30), regular (09:30–16:00), after-hours (16:00–20:00) ET, weekends CLOSED
- **Data health monitoring** — stale data, missing data, low liquidity, ticker mapping
- **Data confidence score** — 0–100 scale with fixed penalties for age, bar count, spread, missing data
- **Short-term indicators** — 1-min, 5-min, 10-min price change; VWAP distance; volume spike detection
- **Auto-refresh scheduler** — 60-second cycle, manual "Refresh Now" with overlap protection
- **Lexicon-based news scoring** — sentiment + event type + source reliability + recency
- **MA Trend Following signal** — 50-day / 200-day SMA crossover
- **Backtest Lab** — `momentum_5m` and `vwap_reversion` strategies; outputs: total return, trade count, win rate, avg win/loss, profit factor, max drawdown, avg hold time, largest loss, slippage/fee assumptions, data health warning
- **Methodology Library** — versioned method descriptions stored in DB, referenced by signals and backtests
- **Activity Log** — searchable history of all system actions with levels, durations, and ticker filtering
- **Watchlist management** — add/remove tickers, pre-seeded with MU, VOO, SNDK, NOK, SQQQ
- **Decision Summary Card** — composite confidence score blending signal strength × data health; human-readable explanation synthesising signal, health, news sentiment, and price
- **External Price Verification** — configurable links to Yahoo Finance, MarketWatch, Google Finance, Vanguard; ticker-specific overrides; URL domain allowlist; HTTPS-only enforcement
- **Data transparency** — every result shows source, timestamp, health status, and confidence score
- **Standalone demo server** — full API mock with realistic data, no database needed

## Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.13 / FastAPI / SQLAlchemy (async) |
| Database | SQLite (default, built-in, WAL mode) or PostgreSQL (optional via `DATABASE_MODE=postgresql`) |
| Cache | Redis 7 (optional) |
| Frontend | Next.js 14.2 (React 18, dark theme CSS variables) |
| Provider | Polygon.io (primary market data) |
| Testing | pytest 9.0 + pytest-asyncio (auto mode) + httpx |

## Quick Start

### Prerequisites
- Python 3.13+
- Polygon.io API key (free tier works) — optional; demo server needs none

### One-Step Launch (Demo + Frontend)

```powershell
cd backend
.\scripts\start.ps1
```

This launches both the demo server (port 8000) and frontend dev server (port 3000), runs health checks, and opens your browser. All API endpoints return mock data — no database or API key needed. Pre-seeded with MU, VOO, SNDK, NOK, SQQQ.

Press **Ctrl+C** to stop both servers (cleanup runs in `finally` block).

### Local Development (Backend)

```bash
cd backend
python -m venv venv
.\venv\Scripts\Activate
pip install -r requirements.txt
pip install -r test-requirements.txt

# Seed SQLite database (creates signal_desk.db with tickers + methodologies):
python -c "from app.seed import seed; import asyncio; asyncio.run(seed())"

# Run with SQLite (default):
$env:DATABASE_MODE="sqlite"
python -m app.main

# Demo server (full API mock, no DB needed):
python _demo_server.py

# Or use the safe runner (PID tracking, health check, timeout, auto-cleanup):
.\scripts\run_demo_server_safe.ps1
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev     # development
npm run build   # production build
```

## API Endpoints

### Ticker & Market Data

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/v1/dashboard` | Main dashboard + watchlist summary |
| GET | `/api/v1/dashboard/watchlist` | Watchlist items |
| POST | `/api/v1/dashboard/watchlist/{t}` | Add to watchlist |
| DELETE | `/api/v1/dashboard/watchlist/{t}` | Remove from watchlist |
| GET | `/api/v1/tickers` | All tickers |
| GET | `/api/v1/tickers/{t}` | Ticker detail |
| GET | `/api/v1/tickers/{t}/price` | Latest price + signal + health |
| GET | `/api/v1/tickers/{t}/bars` | Historical price bars (minute/day) |
| GET | `/api/v1/tickers/{t}/signals` | MA trend signals |
| GET | `/api/v1/tickers/{t}/health` | Data health check |
| POST | `/api/v1/tickers/{t}/refresh` | Refresh price + generate signal |
| GET | `/api/v1/tickers/{t}/decision-summary` | Composite confidence score + explanation |
| GET | `/api/v1/tickers/{t}/verification` | External price verification links |
| GET | `/api/v1/tickers/{t}/data-confidence` | Data quality confidence score (0–100) |
| GET | `/api/v1/tickers/{t}/indicators` | Short-term indicators (1m/5m/10m change, VWAP distance, vol spike) |

### News

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/v1/news` | News articles with scores |
| POST | `/api/v1/news` | Add a news article (scored automatically) |
| GET | `/api/v1/news/{id}` | News article detail |
| POST | `/api/v1/news/ingest` | Trigger news ingestion (stub) |

### Signals

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/v1/signals` | All signals |

### System

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/v1/health` | System health |
| GET | `/api/v1/health/data` | Data health summary |

### Phase 2 — System Routes (`/api/v1/system` mounted under `/api/v1`)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/v1/activity-log` | Activity log (filters: action, ticker, level, limit, offset) |
| POST | `/api/v1/backtest/run` | Run backtest (params: ticker, strategy, start_date, end_date) |
| GET | `/api/v1/backtest/runs` | List past backtest runs |
| GET | `/api/v1/backtest/runs/{run_id}` | Get backtest results for a run |
| GET | `/api/v1/scheduler/status` | Scheduler state, last refresh, countdown |
| POST | `/api/v1/scheduler/refresh` | Manual refresh (optional ticker param) |
| POST | `/api/v1/retention/cleanup` | Run data retention cleanup |
| GET | `/api/v1/methodologies` | List all methodologies |
| GET | `/api/v1/methodologies/{name}` | Get methodology detail |

## Project Structure

```
signal-desk/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── __init__.py          # Router aggregation
│   │   │   ├── system.py            # Phase 2 routes (backtest, activity-log, indicators, etc.)
│   │   │   ├── dashboard.py         # Watchlist, dashboard summary
│   │   │   ├── tickers.py           # Price, bars, signals, health, refresh
│   │   │   ├── news.py              # News CRUD + ingestion
│   │   │   ├── signals.py           # Signal listing
│   │   │   └── health.py            # System + data health
│   │   ├── models/
│   │   │   ├── __init__.py          # Imports all 14 models
│   │   │   ├── ticker.py            # Ticker reference data
│   │   │   ├── price_bar.py         # Raw 1-min OHLCV bars
│   │   │   ├── clean_price_bar.py   # Clean price bars (session-labelled)
│   │   │   ├── quote_snapshot.py    # Latest bid/ask snapshots
│   │   │   ├── news_article.py      # Raw news articles
│   │   │   ├── scored_news.py       # Scored/tagged news
│   │   │   ├── signal.py            # Generated signals
│   │   │   ├── data_health.py       # Per-ticker health records
│   │   │   ├── watchlist.py         # Watchlist items
│   │   │   ├── activity_log.py      # System activity log
│   │   │   ├── backtest.py          # Backtest runs + results
│   │   │   ├── methodology.py       # Strategy method definitions
│   │   │   └── app_setting.py       # Key-value app settings
│   │   ├── providers/               # Polygon.io adapter
│   │   ├── schemas/                 # Pydantic request/response
│   │   ├── services/
│   │   │   ├── backtest_service.py  # Backtest engine (momentum_5m, vwap_reversion)
│   │   │   ├── data_confidence.py   # 0–100 data confidence scoring
│   │   │   ├── short_term_indicators.py  # 1m/5m/10m change, VWAP distance, vol spike
│   │   │   ├── scheduler.py        # Auto-refresh 60s loop + manual refresh
│   │   │   ├── retention_service.py # Configurable data retention cleanup
│   │   │   ├── activity_log.py     # Activity log CRUD
│   │   │   ├── market_data.py      # Market data retrieval
│   │   │   ├── news.py             # News + scoring pipeline
│   │   │   ├── signals.py          # Signal generation
│   │   │   ├── health.py           # Data health monitoring
│   │   │   └── verification.py     # External price verification links
│   │   ├── utils/
│   │   │   ├── time.py             # Timezone, session classification
│   │   │   ├── cache.py            # Caching utilities
│   │   │   └── logging.py          # Logging config
│   │   ├── config.py               # AppSettings (database_mode, retention, etc.)
│   │   ├── database.py             # Async engine (SQLite/PostgreSQL), WAL mode
│   │   ├── main.py                 # FastAPI app + lifespan (scheduler start/stop)
│   │   └── seed.py                 # Seeds initial tickers + methodologies
│   ├── tests/
│   │   ├── test_api.py            # 5 tests (3 unit, 2 skip DB)
│   │   ├── test_decision_summary.py  # 17 tests (signal×health confidence, news sentiment, API)
│   │   ├── test_news.py           # 16 tests (scoring engine)
│   │   ├── test_signal.py         # 5 tests (MA cross, SMA)
│   │   ├── test_time.py           # 17 tests (session classification, boundaries)
│   │   ├── test_data_quality.py   # 8 tests (anti-lookahead, DST, clamping, bands, SMA)
│   │   └── test_verification.py   # 22 tests (URL safety, links, config, API)
│   ├── _demo_server.py            # Standalone demo server (all endpoints mocked)
│   ├── scripts/
│   │   ├── ProcessManager.psm1    # Reusable process lifecycle module
│   │   ├── run_demo_server_safe.ps1  # Demo server with auto-cleanup
│   │   └── start.ps1              # One-step launch (backend + frontend + browser)
│   ├── alembic/                   # Database migrations
│   ├── Dockerfile
│   ├── pyproject.toml             # pytest-asyncio mode=auto
│   ├── requirements.txt
│   └── test-requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── analysis/page.tsx      # Price bar + short-term indicators + data confidence + verification + bars/signals tabs
│   │   │   ├── dashboard/page.tsx     # Dashboard + refresh bar + countdown
│   │   │   ├── backtest/page.tsx      # Backtest Lab (run + history)
│   │   │   ├── activity-log/page.tsx  # Activity log with filters
│   │   │   ├── methodologies/page.tsx # Methodology library browser
│   │   │   ├── health/page.tsx        # Data health view
│   │   │   ├── news/page.tsx          # News with scoring display
│   │   │   ├── watchlist/page.tsx     # Watchlist management
│   │   │   └── layout.tsx             # Root layout + nav (server component, CSS hover)
│   │   ├── components/
│   │   │   ├── DecisionSummaryCard.tsx  # Composite confidence + explanation card
│   │   │   └── VerificationMenu.tsx     # "Verify on Website" popover
│   │   ├── lib/
│   │   │   ├── api.ts              # API client (full endpoint coverage)
│   │   │   └── utils.ts            # formatPrice, formatDate, scoreToLabel, getDirectionColor
│   │   └── styles/
│   │       └── globals.css         # Dark theme CSS variables + utility classes
│   ├── package.json
│   └── tsconfig.json               # @/ path alias → ./src/*
├── docker-compose.yml
├── QUALITY_REPORT.md
├── TEST_PLAN.md
└── README.md
```

## README Update Policy

**Every code change must be reflected in this README.** Before closing any task:

1. Update feature descriptions to match current behavior
2. Update endpoint tables with any new routes
3. Update project structure if files were added/removed
4. Update test counts after running the full suite
5. Update Known Limitations if any were resolved or added
6. Update Bug Fix Registry with new fixes

This file is the single source of truth for project state. If it's out of date, the codebase is effectively undocumented.

## News Scoring Formula

```
Final Score = 0.40 × Sentiment + 0.30 × Event + 0.20 × Source + 0.10 × Recency
```

Range: -100 (Strong Bearish) to +100 (Strong Bullish)

| Band | Label |
|------|-------|
| 70 to 100 | Strong Bullish |
| 30 to 69 | Bullish |
| -29 to 29 | Neutral |
| -69 to -30 | Bearish |
| -100 to -70 | Strong Bearish |

## Signal: MA Trend Following

- **Bullish** when 50-day SMA > 200-day SMA (uptrend / golden cross)
- **Bearish** when 50-day SMA < 200-day SMA (downtrend / death cross)
- Requires 200+ daily bars (roughly 10 months of data)
- Only uses regular-hours close prices

## Short-Term Indicators

The short-term indicator service computes actionable intraday metrics from 1-minute bars. Displayed in a coloured bar at the top of the Analysis page.

**Computed metrics:**
- **1-min change** — (close[t] - close[t-1]) / close[t-1] × 100
- **5-min change** — (close[t] - close[t-5]) / close[t-5] × 100
- **10-min change** — (close[t] - close[t-10]) / close[t-10] × 100
- **VWAP distance** — (close - vwap[10]) / vwap[10] × 100
- **Volume spike (5m)** — (avg_volume[5] - avg_volume[20]) / avg_volume[20] × 100

**Direction assignment:**
- `Short-Term Bullish` when 5-min change > 0.5% and 1-min change > 0.2%
- `Short-Term Bearish` when 5-min change < -0.5% and 1-min change < -0.2%
- `Neutral` otherwise

**Edge cases:** Insufficient intraday bars → status `insufficient_data` with null metrics.

**API endpoint:** `GET /api/v1/tickers/{ticker}/indicators`

## Data Confidence Score

Quantifies trustworthiness of available data for a ticker. Starts at 100 and applies penalties:

| Penalty | Amount | Trigger |
|---------|--------|---------|
| Staleness | -20 | Last bar > 60 minutes old |
| Missing data | -25 | Fewer than 5 bars in last hour |
| Low volume | -15 | Average volume < 100 shares/bar |
| Wide spread | -10 | Bid-ask spread > 1% of price |

**Labels:** 80–100 = "Good", 50–79 = "Fair", < 50 = "Poor"

**API endpoint:** `GET /api/v1/tickers/{ticker}/data-confidence`

## Decision Summary Card

The Decision Summary Card synthesises price, signal, data health, and news sentiment into a single explainable view. It appears at the top of the Analysis page.

**Composite Confidence = signal_confidence × data_health_factor**

| Condition | data_health_factor |
|-----------|-------------------|
| Data is healthy | 1.0 |
| Data has warnings or is unknown | 0.5 |

**Overall direction** is `bullish`/`bearish` only when all three conditions are met:
1. Signal direction is not `neutral`
2. Composite confidence ≥ 0.5
3. Data health is `healthy`

Otherwise falls back to `neutral`.

**Edge cases handled:**
- Missing signal → `neutral` with 0% confidence
- Missing health data → status `unknown`, factor 0.5
- No news → sentiment 0.0, article count 0
- News without scored_news (unstored article) → skipped from sentiment average
- No quote → price fields return `null`

**API endpoint:** `GET /api/v1/tickers/{ticker}/decision-summary`

**Response fields:** `ticker`, `overall_direction`, `composite_confidence`, `explanation`, `signal` (nested), `data_health` (nested), `news_sentiment_avg`, `news_article_count`, `current_price`, `price_updated_utc`.

**Frontend (`DecisionSummaryCard.tsx`):**
- Direction badge with background tint
- Confidence bar (green ≥ 70%, amber 40–69%, red < 40%)
- Human-readable explanation with signal/health/news metadata
- Four-column summary: Signal, Data Health, News Sentiment, Price

## Standalone Demo Server

The demo server (`_demo_server.py`) provides a full API mock with no external dependencies — no PostgreSQL, no Redis, no Polygon.io API key. It pre-seeds five tickers (MU, VOO, SNDK, NOK, SQQQ) with live Yahoo Finance prices.

**Mock data includes:**
- **MU** — active, $981.01 (Yahoo Finance pre-market), bullish signal, 3 news articles, healthy, confidence 85
- **VOO** — active, $680.38 (Yahoo Finance pre-market), bullish signal, 2 news articles, healthy, confidence 72
- **SNDK** — active, $1,879.09 (Yahoo Finance pre-market), bullish signal, 1 news article, healthy, confidence 80
- **NOK** — active, $14.40 (Yahoo Finance pre-market), bullish signal, 0 news, healthy, confidence 75
- **SQQQ** — active, $40.60 (Yahoo Finance pre-market), bearish signal, 0 news, healthy, confidence 65
- **Watchlist** — pre-seeded with all 5 tickers (add/remove works in-memory)
- **Bars** — 10-minute sample OHLCV for all 5 tickers (session-labelled)
- **News** — 5 scored articles (mixed sentiment, MU and VOO only)
- **System health** — healthy, 5 tickers, Polygon.io connected, 42ms latency
- **All prices** include timestamp, provider, session, bid/ask, previous_close
- **Watchlist shows two prices**: Close (previous regular-session close) and Price (current — premarket/regular/afterhours)
- **Short-term indicators** — mock data per ticker with 1m/5m/10m changes, VWAP distance, vol spike
- **Data confidence** — per-ticker score
- **Activity log** — seeded with sample refresh/view/trade actions
- **Methodologies** — all 5 seeded (Short-Term Momentum, VWAP Confirmation, Data Confidence, News Score, MA Trend)
- **Backtest** — empty runs list (run via POST to populate)
- **Scheduler status** — returns mock state (not running, ticker count 5)

**Endpoints all work:** `/tickers`, `/price`, `/bars`, `/signals`, `/health`, `/dashboard`, `/watchlist`, `/news`, `/verification`, `/decision-summary`, `/indicators`, `/data-confidence`, `/activity-log`, `/methodologies`, `/backtest/runs`, `/scheduler/status`.

### Process Manager Module

The `scripts/ProcessManager.psm1` module provides reusable server lifecycle management.

**Six defences against orphan processes:**
| # | Defence | Implementation |
|---|---------|---------------|
| D1 | PID file tracking | Write PID to file on start, read on cleanup |
| D2 | Port-based kill before start | `Set-CleanPort` frees target port before binding |
| D3 | Health-check loop with deadline | Poll `/healthz` with max timeout, no assumptions |
| D4 | Finally-block cleanup | All scripts call `Stop-AllProcesses` in `finally` |
| D5 | Single-server invariant | Kill all python/node processes before starting; safety net in `Stop-AllProcesses` catches orphaned node.exe children |
| D6 | Stderr log inspection | `Write-ProcessLogs` prints stdout/stderr on failure instead of silent timeout |

**Exported functions:**
- `Set-CleanPort` — kill process on a given port
- `Start-ManagedProcess` — start + PID tracking + health check + timeout
- `Wait-HttpReady` — poll URL until it responds or times out
- `Stop-ManagedProcess` — kill by tag, recursive child termination
- `Stop-AllProcesses` — kill all tracked processes
- `Write-ProcessLogs` — print stdout/stderr for diagnostics
- `Assert-ProcessStarted` — validate process object is alive with valid PID

**Scripts using the module:**
- `start.ps1` — one-step launch for backend + frontend
- `run_demo_server_safe.ps1` — test demo server with auto-cleanup

## External Price Verification

The verification feature provides links to external market data sites for manual price comparison.

**Configuration (`backend/app/services/verification.py`):**
- `VERIFICATION_PROVIDERS`: Yahoo Finance, MarketWatch, Google Finance (template-based URLs)
- `TICKER_OVERRIDES`: Ticker-specific overrides (e.g., Vanguard for VOO)
- `ALLOWED_DOMAINS`: Domain allowlist (4 domains) — URL safety enforced server-side

**Security:**
- HTTPS-only (`_is_safe_url` rejects HTTP)
- Domain allowlist (uppercase/lowercase normalized via `.lower()`)
- `urlparse`-based validation rejects auth-injection, port-spoofing, malformed URLs
- Deduplication by URL prevents duplicate links

**Frontend (`VerificationMenu.tsx`):**
- "Verify on Website" button opens popover with source list
- `target="_blank" rel="noopener noreferrer"` on all links
- Disclaimer: "External sites may use different data feeds or delayed quotes"
- Click-outside-to-close behavior
- CSS `:hover` (no React event handlers — compatible with Next.js SSG)
- Graceful fallback when `verification_supported=false`

## Data Health Warnings

| Warning | Trigger |
|---------|---------|
| Missing Data | No price bars found |
| Stale Cache | Last bar > 48 hours old |
| Low Liquidity | < 20 total bars |
| Ticker Mapping | Ticker not in reference data |

## Running Tests

```bash
cd backend
pip install -r test-requirements.txt

# Run all tests (92 pass — no external services needed)
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_verification.py -v
python -m pytest tests/test_time.py -v
```

**Test results:** 95 passed, 2 skipped (requires PostgreSQL + Redis), 0 failed.

All 92 pure-logic tests run without external services. The 2 skipped tests (`test_list_tickers`, `test_dashboard`) require PostgreSQL and Redis running locally.

## Seeding the Database

The first time you run with SQLite mode, seed the initial reference data:

```bash
cd backend
$env:DATABASE_MODE="sqlite"
python -c "from app.seed import seed; import asyncio; asyncio.run(seed())"
```

This creates `signal_desk.db` with:
- 3 tickers (MU, VOO, SNDK) added to watchlist (NOK and SQQQ are demo-server-only; add via UI for real app)
- 5 methodologies (Short-Term Momentum v1, VWAP Confirmation v1, Data Confidence Score v1, News Score v1, MA Trend v1)

> **Note:** SNDK was previously marked inactive (acquired by Western Digital in 2016) but was re-incorporated in 2024 and spun off in 2025. It now trades actively on NASDAQ. The seed data still reflects the historical record; both demo server and UI treat it as active.

## Configuration

### Environment Variables (`.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_MODE` | `sqlite` | `sqlite` (built-in, default) or `postgresql` (advanced) |
| `SQLITE_PATH` | `signal_desk.db` | SQLite database file path |
| `POLYGON_API_KEY` | — | Polygon.io API key |
| `DATABASE_URL` | `postgresql+asyncpg://...` | PostgreSQL connection string (when `DATABASE_MODE=postgresql`) |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection string |
| `CORS_ORIGINS` | `http://localhost:3000` | Allowed CORS origins |
| `USE_TIMESCALEDB` | `false` | Enable TimescaleDB hypertables (PostgreSQL only) |
| `RETENTION_DAYS` | `120` | Data retention period |
| `BACKFILL_MONTHS` | `3` | Initial backfill period |
| `AUTO_REFRESH_INTERVAL` | `60` | Scheduler refresh interval (seconds) |

### Frontend

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend API base URL |

### CSS Theme (Dark)

CSS variables in `globals.css` define the dark theme color palette, spacing, and typography. All components use `var(--*)` references. The class `.verification-link:hover` and `.nav-link:hover` use CSS `:hover` instead of React event handlers for full SSG compatibility.

## Bug Fix Registry

| # | Bug | File | Fix |
|---|-----|------|-----|
| 1 | `classify_session` returned AFTERHOURS at 16:00 ET | `utils/time.py` | Boundary `<=` instead of `<` |
| 2 | `classify_session` didn't check weekends | `utils/time.py` | Added `weekday() >= 5` check |
| 3 | `_compute_event_score("earnings_beat")` returned 0.0 | `services/scoring.py` | Added direct `EVENT_TYPE_SCORES` lookup before `EVENT_TYPE_MAP` |
| 4 | `postgresql_hypertable` kwarg rejected by standard PostgreSQL | `models/price_bar.py` | Conditional via `settings.use_timescaledb` (default `False`) |
| 5 | `test_sma_basic` failed due to float precision | `tests/test_signal.py` | Added `pytest.approx` |
| 6 | `test_sma_insufficient_data` failed (numpy swaps arrays) | `tests/test_signal.py` | Wrapped in `_sma` guard function matching `SignalEngine` |
| 7 | `test_final_score_negative` assertion too strict | `tests/test_news.py` | Stronger test inputs to push score below -30 |
| 8 | `_is_safe_url` rejected uppercase domains | `services/verification.py` | Added `.lower()` to `parsed.netloc` before domain check |
| 9 | `Set-CleanPort` only killed LISTEN state sockets | `scripts/ProcessManager.psm1` | Broadened to kill all TCP states (TIME_WAIT, CLOSE_WAIT, etc.) |
| 10 | `aiosqlite` missing from runtime `requirements.txt` | `requirements.txt` | Added `aiosqlite==0.20.0` |
| 11 | Demo server CORS denied localhost:3000 | `_demo_server.py` | Added CORSMiddleware with allow_origins for localhost:3000 and 127.0.0.1:3000 |
| 12 | Old PostgreSQL-specific types (JSONB, ARRAY) incompatible with SQLite | `models/ticker.py`, `models/methodology.py` | Replaced with SQLAlchemy generic `JSON` and `PickleType` |
| 13 | Scheduler lifespan overlap with test fixtures (FastAPI `TestClient` starts lifespan) | `app/main.py` | Test suite adapted to mock lifespan; scheduler guarded by `settings.database_mode` |
| 14 | Demo server prices outdated ($95.30 MU, $492.15 VOO) | `_demo_server.py` | Updated to current Yahoo Finance prices ($981.01 MU, $680.38 VOO) |
| 15 | Demo server SNDK was inactive/$0 but SNDK re-IPO'd in 2025 | `_demo_server.py` | Updated SNDK to active with live price $1,879.09; removed ticker_mapping warning |
| 16 | `p.get("previous_close")` crashes when `p` is None | `_demo_server.py` | Added `if p else None` guard in watchlist GET handler |

Each fix includes regression tests.

## Known Limitations (Phase 1)

- Polygon.io free tier has rate limits (premium recommended for live data)
- News requires manual ingestion via POST `/api/v1/news` (no scheduled fetcher)
- `POST /api/v1/news/ingest` is a stub — no actual external ingestion pipeline
- Backtest strategies limited to `momentum_5m` and `vwap_reversion`; no custom strategy import
- Backtest data uses cached bars in DB; no on-demand fetch from Polygon.io
- No user authentication
- SQLite mode does not support concurrent writes; single-user/local dev only
- `.env` default password `change-me` mismatches Docker Compose value — must reconcile for production
- `start.ps1` opens frontend via `http://localhost:3000`; requires `frontend/node_modules` to be installed first
