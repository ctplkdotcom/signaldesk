# Signal Desk — Comprehensive Test Plan (Phase 1 MVP)

## 1. Scope

Validate the Phase 1 MVP of Signal Desk:
- Market session classification (time utilities)
- Polygon.io provider adapter (quote + bar fetching)
- Lexicon-based news scoring engine
- MA Trend Following signal engine
- Data health checks
- Reference data / watchlist management
- REST API endpoints
- Frontend pages load correctly

## 2. Test Categories

### A. Unit Tests (no DB/network required)

| Category | Files | Tests |
|----------|-------|-------|
| Time/Session | `test_time.py` | classify_session, to_utc, to_et, is_market_open, boundary conditions, weekend |
| News Scoring | `test_news.py` | sentiment lexicon, event type scoring, source reliability, recency decay, label mapping, final formula |
| Signal Logic | `test_signal.py` | SMA calculation, MA crossover detection, bull/bear direction, insufficient data |

### B. Integration Tests (require DB)

| Category | Files | Tests |
|----------|-------|-------|
| API Health | `test_api.py` | root endpoint, health check, docs |
| API Tickers | `test_api.py` | ticker listing, price, bars, signals, health |
| API News | `test_api.py` | news list, article detail, creation |
| API Dashboard | `test_api.py` | dashboard summary, watchlist CRUD |

### C. Data Quality Tests

| Test | What to verify |
|------|---------------|
| Session boundaries | 04:00, 09:30, 16:00, 20:00 ET exactly |
| Timezone conversion | UTC ↔ ET correctness across DST |
| SMA calculation | Manual verification with known data |
| Signal direction | Bullish when MA50 > MA200, bearish otherwise |
| Sentiment lexicon | Known positive/negative words produce correct polarity |
| Event type mapping | "earnings_beat" -> 0.9, "earnings_miss" -> -0.9 |
| Source reliability | "reuters" > "unknown_blog" |
| Recency decay | 1 hour > 90% score, 30 days < 20% score |
| Score normalization | Final score clamped to [-100, 100] |
| Label bands | ±70 strong, ±30 moderate, between -29..+29 neutral |

### D. Frontend Smoke Tests (manual)

| Page | What to check |
|------|--------------|
| Home | Dashboard loads, watchlist cards render |
| Watchlist | Add/remove tickers, table renders |
| Analysis | Price header, O/H/L/Bid/Ask, tabs switch |
| News | Article list, score badges, filter by ticker |
| Data Health | System status, warning table, refresh button |
| Navigation | All nav links work, correct active states |

## 3. Critical User Journeys

1. User opens dashboard → sees watchlist with prices and signals
2. User clicks watchlist ticker → sees analysis page with MA signal
3. User adds news article → article scored automatically, appears in news list
4. User checks data health → sees system status per ticker

## 4. Acceptance Criteria

| # | Criterion | Pass condition |
|---|-----------|----------------|
| 1 | Session classification | All boundary times return correct session |
| 2 | Sentiment scoring | Positive text > 0, negative text < 0 |
| 3 | Event scoring | Known event types map correctly |
| 4 | MA signal | 200+ bars of uptrend → bullish signal |
| 5 | Source weight | High-reliability sources score higher |
| 6 | Recency | Newer articles score higher than older |
| 7 | Label bands | Correct label for every score band |
| 8 | API health | `/health` returns 200 |
| 9 | API tickers | `GET /api/v1/tickers` returns list |
| 10 | DB init | `init_db()` creates all tables |

## 5. Potential Risks and Failure Modes

- **Missing imports** in test files (NameError)
- **No DB** in test environment (ConnectionError)
- **API key required** for Polygon provider tests
- **DST transition** causing off-by-one in timezone conversion
- **SMA edge case** when data length equals exact period
- **Empty dataset** when no bars or news exist
- **Null/None** values in price/signal/news responses
- **Cache poisoning** from previous test runs
- **Asyncio event loop** conflicts across tests
