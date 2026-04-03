import json

from django.test import TestCase
from django.urls import reverse

from .models import Event, Player, QuizResult
from .views import build_quiz


def make_events(month, day, count, year_start=1000):
    """Helper to bulk-create test events for a given month/day."""
    events = [
        Event(month=month, day=day, year=year_start + i, description=f'Event {i} on {month}/{day}')
        for i in range(count)
    ]
    Event.objects.bulk_create(events)


def make_distractor_events(count, month=6, day=15, year_start=2000):
    """Helper to create distractor events on a different date."""
    events = [
        Event(month=month, day=day, year=year_start + i, description=f'Distractor event {i}')
        for i in range(count)
    ]
    Event.objects.bulk_create(events)


class EventModelTest(TestCase):
    def test_str_representation(self):
        event = Event(year=1969, month=7, day=20, description='Moon landing.')
        self.assertIn('1969', str(event))
        self.assertIn('07', str(event))
        self.assertIn('20', str(event))

    def test_create_and_retrieve(self):
        Event.objects.create(year=1969, month=7, day=20, description='Moon landing.')
        self.assertEqual(Event.objects.count(), 1)
        event = Event.objects.first()
        self.assertEqual(event.year, 1969)
        self.assertEqual(event.month, 7)
        self.assertEqual(event.day, 20)


class BuildQuizTest(TestCase):
    def setUp(self):
        make_events(month=4, day=5, count=15)
        make_distractor_events(count=50)

    def test_returns_at_most_10_questions(self):
        questions = build_quiz(4, 5)
        self.assertLessEqual(len(questions), 10)

    def test_returns_exactly_10_when_enough_events(self):
        questions = build_quiz(4, 5)
        self.assertEqual(len(questions), 10)

    def test_each_question_has_four_choices(self):
        questions = build_quiz(4, 5)
        for q in questions:
            self.assertEqual(len(q['choices']), 4)

    def test_each_question_has_exactly_one_correct(self):
        questions = build_quiz(4, 5)
        for q in questions:
            correct = [c for c in q['choices'] if c['correct']]
            self.assertEqual(len(correct), 1)

    def test_correct_choice_matches_question_description(self):
        questions = build_quiz(4, 5)
        for q in questions:
            correct = next(c for c in q['choices'] if c['correct'])
            self.assertEqual(correct['text'], q['description'])

    def test_no_questions_for_empty_date(self):
        questions = build_quiz(2, 29)  # no events for this date
        self.assertEqual(questions, [])

    def test_fewer_than_10_events_returns_all(self):
        # Only 3 events for month=3, day=3
        make_events(month=3, day=3, count=3)
        questions = build_quiz(3, 3)
        self.assertEqual(len(questions), 3)

    def test_question_contains_year_and_description(self):
        questions = build_quiz(4, 5)
        for q in questions:
            self.assertIn('year', q)
            self.assertIn('description', q)
            self.assertIn('id', q)


class QuizAPITest(TestCase):
    def setUp(self):
        make_events(month=4, day=5, count=10)
        make_distractor_events(count=50)

    def test_valid_date_returns_200(self):
        response = self.client.get('/api/quiz/?date=04-05')
        self.assertEqual(response.status_code, 200)

    def test_response_has_date_and_questions(self):
        response = self.client.get('/api/quiz/?date=04-05')
        data = response.json()
        self.assertIn('date', data)
        self.assertIn('questions', data)
        self.assertEqual(data['date'], '04-05')

    def test_questions_count(self):
        response = self.client.get('/api/quiz/?date=04-05')
        data = response.json()
        self.assertLessEqual(len(data['questions']), 10)

    def test_missing_date_param_returns_400(self):
        response = self.client.get('/api/quiz/')
        self.assertEqual(response.status_code, 400)

    def test_invalid_date_format_returns_400(self):
        response = self.client.get('/api/quiz/?date=2024-04-05')
        self.assertEqual(response.status_code, 400)

    def test_invalid_month_returns_400(self):
        response = self.client.get('/api/quiz/?date=13-05')
        self.assertEqual(response.status_code, 400)

    def test_invalid_day_returns_400(self):
        response = self.client.get('/api/quiz/?date=04-32')
        self.assertEqual(response.status_code, 400)

    def test_date_with_no_events_returns_empty_list(self):
        response = self.client.get('/api/quiz/?date=02-29')
        data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['questions'], [])

    def test_choices_structure(self):
        response = self.client.get('/api/quiz/?date=04-05')
        data = response.json()
        for q in data['questions']:
            self.assertEqual(len(q['choices']), 4)
            correct = [c for c in q['choices'] if c['correct']]
            self.assertEqual(len(correct), 1)


class LoginAPITest(TestCase):
    def _post(self, body):
        return self.client.post(
            '/api/auth/login/',
            data=json.dumps(body),
            content_type='application/json',
        )

    def test_create_new_player(self):
        response = self._post({'name': 'Alice'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['name'], 'Alice')
        self.assertIn('token', data)
        self.assertEqual(Player.objects.count(), 1)

    def test_login_existing_player_returns_same_token(self):
        r1 = self._post({'name': 'Bob'})
        r2 = self._post({'name': 'Bob'})
        self.assertEqual(r1.json()['token'], r2.json()['token'])
        self.assertEqual(Player.objects.count(), 1)

    def test_empty_name_returns_400(self):
        response = self._post({'name': ''})
        self.assertEqual(response.status_code, 400)

    def test_whitespace_only_name_returns_400(self):
        response = self._post({'name': '   '})
        self.assertEqual(response.status_code, 400)

    def test_name_too_long_returns_400(self):
        response = self._post({'name': 'A' * 51})
        self.assertEqual(response.status_code, 400)

    def test_name_is_trimmed(self):
        response = self._post({'name': '  Carol  '})
        self.assertEqual(response.json()['name'], 'Carol')

    def test_invalid_json_returns_400(self):
        response = self.client.post(
            '/api/auth/login/', data='not json', content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_different_names_create_different_players(self):
        self._post({'name': 'Dave'})
        self._post({'name': 'Eve'})
        self.assertEqual(Player.objects.count(), 2)


class SubmitResultAPITest(TestCase):
    def setUp(self):
        self.player = Player.objects.create(name='Tester')
        self.headers = {'HTTP_AUTHORIZATION': f'Token {self.player.token}'}

    def _post(self, body, headers=None):
        h = headers if headers is not None else self.headers
        return self.client.post(
            '/api/quiz/submit/',
            data=json.dumps(body),
            content_type='application/json',
            **h,
        )

    def test_submit_creates_result(self):
        response = self._post({'date': '04-05', 'score': 7, 'total': 10})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(QuizResult.objects.count(), 1)
        r = QuizResult.objects.first()
        self.assertEqual(r.score, 7)

    def test_resubmit_keeps_best_score(self):
        self._post({'date': '04-05', 'score': 5, 'total': 10})
        self._post({'date': '04-05', 'score': 8, 'total': 10})
        self.assertEqual(QuizResult.objects.count(), 1)
        self.assertEqual(QuizResult.objects.first().score, 8)

    def test_resubmit_does_not_overwrite_with_lower_score(self):
        self._post({'date': '04-05', 'score': 8, 'total': 10})
        self._post({'date': '04-05', 'score': 3, 'total': 10})
        self.assertEqual(QuizResult.objects.first().score, 8)

    def test_unauthenticated_returns_401(self):
        response = self._post({'date': '04-05', 'score': 7, 'total': 10}, headers={})
        self.assertEqual(response.status_code, 401)

    def test_invalid_token_returns_401(self):
        response = self._post(
            {'date': '04-05', 'score': 7, 'total': 10},
            headers={'HTTP_AUTHORIZATION': 'Token bad-token'},
        )
        self.assertEqual(response.status_code, 401)

    def test_invalid_date_returns_400(self):
        response = self._post({'date': '2024-04-05', 'score': 7, 'total': 10})
        self.assertEqual(response.status_code, 400)

    def test_score_exceeds_total_returns_400(self):
        response = self._post({'date': '04-05', 'score': 11, 'total': 10})
        self.assertEqual(response.status_code, 400)


class LeaderboardAPITest(TestCase):
    def setUp(self):
        self.alice = Player.objects.create(name='Alice')
        self.bob   = Player.objects.create(name='Bob')
        QuizResult.objects.create(player=self.alice, date='04-05', score=9, total=10)
        QuizResult.objects.create(player=self.bob,   date='04-05', score=7, total=10)
        QuizResult.objects.create(player=self.alice, date='04-06', score=6, total=10)

    def test_daily_leaderboard_ordered_by_score(self):
        response = self.client.get('/api/leaderboard/?scope=daily&date=04-05')
        self.assertEqual(response.status_code, 200)
        entries = response.json()['entries']
        self.assertEqual(entries[0]['name'], 'Alice')
        self.assertEqual(entries[0]['rank'], 1)
        self.assertEqual(entries[1]['name'], 'Bob')

    def test_daily_leaderboard_only_for_given_date(self):
        response = self.client.get('/api/leaderboard/?scope=daily&date=04-05')
        self.assertEqual(len(response.json()['entries']), 2)

    def test_alltime_leaderboard_sums_scores(self):
        response = self.client.get('/api/leaderboard/?scope=alltime')
        self.assertEqual(response.status_code, 200)
        entries = response.json()['entries']
        alice_entry = next(e for e in entries if e['name'] == 'Alice')
        self.assertEqual(alice_entry['total_score'], 15)
        self.assertEqual(alice_entry['quizzes_played'], 2)

    def test_alltime_leaderboard_ordered_by_total_score(self):
        response = self.client.get('/api/leaderboard/?scope=alltime')
        entries = response.json()['entries']
        self.assertEqual(entries[0]['name'], 'Alice')

    def test_missing_scope_returns_400(self):
        response = self.client.get('/api/leaderboard/')
        self.assertEqual(response.status_code, 400)

    def test_daily_missing_date_returns_400(self):
        response = self.client.get('/api/leaderboard/?scope=daily')
        self.assertEqual(response.status_code, 400)
