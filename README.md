# Historical Quiz

A daily history quiz web app. Each day you get a quiz about events that happened on today's month and day in past years, sourced from Wikipedia's "On This Day" data.

Built with **Django** (REST API) + **React + Vite** (SPA).

## Stack

| Layer    | Technology                        |
|----------|-----------------------------------|
| Backend  | Python, Django, Django REST Framework |
| Frontend | React 18, Vite                    |
| Database | SQLite (Django default)           |
| Data     | `day_in_history.en.parquet` (18k+ events) |

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+

### 1 — Clone and set up Python venv

```bash
git clone git@github.com:vvtrunov/historical_quiz.git
cd historical_quiz

python3 -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r backend/requirements.txt
```

### 2 — Initialise the database

```bash
cd backend
python manage.py migrate
python manage.py import_events   # loads ~18k events from the parquet file
```

### 3 — Run the backend

```bash
# still inside backend/
python manage.py runserver       # http://127.0.0.1:8000
```

### 4 — Run the frontend (separate terminal)

```bash
cd frontend
npm install
npm run dev                      # http://localhost:5173
```

Open **http://localhost:5173** — the Vite dev server proxies `/api/*` to Django automatically.

## API

```
GET /api/quiz/?date=MM-DD
```

Returns a JSON object with up to 10 quiz questions for the given month-day, each with 4 choices and a `correct` flag.

**Example:** `GET /api/quiz/?date=04-05`

## Running Tests

```bash
source venv/bin/activate
cd backend
python manage.py test quiz
```

19 tests covering the model, quiz-building logic, and HTTP API.

## Django Admin

Create a superuser to browse and search events at `http://127.0.0.1:8000/admin/`:

```bash
cd backend
python manage.py createsuperuser
```

## How It Works

1. The browser computes today's date and calls `/api/quiz/?date=MM-DD`.
2. Django picks up to 10 events for that month/day and builds 4-choice questions, using events from the same month as distractors.
3. Users answer one question at a time — correct/wrong feedback is shown instantly.
4. A final score screen appears after all questions with a **Play Again** button.
