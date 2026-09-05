import os
import io
import unittest
from app import create_app
from models import db, User, JobPosting, JobApplication


class DeleteAllJobsTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()

        self.app_context = self.app.app_context()
        self.app_context.push()

        db.create_all()

        # Clean slate
        JobApplication.query.delete()
        JobPosting.query.delete()
        db.session.commit()

        # Ensure admin user
        self.admin = User.query.filter_by(email='admin@antimatrix.ai').first()
        if not self.admin:
            self.admin = User(name='Test Admin', email='admin@antimatrix.ai', role='admin', is_active=True)
            self.admin.set_password('Admin@AntiMatrix2026!')
            db.session.add(self.admin)
            db.session.commit()

        # Ensure member user
        self.member = User.query.filter_by(email='member@example.com').first()
        if not self.member:
            self.member = User(name='Regular Member', email='member@example.com', role='member', is_active=True)
            self.member.set_password('Member@2026!')
            db.session.add(self.member)
            db.session.commit()

    def tearDown(self):
        self.app_context.pop()

    def seed_test_jobs(self, count=5):
        jobs = []
        for i in range(1, count + 1):
            job = JobPosting(
                title=f"Test Position #{i}",
                department="Engineering",
                location="Remote",
                employment_type="Full-time",
                short_description=f"Short description for job #{i}",
                description=f"Comprehensive full description for test role #{i}",
                skills="Python, SQL, Cloud",
                requirements="Requirements line 1\nRequirements line 2",
                responsibilities="Responsibility 1\nResponsibility 2",
                salary="$100k - $120k",
                is_active=True
            )
            jobs.append(job)
        db.session.add_all(jobs)
        db.session.commit()

        # Add candidate application to job 1
        app_record = JobApplication(
            job_id=jobs[0].id,
            full_name="Candidate One",
            email="candidate1@example.com",
            phone="+1 555 123 4567",
            college="MIT",
            degree="BS CS",
            department="CS",
            graduation_year="2025",
            skills="Python, Cloud",
            cover_letter="Cover letter...",
            resume_filename="test_resume.pdf",
            resume_path=os.path.join(self.app.config['UPLOAD_FOLDER'], 'test_resume.pdf'),
            status="New"
        )
        db.session.add(app_record)
        db.session.commit()

    def login_admin(self):
        return self.client.post('/login', data={'email': 'admin@antimatrix.ai', 'password': 'Admin@AntiMatrix2026!'})

    def login_member(self):
        return self.client.post('/login', data={'email': 'member@example.com', 'password': 'Member@2026!'})

    def logout(self):
        return self.client.get('/logout')

    def test_01_unauthorized_access(self):
        """Test guest and member access to delete-all endpoint."""
        self.seed_test_jobs(3)

        # 1. Guest request -> redirect to login
        res = self.client.post('/admin/jobs/delete-all', data={'confirmation': 'DELETE'})
        self.assertIn(res.status_code, [302, 308])
        self.assertEqual(JobPosting.query.count(), 3)

        # 2. Member request -> 403 Forbidden
        self.login_member()
        res = self.client.post('/admin/jobs/delete-all', data={'confirmation': 'DELETE'})
        self.assertEqual(res.status_code, 403)
        self.assertEqual(JobPosting.query.count(), 3)
        self.logout()

    def test_02_invalid_confirmation_rejected(self):
        """Test that invalid confirmation inputs (e.g. 'delete', empty, 'NO') are rejected."""
        self.seed_test_jobs(3)
        self.login_admin()

        # Lowercase 'delete'
        res = self.client.post('/admin/jobs/delete-all', data={'confirmation': 'delete'}, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Deletion cancelled. You must type DELETE to confirm.', res.data)
        self.assertEqual(JobPosting.query.count(), 3)

        # Empty string
        res = self.client.post('/admin/jobs/delete-all', data={'confirmation': ''}, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Deletion cancelled. You must type DELETE to confirm.', res.data)
        self.assertEqual(JobPosting.query.count(), 3)

        self.logout()

    def test_03_successful_bulk_deletion(self):
        """Test deleting 5 jobs with exact DELETE confirmation."""
        self.seed_test_jobs(5)
        self.login_admin()

        # Verify 5 jobs before delete
        res_before = self.client.get('/admin/jobs')
        self.assertEqual(res_before.status_code, 200)
        self.assertIn(b'Job Postings (5)', res_before.data)
        self.assertIn(b'Delete All Job Postings', res_before.data)

        # Perform delete-all
        res_delete = self.client.post('/admin/jobs/delete-all', data={'confirmation': 'DELETE'}, follow_redirects=True)
        self.assertEqual(res_delete.status_code, 200)
        self.assertIn(b'All job postings have been deleted successfully.', res_delete.data)
        self.assertIn(b'Job Postings (0)', res_delete.data)
        self.assertIn(b'No Job Postings Match Criteria', res_delete.data)

        # Database verification
        self.assertEqual(JobPosting.query.count(), 0)
        self.assertEqual(JobApplication.query.count(), 0)

        # Verify Dashboard stats updated
        res_dash = self.client.get('/admin')
        self.assertEqual(res_dash.status_code, 200)
        self.assertIn(b'Job Postings (0)', res_dash.data)

        # Verify Public Careers page shows empty state
        res_careers = self.client.get('/careers')
        self.assertEqual(res_careers.status_code, 200)
        self.assertIn(b'No Open Positions Currently', res_careers.data)
        self.assertNotIn(b'Test Position #1', res_careers.data)

        self.logout()

    def test_04_individual_delete_still_works(self):
        """Verify that deleting a single job posting continues to work properly."""
        self.seed_test_jobs(2)
        self.login_admin()

        job_to_delete = JobPosting.query.first()
        job_id = job_to_delete.id

        res = self.client.post(f'/admin/jobs/delete/{job_id}', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'safely removed', res.data)
        self.assertEqual(JobPosting.query.count(), 1)

        self.logout()


if __name__ == '__main__':
    unittest.main()
