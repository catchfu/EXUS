# EXUS – Cognitive Mining MVP

Transform digital consciousness into liquid, user-owned assets. This MVP ingests activity, derives a cognitive vector, generates a privacy-preserving commitment, mints a soulbound cNFT, scores cognition, and tracks blocks.

## Features
- Login and session (dev login, optional GitHub OAuth)
- Async mining jobs with status API
- Persistence (SQLite + SQLAlchemy) for Users, cNFTs, Blocks, Jobs
- Real GitHub miner when `GITHUB_PAT` or OAuth token is present; demo fallback otherwise
- Dashboard UI with mining, cNFT list, chain stats, and market context

## Quick Start
1. Install
```
pip install -r requirements.txt
```
2. Run
```
python -m ui.app
```
3. Open `http://127.0.0.1:5000/`
4. Use LOGIN (dev) or GitHub OAuth, then click START JOB MINING

## Environment Variables
Set via your shell or system environment:
- `GITHUB_PAT`: Personal Access Token for GitHub (scopes: `repo`, `user`) – optional, improves miner results
- `GITHUB_CLIENT_ID`: GitHub OAuth App Client ID – for OAuth login
- `GITHUB_CLIENT_SECRET`: GitHub OAuth App Client Secret – for OAuth login
- `OAUTH_REDIRECT_URI`: Callback URL, default `http://127.0.0.1:5000/auth/github/callback`
- `FRED_API_KEY`: Optional, for market data expansion (not required in MVP)
- `EXUS_SECRET`: Encryption secret for OAuth tokens (recommended)
- `REDIS_URL`: Optional Redis URL to enable RQ queue (e.g., `redis://localhost:6379/0`)

## OAuth Setup (GitHub)
1. Create a GitHub OAuth app (Developer settings → OAuth Apps)
2. Set Authorization callback URL to `http://127.0.0.1:5000/auth/github/callback`
3. Export `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET`
4. From the dashboard, click LOGIN WITH GITHUB to start the flow

## APIs
- `POST /api/login/dev` – Dev login: `{"username":"alice"}`
- `POST /api/mine/job` – Queue mining job: `{"username":"alice"}` → `{ job_id }`
- `GET /api/job/:job_id` – Job status and result
- `GET /api/user/me` – Current user and GitHub connection status
- `GET /api/cnft/list` – cNFTs for user
- `GET /api/chain/stats` – Basic chain stats
- `GET /api/chain/blocks` – Last blocks (in-memory)
- `GET /api/market/data` - Market context (stubbed)
- `GET /api/metrics` - Basic metrics (users, cNFTs, jobs)
- `GET /api/health` - Service health
- `GET /api/user/export` – Export user-related data
- `DELETE /api/user/data` – Delete user’s cNFT data (simulated DSR)

## Development
- Database: `core/db.py` configures SQLite; `core/models.py` defines schema
- Jobs: In-process threads in `ui/app.py`; replace with a worker (RQ/Celery) in production
- Worker: `python -m scripts.worker` processes queued jobs; set `WORKER_USERNAME` for target user
- RQ Worker: `python -m scripts.rq_worker` to run an RQ worker if `REDIS_URL` is set
- Miner: `miners/github_miner.py` fetches real commits or falls back to demo
- UI: `ui/templates/dashboard.html` for the dashboard; `ui/app.py` server routes

## Notes
- Do not commit secrets. Use environment variables for client ID/secret and PATs.
- This MVP uses an in-memory chain; replace with an EVM devnet for smart contracts.
- DSR delete currently removes user cNFT records only; chain is append-only and simulated.
- Requests include `X-Request-Id` header for correlation; JSON logs capture request metadata.
