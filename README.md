# Yandex GO Car Registration Bot

Telegram bot for registering cars with Yandex GO. Supports both passenger and cargo vehicles.

## Features

- Registration for passenger and cargo vehicles
- Photo upload (4 car photos, 2 STS photos for cargo)
- Admin panel with request management
- Database storage (SQLite or PostgreSQL)
- Web dashboard for viewing database content
- Modern React frontend application
- Docker support

## Requirements

- Python 3.11+
- Telegram Bot Token
- Docker and Docker Compose (for containerized deployment)

## Installation

### Using Docker (Recommended)

1. Create a `.env` file based on `.env.example`:
```bash
cp .env.example .env
```

2. Fill in your bot token and admin IDs in the `.env` file.

3. Build and run with Docker Compose:
```bash
# Run both bot and web app
docker compose up --build

# Run only the web app and frontend
docker compose -f docker-compose.web.yml up --build
```

Note: The application now supports both SQLite (default) and PostgreSQL databases. 
By default, it uses SQLite for simplicity. To use PostgreSQL, uncomment the PostgreSQL 
configuration in your `.env` file.

## Environment Variables

- `BOT_TOKEN`: Your Telegram bot token
- `ADMIN_IDS`: Comma-separated list of admin Telegram IDs
- `DATABASE_URL`: Database connection string
  - SQLite (default): `sqlite+aiosqlite:///./storage/app.db`
  - PostgreSQL: `postgresql+asyncpg://user:password@host:port/database`
- `DATABASE_TYPE`: Database type (`sqlite` or `postgresql`)
- `BASE_DIR`: Base directory of the project
- `UPLOAD_DIR`: Directory for uploaded files
- `FAKE_FILES`: Set to "true" to skip actual file downloads (for testing)

## Database Support

This application supports both SQLite and PostgreSQL databases:

### SQLite (Default)
- Simple setup, good for development and small deployments
- Data stored in a local file (`storage/app.db`)

### PostgreSQL
- More robust, suitable for production environments
- Better performance and scalability
- Requires a PostgreSQL server

To switch to PostgreSQL:
1. Update your `.env` file with PostgreSQL configuration
2. Make sure the PostgreSQL server is running
3. Run the database initialization script

## Web Application

The project includes a web application for viewing database content:

- Dashboard with statistics: http://localhost:8000/dashboard
- JSON API endpoints for all database tables
- HTML views for easy browsing of data

For more information about the web application, see [app/webapp/README.md](app/webapp/README.md).

## Frontend Application

The project also includes a modern React frontend application:

- Built with React and Vite
- Responsive design
- API integration with the backend
- Available at http://localhost:3000 when running via Docker

For more information about the frontend application, see [frontend/README.md](frontend/README.md).

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
│  ├─ utils/ (formatters.py, middleware.py)
│  └─ webapp/ (main.py, run.py, templates.py)
├─ domain/
│  ├─ models.py
│  └─ schemas.py
├─ frontend/ (React application)
│  ├─ src/
│  │  ├─ components/
│  │  ├─ pages/
│  │  └─ ...
│  ├─ package.json
│  └─ ...
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