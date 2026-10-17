# Saksham Panel (separate service)

A private Flask dashboard for the existing bot's supported panel APIs. It never reads the bot database directly and never puts `PANEL_API_SECRET` in browser JavaScript.

## Render environment variables
- `PANEL_USERNAME`: login username (example: `sakshamadmin`)
- `PANEL_PASSWORD`: strong, unique password (required; login is disabled if empty)
- `FLASK_SECRET_KEY`: long random secret (generate a unique value)
- `BOT_API_URL`: base URL of the existing bot Render web service, e.g. `https://YOUR-BOT.onrender.com`
- `PANEL_API_SECRET`: same random secret configured on the existing bot service
- `UPTIME_URLS`: comma-separated URLs to check, e.g. `https://YOUR-BOT.onrender.com/health,https://mytronuserbot.onrender.com/health,https://sakshamxmusic.onrender.com/health`

## Deploy
1. Create a NEW GitHub repository, e.g. `saksham-panel`. Do not edit or replace the existing bot repository.
2. Upload `app.py`, `templates/`, `requirements.txt`, `Procfile`, `.gitignore`, and `README.md`.
3. Render → New + → Web Service → connect only the new `saksham-panel` repository.
4. Runtime: Python. Build command: `pip install -r requirements.txt`. Start command: `gunicorn app:app --workers 2 --threads 4 --timeout 30`.
5. Add the environment variables listed above. Generate unique secrets and never paste them into chat or source code.
6. Deploy, then open the new service URL and log in.
7. In the EXISTING bot service, set `PANEL_URL` to the new panel URL, and set `PANEL_API_SECRET` to the same value used by the panel service. Do not change other variables. Redeploy the bot only after saving; this is the only integration change required for `/panel` to point at the new dashboard.

## Existing API limitations
The supplied `bot.py` currently exposes `/panel-api/groups`, `/panel-api/wallet`, and `/panel-api/wallet/debit`. It does not expose API endpoints for listing all users, aggregate stats, XP, or rewards. The dashboard marks those sections as unavailable instead of fabricating data. Uptime checks are basic HTTP reachability checks, not historical uptime monitoring.
