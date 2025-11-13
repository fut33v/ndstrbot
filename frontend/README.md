# Yandex GO Car Registration Bot - Frontend

Modern React frontend application for the Yandex GO Car Registration Bot admin panel.

## Features

- Dashboard with statistics
- Data tables for all database entities
- Responsive design
- API integration with backend

## Technologies Used

- React 18
- Vite
- Axios for API requests
- CSS Modules for styling

## Development

### Prerequisites

- Node.js 16+
- npm or yarn

### Local Development

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

The application will be available at http://localhost:3000

### Building for Production

```bash
npm run build
```

## Docker

The application can be run using Docker:

```bash
docker compose -f ../docker-compose.web.yml up --build
```

This will start both the backend API and the frontend application.

## Project Structure

```
src/
├── components/     # Reusable components
├── pages/          # Page components
├── services/       # API service functions
├── utils/          # Utility functions
├── App.jsx         # Main application component
├── main.jsx        # Entry point
├── App.css         # Global styles
└── index.css       # Base styles
```

## API Integration

The frontend communicates with the backend API through the following endpoints:

- `/api/users` - User data
- `/api/admins` - Admin data
- `/api/requests` - Request data
- `/api/files` - File data
- `/api/audit` - Audit log data

All API requests are proxied through `/api` prefix during development.