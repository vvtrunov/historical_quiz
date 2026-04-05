# Historical Quiz

A daily history quiz web app. Each day you get a quiz about events that happened on today's month and day in past years, sourced from Wikipedia's "On This Day" data.

Built with **Django** (REST API) + **React + Vite** (SPA).

## Features

- **Daily quiz** — up to 10 events from today's month/day in history, each as a 4-choice question
- **Years-ago context** — each question shows how many years ago the event happened
- **Player accounts** — enter a name to get a persistent token (stored in localStorage)
- **Score submission** — results are submitted automatically on quiz completion; best score per day is kept
- **Leaderboard** — daily and all-time rankings, with your own row highlighted
- **Confetti** — visual celebration on the score screen (intensity scales with score)

## Stack

| Layer    | Technology                                    |
|----------|-----------------------------------------------|
| Backend  | Python, Django, SQLite                        |
| Frontend | React 18, Vite, canvas-confetti               |
| Data     | `day_in_history.en.parquet` (18k+ events)     |

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- `day_in_history.en.parquet` in the project root

### One-shot startup (recommended)

```bash
git clone git@github.com:vvtrunov/historical_quiz.git
cd historical_quiz
bash start.sh
```

`start.sh` handles everything automatically: creates a Python venv, installs dependencies, runs migrations, imports events if the DB is empty, and starts both Django and Vite. Press **Ctrl+C** to stop all services cleanly.

Open **http://localhost:5173** in your browser.

### Manual setup

<details>
<summary>Expand for step-by-step instructions</summary>

```bash
git clone git@github.com:vvtrunov/historical_quiz.git
cd historical_quiz

# Python venv
python3 -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r backend/requirements.txt

# Database
cd backend
python manage.py migrate
python manage.py import_events   # loads ~18k events from the parquet file

# Backend (terminal 1)
python manage.py runserver       # http://127.0.0.1:8000

# Frontend (terminal 2)
cd ../frontend
npm install
npm run dev                      # http://localhost:5173
```

</details>

## API

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/auth/login/` | — | Find-or-create player by name, returns token |
| `GET`  | `/api/quiz/?date=MM-DD` | optional | Up to 10 questions for the given date |
| `POST` | `/api/quiz/submit/` | required | Submit score; best score per date is kept |
| `GET`  | `/api/leaderboard/?scope=daily&date=MM-DD` | — | Top 20 for a specific date |
| `GET`  | `/api/leaderboard/?scope=alltime` | — | Top 20 all-time by total score |

Auth header: `Authorization: Token <uuid>`

## Running Tests

```bash
source venv/bin/activate
cd backend

python manage.py test quiz          # unit tests (40 tests)
python manage.py test quiz.test_e2e # end-to-end flow tests
```

## Django Admin

Create a superuser to browse and search events at `http://127.0.0.1:8000/admin/`:

```bash
cd backend
python manage.py createsuperuser
```

## How It Works

1. On load, the app checks localStorage for a saved token. If none exists, a name form is shown.
2. After login, the browser calls `/api/quiz/?date=MM-DD` with today's date.
3. Django picks up to 10 events for that month/day and builds 4-choice questions, using same-month events as distractors.
4. Players answer one question at a time — correct/wrong feedback is shown after each answer.
5. After the last question, the score is submitted to the backend (best score per player per day is kept).
6. A score screen shows the result with confetti, plus a leaderboard with daily and all-time rankings.
