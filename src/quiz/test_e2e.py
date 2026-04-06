"""
End-to-end tests covering the full user flow:
  login → quiz → score → leaderboard → logout
"""
from datetime import date as date_class

from django.test import TestCase

from .models import Event, Player, QuizResult


def make_events(month, day, count):
    Event.objects.bulk_create([
        Event(month=month, day=day, year=1000 + i, description=f'Event {i}')
        for i in range(count)
    ])


def make_distractors(count):
    Event.objects.bulk_create([
        Event(month=6, day=15, year=2000 + i, description=f'Distractor {i}')
        for i in range(count)
    ])


class FullQuizFlowTest(TestCase):
    def setUp(self):
        today = date_class.today()
        make_events(today.month, today.day, count=10)
        make_distractors(count=50)

    def test_full_quiz_flow(self):
        today = date_class.today()
        date_str = f'{today.month:02d}-{today.day:02d}'

        # ── Step 1: Login page accessible ────────────────────────
        r = self.client.get('/')
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Historical Quiz')

        # ── Step 2: Login creates session ─────────────────────────
        r = self.client.post('/', {'name': 'E2EPlayer'})
        self.assertRedirects(r, '/quiz/')
        self.assertEqual(self.client.session['player_name'], 'E2EPlayer')

        # ── Step 3: Re-login reuses same token ────────────────────
        token_before = self.client.session['player_token']
        self.client.post('/', {'name': 'E2EPlayer'})
        self.assertEqual(self.client.session['player_token'], token_before)

        # ── Step 4: Quiz loads with questions ─────────────────────
        r = self.client.get('/quiz/')
        self.assertEqual(r.status_code, 200)
        quiz = self.client.session['quiz']
        total = len(quiz['questions'])
        self.assertGreater(total, 0)
        self.assertLessEqual(total, 10)

        # ── Step 5: Answer all questions correctly ─────────────────
        for _ in range(total):
            quiz = self.client.session['quiz']
            question = quiz['questions'][quiz['index']]
            correct = next(c for c in question['choices'] if c['correct'])
            self.client.post('/quiz/', {'action': 'answer', 'choice_id': correct['id']})
            r = self.client.post('/quiz/', {'action': 'next'})

        # ── Step 6: Redirects to score page ───────────────────────
        self.assertRedirects(r, '/score/')
        r = self.client.get('/score/')
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, str(total))

        # ── Step 7: Result saved with perfect score ───────────────
        player = Player.objects.get(name='E2EPlayer')
        result = QuizResult.objects.get(player=player, date=date_str)
        self.assertEqual(result.score, total)

        # ── Step 8: Re-submit lower score — best kept ─────────────
        session = self.client.session
        session['quiz'] = {
            'questions': quiz['questions'],
            'index': 0,
            'score': 0,
            'date': date_str,
            'answered': None,
        }
        session.save()
        for _ in range(total):
            q = self.client.session['quiz']['questions'][self.client.session['quiz']['index']]
            choice = next(c for c in q['choices'] if not c['correct'])
            self.client.post('/quiz/', {'action': 'answer', 'choice_id': choice['id']})
            self.client.post('/quiz/', {'action': 'next'})
        result.refresh_from_db()
        self.assertEqual(result.score, total)  # still the perfect score

        # ── Step 9: Daily leaderboard shows player ─────────────────
        r = self.client.get(f'/leaderboard/?scope=daily&date={date_str}')
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'E2EPlayer')

        # ── Step 10: All-time leaderboard shows player ─────────────
        r = self.client.get('/leaderboard/?scope=alltime')
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'E2EPlayer')

        # ── Step 11: Logout clears session ────────────────────────
        r = self.client.post('/logout/')
        self.assertRedirects(r, '/')
        self.assertNotIn('player_name', self.client.session)


class MultiPlayerLeaderboardTest(TestCase):
    def setUp(self):
        today = date_class.today()
        make_events(today.month, today.day, count=10)
        make_distractors(count=50)

    def _complete_quiz(self, player_name, correct_target):
        self.client.post('/', {'name': player_name})
        self.client.get('/quiz/')
        answered_correctly = 0
        for _ in range(10):
            quiz = self.client.session.get('quiz')
            if not quiz:
                break
            question = quiz['questions'][quiz['index']]
            if answered_correctly < correct_target:
                choice = next(c for c in question['choices'] if c['correct'])
                answered_correctly += 1
            else:
                choice = next(c for c in question['choices'] if not c['correct'])
            self.client.post('/quiz/', {'action': 'answer', 'choice_id': choice['id']})
            self.client.post('/quiz/', {'action': 'next'})

    def test_ranking_order(self):
        today = date_class.today()
        date_str = f'{today.month:02d}-{today.day:02d}'

        self._complete_quiz('Alice', correct_target=9)
        self.client.post('/logout/')
        self._complete_quiz('Bob', correct_target=6)

        self.client.post('/logout/')
        r = self.client.get(f'/leaderboard/?scope=daily&date={date_str}')
        content = r.content.decode()
        self.assertLess(content.index('Alice'), content.index('Bob'))

    def test_alltime_accumulates_across_days(self):
        alice = Player.objects.create(name='AliceMulti')
        QuizResult.objects.create(player=alice, date='04-05', score=8, total=10)
        QuizResult.objects.create(player=alice, date='04-06', score=7, total=10)

        r = self.client.get('/leaderboard/?scope=alltime')
        content = r.content.decode()
        self.assertIn('AliceMulti', content)
        self.assertIn('15', content)
