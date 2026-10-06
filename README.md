# Finance Telegram Bot

A personal finance tracker that lives in Telegram: log income and expenses through a guided conversation, get day / week / month reports, and export the whole history to CSV.

Built on **aiogram 3** with an **async SQLAlchemy** stack, running in **webhook mode behind FastAPI**.

---

## Status

The code is complete and was running in production on Render in webhook mode.
The deployment and the database are currently **paused** — see [Running it yourself](#running-it-yourself) to bring it up locally.

---

## Features

- **Guided transaction entry** — amount → category → description, as a finite-state conversation with an explicit *Cancel* available at every step.
- **Onboarding** — `/start` registers the user and seeds six default categories (2 income, 4 expense) in a single transaction.
- **Per-user isolation** — every query is scoped by the Telegram user id, so one user never sees another's data.
- **Period reports** — today / this week / this month: income, expense, balance and transaction count.
- **CSV export** — full transaction history as a downloadable Telegram document, generated in memory.
- **Validation** — amounts are parsed with both `.` and `,` as the decimal separator and rejected if not positive; categories are re-checked against the database rather than trusted from the keyboard.

---

## How it works

### Conversation flow (FSM)

Transaction entry is a three-step state machine — `waiting_for_amount` → `waiting_for_category` → `waiting_for_description`. The income/expense flag is captured from the entry button and carried through the FSM context, so the category list offered at step two is always filtered to the right kind.

The category keyboard is built from the database on each pass, and the chosen name is looked up again server-side. A user cannot inject a category that does not belong to them or does not match the transaction type.

### Reporting

`ReportService` computes period boundaries in UTC and aggregates in Python after a single joined query:

```
period "day"   → today 00:00 UTC
period "week"  → Monday 00:00 UTC of the current week
period "month" → the 1st of the current month, 00:00 UTC
```

Income and expense are split by `Category.is_income`, and the balance is derived from them. `selectinload` keeps the category fetch to one extra query instead of N.

### Webhook mode

`finance_bot/web/web_app.py` exposes a FastAPI app:

- on startup (via the lifespan handler) it creates the tables (`init_db`) and registers the Telegram webhook using `BASE_WEBHOOK_URL` + `WEBHOOK_PATH` from configuration — startup fails fast with a clear error if the base URL is missing;
- `POST /webhook` converts the incoming payload into an aiogram `Update` and feeds it to the dispatcher via `dp.feed_update`;
- on shutdown the bot session is closed cleanly.

The bot instance and dispatcher are defined once in `finance_bot/main.py` and imported by both entry points, so the routers are wired in exactly one place.

---

## Data model

```
User                          Category                       Transaction
├── id                        ├── id                         ├── id
├── telegram_id (unique, idx) ├── user_id ──► User           ├── user_id ──► User
├── username                  ├── name                       ├── category_id ──► Category
└── created_at                ├── is_income                  ├── amount  DECIMAL(10,2)
                              └── is_default                 ├── description
                                                             └── created_at
```

Deleting a user cascades to their categories and transactions (`cascade="all, delete-orphan"`).

---

## Stack

| Layer | Technology |
|---|---|
| Bot framework | aiogram 3.26, FSM with `MemoryStorage` |
| Database | PostgreSQL via SQLAlchemy 2.0 async + `asyncpg` |
| Web server | FastAPI + uvicorn (webhook mode) |
| Configuration | `pydantic-settings`, secrets as `SecretStr` |
| Export | Python `csv` into an in-memory buffer |

---

## Project structure

```
finance_bot/
├── main.py                  # Bot + Dispatcher, routers wired here
├── config.py                # pydantic-settings, loaded from .env
├── database.py              # async engine, session factory, init_db()
├── models.py                # User, Category, Transaction
├── key_boards.py            # reply and inline keyboards
├── handlers/
│   ├── common.py            # /start with default categories, cancel
│   ├── transaction.py       # 3-step FSM for adding a transaction
│   └── reporting.py         # period reports, CSV export
├── services/
│   └── report_service.py    # period aggregation + CSV generation
└── web/
    └── web_app.py           # FastAPI app, webhook endpoint
```

---

## Configuration

Settings are read from `.env` (see `.env.example`):

| Variable | Purpose |
|---|---|
| `BOT_TOKEN` | Telegram bot token, stored as `SecretStr` |
| `DATABASE_URL` | async PostgreSQL DSN, e.g. `postgresql+asyncpg://user:pass@host/db` |
| `BASE_WEBHOOK_URL` | public base URL of the deployment |
| `WEBHOOK_PATH` | webhook route, defaults to `/webhook` |

---

## Running it yourself

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # fill in BOT_TOKEN, DATABASE_URL and BASE_WEBHOOK_URL
```

Webhook mode (the mode this project runs in):

```bash
uvicorn finance_bot.web.web_app:app --reload
```

The app creates the tables on startup and registers the webhook, so the process must be reachable from the internet for Telegram to deliver updates — behind a tunnel (ngrok, cloudflared) during local development.

`BASE_WEBHOOK_URL` must therefore point at the **public** address of the running app: the tunnel URL locally, or the service URL on Render (set as an environment variable in the dashboard). If it points at `localhost`, Telegram cannot deliver updates and the bot will appear silent.

---

## Roadmap and known limitations

Honest list of what a next iteration would address:

- [ ] **Validate the webhook secret token.** The endpoint accepts any POST; Telegram supports a `secret_token` header that should be checked.
- [ ] **Add a polling entry point** so the bot can be run locally with no public URL.
- [ ] **Persist FSM state.** `MemoryStorage` means an in-flight conversation is lost on restart; Redis storage is the drop-in fix.
- [ ] **Tests.** There are none yet — handler and report-service tests with a mocked session are the obvious first targets.
- [ ] **Custom category management.** The `⚙️ Настройки` button exists in the main keyboard but is not wired to a handler yet.

---

## License

MIT — see [LICENSE](LICENSE).
