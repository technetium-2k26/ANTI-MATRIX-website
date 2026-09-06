import unittest
from flask_login import login_user
from app import create_app
from models import db, User


class ProfileNavigationTestCase(unittest.TestCase):
    """Test suite for profile page and navbar display for user and admin."""

    def setUp(self):
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

        # Regular user
        self.user = User(
            name='Regular Tester',
            email='user@test.com',
            role='member',
            phone='+1 555-0199',
            provider='email'
        )
        self.user.set_password('Password123!')
        db.session.add(self.user)

        # Admin user
        self.admin = User(
            name='Admin Master',
            email='admin@test.com',
            role='admin',
            phone='+1 555-0988',
            provider='email'
        )
        self.admin.set_password('AdminPass123!')
        db.session.add(self.admin)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _login(self, email, password):
        return self.client.post('/login', data={
            'email': email,
            'password': password
        }, follow_redirects=True)

    def test_unauthenticated_profile_redirects_to_login(self):
        resp = self.client.get('/profile', follow_redirects=False)
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login', resp.headers['Location'])

    def test_user_profile_page_displays_name_email_phone_no_member_badge(self):
        self._login('user@test.com', 'Password123!')
        resp = self.client.get('/profile')
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)

        # Must display Name, Email, and Phone
        self.assertIn('Regular Tester', html)
        self.assertIn('user@test.com', html)
        self.assertIn('+1 555-0199', html)

        # Must not contain Member badge
        self.assertNotIn('>Member<', html)
        self.assertNotIn('badge">Member', html)

        # Dropdown links
        self.assertIn('My Profile', html)
        self.assertIn('My Applications', html)
        self.assertIn('Log Out', html)

    def test_user_navbar_removes_name_from_trigger_button(self):
        self._login('user@test.com', 'Password123!')
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)

        # Trigger button has profile-dropdown-btn with avatar and chevron, but NOT "Regular Tester"
        # The trigger button ends at </button> before #profile-dropdown-panel
        btn_start = html.find('id="profile-dropdown-btn"')
        self.assertNotEqual(btn_start, -1)
        btn_end = html.find('</button>', btn_start)
        btn_content = html[btn_start:btn_end]

        # Name should NOT be inside the button trigger
        self.assertNotIn('Regular Tester', btn_content)

        # But initial letter should be there
        self.assertIn('R', btn_content)

    def test_admin_profile_page_and_navbar_no_member(self):
        self._login('admin@test.com', 'AdminPass123!')
        resp = self.client.get('/profile')
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)

        # Displays Name, Email, and Phone
        self.assertIn('Admin Master', html)
        self.assertIn('admin@test.com', html)
        self.assertIn('+1 555-0988', html)

        # No Member mention
        self.assertNotIn('>Member<', html)

        # Dropdown links for admin
        self.assertIn('My Profile', html)
        self.assertIn('My Applications', html)
        self.assertIn('Admin Dashboard', html)
        self.assertIn('Log Out', html)

    def test_update_profile_saves_name_and_phone(self):
        self._login('user@test.com', 'Password123!')
        resp = self.client.post('/profile', data={
            'name': 'Updated User Name',
            'phone': '+91 99999 88888'
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)

        # Verify DB
        u = db.session.get(User, self.user.id)
        self.assertEqual(u.name, 'Updated User Name')
        self.assertEqual(u.phone, '+91 99999 88888')
