import json
import random
import re

from django.db.models import Sum, Count
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from .models import Event, Player, QuizResult


# ── Auth helper ───────────────────────────────────────────────────────────────

def get_player_from_request(request):
    """Return Player for a valid Bearer token, or None."""
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Token '):
        return None
    token = auth[6:].strip()
    try:
        return Player.objects.get(token=token)
    except (Player.DoesNotExist, Exception):
        return None


# ── Quiz generation ───────────────────────────────────────────────────────────

def build_quiz(month: int, day: int, n_questions: int = 10):
    today_events = list(Event.objects.filter(month=month, day=day))
    questions = today_events[:n_questions]

    if not questions:
        return []

    today_ids = {e.id for e in today_events}

    # Distractors: same month, different days
    distractor_pool = list(
        Event.objects.filter(month=month)
        .exclude(id__in=today_ids)
        .order_by('?')[:200]
    )

    # Supplement with random events if pool too small
    if len(distractor_pool) < 30:
        extra = list(
            Event.objects.exclude(id__in=today_ids)
            .order_by('?')[:200]
        )
        merged = {e.id: e for e in distractor_pool + extra}
        distractor_pool = list(merged.values())

    result = []
    for event in questions:
        distractors = random.sample(distractor_pool, min(3, len(distractor_pool)))
        choices = [{'id': event.id, 'text': event.description, 'correct': True}]
        for d in distractors:
            choices.append({'id': d.id, 'text': d.description, 'correct': False})
        random.shuffle(choices)
        result.append({
            'id': event.id,
            'year': event.year,
            'description': event.description,
            'choices': choices,
        })
    return result


# ── Views ─────────────────────────────────────────────────────────────────────

@method_decorator(csrf_exempt, name='dispatch')
class LoginView(View):
    """POST /api/auth/login/  body: {"name": "Alice"}
    Find-or-create a player by name. Returns token + name.
    """
    def post(self, request):
        try:
            body = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        name = str(body.get('name', '')).strip()
        if not name:
            return JsonResponse({'error': 'Name is required'}, status=400)
        if len(name) > 50:
            return JsonResponse({'error': 'Name must be 50 characters or fewer'}, status=400)

        player, _ = Player.objects.get_or_create(name=name)
        return JsonResponse({'token': str(player.token), 'name': player.name})


class QuizView(View):
    def get(self, request):
        date_param = request.GET.get('date', '')
        match = re.fullmatch(r'(\d{2})-(\d{2})', date_param)
        if not match:
            return JsonResponse(
                {'error': 'date parameter must be MM-DD'},
                status=400,
            )

        month = int(match.group(1))
        day = int(match.group(2))

        if not (1 <= month <= 12 and 1 <= day <= 31):
            return JsonResponse(
                {'error': 'Invalid month or day value'},
                status=400,
            )

        questions = build_quiz(month, day)
        return JsonResponse({'date': date_param, 'questions': questions})


@method_decorator(csrf_exempt, name='dispatch')
class SubmitResultView(View):
    """POST /api/quiz/submit/  (auth required)
    body: {"date": "MM-DD", "score": 8, "total": 10}
    Creates or updates (keeping best score) the player's result for that date.
    """
    def post(self, request):
        player = get_player_from_request(request)
        if player is None:
            return JsonResponse({'error': 'Authentication required'}, status=401)

        try:
            body = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        date_param = str(body.get('date', ''))
        if not re.fullmatch(r'\d{2}-\d{2}', date_param):
            return JsonResponse({'error': 'date must be MM-DD'}, status=400)

        try:
            score = int(body['score'])
            total = int(body['total'])
        except (KeyError, ValueError, TypeError):
            return JsonResponse({'error': 'score and total are required integers'}, status=400)

        if not (0 <= score <= total) or total <= 0:
            return JsonResponse({'error': 'Invalid score/total values'}, status=400)

        existing = QuizResult.objects.filter(player=player, date=date_param).first()
        if existing:
            # Keep best score
            if score > existing.score:
                existing.score = score
                existing.total = total
                existing.save(update_fields=['score', 'total'])
            result = existing
        else:
            result = QuizResult.objects.create(
                player=player, date=date_param, score=score, total=total
            )

        return JsonResponse({
            'date': date_param,
            'score': result.score,
            'total': result.total,
        })


class LeaderboardView(View):
    """GET /api/leaderboard/?scope=daily&date=MM-DD
       GET /api/leaderboard/?scope=alltime
    """
    def get(self, request):
        scope = request.GET.get('scope', '')

        if scope == 'daily':
            return self._daily(request)
        elif scope == 'alltime':
            return self._alltime(request)
        else:
            return JsonResponse({'error': 'scope must be daily or alltime'}, status=400)

    def _daily(self, request):
        date_param = request.GET.get('date', '')
        if not re.fullmatch(r'\d{2}-\d{2}', date_param):
            return JsonResponse({'error': 'date must be MM-DD'}, status=400)

        rows = (
            QuizResult.objects
            .filter(date=date_param)
            .select_related('player')
            .order_by('-score', 'played_at')[:20]
        )
        entries = [
            {
                'rank': i + 1,
                'name': r.player.name,
                'score': r.score,
                'total': r.total,
                'played_at': r.played_at.isoformat(),
            }
            for i, r in enumerate(rows)
        ]
        return JsonResponse({'scope': 'daily', 'date': date_param, 'entries': entries})

    def _alltime(self, request):
        rows = (
            QuizResult.objects
            .values('player__name')
            .annotate(total_score=Sum('score'), quizzes_played=Count('id'))
            .order_by('-total_score', 'player__name')[:20]
        )
        entries = [
            {
                'rank': i + 1,
                'name': r['player__name'],
                'total_score': r['total_score'],
                'quizzes_played': r['quizzes_played'],
            }
            for i, r in enumerate(rows)
        ]
        return JsonResponse({'scope': 'alltime', 'entries': entries})
