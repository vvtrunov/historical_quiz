from datetime import date as date_class

from django.test import TestCase

from .models import Event, Player, QuizResult
from .views import build_quiz


def make_events(month, day, count, year_start=1000):
    Event.objects.bulk_create([
        Event(month=month, day=day, year=year_start + i, description=f'Event {i} on {month}/{day}')
        for i in range(count)
    ])


def make_distractor_events(count, month=6, day=15, year_start=2000):
    Event.objects.bulk_create([
        Event(month=month, day=day, year=year_start + i, description=f'Distractor event {i}')
        for i in range(count)
    ])


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
        questions = build_quiz(2, 29)
        self.assertEqual(questions, [])

    def test_fewer_than_10_events_returns_all(self):
        make_events(month=3, day=3, count=3)
        questions = build_quiz(3, 3)
        self.assertEqual(len(questions), 3)

    def test_question_contains_year_and_description(self):
        questions = build_quiz(4, 5)
        for q in questions:
            self.assertIn('year', q)
            self.assertIn('description', q)
            self.assertIn('id', q)


class LoginViewTest(TestCase):
    def test_get_shows_login_form(self):
        r = self.client.get('/')
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'name="name"')

    def test_get_redirects_if_logged_in(self):
        session = self.client.session
        session['player_name'] = 'Alice'
        session.save()
        r = self.client.get('/')
        self.assertRedirects(r, '/quiz/')

    def test_post_valid_name_redirects_to_quiz(self):
        r = self.client.post('/', {'name': 'Alice'})
        self.assertRedirects(r, '/quiz/')

    def test_post_creates_player(self):
        self.client.post('/', {'name': 'Bob'})
        self.assertEqual(Player.objects.count(), 1)
        self.assertEqual(Player.objects.first().name, 'Bob')

    def test_post_sets_session(self):
        self.client.post('/', {'name': 'Carol'})
        self.assertEqual(self.client.session['player_name'], 'Carol')
        self.assertIn('player_token', self.client.session)

    def test_post_existing_player_reuses(self):
        self.client.post('/', {'name': 'Dave'})
        self.client.post('/', {'name': 'Dave'})
        self.assertEqual(Player.objects.count(), 1)

    def test_post_empty_name_shows_error(self):
        r = self.client.post('/', {'name': ''})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'required')

    def test_post_whitespace_name_shows_error(self):
        r = self.client.post('/', {'name': '   '})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'required')

    def test_post_long_name_shows_error(self):
        r = self.client.post('/', {'name': 'A' * 51})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, '50')

    def test_post_trims_whitespace(self):
        self.client.post('/', {'name': '  Eve  '})
        self.assertEqual(Player.objects.first().name, 'Eve')


class LogoutViewTest(TestCase):
    def setUp(self):
        session = self.client.session
        session['player_name'] = 'TestUser'
        session.save()

    def test_post_clears_session(self):
        self.client.post('/logout/')
        self.assertNotIn('player_name', self.client.session)

    def test_post_redirects_to_login(self):
        r = self.client.post('/logout/')
        self.assertRedirects(r, '/')


class QuizViewTest(TestCase):
    def setUp(self):
        today = date_class.today()
        make_events(today.month, today.day, count=10)
        make_distractor_events(count=50)
        self.player = Player.objects.create(name='Tester')
        session = self.client.session
        session['player_name'] = 'Tester'
        session['player_token'] = str(self.player.token)
        session.save()

    def test_get_without_login_redirects(self):
        self.client.session.flush()
        r = self.client.get('/quiz/')
        self.assertRedirects(r, '/')

    def test_get_builds_quiz_in_session(self):
        self.client.get('/quiz/')
        self.assertIn('quiz', self.client.session)

    def test_get_shows_question(self):
        r = self.client.get('/quiz/')
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'years ago')

    def test_post_answer_redirects(self):
        self.client.get('/quiz/')
        quiz = self.client.session['quiz']
        correct = next(c for c in quiz['questions'][0]['choices'] if c['correct'])
        r = self.client.post('/quiz/', {'action': 'answer', 'choice_id': correct['id']})
        self.assertRedirects(r, '/quiz/')

    def test_post_correct_answer_increments_score(self):
        self.client.get('/quiz/')
        quiz = self.client.session['quiz']
        correct = next(c for c in quiz['questions'][0]['choices'] if c['correct'])
        self.client.post('/quiz/', {'action': 'answer', 'choice_id': correct['id']})
        self.assertEqual(self.client.session['quiz']['score'], 1)

    def test_post_wrong_answer_no_score(self):
        self.client.get('/quiz/')
        quiz = self.client.session['quiz']
        wrong = next(c for c in quiz['questions'][0]['choices'] if not c['correct'])
        self.client.post('/quiz/', {'action': 'answer', 'choice_id': wrong['id']})
        self.assertEqual(self.client.session['quiz']['score'], 0)

    def test_post_next_advances_index(self):
        self.client.get('/quiz/')
        quiz = self.client.session['quiz']
        correct = next(c for c in quiz['questions'][0]['choices'] if c['correct'])
        self.client.post('/quiz/', {'action': 'answer', 'choice_id': correct['id']})
        self.client.post('/quiz/', {'action': 'next'})
        self.assertEqual(self.client.session['quiz']['index'], 1)


class ScoreViewTest(TestCase):
    def setUp(self):
        self.player = Player.objects.create(name='Tester')
        session = self.client.session
        session['player_name'] = 'Tester'
        session['player_token'] = str(self.player.token)
        session.save()

    def test_get_without_login_redirects(self):
        self.client.session.flush()
        r = self.client.get('/score/')
        self.assertRedirects(r, '/')

    def test_get_without_last_score_redirects(self):
        r = self.client.get('/score/')
        self.assertRedirects(r, '/quiz/')

    def test_get_shows_score(self):
        session = self.client.session
        session['last_score'] = {'score': 7, 'total': 10, 'date': '04-05'}
        session.save()
        r = self.client.get('/score/')
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, '7')
        self.assertContains(r, '10')
        self.assertContains(r, '70%')


class LeaderboardViewTest(TestCase):
    def setUp(self):
        alice = Player.objects.create(name='Alice')
        bob = Player.objects.create(name='Bob')
        QuizResult.objects.create(player=alice, date='04-05', score=9, total=10)
        QuizResult.objects.create(player=bob,   date='04-05', score=6, total=10)
        QuizResult.objects.create(player=alice, date='04-06', score=7, total=10)

    def test_daily_leaderboard(self):
        r = self.client.get('/leaderboard/?scope=daily&date=04-05')
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Alice')
        self.assertContains(r, 'Bob')

    def test_alltime_leaderboard(self):
        r = self.client.get('/leaderboard/?scope=alltime')
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Alice')

    def test_alltime_sums_scores(self):
        r = self.client.get('/leaderboard/?scope=alltime')
        self.assertContains(r, '16')  # Alice: 9+7

    def test_default_scope_is_daily(self):
        r = self.client.get('/leaderboard/')
        self.assertEqual(r.status_code, 200)

    def test_alice_ranked_above_bob_daily(self):
        r = self.client.get('/leaderboard/?scope=daily&date=04-05')
        content = r.content.decode()
        self.assertLess(content.index('Alice'), content.index('Bob'))
