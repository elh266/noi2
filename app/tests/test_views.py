from flask.ext.testing import TestCase

from app import QUESTIONS_BY_ID, MIN_QUESTIONS_TO_JOIN
from app.factory import create_app
from app.views import get_area_questionnaire_or_404
from app.models import User, Event

from .test_models import DbTestCase

LOGGED_IN_SENTINEL = '<a href="/me"'

class ViewTestCase(DbTestCase):
    def create_app(self):
        config = self.BASE_APP_CONFIG.copy()
        config.update(
            DEBUG=False,
            WTF_CSRF_ENABLED=False,
            # This speeds tests up considerably.
            SECURITY_PASSWORD_HASH='plaintext',
            CACHE_NO_NULL_WARNING=True,
        )
        return create_app(config=config)

    def register_and_login(self, username, password):
        res = self.client.post('/register', data=dict(
            next='/',
            first_name='John',
            last_name='Doe',
            email=username,
            password=password,
            password_confirm=password,
            submit='Register'
        ), follow_redirects=True)
        self.assert200(res)
        assert LOGGED_IN_SENTINEL in res.data
        return res

    def logout(self):
        res = self.client.get('/logout', follow_redirects=True)
        self.assert200(res)
        assert LOGGED_IN_SENTINEL not in res.data
        return res

    def create_user(self, email, password):
        datastore = self.app.extensions['security'].datastore
        user = datastore.create_user(email=email, password=password)
        self.last_created_user = user
        return user

    def login(self, email=None, password=None):
        if email is None:
            email = u'test@example.org'
            password = 'test123'
            self.create_user(email=email, password=password)
        res = self.client.post('/login', data=dict(
            next='/',
            submit="Login",
            email=email,
            password=password
        ), follow_redirects=True)
        self.assert200(res)
        assert LOGGED_IN_SENTINEL in res.data
        return res

class MultiStepRegistrationTests(ViewTestCase):
    OPENDATA_QUESTIONNAIRE = get_area_questionnaire_or_404('opendata')
    NUM_OPENDATA_QUESTIONS = len(OPENDATA_QUESTIONNAIRE['questions'])

    def setUp(self):
        super(MultiStepRegistrationTests, self).setUp()
        self.login()

    def test_step_2_is_ok(self):
        res = self.client.get('/register/step/2')
        self.assert200(res)

    def test_step_2_redirects_to_step_3(self):
        self.assertRedirects(self.client.post('/register/step/2'),
                             '/register/step/3')

    def test_step_3_is_ok(self):
        res = self.client.get('/register/step/3')
        self.assert200(res)
        self.assertContext('user_can_join', False)

    def test_step_3_with_areaid_redirects_to_first_unanswered_question(self):
        self.assertRedirects(self.client.get('/register/step/3/opendata'),
                             '/register/step/3/opendata/1')

        self.client.post('/register/step/3/opendata/1', data={
            'answer': '-1'
        })
        self.assertRedirects(self.client.get('/register/step/3/opendata'),
                             '/register/step/3/opendata/2')

    def test_step_3_with_questionid_is_ok(self):
        self.assert200(self.client.get('/register/step/3/opendata/1'))
        self.assert200(self.client.get('/register/step/3/opendata/%d' % (
            self.NUM_OPENDATA_QUESTIONS
        )))
        self.assertContext('user_can_join', False)

    def test_step_3_user_can_join_when_min_questions_are_answered(self):
        for i in range(1, MIN_QUESTIONS_TO_JOIN + 1):
            self.client.post('/register/step/3/opendata/%d' % i, data={
                'answer': '-1'
            })
        self.client.get('/register/step/3')
        self.assertContext('user_can_join', True)

    def test_step_3_answering_last_question_works(self):
        self.assertEqual(len(self.last_created_user.skills), 0)
        res = self.client.post('/register/step/3/opendata/%d' % (
            self.NUM_OPENDATA_QUESTIONS
        ), data={
            'answer': '-1'
        })
        self.assertRedirects(res, '/register/step/3')
        self.assertEqual(len(self.last_created_user.skills), 1)

    def test_step_3_answering_first_question_works(self):
        self.assertEqual(len(self.last_created_user.skills), 0)
        res = self.client.post('/register/step/3/opendata/1', data={
            'answer': '-1'
        })
        self.assertRedirects(res, '/register/step/3/opendata/2')
        self.assertEqual(len(self.last_created_user.skills), 1)

    def test_step_3_with_invalid_questionid_is_not_found(self):
        self.assert404(self.client.get('/register/step/3/opendata/0'))
        self.assert404(self.client.get('/register/step/3/opendata/blah'))
        self.assert404(self.client.get('/register/step/3/opendata/%d' % (
            (self.NUM_OPENDATA_QUESTIONS + 1)
        )))

    def test_step_3_with_invalid_areaid_is_not_found(self):
        self.assert404(self.client.get('/register/step/3/blah'))
        self.assert404(self.client.get('/register/step/3/blah/1'))

class ActivityFeedTests(ViewTestCase):
    def test_posting_activity_requires_full_name(self):
        self.login()
        res = self.client.post('/activity', data=dict(
            message="hello there"
        ), follow_redirects=True)
        self.assert200(res)
        self.assertEqual(Event.query_in_deployment().count(), 0)
        assert 'We need your name before you can post' in res.data

    def test_posting_activity_works(self):
        self.login()
        user = User.query_in_deployment()\
                 .filter(User.email=='test@example.org').one()
        user.first_name = 'John'
        user.last_name = 'Doe'
        res = self.client.post('/activity', data=dict(
            message="hello there"
        ), follow_redirects=True)
        self.assert200(res)
        self.assertEqual(Event.query_in_deployment().count(), 1)
        assert 'Message posted' in res.data
        assert 'hello there' in res.data

    def test_activity_is_ok(self):
        self.login()
        self.assert200(self.client.get('/activity'))

class MyProfileTests(ViewTestCase):
    def test_get_is_ok(self):
        self.login()
        self.assert200(self.client.get('/me'))

    def test_updating_profile_works(self):
        self.login()
        user = self.last_created_user
        res = self.client.post('/me', data={
            'first_name': 'John2',
            'expertise_domain_names': 'Agriculture',
            'locales': 'af'
        }, follow_redirects=True)
        assert 'Your profile has been saved' in res.data
        self.assert200(res)
        self.assertEqual(user.first_name, 'John2')
        self.assertEqual(user.expertise_domain_names, ['Agriculture'])
        self.assertEqual(len(user.locales), 1)
        self.assertEqual(str(user.locales[0]), 'af')

class MyExpertiseTests(ViewTestCase):
    def setUp(self):
        super(MyExpertiseTests, self).setUp()
        self.question_id_0 = QUESTIONS_BY_ID.keys()[0]
        self.question_id_1 = QUESTIONS_BY_ID.keys()[1]

    def test_get_is_ok(self):
        self.login()
        self.assert200(self.client.get('/my-expertise'))

    def test_updating_expertise_works(self):
        self.login()
        user = self.last_created_user
        self.assertEqual(user.skill_levels, {})
        res = self.client.post('/my-expertise', data={
            self.question_id_0: '-1',
            self.question_id_1: 'invalid value',
            'invalid_question_id': '-1'
        })
        self.assert200(res)
        self.assertEqual(user.skill_levels, {
            self.question_id_0: -1
        })

class ViewTests(ViewTestCase):
    def test_main_page_is_ok(self):
        self.assert200(self.client.get('/'))

    def test_about_page_is_ok(self):
        self.assert200(self.client.get('/about'))

    def test_feedback_page_is_ok(self):
        self.assert200(self.client.get('/feedback'))

    def test_nonexistent_page_is_not_found(self):
        self.assert404(self.client.get('/nonexistent'))

    def test_registration_works(self):
        self.register_and_login('foo@example.org', 'test123')
        self.logout()
        self.login('foo@example.org', 'test123')

    def test_existing_user_profile_is_ok(self):
        u = self.create_user(email=u'u@example.org', password='t')
        self.login('u@example.org', 't')
        self.assert200(self.client.get('/user/%d' % u.id))

    def test_nonexistent_user_profile_is_not_found(self):
        self.login()
        self.assert404(self.client.get('/user/1234'))

    def test_dashboard_is_ok(self):
        self.login()
        self.assert200(self.client.get('/dashboard'))

    def test_search_is_ok(self):
        self.login()
        res = self.client.get('/search')
        self.assert200(res)
        assert "Search for Innovators" in res.data

    def test_search_results_is_ok(self):
        self.login()
        res = self.client.get('/search?country=ZZ')
        self.assert200(res)
        assert "Expertise search" in res.data

    def test_recent_users_is_ok(self):
        self.login()
        self.assert200(self.client.get('/users/recent'))

    def test_user_profiles_require_login(self):
        self.assertRedirects(self.client.get('/user/1234'),
                             '/login?next=%2Fuser%2F1234')
