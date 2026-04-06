import random
from datetime import date as date_class

from django.db.models import Count, Sum
from django.shortcuts import redirect, render
from django.views import View

from .models import Event, Player, QuizResult


def get_today():
    today = date_class.today()
    return f'{today.month:02d}-{today.day:02d}'


def build_quiz(month: int, day: int, n_questions: int = 10):
    today_events = list(Event.objects.filter(month=month, day=day))
    questions = today_events[:n_questions]

    if not questions:
        return []

    today_ids = {e.id for e in today_events}

    distractor_pool = list(
        Event.objects.filter(month=month)
        .exclude(id__in=today_ids)
        .order_by('?')[:200]
    )

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


def save_result(player_token, date_str, score, total):
    try:
        player = Player.objects.get(token=player_token)
        existing = QuizResult.objects.filter(player=player, date=date_str).first()
        if existing:
            if score > existing.score:
                existing.score = score
                existing.total = total
                existing.save(update_fields=['score', 'total'])
        else:
            QuizResult.objects.create(player=player, date=date_str, score=score, total=total)
    except Player.DoesNotExist:
        pass


class LoginView(View):
    def get(self, request):
        if request.session.get('player_name'):
            return redirect('quiz')
        return render(request, 'quiz/login.html')

    def post(self, request):
        name = request.POST.get('name', '').strip()
        if not name:
            return render(request, 'quiz/login.html', {'error': 'Name is required.'})
        if len(name) > 50:
            return render(request, 'quiz/login.html', {
                'error': 'Name must be 50 characters or fewer.',
                'name': name,
            })
        player, _ = Player.objects.get_or_create(name=name)
        request.session['player_name'] = player.name
        request.session['player_token'] = str(player.token)
        return redirect('quiz')


class LogoutView(View):
    def post(self, request):
        request.session.flush()
        return redirect('login')


class QuizView(View):
    def get(self, request):
        if not request.session.get('player_name'):
            return redirect('login')

        quiz = request.session.get('quiz')
        if not quiz:
            date_str = get_today()
            month, day = int(date_str[:2]), int(date_str[3:])
            questions = build_quiz(month, day)
            if not questions:
                return render(request, 'quiz/quiz.html', {'empty': True, 'date': date_str})
            quiz = {
                'questions': questions,
                'index': 0,
                'score': 0,
                'date': date_str,
                'answered': None,
            }
            request.session['quiz'] = quiz

        question = quiz['questions'][quiz['index']]
        years_ago = date_class.today().year - question['year']

        return render(request, 'quiz/quiz.html', {
            'question': question,
            'index': quiz['index'],
            'total': len(quiz['questions']),
            'score': quiz['score'],
            'date': quiz['date'],
            'answered': quiz.get('answered'),
            'years_ago': years_ago,
        })

    def post(self, request):
        if not request.session.get('player_name'):
            return redirect('login')

        quiz = request.session.get('quiz')
        if not quiz:
            return redirect('quiz')

        action = request.POST.get('action')

        if action == 'answer':
            return self._handle_answer(request, quiz)
        if action == 'next':
            return self._handle_next(request, quiz)
        return redirect('quiz')

    def _handle_answer(self, request, quiz):
        try:
            choice_id = int(request.POST.get('choice_id', 0))
        except (ValueError, TypeError):
            return redirect('quiz')
        question = quiz['questions'][quiz['index']]
        correct = any(c['id'] == choice_id and c['correct'] for c in question['choices'])
        if correct:
            quiz['score'] += 1
        quiz['answered'] = {'choice_id': choice_id, 'correct': correct}
        request.session['quiz'] = quiz
        return redirect('quiz')

    def _handle_next(self, request, quiz):
        quiz['answered'] = None
        quiz['index'] += 1
        if quiz['index'] >= len(quiz['questions']):
            score = quiz['score']
            total = len(quiz['questions'])
            date_str = quiz['date']
            save_result(request.session.get('player_token'), date_str, score, total)
            request.session['last_score'] = {'score': score, 'total': total, 'date': date_str}
            del request.session['quiz']
            return redirect('score')
        request.session['quiz'] = quiz
        return redirect('quiz')


class ScoreView(View):
    def get(self, request):
        if not request.session.get('player_name'):
            return redirect('login')

        last = request.session.get('last_score')
        if not last:
            return redirect('quiz')

        score = last['score']
        total = last['total']
        pct = round(score / total * 100) if total > 0 else 0

        if pct == 100:
            message = 'Perfect score!'
        elif pct >= 70:
            message = 'Great job!'
        elif pct >= 40:
            message = 'Not bad!'
        else:
            message = 'Better luck next time!'

        return render(request, 'quiz/score.html', {
            'score': score,
            'total': total,
            'pct': pct,
            'message': message,
            'date': last['date'],
        })


class LeaderboardView(View):
    def get(self, request):
        scope = request.GET.get('scope', 'daily')
        today = get_today()
        date_str = request.GET.get('date', today)

        if scope == 'alltime':
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
        else:
            scope = 'daily'
            rows = (
                QuizResult.objects
                .filter(date=date_str)
                .select_related('player')
                .order_by('-score', 'played_at')[:20]
            )
            entries = [
                {
                    'rank': i + 1,
                    'name': r.player.name,
                    'score': r.score,
                    'total': r.total,
                }
                for i, r in enumerate(rows)
            ]

        return render(request, 'quiz/leaderboard.html', {
            'scope': scope,
            'date': date_str,
            'today': today,
            'entries': entries,
            'player_name': request.session.get('player_name'),
        })
