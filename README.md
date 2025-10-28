# Yandex GO Car Registration Bot

Telegram bot for registering cars with Yandex GO. Supports both passenger and cargo vehicles.

## Features

- Registration for passenger and cargo vehicles
- Photo upload (4 car photos, 2 STS photos for cargo)
- Admin panel with request management
- SQLite database storage
- Docker support

## Requirements

- Python 3.11+
- Telegram Bot Token
- Poetry (for dependency management)

## Installation

### Local Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ndstrbot
```

2. Install dependencies using Poetry:
```bash
poetry install
```

3. Create a `.env` file based on `.env.example`:
```bash
cp .env.example .env
```

4. Fill in your bot token and admin IDs in the `.env` file.

5. Initialize the database:
```bash
poetry run python create_db.py
```

6. Run the bot:
```bash
poetry run python run.py
```

### Using Docker

1. Create a `.env` file based on `.env.example`:
```bash
cp .env.example .env
```

2. Fill in your bot token and admin IDs in the `.env` file.

3. Build and run with Docker Compose:
```bash
docker-compose up --build
```

## Environment Variables

- `BOT_TOKEN`: Your Telegram bot token
- `ADMIN_IDS`: Comma-separated list of admin Telegram IDs
- `DATABASE_URL`: Database connection string (default: sqlite+aiosqlite:///./storage/app.db)
- `BASE_DIR`: Base directory of the project
- `UPLOAD_DIR`: Directory for uploaded files
- `FAKE_FILES`: Set to "true" to skip actual file downloads (for testing)

## Bot Commands

### User Commands
- `/start`: Start the registration process

### Admin Commands
- `/admin`: Show admin panel
- `/stats`: Show request statistics
- `/find <tg_id|req_id>`: Find user or request
- `/approve <req_id>`: Approve request
- `/reject <req_id>`: Reject request

## Project Structure

```
.
├─ app/
│  ├─ bot.py
│  ├─ handlers/ (start.py, light.py, cargo.py, actions.py, admin.py, common.py)
│  ├─ keyboards/ (reply.py, inline.py)
│  ├─ states/ (light.py, cargo.py)
│  ├─ services/ (uploader.py, validators.py, notifier.py)
│  └─ utils/ (formatters.py, middleware.py)
├─ domain/
│  ├─ models.py
│  └─ schemas.py
├─ infra/
│  ├─ db.py
│  ├─ config.py
│  └─ logging.py
├─ storage/uploads/.gitkeep
├─ logs/.gitkeep
├─ run.py
├─ create_db.py
├─ .env.example
├─ pyproject.toml (ruff, deps)
├─ Dockerfile
├─ docker-compose.yml
└─ README.md
```

## Development

### Running Tests

```bash
poetry run pytest
```

### Code Formatting

```bash
poetry run ruff format .
```

### Linting

```bash
poetry run ruff check .
```

## License

MIT