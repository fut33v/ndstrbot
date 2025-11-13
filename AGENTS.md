# Repository Guidelines

## Project Structure & Module Organization
- `app/` contains the aiogram bot, state machines, and supporting services; `app/webapp/` exposes FastAPI admin pages and JSON endpoints.
- `domain/` defines SQLModel entities shared across the bot, webapp, and scripts; `infra/` centralizes config, DB wiring, and logging helpers.
- `frontend/` hosts the Vite/React dashboard (see its README for npm scripts), while `tests/` and `test_webapp.py` cover bot flows and HTTP handlers.
- Persistent artifacts live in `storage/` (SQLite db, uploads) and `logs/`; keep large fixtures or secrets out of git.

## Build, Test, and Development Commands
- `poetry install` — install Python dependencies defined in `pyproject.toml`.
- `poetry run python run.py` — launch the Telegram bot with the currently configured database.
- `docker compose up --build` — bring up the bot, FastAPI admin, and frontend together for full-stack testing.
- `poetry run pytest` — run the asynchronous test suite; add `-k` filters for focused debugging.
- `poetry run ruff check .` and `poetry run ruff format .` — lint plus auto-format to the enforced style.

## Coding Style & Naming Conventions
- Python code targets 3.11, 4-space indentation, Ruff-managed linting with 88-char lines and double quotes. Follow existing folder conventions (`handlers/`, `states/`, `services/`).
- Prefer descriptive module names (e.g., `actions_light.py` over `utils2.py`) and snake_case for functions, PascalCase for SQLModel classes, and SCREAMING_SNAKE_CASE for env constants.
- Keep bot message texts and reply markup definitions near their handlers to simplify localization.

## Testing Guidelines
- Tests use `pytest` plus `pytest-asyncio`; name files `test_*.py` and co-locate fixtures under `tests/conftest.py` when needed.
- Mock Telegram APIs when possible; integration tests may rely on SQLite temp databases stored under `storage/test_*.db`.
- Pull requests should include failing-reproduction tests before bug fixes and high-level scenario tests for new flows.

## Commit & Pull Request Guidelines
- Use short, imperative commits (e.g., `Add cargo validator`) and keep logical changes isolated; leverage `git commit -p` to curate diffs.
- PRs should describe the feature, mention impacted services (`bot`, `webapp`, `frontend`), link the tracking issue, and paste screenshots or cURL snippets for UI/API changes.
- Ensure CI-critical commands (`ruff check`, `pytest`) pass locally before requesting review; include notes on env prerequisites or migration steps.

## Security & Configuration Tips
- Duplicate `.env.example` to `.env`, fill `BOT_TOKEN`, `ADMIN_IDS`, and `DATABASE_URL`, and never commit populated secrets.
- For testing uploads without Telegram traffic, set `FAKE_FILES=true`; reset to `false` before deploying so files land under `storage/uploads/`.
- When switching to PostgreSQL, validate the connection string with `poetry run python create_db.py` before redeploying containers.
