# HomeShip

Imagine your apartment is your spaceship and you are the crew on this ship! You have lots of maintenance tasks you need to keep track of: laundry, watering plants, vacuum cleaning, and you need to make sure you have enough supplies. With the HomeShip App, all members of your household are crew members with the access to the ship console, you can create tasks, shopping lists and share all of it with each other. As long, as you keep your cargo bay full, and complete all maintenance tasks, you make progress through your journey in space and gain light years of travel. But be careful, procrastinating on maintenance will result in yellow or even red alert and endanger your ship! Avoid auto-destruction and try to get as far away from Earth as possible! Each day without red alert on your HomeShip will add another light year to your journey through the galaxy.

---

## Overview

**Problem.** Keeping track of household chores is tedious but necessary. With several people living together, this task can become even more complicated.

**Solution.** Sharing a household chores list with everyone allows keeping track of what needs to be done, and what was already done by someone else. The space-travel angle makes tedious tasks more fun.

This repo is the **backend HTTP API**, designed so any number of clients can sit on top of it. A **web client** (Flask + Jinja2) is already in active development at [HomeShip-Web](https://github.com/yanucodes/HomeShip-Web), and a native **iOS** client is planned.

### Key Features
- JWT-based authentication (login with email **or** username; Argon2 password hashing).
- Households modeled as **ships** with a shared crew (many-to-many users ↔ ships, each with a role).
- CRUD plus lifecycle operations for **tasks** (complete, postpone, change frequency, deactivate) and **supplies** (change stock state, reschedule deadline, deactivate).
- A shared **alert state** vocabulary across tasks and supplies, derived automatically from schedules and stock.
- A **journey mechanic**: an hourly cron advances each ship once per local day, accruing light-years of distance from its alert mix.

## Tech Stack
- **FastAPI** — HTTP layer and dependency injection.
- **SQLAlchemy 2.0** (typed `Mapped` models) on **PostgreSQL** via **psycopg 3**.
- **Pydantic v2** / **pydantic-settings** — request/response schemas and env-backed config.
- **Alembic** — database migrations.
- **Argon2** (`argon2-cffi`) for password hashing, **PyJWT** for tokens.
- **Docker** — the app ships as a container image (built in CI, run locally via `docker compose`, deployed to Render).

## Architecture

A thin, layered request path keeps HTTP, business logic, and persistence separate:

```
routers/        FastAPI endpoints — HTTP shape only, no business logic
  → services/   ShipService & UserService — orchestration & rules
    → repositories/  data-access wrappers over SQLAlchemy sessions
      → models/      ORM models (the tables below)
schemas/        Pydantic request/response models (validation boundary)
jobs/           hourly_update.py — the daily-advance cron entry point
```

Alert states and the schedule fields are **derived in the model layer** (e.g. `Task.scheduled`, `Supply.set_alert_on_creation`, `*.get_changes_on_*`) so the same rules apply whether a change comes from an endpoint or the cron.

### Client-agnostic by design

The models, business rules, and the journey mechanic all live **server-side**; a client never sees an ORM model, only JSON over HTTP. So a client needs nothing more than the documented endpoints — no shared schema, no embedded logic. That keeps the same backend usable, unchanged, by very different front-ends: the Flask/Jinja2 [web client](https://github.com/yanucodes/HomeShip-Web) renders server-side pages against it today, and a future iOS app would consume the exact same API. New behavior is added once, at the API, and every client benefits without duplicating rules.

## The journey mechanic

Each ship's progress is computed from the alert mix of its tasks and supplies (see `Ship.current_speed` / `get_daily_changes`):

- The ship cruises at the fraction of its active items that are on track — `green / (green + yellow)` light-years per day.
- A single **red** alert freezes progress (speed `0.0`).
- An **auto-destruct** wipes the journey: `distance` resets to `0.0` and `start_date` resets to today.

The hourly job (`python -m jobs.hourly_update`) converts a single reference instant into each ship's timezone and advances a ship only when its local `daily_rollover_hour` (default 3 AM) has arrived and it hasn't already advanced that day — making the run idempotent and self-healing.

## Database Schema

### `users`
| Column        | Type         | Notes                              |
|---------------|--------------|------------------------------------|
| user_id       | UUID         | primary key (`uuid4`)              |
| username      | VARCHAR(30)  | unique, not null                   |
| display_name  | VARCHAR(30)  | not null                           |
| email         | VARCHAR(254) | unique, not null                   |
| password_hash | VARCHAR      | not null, Argon2 hash              |

### `ships`
| Column           | Type        | Notes                                                                 |
|------------------|-------------|-----------------------------------------------------------------------|
| ship_id          | UUID        | primary key (`uuid4`)                                                  |
| shipname         | VARCHAR(50) | not null                                                               |
| start_date       | DATE        | not null; set to today on creation, reset on auto-destruct            |
| distance         | FLOAT       | not null, default `0.0`; light-years, recomputed daily by the cron    |
| timezone         | VARCHAR(64) | not null, default `"UTC"`; IANA name (e.g. `Europe/Berlin`)           |
| `last_advanced_on` | DATE        | nullable; ship-local date the cron last advanced this ship            |

Derived (not stored): `current_alerts` (alert mix) and `current_speed`.

### `ship_members`
Association object linking users to ships (many-to-many) with role data.

| Column  | Type        | Notes                                       |
|---------|-------------|---------------------------------------------|
| user_id | UUID        | composite PK, references `users.user_id`    |
| ship_id | UUID        | composite PK, references `ships.ship_id`    |
| role    | VARCHAR(30) | not null, default `"Crew Member"`           |

### `tasks`
| Column      | Type        | Notes                                                      |
|-------------|-------------|------------------------------------------------------------|
| task_id     | UUID        | primary key (`uuid4`)                                      |
| ship_id     | UUID        | not null, references `ships.ship_id`                       |
| frequency   | INTERVAL    | nullable; null for non-repeating tasks                     |
| content     | VARCHAR(200)| not null                                                   |
| date_last   | DATE        | nullable; null if never completed                          |
| date_due    | DATE        | nullable; null for archived non-repeating tasks            |
| alert_state | ALERT_STATE | not null, column default `inactive` (derived at creation)  |

### `supplies`
| Column      | Type        | Notes                                                      |
|-------------|-------------|------------------------------------------------------------|
| supply_id   | UUID        | primary key (`uuid4`)                                      |
| ship_id     | UUID        | not null, references `ships.ship_id`                       |
| name        | VARCHAR(200)| not null                                                   |
| stock_state | STOCK_STATE | not null, default `out_of_stock` (see enum below)          |
| quantity    | INTEGER     | nullable; units on hand (independent of the alert)         |
| date_due    | DATE        | nullable; buy-by deadline                                  |
| alert_state | ALERT_STATE | not null, column default `inactive` (derived at creation)  |

### `stock_state` enum (`supplies`)
| Value          | Meaning                          |
|----------------|----------------------------------|
| `in_stock`     | Sufficient amount on hand        |
| `running_low`  | Insufficient amount on hand      |
| `out_of_stock` | None left                        |

### `alert_state` enum
Shared by `tasks` and `supplies` so a ship's overall alert level is computed uniformly across both.

| Value           | Task meaning                                  | Supply meaning                                  |
|-----------------|-----------------------------------------------|-------------------------------------------------|
| `inactive`      | Archived non-repeating task / not tracked     | No longer tracked                               |
| `green`         | On schedule                                   | In stock, or deadline still far off             |
| `yellow`        | Overdue or postponed once                     | Running low, or deadline approaching            |
| `red`           | Postponed twice                               | Out of stock, or deadline imminent              |
| `auto-destruct` | Cannot be postponed anymore                   | Deadline passed / critical-item outage          |

## API

All endpoints are JSON. Everything except `POST /users`, `POST /auth/login`, and the root/health probes requires a `Bearer` token.

| Area    | Endpoints |
|---------|-----------|
| System  | `GET /` · `GET /health` |
| Auth    | `POST /auth/login` (form: `username` = email or username, `password`) |
| Users   | `POST /users` · `GET/PATCH/DELETE /users/me` |
| Ships (owner) | `POST/GET /users/me/ships` · `PATCH/DELETE /users/me/ships/{ship_id}` |
| Ships   | `GET /ships/{ship_id}` · `GET/POST /ships/{ship_id}/members` · `PATCH /ships/{ship_id}/members/me` |
| Tasks   | `GET/POST /ships/{ship_id}/tasks` · `GET/PATCH/DELETE /ships/{ship_id}/tasks/{task_id}` · `POST .../complete` · `.../postpone` · `.../change_frequency` · `.../deactivate` |
| Supplies| `GET/POST /ships/{ship_id}/supplies` · `GET/PATCH/DELETE /ships/{ship_id}/supplies/{supply_id}` · `POST .../change_stock_state` · `.../reschedule` · `.../deactivate` |

Interactive docs are available at `/docs` (Swagger) and `/redoc` once the app is running.

## Running locally

### With Docker (full stack)

The quickest way to get a running instance is `docker compose up --build`. This starts PostgreSQL and the API together; the API container applies migrations (`alembic upgrade head`) at startup and then serves on `http://127.0.0.1:8000`. Connection details and a throwaway `JWT_SECRET_KEY` are baked into `docker-compose.yml`, so no `.env` is needed for this path.

### Natively (for development)

For an editable, auto-reloading workflow:

**Prerequisites:** Python 3.11+ and a PostgreSQL database. You can spin up just the database with `docker compose up -d db` and point `DATABASE_URL` at it.

1. Install dependencies (e.g. with `uv` or `pip install -e .`).
2. Create a `.env` file. Required settings (see `.env.example` for the full list and `config.py` for defaults):
   - `DATABASE_URL` — PostgreSQL connection string (a bare `postgres://`/`postgresql://` URL is rewritten to the `psycopg` driver automatically).
   - `JWT_SECRET_KEY` — secret used to sign tokens.
   - Optional tuning: `JWT_ALGORITHM` (default `HS256`), `ACCESS_TOKEN_EXPIRE_MINUTES`, `DEFAULT_POSTPONE_DAYS`, `SUPPLY_DEADLINE_RED_DAYS`, `SUPPLY_DEADLINE_YELLOW_DAYS`, `DAILY_ROLLOVER_HOUR`.
3. Apply migrations: `alembic upgrade head`.
4. Run the API: `uvicorn main:app --reload` (serves on `http://127.0.0.1:8000`).
5. Run the daily advance manually (normally scheduled hourly): `python -m jobs.hourly_update`.

## Deployment

### CI/CD pipeline

Every push and pull request runs through GitHub Actions (`.github/workflows/ci.yml`) as three dependent jobs:

1. **`test`** — starts PostgreSQL via `docker compose`, installs the project with its `[dev]` extras, lints every tracked `.py` file with `pylint`, then runs the unit and integration suites as separate steps.
2. **`build-image`** — builds the full stack with `docker compose up --build`, waits for `/health`, and runs the end-to-end smoke test against it. On pushes to `main`, it then logs in to Docker Hub and pushes the image tagged both `:latest` and `:<commit-sha>`.
3. **`deploy`** — on pushes to `main`, triggers a Render deploy by calling its deploy hook.

So `main` is only ever deployed from an image that already passed lint, unit, integration, and end-to-end checks.

### Render

The API runs on [Render](https://render.com), provisioned from a `render.yaml` **Blueprint** so the topology — a web service plus a managed PostgreSQL database — is defined as code. When the Blueprint is first applied, Render creates the database and injects its connection string into the web service as `DATABASE_URL`; `JWT_SECRET_KEY` is generated then too. That database is a persistent, managed instance — it lives on across deploys and is **not** recreated on each one.

Rather than building from source, the web service uses `runtime: image` and **pulls the prebuilt image** (`docker.io/yanucodes/homeship-api`) that CI published. `autoDeploy` is off — deploys are triggered only by the pipeline's deploy hook, so what's live is always a CI-verified image. A deploy swaps in the new image against the same database; only migrations (run at startup) change its schema.

Deploying a self-contained image rather than a Render-specific build keeps the app **portable**: today it runs on Render, but the same image runs unchanged on any host that can pull a container and hand it a PostgreSQL URL — there's no lock-in to one provider's build system.

## Testing

**Unit tests** (`tests/unit/`) — pure, no database. They cover the logic derived in each model layer:
- `test_alert_state.py` — the `AlertState.escalate` state machine.
- `test_task_model.py` — `Task`'s pure derivation methods.

Run them with `pytest tests/unit` — no setup required. Coverage currently spans the **alert state** and **task** models; supply and ship model suites are in progress.

**Integration tests** (`tests/integration/`) — exercise the service and HTTP layers against a real PostgreSQL database (`TEST_DATABASE_URL`):
- `test_user_service.py` — `UserService` behavior (e.g. passwords are stored hashed).
- `test_user_endpoints.py` — the users router over HTTP via FastAPI's `TestClient`.

The shared `conftest.py` creates the schema once per session, then wraps **each test in a transaction that is rolled back afterward** (via a SQLAlchemy savepoint), so tests stay isolated without re-creating tables. The `TestClient` is wired to that same rolled-back session through a dependency override. Run them with `pytest tests/integration`. Coverage currently spans the **user** domain; ship, task, and supply service/endpoint suites are in progress.

**End-to-end API smoke test** — with the server running, `./scripts/api_smoke_test.sh` drives the full user → ship → task → supply lifecycle over HTTP and asserts the responses. Requires [`httpie`](https://httpie.io) and [`jq`](https://jqlang.github.io/jq); target a remote instance by passing the base URL as an argument (or via `BASE_URL=...`). CI runs this against the containerized stack on every push.
