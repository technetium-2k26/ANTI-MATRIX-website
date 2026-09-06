import unittest
from unittest.mock import patch, MagicMock
from flask import session
from app import create_app
from models import db, User
from services.oauth_service import find_or_create_oauth_user


class OAuthSystemTestCase(unittest.TestCase):
    """Test suite for Google and GitHub OAuth authentication system."""

    def setUp(self):
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    # ── 1. Helper / Unit Tests: find_or_create_oauth_user ───────────────────

    def test_find_or_create_new_oauth_user(self):
        """A brand new OAuth user should be registered automatically."""
        user = find_or_create_oauth_user(
            provider='google',
            provider_id='g_123456789',
            email='alex.doe@example.com',
            name='Alex Doe',
            picture='https://example.com/alex.jpg'
        )

        self.assertIsNotNone(user.id)
        self.assertEqual(user.email, 'alex.doe@example.com')
        self.assertEqual(user.name, 'Alex Doe')
        self.assertEqual(user.provider, 'google')
        self.assertEqual(user.provider_id, 'g_123456789')
        self.assertEqual(user.profile_picture, 'https://example.com/alex.jpg')
        self.assertIsNotNone(user.last_login)
        self.assertTrue(user.is_active)

    def test_find_or_create_account_linking_with_existing_email(self):
        """Logging in via OAuth with an email that exists should link the account, not create a duplicate."""
        # Pre-existing user who registered via password
        existing = User(
            name='Sarah Connor',
            email='sarah@skynet.com',
            role='member',
            provider='email'
        )
        existing.set_password('Password123!')
        db.session.add(existing)
        db.session.commit()
        original_id = existing.id

        # User now logs in via Google
        linked_user = find_or_create_oauth_user(
            provider='google',
            provider_id='google_sub_9999',
            email='sarah@skynet.com',
            name='Sarah Connor',
            picture='https://lh3.googleusercontent.com/photo.jpg'
        )

        self.assertEqual(linked_user.id, original_id)
        self.assertEqual(linked_user.provider, 'google')
        self.assertEqual(linked_user.provider_id, 'google_sub_9999')
        self.assertEqual(linked_user.profile_picture, 'https://lh3.googleusercontent.com/photo.jpg')
        
        # Verify no duplicate user was created for the email
        matching_users = User.query.filter_by(email='sarah@skynet.com').all()
        self.assertEqual(len(matching_users), 1)

    def test_oauth_user_case_insensitive_email_linking(self):
        """Email matching should be case-insensitive (e.g. USER@Example.COM)."""
        existing = User(
            name='Case Test',
            email='john.smith@domain.com',
            role='member',
            provider='email'
        )
        db.session.add(existing)
        db.session.commit()

        linked = find_or_create_oauth_user(
            provider='github',
            provider_id='gh_445566',
            email='John.Smith@DOMAIN.com',
            name='John Smith'
        )
        self.assertEqual(linked.id, existing.id)
        matching_users = User.query.filter_by(email='john.smith@domain.com').all()
        self.assertEqual(len(matching_users), 1)

    # ── 2. Google OAuth Routes ──────────────────────────────────────────────

    def test_google_login_unconfigured_shows_friendly_warning(self):
        """If Google OAuth credentials are not configured, user is gracefully redirected with a flash warning."""
        self.app.config['GOOGLE_CLIENT_ID'] = ''
        self.app.config['GOOGLE_CLIENT_SECRET'] = ''

        response = self.client.get('/auth/google', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Google Login is currently not configured', response.data)

    @patch('services.oauth_service.oauth.google.authorize_redirect')
    def test_google_login_initiation_redirects_to_google(self, mock_authorize):
        """When configured, /auth/google initiates OAuth authorization redirect and preserves next destination."""
        self.app.config['GOOGLE_CLIENT_ID'] = 'real-google-id.apps.googleusercontent.com'
        self.app.config['GOOGLE_CLIENT_SECRET'] = 'real-google-secret'

        mock_authorize.return_value = self.app.response_class(
            status=302,
            headers={'Location': 'https://accounts.google.com/o/oauth2/v2/auth'}
        )

        response = self.client.get('/auth/google?next=/pricing')
        self.assertEqual(response.status_code, 302)
        mock_authorize.assert_called_once()

    def test_google_callback_user_denied_access(self):
        """When user clicks cancel on Google consent, handle cleanly without error."""
        response = self.client.get('/auth/google/callback?error=access_denied', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Google sign-in was cancelled', response.data)

    @patch('services.oauth_service.oauth.google.authorize_access_token')
    def test_google_callback_success_creates_user_and_session(self, mock_token):
        """Successful Google callback logs user in and redirects to destination."""
        mock_token.return_value = {
            'access_token': 'test-google-token',
            'userinfo': {
                'sub': 'google_user_101',
                'email': 'newgoogle@antimatrix.ai',
                'name': 'Google User',
                'picture': 'https://example.com/pic.jpg'
            }
        }

        # Set session return target
        with self.client.session_transaction() as sess:
            sess['oauth_next'] = '/careers'

        response = self.client.get('/auth/google/callback', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Location'], '/careers')

        # Verify user is created in database
        user = User.query.filter_by(email='newgoogle@antimatrix.ai').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.name, 'Google User')
        self.assertEqual(user.provider, 'google')
        self.assertEqual(user.provider_id, 'google_user_101')
        self.assertEqual(user.profile_picture, 'https://example.com/pic.jpg')

    # ── 3. GitHub OAuth Routes ──────────────────────────────────────────────

    def test_github_login_unconfigured_shows_friendly_warning(self):
        """If GitHub OAuth credentials are not configured, user is gracefully redirected with a flash warning."""
        self.app.config['GITHUB_CLIENT_ID'] = ''
        self.app.config['GITHUB_CLIENT_SECRET'] = ''

        response = self.client.get('/auth/github', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'GitHub Login is currently not configured', response.data)

    @patch('services.oauth_service.oauth.github.authorize_redirect')
    def test_github_login_initiation_redirects_to_github(self, mock_authorize):
        """When configured, /auth/github initiates OAuth authorization redirect."""
        self.app.config['GITHUB_CLIENT_ID'] = 'real-github-client-id'
        self.app.config['GITHUB_CLIENT_SECRET'] = 'real-github-secret'

        mock_authorize.return_value = self.app.response_class(
            status=302,
            headers={'Location': 'https://github.com/login/oauth/authorize'}
        )

        response = self.client.get('/auth/github')
        self.assertEqual(response.status_code, 302)
        mock_authorize.assert_called_once()

    @patch('services.oauth_service.oauth.github.get')
    @patch('services.oauth_service.oauth.github.authorize_access_token')
    def test_github_callback_with_private_email_resolution(self, mock_token, mock_get):
        """When GitHub user profile has private email, /user/emails endpoint resolves primary verified email."""
        mock_token.return_value = {'access_token': 'gho_secret123'}

        # Mock /user profile response (email is None)
        profile_resp = MagicMock()
        profile_resp.json.return_value = {
            'id': 78910,
            'name': 'Octo Developer',
            'login': 'octodev',
            'email': None,
            'avatar_url': 'https://avatars.githubusercontent.com/u/78910'
        }

        # Mock /user/emails response
        emails_resp = MagicMock()
        emails_resp.json.return_value = [
            {'email': 'secondary@noreply.github.com', 'primary': False, 'verified': True},
            {'email': 'developer@octo.dev', 'primary': True, 'verified': True}
        ]

        def get_side_effect(endpoint, **kwargs):
            if endpoint == 'user':
                return profile_resp
            elif endpoint == 'user/emails':
                return emails_resp
            raise ValueError(f"Unexpected endpoint {endpoint}")

        mock_get.side_effect = get_side_effect

        response = self.client.get('/auth/github/callback', follow_redirects=False)
        self.assertEqual(response.status_code, 302)

        # Verify user was created with the resolved primary verified email
        user = User.query.filter_by(email='developer@octo.dev').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.name, 'Octo Developer')
        self.assertEqual(user.provider, 'github')
        self.assertEqual(user.provider_id, '78910')
        self.assertEqual(user.profile_picture, 'https://avatars.githubusercontent.com/u/78910')

    # ── 4. Standard Auth & Regressions ─────────────────────────────────────

    def test_email_password_login_continues_to_work(self):
        """Standard email and password login flow remains 100% functional."""
        user = User(name='Local Tester', email='local@antimatrix.ai')
        user.set_password('SecretPass2026!')
        db.session.add(user)
        db.session.commit()

        # Login via POST
        res = self.client.post('/login', data={
            'email': 'local@antimatrix.ai',
            'password': 'SecretPass2026!'
        }, follow_redirects=False)

        self.assertEqual(res.status_code, 302)

    def test_logout_flow(self):
        """Logging out clears session and redirects to home."""
        user = User(name='Logout User', email='logout@antimatrix.ai')
        user.set_password('SecretPass2026!')
        db.session.add(user)
        db.session.commit()

        self.client.post('/login', data={'email': 'logout@antimatrix.ai', 'password': 'SecretPass2026!'})
        logout_res = self.client.get('/logout', follow_redirects=False)
        self.assertEqual(logout_res.status_code, 302)

    def test_login_page_renders_oauth_buttons(self):
        """Login page displays 'Continue with Google' and 'Continue with GitHub' buttons."""
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Continue with Google', response.data)
        self.assertIn(b'Continue with GitHub', response.data)
        self.assertIn(b'btn-google-login', response.data)
        self.assertIn(b'btn-github-login', response.data)

    def test_signup_page_renders_oauth_buttons(self):
        """Signup page displays 'Continue with Google' and 'Continue with GitHub' buttons."""
        response = self.client.get('/signup')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Continue with Google', response.data)
        self.assertIn(b'Continue with GitHub', response.data)
        self.assertIn(b'btn-google-signup', response.data)
        self.assertIn(b'btn-github-signup', response.data)

    def test_core_pages_continue_to_work(self):
        """Verify that public site pages load without any errors."""
        routes = ['/', '/about', '/services', '/careers', '/pricing', '/contact']
        for r in routes:
            res = self.client.get(r)
            self.assertEqual(res.status_code, 200, f"Route {r} failed with status {res.status_code}")


if __name__ == '__main__':
    unittest.main()
