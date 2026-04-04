"""
End-to-end tests covering the full user flow:
  login → fetch quiz → submit result → check leaderboard
"""
import json

from django.test import TestCase

from .models import Event


def _make_events(month, day, count):
    Event.objects.bulk_create([
        Event(month=month, day=day, year=1000 + i, description=f'Event {i}')
        for i in range(count)
    ])


def _make_distractors(count):
    Event.objects.bulk_create([
        Event(month=6, day=15, year=2000 + i, description=f'Distractor {i}')
        for i in range(count)
    ])


class FullQuizFlowTest(TestCase):
    """Single test that walks through every API endpoint in order."""

    def setUp(self):
        _make_events(month=4, day=5, count=10)
        _make_distractors(count=50)

    def _post(self, url, body, token=None):
        headers = {'HTTP_AUTHORIZATION': f'Token {token}'} if token else {}
        return self.client.post(
            url,
            data=json.dumps(body),
            content_type='application/json',
            **headers,
        )

    def test_full_quiz_flow(self):
        # ── Step 1: Login (creates new player) ───────────────────
        r = self._post('/api/auth/login/', {'name': 'E2EPlayer'})
        self.assertEqual(r.status_code, 200, r.content)
        token = r.json()['token']
        self.assertEqual(r.json()['name'], 'E2EPlayer')

        # ── Step 2: Re-login returns the same token ───────────────
        r2 = self._post('/api/auth/login/', {'name': 'E2EPlayer'})
        self.assertEqual(r2.json()['token'], token)

        # ── Step 3: Fetch quiz ────────────────────────────────────
        r = self.client.get('/api/quiz/?date=04-05',
                            HTTP_AUTHORIZATION=f'Token {token}')
        self.assertEqual(r.status_code, 200)
        questions = r.json()['questions']
        self.assertGreater(len(questions), 0)
        self.assertLessEqual(len(questions), 10)

        # Each question must have 4 choices with exactly 1 correct
        for q in questions:
            self.assertEqual(len(q['choices']), 4)
            self.assertEqual(sum(1 for c in q['choices'] if c['correct']), 1)

        # ── Step 4: Submit a perfect score ────────────────────────
        total = len(questions)
        r = self._post('/api/quiz/submit/',
                       {'date': '04-05', 'score': total, 'total': total},
                       token=token)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['score'], total)

        # ── Step 5: Re-submit a lower score — best score kept ─────
        r = self._post('/api/quiz/submit/',
                       {'date': '04-05', 'score': 1, 'total': total},
                       token=token)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['score'], total)  # still the perfect score

        # ── Step 6: Daily leaderboard — player is #1 ─────────────
        r = self.client.get('/api/leaderboard/?scope=daily&date=04-05')
        self.assertEqual(r.status_code, 200)
        entries = r.json()['entries']
        self.assertEqual(entries[0]['name'], 'E2EPlayer')
        self.assertEqual(entries[0]['rank'], 1)
        self.assertEqual(entries[0]['score'], total)

        # ── Step 7: All-time leaderboard — player is present ──────
        r = self.client.get('/api/leaderboard/?scope=alltime')
        self.assertEqual(r.status_code, 200)
        names = [e['name'] for e in r.json()['entries']]
        self.assertIn('E2EPlayer', names)
        e2e_entry = next(e for e in r.json()['entries'] if e['name'] == 'E2EPlayer')
        self.assertEqual(e2e_entry['total_score'], total)
        self.assertEqual(e2e_entry['quizzes_played'], 1)


class MultiPlayerLeaderboardTest(TestCase):
    """Two players compete; leaderboard ordering is correct."""

    def setUp(self):
        _make_events(month=4, day=5, count=10)
        _make_distractors(count=50)

    def _login(self, name):
        r = self.client.post(
            '/api/auth/login/',
            data=json.dumps({'name': name}),
            content_type='application/json',
        )
        return r.json()['token']

    def _submit(self, token, score, total, date='04-05'):
        self.client.post(
            '/api/quiz/submit/',
            data=json.dumps({'date': date, 'score': score, 'total': total}),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Token {token}',
        )

    def test_ranking_order(self):
        alice = self._login('Alice')
        bob   = self._login('Bob')

        self._submit(alice, score=9, total=10)
        self._submit(bob,   score=6, total=10)

        entries = self.client.get(
            '/api/leaderboard/?scope=daily&date=04-05'
        ).json()['entries']

        self.assertEqual(entries[0]['name'], 'Alice')
        self.assertEqual(entries[1]['name'], 'Bob')

    def test_alltime_accumulates_across_days(self):
        alice = self._login('Alice')

        self._submit(alice, score=8, total=10, date='04-05')
        self._submit(alice, score=7, total=10, date='04-06')

        entry = next(
            e for e in self.client.get('/api/leaderboard/?scope=alltime').json()['entries']
            if e['name'] == 'Alice'
        )
        self.assertEqual(entry['total_score'], 15)
        self.assertEqual(entry['quizzes_played'], 2)
