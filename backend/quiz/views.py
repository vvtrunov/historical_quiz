import random
import re

from django.http import JsonResponse
from django.views import View

from .models import Event


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
