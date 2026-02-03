# ExpenseBot

A Telegram expense tracking bot with a lightweight web dashboard for charts. The bot accepts free-form messages like "coffee 250", categorizes the expense, stores it, and provides quick summaries in chat plus a charts page at `/stats`.

## Features
- **Admin-gated access**: Only Telegram users listed in `ADMIN_IDS` can interact with the bot.
- **Natural input**: Send messages like `coffee 250` to record expenses.
- **Auto-categorization**: Suggests/assigns subcategories for new items and prompts when ambiguous.
- **Inline keyboards**: Pagination for long outputs and quick subcategory assignment.
- **Quick summaries**:
  - `/today` — today’s spendings
  - `/week` — weekly spendings
  - `/month` — monthly spendings
  - `/my_month` — spendings since the start of the month
  - `/del_last_note` — delete the last record
  - `/charts` — opens charts dashboard link
- **Charts dashboard**: `/stats` shows cumulative daily spend, selectable category/month, and a 3‑month average. Serves static files from `app/static` and templates from `app/templates`.
- **Daily timer job**: Background task launched on startup for scheduled work.

## Tech Stack
- **Python**, **Aiogram** (Telegram bot, webhook mode)
- **Aiohttp** + **aiohttp_jinja2/Jinja2** (web server + templating)
- Simple database access layer (see `app/database/*`)

## Project Structure (high-level)
- `bot.py` — entrypoint; configures webhook, aiohttp app, routes `/stats`, and starts server
- `app/handlers/*` — bot routers and message/callback handlers
- `app/lexicon/*` — texts, commands, labels
- `app/keyboards/*` — inline keyboards and menu commands
- `app/services/*` — services, background jobs, helpers
- `app/database/*` — data access functions
- `app/templates`, `app/static` — web UI assets for the charts page
- `app/config/config.py` — env config loader and small globals helper

## Requirements
- Python 3.11+
- A Telegram Bot token (from @BotFather)
- Public HTTPS endpoint for webhooks (e.g., ngrok, Cloudflare Tunnel, Fly.io, etc.)

## Configuration
Create a `.env` file in the project root with at least:

```
BOT_TOKEN=<telegram-bot-token>
ADMIN_IDS=<comma-separated-admin-user-ids>
APP_ENV=development
BASE_WEBHOOK_URL=https://<your-public-host>
DB_PATH=data/real.db
```

Notes:
- `ADMIN_IDS` must be numeric Telegram user IDs, e.g.: `ADMIN_IDS=12345678,87654321`.
- `BASE_WEBHOOK_URL` must be publicly reachable over HTTPS; the bot sets a webhook to `${BASE_WEBHOOK_URL}/bot<token>`.
- `DB_PATH` is a local path to the SQLite (or similar) DB used by the app’s data layer.

## Installation
1. Create and activate a virtual environment (recommended).
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## How to Run (Webhook mode)
The app runs an aiohttp server and registers a Telegram webhook on startup.

1. Ensure your tunnel or hosting exposes an HTTPS URL and forwards to your local server.
2. Set the `.env` values (especially `BOT_TOKEN`, `ADMIN_IDS`, `BASE_WEBHOOK_URL`).
3. Start the app:
   ```bash
   python bot.py
   ```
4. You should see logs like:
   - `✅ Webhook set for <APP_ENV> environment`
   - `🚀 Running in <APP_ENV> mode`
5. In Telegram, open your bot and use `/start`.

Default server config (see `bot.py`):
- Host: `0.0.0.0`
- Port: `80`
- Webhook path: `/bot<token>`
- Charts page: `/stats`

If port 80 is unavailable on your system, change the port in `bot.py` (`WEB_SERVER_PORT`) and update your tunnel/forwarding accordingly.

## Development Tips
- You can open the charts dashboard directly at: `https://<BASE_WEBHOOK_URL>/stats` (with query params like `?category=Уля&month=Oct`).
- Static files are served at `/static/`.
- The bot’s menu commands are configured from `LEXICON_COMMANDS`.
- Handlers are split into `user_handlers.py` and `other_handlers.py` and gated by the `IsAdmin` filter.

## Notes & Troubleshooting
- If the webhook fails to register, verify:
  - `BASE_WEBHOOK_URL` is publicly reachable over HTTPS
  - Your tunnel/hosting forwards to the correct local host/port
  - `BOT_TOKEN` is valid and not revoked by @BotFather
- Only users listed in `ADMIN_IDS` can interact with the bot; others will be ignored by handlers.
- Ensure your locale/timezone are correct if daily stats appear shifted.

