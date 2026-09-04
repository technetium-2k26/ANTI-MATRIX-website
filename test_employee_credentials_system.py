import os
import unittest
import string
from app import create_app
from models import db, User, JobPosting, JobApplication, Payment, Employee


class EmployeeCredentialsTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('development')
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()

        self.app_context = self.app.app_context()
        self.app_context.push()

        db.create_all()
        Employee.query.delete()
        JobApplication.query.filter(
            (JobApplication.email.like('kavitha_%')) |
            (JobApplication.email == 'unpaid.candidate@example.com')
        ).delete()
        db.session.commit()

        # Create or fetch test admin
        self.admin = User.query.filter_by(email='admin@antimatrix.ai').first()
        if not self.admin:
            self.admin = User(name='Test Admin', email='admin@antimatrix.ai', role='admin', is_active=True)
            self.admin.set_password('Admin@AntiMatrix2026!')
            db.session.add(self.admin)
            db.session.commit()

        # Create normal member
        self.member = User.query.filter_by(email='member@example.com').first()
        if not self.member:
            self.member = User(name='Regular Member', email='member@example.com', role='member', is_active=True)
            self.member.set_password('Member@2026!')
            db.session.add(self.member)
            db.session.commit()

        # Ensure a base internship job posting exists
        self.job = JobPosting.query.filter_by(title='AI Research Scientist Intern').first()
        if not self.job:
            self.job = JobPosting(
                title='AI Research Scientist Intern',
                department='AI & Data',
                location='Remote (Worldwide)',
                employment_type='Internship',
                duration='3_months',
                short_description='Research and build next-generation AI architectures.',
                skills='PyTorch, Python, Transformers',
                description='AI research intern description.',
                is_active=True
            )
            db.session.add(self.job)
            db.session.commit()

    def tearDown(self):
        db.session.rollback()
        self.app_context.pop()

    def login_admin(self):
        return self.client.post('/login', data={'email': 'admin@antimatrix.ai', 'password': 'Admin@AntiMatrix2026!'})

    def login_member(self):
        return self.client.post('/login', data={'email': 'member@example.com', 'password': 'Member@2026!'})

    def logout(self):
        return self.client.get('/logout')

    def create_paid_application(self, email_suffix: str = "1"):
        """Helper to create a valid, paid, submitted application."""
        app_record = JobApplication(
            job_id=self.job.id,
            first_name='Kavitha',
            last_name=f'Raman_{email_suffix}',
            full_name=f'Kavitha Raman {email_suffix}',
            email=f'kavitha_{email_suffix}@example.com',
            phone='9876543210',
            address='456 Cyber Gateway',
            state='Karnataka',
            city='Bengaluru',
            pincode='560001',
            education_level="Bachelor's Degree",
            degree='B.Tech Computer Science',
            major='Computer Science',
            graduation_year='2026',
            resume_filename=f'resume_{email_suffix}.pdf',
            resume_path=f'uploads/resumes/resume_{email_suffix}.pdf',
            duration='3_months',
            application_fee=399,
            payment_status='paid',
            application_status='submitted',
            status='New'
        )
        db.session.add(app_record)
        db.session.flush()
        app_record.application_code = f"AM-APP-{app_record.id:06d}"
        db.session.commit()
        return app_record

    def create_unpaid_application(self):
        """Helper to create an unpaid draft application."""
        app_record = JobApplication(
            job_id=self.job.id,
            first_name='Unpaid',
            last_name='Candidate',
            full_name='Unpaid Candidate',
            email='unpaid.candidate@example.com',
            phone='9876543210',
            address='789 Silicon Street',
            state='Tamil Nadu',
            city='Chennai',
            pincode='600001',
            education_level="Bachelor's Degree",
            degree='B.Tech IT',
            major='IT',
            graduation_year='2027',
            resume_filename='unpaid_resume.pdf',
            resume_path='uploads/resumes/unpaid_resume.pdf',
            duration='1_month',
            application_fee=199,
            payment_status='pending',
            application_status='pending_payment',
            status='New'
        )
        db.session.add(app_record)
        db.session.flush()
        app_record.application_code = f"AM-APP-{app_record.id:06d}"
        db.session.commit()
        return app_record

    # -------------------------------------------------------------
    # TEST 1: Admin logs in -> Create Employee ID button visible
    # -------------------------------------------------------------
    def test_01_admin_dashboard_create_employee_button(self):
        self.login_admin()
        res = self.client.get('/admin/dashboard')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Create Employee ID', res.data)
        self.assertIn(b'/admin/employees/create', res.data)

    # -------------------------------------------------------------
    # TEST 2: Admin opens Create Employee ID -> Eligible apps displayed
    # -------------------------------------------------------------
    def test_02_open_create_employee_page(self):
        paid_app = self.create_paid_application(email_suffix="test2")
        self.login_admin()

        res = self.client.get('/admin/employees/create')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Create Employee ID', res.data)
        self.assertIn(paid_app.full_name.encode('utf-8'), res.data)
        self.assertIn(paid_app.formatted_code.encode('utf-8'), res.data)

    # -------------------------------------------------------------
    # TEST 3: Admin creates Employee ID for paid application -> Format AM####
    # -------------------------------------------------------------
    def test_03_create_employee_id_format(self):
        paid_app = self.create_paid_application(email_suffix="test3")
        self.login_admin()

        res = self.client.post('/admin/employees/create', data={'application_id': paid_app.id}, follow_redirects=False)
        self.assertEqual(res.status_code, 200)
        
        # Verify employee record created in DB
        emp = Employee.query.filter_by(application_id=paid_app.id).first()
        self.assertIsNotNone(emp)
        
        # Verify AM + 4 digits format
        self.assertTrue(emp.employee_id.startswith('AM'))
        self.assertEqual(len(emp.employee_id), 6)
        digits_part = emp.employee_id[2:]
        self.assertTrue(digits_part.isdigit())
        self.assertEqual(len(digits_part), 4)

        # Check response contains employee ID and credential confirmation
        self.assertIn(emp.employee_id.encode('utf-8'), res.data)
        self.assertIn(b'Employee Account Created Successfully', res.data)

    # -------------------------------------------------------------
    # TEST 4: Non-sequential random generation for multiple employees
    # -------------------------------------------------------------
    def test_04_non_sequential_random_ids(self):
        app1 = self.create_paid_application(email_suffix="test4_1")
        app2 = self.create_paid_application(email_suffix="test4_2")
        self.login_admin()

        self.client.post('/admin/employees/create', data={'application_id': app1.id})
        self.client.post('/admin/employees/create', data={'application_id': app2.id})

        emp1 = Employee.query.filter_by(application_id=app1.id).first()
        emp2 = Employee.query.filter_by(application_id=app2.id).first()

        self.assertIsNotNone(emp1)
        self.assertIsNotNone(emp2)
        self.assertNotEqual(emp1.employee_id, emp2.employee_id)

        # Verify neither is purely hardcoded sequential 'AM0001', 'AM0002'
        # Check that both have format AM + 4 digits
        self.assertTrue(emp1.employee_id.startswith('AM') and emp1.employee_id[2:].isdigit())
        self.assertTrue(emp2.employee_id.startswith('AM') and emp2.employee_id[2:].isdigit())

    # -------------------------------------------------------------
    # TEST 5: Database constraint check -> employee_id is unique
    # -------------------------------------------------------------
    def test_05_employee_id_uniqueness(self):
        app1 = self.create_paid_application(email_suffix="test5_1")
        app2 = self.create_paid_application(email_suffix="test5_2")

        emp1 = Employee(employee_id='AM9999', application_id=app1.id, account_status='active')
        emp1.set_password('Pass1234@#AM')
        db.session.add(emp1)
        db.session.commit()

        # Attempt to insert duplicate employee_id 'AM9999' -> should raise integrity error
        emp2 = Employee(employee_id='AM9999', application_id=app2.id, account_status='active')
        emp2.set_password('Pass5678@#AM')
        db.session.add(emp2)
        with self.assertRaises(Exception):
            db.session.commit()
        db.session.rollback()

    # -------------------------------------------------------------
    # TEST 6: Database password check -> Only password_hash stored
    # -------------------------------------------------------------
    def test_06_database_password_hashing(self):
        app = self.create_paid_application(email_suffix="test6")
        self.login_admin()

        res = self.client.post('/admin/employees/create', data={'application_id': app.id})
        self.assertEqual(res.status_code, 200)

        emp = Employee.query.filter_by(application_id=app.id).first()
        self.assertIsNotNone(emp)
        
        # Verify password_hash is stored and is a valid Werkzeug/scrypt/pbkdf2 hash
        self.assertIsNotNone(emp.password_hash)
        self.assertTrue(emp.password_hash.startswith('scrypt:') or emp.password_hash.startswith('pbkdf2:'))
        
        # Verify model has no 'password' plaintext attribute in DB columns
        columns = [c.name for c in Employee.__table__.columns]
        self.assertIn('password_hash', columns)
        self.assertNotIn('password', columns)

    # -------------------------------------------------------------
    # TEST 7, 8, 9: Copy Employee ID, Copy Password, Copy Credentials
    # -------------------------------------------------------------
    def test_07_08_09_copy_credentials_buttons(self):
        app = self.create_paid_application(email_suffix="test789")
        self.login_admin()

        res = self.client.post('/admin/employees/create', data={'application_id': app.id})
        self.assertEqual(res.status_code, 200)

        html = res.data.decode('utf-8')
        # Check for Copy Employee ID button
        self.assertIn('Copy Employee ID', html)
        # Check for Copy Password button
        self.assertIn('Copy Password', html)
        # Check for Copy Credentials button
        self.assertIn('Copy Credentials', html)
        # Check for password toggle
        self.assertIn('togglePasswordVisibility', html)

    # -------------------------------------------------------------
    # TEST 10: Refresh/revisit employee details -> Plaintext password NOT retrievable
    # -------------------------------------------------------------
    def test_10_revisit_employee_detail_no_plaintext_password(self):
        app = self.create_paid_application(email_suffix="test10")
        self.login_admin()

        # Create employee
        self.client.post('/admin/employees/create', data={'application_id': app.id})
        emp = Employee.query.filter_by(application_id=app.id).first()

        # Visit employee profile
        res_view = self.client.get(f'/admin/employees/{emp.employee_id}')
        self.assertEqual(res_view.status_code, 200)
        
        html_view = res_view.data.decode('utf-8')
        # Employee ID is visible
        self.assertIn(emp.employee_id, html_view)
        # Candidate name and job visible
        self.assertIn(app.full_name, html_view)
        # Password hash or password must NOT be in the HTML view
        self.assertNotIn(emp.password_hash, html_view)
        self.assertNotIn('Generated Password', html_view)

    # -------------------------------------------------------------
    # TEST 11: Duplicate employee creation prevented
    # -------------------------------------------------------------
    def test_11_prevent_duplicate_employee(self):
        app = self.create_paid_application(email_suffix="test11")
        self.login_admin()

        # First creation -> succeeds
        res1 = self.client.post('/admin/employees/create', data={'application_id': app.id})
        self.assertEqual(res1.status_code, 200)
        emp = Employee.query.filter_by(application_id=app.id).first()

        # Second creation attempt for same application -> redirected with warning
        res2 = self.client.post('/admin/employees/create', data={'application_id': app.id}, follow_redirects=True)
        self.assertEqual(res2.status_code, 200)
        self.assertIn(b'already exists', res2.data)
        
        # Verify total employee count for this app is still exactly 1
        emp_count = Employee.query.filter_by(application_id=app.id).count()
        self.assertEqual(emp_count, 1)

    # -------------------------------------------------------------
    # TEST 12: Attempt employee creation for unpaid application blocked
    # -------------------------------------------------------------
    def test_12_block_unpaid_application_employee_creation(self):
        unpaid_app = self.create_unpaid_application()
        self.login_admin()

        res = self.client.post('/admin/employees/create', data={'application_id': unpaid_app.id}, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'cannot be created until the application payment is completed', res.data)

        # Verify no employee was created in database
        emp = Employee.query.filter_by(application_id=unpaid_app.id).first()
        self.assertIsNone(emp)

    # -------------------------------------------------------------
    # TEST 13: Normal / Non-admin user access denied
    # -------------------------------------------------------------
    def test_13_non_admin_access_denied(self):
        paid_app = self.create_paid_application(email_suffix="test13")

        # 1. Unauthenticated guest -> redirects to login
        res_guest = self.client.get('/admin/employees/create')
        self.assertIn(res_guest.status_code, [302, 308])

        res_guest_post = self.client.post('/admin/employees/create', data={'application_id': paid_app.id})
        self.assertIn(res_guest_post.status_code, [302, 308])

        # 2. Regular user (role='member') -> 403 Forbidden
        self.login_member()
        res_member_get = self.client.get('/admin/employees/create')
        self.assertEqual(res_member_get.status_code, 403)

        res_member_post = self.client.post('/admin/employees/create', data={'application_id': paid_app.id})
        self.assertEqual(res_member_post.status_code, 403)
        self.logout()

    # -------------------------------------------------------------
    # TEST 14: Server validates actual DB record, rejects manipulated IDs
    # -------------------------------------------------------------
    def test_14_reject_invalid_or_manipulated_application_ids(self):
        self.login_admin()

        # Non-existent application ID
        res_invalid = self.client.post('/admin/employees/create', data={'application_id': 999999}, follow_redirects=True)
        self.assertEqual(res_invalid.status_code, 200)
        self.assertIn(b'does not exist', res_invalid.data)

        # Empty / non-integer application ID
        res_bad_id = self.client.post('/admin/employees/create', data={'application_id': 'malicious_input'}, follow_redirects=True)
        self.assertEqual(res_bad_id.status_code, 200)
        self.assertIn(b'Invalid application identifier', res_bad_id.data)


if __name__ == '__main__':
    unittest.main()
