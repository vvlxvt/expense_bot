# ExpenseBot

ExpenseBot is a Telegram bot for tracking personal expenses. It accepts free-form expense messages, stores them in a database, updates the user's balance, suggests categories for unknown items, and exposes a small web dashboard with charts.

The bot understands messages such as `coffee 12.50` or `12.50 coffee`. Known items are categorized automatically. Unknown items are queued and shown back to the user with category suggestions from both an ML classifier and fuzzy matching, plus a manual category picker.

## Features

- Admin-only access through Telegram IDs listed in `ADMIN_IDS`.
- Free-form expense input, including multiple lines in one message.
- Automatic category assignment for known items.
- Category suggestions for unknown items:
  - `predict()` uses a TF-IDF + Logistic Regression classifier.
  - `fuzzy_root()` uses RapidFuzz to find similar known items.
  - Manual fallback through inline category buttons.
- Chosen categories are saved back into the item dictionary.
- User balance tracking with deposits and spending deductions.
- Daily, weekly, and monthly summaries in chat.
- Pagination for long expense lists.
- Web dashboard at `/stats` with category and month filters.
- ML model retraining on application startup.
- Background daily timer task.

## Expense Flow

1. The user sends one or more expense lines:
   ```text
   milk 4.80
   bread 2.50
   ```
2. Each line is parsed into an item name and a price.
3. If the item exists in the dictionary, the expense is saved immediately with its known category.
4. If the item is unknown, it is added to the `no_subs` queue.
5. For the queued item, the bot displays inline buttons:
   - the ML category guess;
   - the fuzzy-match category guess;
   - `Выбрать вручную` for manual selection;
   - `ОТМЕНИТЬ` to skip the item.
6. Once the user chooses a suggested or manual category, the expense is saved and the item dictionary is updated.

## Bot Commands

| Command | Description |
| --- | --- |
| `/start` | Sends the welcome message |
| `/help` | Shows the expected input format |
| `/deposit <amount>` | Adds money to the user's balance |
| `/balance` | Shows the current balance |
| `/today` | Shows today's spending |
| `/week` | Shows current-week spending grouped by category |
| `/month` | Opens month selection for monthly statistics |
| `/my_month` | Shows paginated expenses since the start of the current month |
| `/del_last_note` | Deletes the latest expense record |
| `/charts` | Sends a link to the web charts page |

## Tech Stack

- Python 3.11+
- Aiogram 3
- Aiohttp
- aiohttp-jinja2 / Jinja2
- SQLAlchemy 2 async
- SQLite through `aiosqlite`
- Alembic
- scikit-learn
- pandas / numpy
- joblib
- RapidFuzz

## Installation

Create and activate a virtual environment:

```bash
python -m venv .venv
```

On Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the project root:

```env
BOT_TOKEN=<telegram-bot-token>
ADMIN_IDS=123456789,987654321
APP_ENV=development
BASE_WEBHOOK_URL=https://<public-https-host>
DB_PATH=data/real.db
```

Environment variables:

- `BOT_TOKEN` is the Telegram bot token from BotFather.
- `ADMIN_IDS` is a comma-separated list of allowed Telegram user IDs.
- `APP_ENV` is the environment name, for example `development` or `production`.
- `BASE_WEBHOOK_URL` is the public HTTPS URL used by Telegram webhooks.
- `DB_PATH` is the database file path.

The SQLAlchemy URL is built as:

```text
sqlite+aiosqlite:///<DB_PATH>
```

## Running

The application runs in webhook mode and starts an aiohttp server:

```bash
python bot.py
```

On startup, the app:

1. Creates `DB_Manager`.
2. Registers the webhook at `${BASE_WEBHOOK_URL}/bot<BOT_TOKEN>`.
3. Configures the bot command menu.
4. Starts `daily_timer()`.
5. Starts ML model retraining.
6. Starts the web server.

Default server values:

| Setting | Value |
| --- | --- |
| Host | `0.0.0.0` |
| Port | `80` |
| Webhook path | `/bot<BOT_TOKEN>` |
| Charts page | `/stats` |
| Static files | `/static/` |

For local development, expose the local server through a public HTTPS tunnel such as ngrok, Cloudflare Tunnel, or a similar tool.

## Web Dashboard

The statistics page is available at:

```text
https://<BASE_WEBHOOK_URL>/stats
```

It uses:

- templates from `app/templates`;
- static files from `app/static`;
- database query helpers from `app/database/functions.py`.

## Project Structure

```text
expensebot/
├── bot.py
├── app/
│   ├── config/
│   ├── database/
│   ├── filters/
│   ├── handlers/
│   ├── keyboards/
│   ├── lexicon/
│   ├── ml/
│   ├── services/
│   ├── static/
│   ├── templates/
│   ├── utils/
│   └── web/
├── alembic/
├── data/
├── requirements.txt
└── README.md
```

Important files:

- `bot.py` is the entrypoint for the webhook, aiohttp app, and web routes.
- `app/handlers/user_handlers.py` contains user commands, reports, balance actions, and pagination callbacks.
- `app/handlers/other_handlers.py` handles free-form expense messages and category selection.
- `app/services/notes_handling.py` parses expense text and queues unknown items.
- `app/services/fuzzy_wuzzy.py` resolves fuzzy category suggestions from known items.
- `app/ml/categorizer.py` loads the trained model and predicts category IDs.
- `app/ml/ml_model.py` retrains the model from labeled dictionary items.
- `app/database/interaction_db.py` saves expenses and updates the item dictionary.
- `app/lexicon/lexicon.py` defines command labels, button labels, and category mappings.

## Categories

Category labels and callback keys live in `app/lexicon/lexicon.py`.

Top-level manual choices:

- `зефир`
- `Уля`
- `животные`
- `аптека`
- `основные продукты`
- `неосновные продукты`
- `крупные покупки`

The `основные продукты` and `неосновные продукты` buttons open their own subcategory menus.

## ML and Fuzzy Suggestions

The model file is stored at:

```text
app/ml/model.pkl
```

On startup, `retrain_model()` loads labeled items from the database, trains the classifier, and stores:

- `model`: a `TfidfVectorizer + LogisticRegression` pipeline;
- `exact`: an exact-match dictionary of `item -> cat_id`.

When choosing a category for a new item:

- the ML classifier returns a `cat_id`, which is resolved to a category name from the `categories` table;
- fuzzy matching compares the item name with already known items and returns the category of the closest match;
- when the user chooses one of the suggestions, the expense is saved and the item becomes known for future automatic categorization.

## Development

Useful syntax check:

```bash
python -m compileall app
```

If Git complains about repository ownership in a sandboxed environment, use:

```bash
git -c safe.directory=C:/Users/vital/PycharmProjects/expensebot status --short
```

## Troubleshooting

- Webhook registration fails: check `BOT_TOKEN`, `BASE_WEBHOOK_URL`, and public HTTPS availability.
- The bot ignores messages: make sure your Telegram user ID is listed in `ADMIN_IDS`.
- `/stats` does not open: check that the app is running and the tunnel points to the configured port.
- The model does not suggest useful categories: make sure the database contains labeled items and `app/ml/model.pkl` is writable.
- Port `80` is already in use: change `WEB_SERVER_PORT` in `bot.py` and update the tunnel forwarding target.
