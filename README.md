# Historical Quiz

A daily history quiz web app. Each day, users are quizzed on events that happened on today's month and day in past years.

Built with **Django** (REST API backend) + **React + Vite** (SPA frontend).

## Stack

- Python / Django + Django REST Framework
- React 18 + Vite
- SQLite (via Django default)
- Data: Wikipedia "On This Day" dataset (`day_in_history.en.parquet`)

## Setup

### Prerequisites

- Python 3.10+
- Node.js 18+

### Backend

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r backend/requirements.txt

cd backend
python manage.py migrate
python manage.py import_events    # loads parquet data into SQLite
python manage.py runserver
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open <http://localhost:5173> in your browser.

## How It Works

1. On page load, the frontend fetches today's quiz from `GET /api/quiz/?date=MM-DD`.
2. Up to 10 questions are shown, one at a time.
3. Each question has 4 choices — pick one to see instant feedback.
4. After all questions, a final score screen is shown.
