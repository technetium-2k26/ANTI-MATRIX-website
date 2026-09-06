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

    def test_dropdown_panel_contains_only_menu_links_and_no_user_info(self):
        """Dropdown menu panel must only display My Profile, My Applications, and Log Out (no name/email header card)."""
        self._login('user@test.com', 'Password123!')
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)

        panel_start = html.find('id="profile-dropdown-panel"')
        self.assertNotEqual(panel_start, -1)
        panel_end = html.find('</div>\n        </div>\n      {% else %}', panel_start)
        if panel_end == -1:
            panel_end = html.find('</nav>', panel_start)
        panel_content = html[panel_start:panel_end]

        # Must NOT contain user name or user email inside the dropdown popup
        self.assertNotIn('Regular Tester', panel_content)
        self.assertNotIn('user@test.com', panel_content)

        # Must contain menu links
        self.assertIn('My Profile', panel_content)
        self.assertIn('My Applications', panel_content)
        self.assertIn('Log Out', panel_content)

    def test_user_profile_shows_applied_jobs(self):
        """Profile page must display what positions the user applied for."""
        from models.job import JobPosting, JobApplication
        
        job = JobPosting(
            title='Senior Backend Architect',
            department='Engineering',
            location='Bengaluru, India',
            experience='4-7 Years',
            employment_type='Full-time',
            short_description='Test Job Short Description',
            description='Test Job Description',
            requirements='Python, Flask',
            is_active=True
        )
        db.session.add(job)
        db.session.flush()

        app = JobApplication(
            job_id=job.id,
            user_id=self.user.id,
            application_code='AM-APP-998877',
            full_name='Regular Tester',
            email='user@test.com',
            phone='+1 555-0199',
            resume_filename='resume.pdf',
            resume_path='/tmp/resume.pdf',
            status='Under Review'
        )
        db.session.add(app)
        db.session.commit()

        self._login('user@test.com', 'Password123!')
        resp = self.client.get('/profile')
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)

        # Must display the applied job title and reference code
        self.assertIn('Senior Backend Architect', html)
        self.assertIn('AM-APP-998877', html)
        self.assertIn('Under Review', html)

    def test_user_navbar_removes_name_from_trigger_button(self):
        self._login('user@test.com', 'Password123!')
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)

        # Trigger button has profile-dropdown-btn with avatar and chevron, but NOT "Regular Tester"
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

