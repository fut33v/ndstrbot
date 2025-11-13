# Web Application for Yandex GO Car Registration Bot

This web application provides a dashboard and API endpoints to view the contents of the database used by the Telegram bot.

## Features

- Dashboard with statistics and links to all data views
- JSON and HTML endpoints for all database tables
- Responsive web interface for easy data browsing

## Endpoints

### Dashboard
- `/dashboard` - Main dashboard with statistics and navigation

### Users
- `/users` or `/users/json` - Get all users in JSON format
- `/users/html` - Get all users in HTML table format

### Admins
- `/admins` or `/admins/json` - Get all admins in JSON format
- `/admins/html` - Get all admins in HTML table format

### Requests
- `/requests` or `/requests/json` - Get all requests in JSON format
- `/requests/html` - Get all requests in HTML table format

### Files
- `/files` or `/files/json` - Get all files in JSON format
- `/files/html` - Get all files in HTML table format

### Audit Logs
- `/audit` or `/audit/json` - Get all audit logs in JSON format
- `/audit/html` - Get all audit logs in HTML table format

## Running the Web Application

### Using Docker (Recommended)
```bash
# Run both bot and web app
docker-compose up --build

# Run only the web app
docker-compose up --build web
```

### Local Development
```bash
# Install dependencies
poetry install

# Run the web app
poetry run python run.py web
```

The web application will be available at http://localhost:8000