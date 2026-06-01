# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Setup virtual environment (Python 3.9)
python3.9 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements-dev.txt   # includes pylint for linting
pip install -r requirements.txt       # production deps only

# Run locally
hypercorn api/index.py --reload       # serves at http://127.0.0.1:8000

# Lint
pylint api/ utils/
```

There are no automated tests. Manual testing is done with curl or by hitting the local server.

## Architecture

This is a **FastAPI backend** deployed on Vercel as a serverless function. All routes are in `api/index.py`; Vercel rewrites every path to `/api/index` (see `vercel.json`).

### Request flow for `/calendar`

1. Look up user in MongoDB by `uid` (ObjectId)
2. Refresh Strava access token if expiring within 30 minutes (`utils/utils.py:refresh_access_token_if_expired`)
3. Fetch all Strava activities concurrently via `get_all_activities` — uses `asyncio` with a semaphore (14 concurrent requests) and a `TTLCache` keyed on access token (10-minute TTL, 256 entries)
4. Summarize activities into a daily pandas DataFrame via `summarize_activity`
5. Render a calendar heatmap PNG via `plot_calendar` → `utils/calplot.py:calplot`
6. Return the PNG as a `StreamingResponse` (base64-decoded from the matplotlib render)

### Key files

- `api/index.py` — FastAPI app, MongoDB connection, all route handlers
- `utils/utils.py` — Strava API calls, token refresh, activity summarization, matplotlib rendering
- `utils/calplot.py` — Custom fork of the `calplot` library for calendar heatmap rendering (loads custom fonts from `fonts/`)

### Environment variables (see `.env.example`)

| Variable | Purpose |
|---|---|
| `CLIENT_ID` / `CLIENT_SECRET` | Strava OAuth app credentials |
| `ACCESS_TOKEN` / `REFRESH_TOKEN` | Strava tokens (initial seed) |
| `MONGODB_PASSWORD` | MongoDB Atlas password (username hardcoded as `samliao`) |
| `REQUEST_TOKEN_URL` | `https://www.strava.com/oauth/token` |
| `REFRESH_TOKEN_URL` | `https://www.strava.com/api/v3/oauth/token` |

### Data model (MongoDB `strava-calendar.users`)

Each document stores: `access_token`, `refresh_token`, `expires_at`, `username`.

### Sport type handling

- Sports evaluated by **distance**: Run, Ride, Swim, Walk, Hike, Trail Run, Alpine Ski
- Sports evaluated by **moving_time**: Yoga, HIIT, Weight Training, Workout
- `Ride` also includes `VirtualRide`; `Run` includes `VirtualRun`

### Activity pagination

`activity_num_estimator` in `utils/utils.py` probes page 4 and page 8 synchronously to estimate user activity volume, then fetches pages 1–N concurrently (N = 4, 8, or 15).

### CORS

Allowed origins: `http://localhost:4200` and `https://strava-calender.vercel.app`.
