#!/usr/bin/env bash
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
VENV="$ROOT/venv"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"

# ── Colours ──────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

info()    { echo -e "${CYAN}▶ $*${NC}"; }
success() { echo -e "${GREEN}✔ $*${NC}"; }
warn()    { echo -e "${YELLOW}⚠ $*${NC}"; }
die()     { echo -e "${RED}✖ $*${NC}" >&2; exit 1; }

# ── Cleanup on exit ───────────────────────────────────────────
DJANGO_PID=""
cleanup() {
  echo ""
  info "Stopping Django…"
  [[ -n "$DJANGO_PID" ]] && kill "$DJANGO_PID" 2>/dev/null || true
  pkill -f "manage.py runserver" 2>/dev/null || true
  info "Bye!"
}
trap cleanup EXIT INT TERM

# ── 1. Python venv ────────────────────────────────────────────
if [[ ! -f "$VENV/bin/activate" ]]; then
  info "Creating Python virtual environment…"
  python3 -m venv "$VENV"
fi
# shellcheck source=/dev/null
source "$VENV/bin/activate"
success "venv active ($(python --version))"

# ── 2. Python dependencies ────────────────────────────────────
info "Checking Python dependencies…"
pip install -q -r "$BACKEND/requirements.txt"
success "Python dependencies OK"

# ── 3. Django migrate ─────────────────────────────────────────
info "Running migrations…"
python "$BACKEND/manage.py" migrate --run-syncdb -v 0
success "Database up to date"

# ── 4. Import events if DB is empty ───────────────────────────
EVENT_COUNT=$(python "$BACKEND/manage.py" shell -c \
  "from quiz.models import Event; print(Event.objects.count())" 2>/dev/null || echo "0")
if [[ "$EVENT_COUNT" -eq 0 ]]; then
  info "Database is empty — importing events from parquet…"
  python "$BACKEND/manage.py" import_events
  success "Events imported"
else
  success "Events already in DB ($EVENT_COUNT rows)"
fi

# ── 5. Node dependencies ──────────────────────────────────────
if [[ ! -d "$FRONTEND/node_modules" ]]; then
  info "Installing Node dependencies…"
  npm --prefix "$FRONTEND" install --silent
  success "Node dependencies installed"
else
  success "Node dependencies OK"
fi

# ── 6. Kill any stale Django on port 8000 ────────────────────
pkill -f "manage.py runserver" 2>/dev/null || true

# ── 7. Start Django in background ────────────────────────────
info "Starting Django on http://127.0.0.1:8000 …"
python "$BACKEND/manage.py" runserver &
DJANGO_PID=$!
sleep 1
if ! kill -0 "$DJANGO_PID" 2>/dev/null; then
  die "Django failed to start"
fi
success "Django running (pid $DJANGO_PID)"

# ── 8. Start Vite in foreground ───────────────────────────────
echo ""
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "  ${GREEN}${BOLD}Historical Quiz is starting!${NC}"
echo -e "  Open ${CYAN}http://localhost:5173${NC} in your browser"
echo -e "  Press ${YELLOW}Ctrl+C${NC} to stop everything"
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

npm --prefix "$FRONTEND" run dev
