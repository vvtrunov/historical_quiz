# Historical Quiz

A daily history quiz web app. Each day you get a quiz about events that happened on today's month and day in past years, sourced from Wikipedia's "On This Day" data.

Built with **Django** (server-rendered HTML templates + SQLite).

## Features

- **Daily quiz** — up to 10 events from today's month/day in history, each as a 4-choice question
- **Years-ago context** — each question shows how many years ago the event happened
- **Player accounts** — enter a name to play; session-based authentication
- **Score submission** — results are saved automatically on quiz completion; best score per day is kept
- **Leaderboard** — daily and all-time rankings, with your own row highlighted
- **Confetti** — visual celebration on the score screen (intensity scales with score)

## Stack

| Layer    | Technology                                |
|----------|-------------------------------------------|
| Backend  | Python, Django, SQLite                    |
| Frontend | Django HTML templates, custom CSS         |
| Data     | `day_in_history.en.parquet` (18k+ events) |

## Project Structure

```
historical_quiz/
  src/                  ← Django project
    config/             ← settings, urls, wsgi, asgi
    quiz/               ← main app (models, views, templates, static)
    manage.py
    requirements.txt
  start.sh              ← one-shot startup script
  venv/                 ← Python virtual environment
  day_in_history.en.parquet
```

## Pages

| URL | Description |
|-----|-------------|
| `/` | Login — enter your name to play |
| `/quiz/` | Quiz — answer one question at a time |
| `/score/` | Score — results with confetti and link to leaderboard |
| `/leaderboard/` | Leaderboard — daily and all-time tabs |

## Quick Start

### Prerequisites

- Python 3.10+
- `day_in_history.en.parquet` in the project root

### One-shot startup (recommended)

```bash
git clone git@github.com:vvtrunov/historical_quiz.git
cd historical_quiz
bash start.sh
```

`start.sh` handles everything: creates a Python venv, installs dependencies, runs migrations, imports events if the DB is empty, and starts Django. Press **Ctrl+C** to stop.

Open **http://127.0.0.1:8000** in your browser.

### Manual setup

<details>
<summary>Expand for step-by-step instructions</summary>

```bash
git clone git@github.com:vvtrunov/historical_quiz.git
cd historical_quiz

# Python venv
python3 -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r src/requirements.txt

# Database
python src/manage.py migrate
python src/manage.py import_events   # loads ~18k events from the parquet file

# Start
python src/manage.py runserver       # http://127.0.0.1:8000
```

</details>

## Running Tests

```bash
source venv/bin/activate

python src/manage.py test quiz          # unit tests
python src/manage.py test quiz.test_e2e # end-to-end flow tests
```

## Django Admin

Create a superuser to browse and search events at `http://127.0.0.1:8000/admin/`:

```bash
python src/manage.py createsuperuser
```

## Author

Vladimir Trunov — [github.com/vvtrunov](https://github.com/vvtrunov)

## How It Works

1. On first visit, a name form is shown. Submitting creates a player and starts a session.
2. Django picks up to 10 events for today's month/day and builds 4-choice questions using same-month events as distractors.
3. Players answer one question at a time — correct/wrong feedback is shown after each answer.
4. After the last question, the score is saved to the database (best score per player per day is kept).
5. A score screen shows the result with confetti, plus links to the leaderboard.
