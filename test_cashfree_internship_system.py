import os
import io
import json
import time
import unittest
from app import create_app
from models import db, User, JobPosting, JobApplication, Payment
from services.cashfree_service import CashfreeService
from config import INTERNSHIP_FEES, INDIA_STATES_AND_CITIES


class CashfreeInternshipSystemTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app.config['CASHFREE_ENVIRONMENT'] = 'test'
        self.app.config['PAYMENT_TEST_MODE'] = False
        self.client = self.app.test_client()

        self.app_context = self.app.app_context()
        self.app_context.push()

        db.create_all()
        Payment.query.delete()
        JobApplication.query.delete()
        db.session.commit()

        # Create Admin
        self.admin = User.query.filter_by(email='admin@antimatrix.ai').first()
        if not self.admin:
            self.admin = User(name='Test Admin', email='admin@antimatrix.ai', role='admin', is_active=True)
            self.admin.set_password('Admin@AntiMatrix2026!')
            db.session.add(self.admin)
            db.session.commit()

        # Create Normal Member
        self.member = User.query.filter_by(email='member@example.com').first()
        if not self.member:
            self.member = User(name='Regular Member', email='member@example.com', role='member', is_active=True)
            self.member.set_password('Member@2026!')
            db.session.add(self.member)
            db.session.commit()

        # By default authenticate client as member for candidate endpoints
        self.login_member()

    def tearDown(self):
        self.app_context.pop()

    def login_admin(self):
        self.logout_user()
        return self.client.post('/login', data={'email': 'admin@antimatrix.ai', 'password': 'Admin@AntiMatrix2026!'})

    def login_member(self):
        self.logout_user()
        return self.client.post('/login', data={'email': 'member@example.com', 'password': 'Member@2026!'})

    def logout_user(self):
        return self.client.get('/logout')

    def _create_candidate_application(self, duration='3_months', payment_status='pending', app_status='pending_payment', full_name='Arun Kumar', email='arun.kumar@example.com'):
        """Helper to create a fully populated candidate application fixture."""
        job = JobPosting.query.filter_by(title=f'AI Engineer Intern ({duration})').first()
        if not job:
            job = JobPosting(
                title=f'AI Engineer Intern ({duration})',
                department='Artificial Intelligence',
                location='Chennai, India',
                employment_type='Internship',
                duration=duration,
                short_description='Work on cutting-edge LLMs and computer vision pipelines.',
                description='Comprehensive AI internship working directly with senior architects.',
                skills='Python, PyTorch, Transformers, FastAPI',
                is_active=True
            )
            db.session.add(job)
            db.session.commit()

        doc_dir = os.path.join(self.app.root_path, 'uploads', 'documents')
        res_dir = os.path.join(self.app.root_path, 'uploads', 'resumes')
        os.makedirs(doc_dir, exist_ok=True)
        os.makedirs(res_dir, exist_ok=True)

        aadhaar_path = os.path.join(doc_dir, 'test_aadhaar.pdf')
        pan_path = os.path.join(doc_dir, 'test_pan.pdf')
        college_id_path = os.path.join(doc_dir, 'test_college_id.pdf')
        resume_path = os.path.join(res_dir, 'test_resume.pdf')

        for p in [aadhaar_path, pan_path, college_id_path, resume_path]:
            with open(p, 'wb') as f:
                f.write(b'%PDF-1.4 Mock document')

        parts = full_name.split(' ', 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else 'Kumar'

        app_record = JobApplication(
            user_id=self.member.id,
            job_id=job.id,
            first_name=first_name,
            last_name=last_name,
            full_name=full_name,
            email=email,
            phone='9876543210',
            address='123 Tech Park Avenue',
            state='Tamil Nadu',
            city='Chennai',
            pincode='600001',
            education_level="Bachelor's Degree",
            college='Anna University',
            department='Computer Science & Engineering',
            degree='B.Tech',
            major='Computer Science & Engineering',
            year_of_study='3rd Year',
            graduation_year='2026',
            current_cgpa=8.65,
            skills='Python, PyTorch, SQL',
            duration=duration,
            application_fee=399 if duration == '3_months' else 199,
            payment_status=payment_status,
            application_status=app_status,
            aadhaar_filename='test_aadhaar.pdf',
            aadhaar_path=aadhaar_path,
            pan_filename='test_pan.pdf',
            pan_path=pan_path,
            college_id_filename='test_college_id.pdf',
            college_id_path=college_id_path,
            resume_filename='test_resume.pdf',
            resume_path=resume_path,
            status='New'
        )
        db.session.add(app_record)
        db.session.commit()
        return job, app_record

    # -------------------------------------------------------------
    # TEST SCENARIO 1: 1-Month Internship Flow (₹199, No Proofs in UI)
    # -------------------------------------------------------------
    def test_scenario_01_1month_internship_flow(self):
        """
        Scenario 1:
        Job duration: 1 Month
        Expected: Form displays Personal fields, Address, Education, Resume.
        Does NOT display: Aadhaar, PAN, College ID upload fields.
        Payment: ₹199.
        Successful Cashfree payment: Application ID generated, details stored, submitted, success page.
        """
        self.login_admin()
        JobPosting.query.filter_by(title='Web Engineering Intern (1M)').delete()
        db.session.commit()

        job_data = {
            'title': 'Web Engineering Intern (1M)',
            'department': 'Engineering',
            'location': 'Chennai',
            'employment_type': 'Internship',
            'duration': '1_month',
            'short_description': 'Build modern enterprise web applications.',
            'description': 'Full stack engineering internship.',
            'is_active': 'true'
        }
        res = self.client.post('/admin/jobs/create', data=job_data, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.login_member()

        job = JobPosting.query.filter_by(title='Web Engineering Intern (1M)').first()
        self.assertEqual(job.duration, '1_month')
        self.assertEqual(job.fee_inr, 199)

        # GET Apply page -> Verify 1 Month duration shown and proofs section not rendered
        apply_page = self.client.get(f'/careers/apply/{job.id}')
        self.assertEqual(apply_page.status_code, 200)
        html = apply_page.data.decode('utf-8')
        self.assertIn('Internship Duration: 1 Month', html)
        self.assertIn('₹199', html)
        self.assertNotIn('Upload Aadhaar Card', html)
        self.assertNotIn('Upload PAN Card', html)
        self.assertNotIn('Upload College ID', html)
        self.assertIn('Resume / Curriculum Vitae', html)

        # Submit 1-month application
        resume_file = (io.BytesIO(b'%PDF-1.4 Mock resume for 1M candidate'), 'arun_1m_resume.pdf')
        form_data = {
            'first_name': 'Arun',
            'last_name': 'Kumar',
            'email': 'arun.1m@example.com',
            'phone': '9876543210',
            'address': 'Flat 4A, Green Meadows, Anna Nagar',
            'state': 'Tamil Nadu',
            'city': 'Chennai',
            'pincode': '600040',
            'education_level': "Bachelor's Degree",
            'degree': 'B.Tech',
            'major': 'Information Technology',
            'graduation_year': '2026',
            'resume': resume_file
        }
        res_post = self.client.post(f'/careers/apply/{job.id}', data=form_data, content_type='multipart/form-data', follow_redirects=False)
        self.assertEqual(res_post.status_code, 302)

        app_record = JobApplication.query.filter_by(email='arun.1m@example.com').first()
        self.assertIsNotNone(app_record)
        self.assertEqual(app_record.duration, '1_month')
        self.assertEqual(app_record.application_fee, 199)
        self.assertEqual(app_record.first_name, 'Arun')
        self.assertEqual(app_record.last_name, 'Kumar')
        self.assertEqual(app_record.address, 'Flat 4A, Green Meadows, Anna Nagar')
        self.assertEqual(app_record.state, 'Tamil Nadu')
        self.assertEqual(app_record.city, 'Chennai')
        self.assertEqual(app_record.pincode, '600040')
        self.assertEqual(app_record.payment_status, 'pending')
        self.assertEqual(app_record.application_status, 'pending_payment')

        # Review page
        rev_res = self.client.get(f'/careers/apply/review/{app_record.id}')
        self.assertEqual(rev_res.status_code, 200)
        self.assertIn(b'199', rev_res.data)

        # Checkout initiation
        chk_res = self.client.post(f'/careers/apply/checkout/{app_record.id}', follow_redirects=False)
        self.assertEqual(chk_res.status_code, 302)
        payment = Payment.query.filter_by(application_id=app_record.id).first()
        self.assertEqual(payment.amount, 199.0)

        # Payment Return Callback -> Success
        ret_res = self.client.get(f'/payment/cashfree/return?order_id={payment.cashfree_order_id}&sim_status=SUCCESS', follow_redirects=True)
        self.assertEqual(ret_res.status_code, 200)
        self.assertIn(b'Application Submitted Successfully', ret_res.data)
        self.assertIn(b'199', ret_res.data)

        db.session.refresh(app_record)
        self.assertEqual(app_record.payment_status, 'paid')
        self.assertIn(app_record.application_status, ['submitted', 'APPLIED'])
        self.assertTrue(app_record.application_code.startswith('AM-APP-'))

    # -------------------------------------------------------------
    # TEST SCENARIO 2: 3-Month Internship Flow (₹399, Aadhaar Required)
    # -------------------------------------------------------------
    def test_scenario_02_3month_internship_flow(self):
        """
        Scenario 2:
        Job duration: 3 Months
        Expected: Form displays Personal fields, Address, Education, Aadhaar, PAN, College ID, Resume.
        Aadhaar required. PAN optional. College ID optional.
        Payment: ₹399.
        Successful Cashfree payment: Application ID generated, details stored, submitted, success page.
        """
        self.login_admin()
        JobPosting.query.filter_by(title='AI Engineer Intern (3M)').delete()
        db.session.commit()

        job_data = {
            'title': 'AI Engineer Intern (3M)',
            'department': 'Artificial Intelligence',
            'location': 'Chennai',
            'employment_type': 'Internship',
            'duration': '3_months',
            'short_description': 'Deep learning models.',
            'description': 'AI internship.',
            'is_active': 'true'
        }
        self.client.post('/admin/jobs/create', data=job_data, follow_redirects=True)
        self.login_member()

        job = JobPosting.query.filter_by(title='AI Engineer Intern (3M)').first()
        self.assertEqual(job.duration, '3_months')
        self.assertEqual(job.fee_inr, 399)

        # GET Apply page -> Verify 3 Month duration and proofs section are rendered
        apply_page = self.client.get(f'/careers/apply/{job.id}')
        self.assertEqual(apply_page.status_code, 200)
        html = apply_page.data.decode('utf-8')
        self.assertIn('Internship Duration: 3 Months', html)
        self.assertIn('₹399', html)
        self.assertIn('Upload Aadhaar Card', html)
        self.assertIn('Upload PAN Card', html)
        self.assertIn('Upload College ID', html)

        # Submit with Aadhaar and Resume (PAN and College ID omitted)
        resume_file = (io.BytesIO(b'%PDF-1.4 Mock resume'), 'divya_resume.pdf')
        aadhaar_file = (io.BytesIO(b'%PDF-1.4 Mock aadhaar'), 'divya_aadhaar.pdf')
        form_data = {
            'first_name': 'Divya',
            'last_name': 'Ramesh',
            'email': 'divya.ramesh@example.com',
            'phone': '9876543211',
            'address': 'No 15, Lake View Road',
            'state': 'Karnataka',
            'city': 'Bengaluru',
            'pincode': '560001',
            'education_level': "Master's Degree",
            'degree': 'M.Tech',
            'major': 'Artificial Intelligence',
            'graduation_year': '2027',
            'resume': resume_file,
            'aadhaar': aadhaar_file
        }
        res_post = self.client.post(f'/careers/apply/{job.id}', data=form_data, content_type='multipart/form-data', follow_redirects=False)
        self.assertEqual(res_post.status_code, 302)

        app_record = JobApplication.query.filter_by(email='divya.ramesh@example.com').first()
        self.assertIsNotNone(app_record)
        self.assertEqual(app_record.duration, '3_months')
        self.assertEqual(app_record.application_fee, 399)

        # Checkout -> ₹399
        self.client.post(f'/careers/apply/checkout/{app_record.id}', follow_redirects=False)
        payment = Payment.query.filter_by(application_id=app_record.id).first()
        self.assertEqual(payment.amount, 399.0)

        # Return callback
        ret_res = self.client.get(f'/payment/cashfree/return?order_id={payment.cashfree_order_id}&sim_status=SUCCESS', follow_redirects=True)
        self.assertEqual(ret_res.status_code, 200)
        self.assertIn(b'Application Submitted Successfully', ret_res.data)
        self.assertIn(b'399', ret_res.data)

    # -------------------------------------------------------------
    # TEST SCENARIO 3: Amount Manipulation Defense (₹399 Enforced)
    # -------------------------------------------------------------
    def test_scenario_03_price_tampering_defense(self):
        """Scenario 3: 3-month internship but candidate modifies browser amount to ₹199 or ₹1. Backend ignores it."""
        job, app_record = self._create_candidate_application(duration='3_months')

        # Candidate attempts to inject manipulated amount parameters
        self.client.post(
            f'/careers/apply/checkout/{app_record.id}',
            data={'amount': '199', 'fee': '1', 'order_amount': '10'},
            follow_redirects=False
        )

        payment = Payment.query.filter_by(application_id=app_record.id).first()
        self.assertIsNotNone(payment)
        self.assertEqual(payment.amount, 399.0, "Server must enforce 399.0 for 3-month internship ignoring client values")

    # -------------------------------------------------------------
    # TEST SCENARIO 4: 1-Month Missing Resume Rejected
    # -------------------------------------------------------------
    def test_scenario_04_1month_missing_resume_rejected(self):
        """Scenario 4: 1-month internship submitted without Resume -> Validation error."""
        job = JobPosting.query.filter_by(duration='1_month').first()
        if not job:
            job = JobPosting(title='Intern 1M', department='IT', location='Chennai', employment_type='Internship', duration='1_month', is_active=True, short_description='s', description='d')
            db.session.add(job)
            db.session.commit()

        form_data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test.noresume@example.com',
            'phone': '9876543210',
            'address': 'Some Address',
            'state': 'Tamil Nadu',
            'city': 'Chennai',
            'pincode': '600001',
            'education_level': "Bachelor's Degree",
            'degree': 'B.Tech',
            'major': 'CS',
            'graduation_year': '2026'
            # No resume attached
        }
        res = self.client.post(f'/careers/apply/{job.id}', data=form_data, content_type='multipart/form-data', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Resume: File is required', res.data)

    # -------------------------------------------------------------
    # TEST SCENARIO 5: 3-Month Missing Aadhaar Rejected
    # -------------------------------------------------------------
    def test_scenario_05_3month_missing_aadhaar_rejected(self):
        """Scenario 5: 3-month internship submitted without Aadhaar -> Validation error."""
        job = JobPosting.query.filter_by(duration='3_months').first()
        if not job:
            job = JobPosting(title='Intern 3M', department='IT', location='Chennai', employment_type='Internship', duration='3_months', is_active=True, short_description='s', description='d')
            db.session.add(job)
            db.session.commit()

        resume_file = (io.BytesIO(b'%PDF-1.4 Mock resume'), 'resume.pdf')
        form_data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test.noaadhaar@example.com',
            'phone': '9876543210',
            'address': 'Some Address',
            'state': 'Tamil Nadu',
            'city': 'Chennai',
            'pincode': '600001',
            'education_level': "Bachelor's Degree",
            'degree': 'B.Tech',
            'major': 'CS',
            'graduation_year': '2026',
            'resume': resume_file
            # No aadhaar attached
        }
        res = self.client.post(f'/careers/apply/{job.id}', data=form_data, content_type='multipart/form-data', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Aadhaar Card: File is required', res.data)

    # -------------------------------------------------------------
    # TEST SCENARIO 6: 3-Month Without PAN Accepted
    # -------------------------------------------------------------
    def test_scenario_06_3month_without_pan_accepted(self):
        """Scenario 6: 3-month internship where candidate does not upload PAN -> Proceeds successfully."""
        job = JobPosting.query.filter_by(duration='3_months').first()
        if not job:
            job = JobPosting(title='Intern 3M', department='IT', location='Chennai', employment_type='Internship', duration='3_months', is_active=True, short_description='s', description='d')
            db.session.add(job)
            db.session.commit()

        resume_file = (io.BytesIO(b'%PDF-1.4 Mock resume'), 'resume.pdf')
        aadhaar_file = (io.BytesIO(b'%PDF-1.4 Mock aadhaar'), 'aadhaar.pdf')
        form_data = {
            'first_name': 'Sanjay',
            'last_name': 'Verma',
            'email': 'sanjay.nopan@example.com',
            'phone': '9876543210',
            'address': 'Some Address',
            'state': 'Maharashtra',
            'city': 'Mumbai',
            'pincode': '400001',
            'education_level': "Bachelor's Degree",
            'degree': 'B.Sc',
            'major': 'Data Science',
            'graduation_year': '2025',
            'resume': resume_file,
            'aadhaar': aadhaar_file
            # PAN omitted
        }
        res = self.client.post(f'/careers/apply/{job.id}', data=form_data, content_type='multipart/form-data', follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        app_record = JobApplication.query.filter_by(email='sanjay.nopan@example.com').first()
        self.assertIsNotNone(app_record)
        self.assertIsNone(app_record.pan_filename)

    # -------------------------------------------------------------
    # TEST SCENARIO 7: 3-Month Without College ID Accepted
    # -------------------------------------------------------------
    def test_scenario_07_3month_without_college_id_accepted(self):
        """Scenario 7: 3-month internship where candidate does not upload College ID -> Proceeds successfully."""
        job = JobPosting.query.filter_by(duration='3_months').first()
        if not job:
            job = JobPosting(title='Intern 3M', department='IT', location='Chennai', employment_type='Internship', duration='3_months', is_active=True, short_description='s', description='d')
            db.session.add(job)
            db.session.commit()

        resume_file = (io.BytesIO(b'%PDF-1.4 Mock resume'), 'resume.pdf')
        aadhaar_file = (io.BytesIO(b'%PDF-1.4 Mock aadhaar'), 'aadhaar.pdf')
        form_data = {
            'first_name': 'Kavya',
            'last_name': 'Natarajan',
            'email': 'kavya.noid@example.com',
            'phone': '9876543210',
            'address': 'Some Address',
            'state': 'Tamil Nadu',
            'city': 'Coimbatore',
            'pincode': '641001',
            'education_level': "Bachelor's Degree",
            'degree': 'B.E.',
            'major': 'ECE',
            'graduation_year': '2026',
            'resume': resume_file,
            'aadhaar': aadhaar_file
            # College ID omitted
        }
        res = self.client.post(f'/careers/apply/{job.id}', data=form_data, content_type='multipart/form-data', follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        app_record = JobApplication.query.filter_by(email='kavya.noid@example.com').first()
        self.assertIsNotNone(app_record)
        self.assertIsNone(app_record.college_id_filename)

    # -------------------------------------------------------------
    # TEST SCENARIO 8: Invalid State/City Combination Rejected
    # -------------------------------------------------------------
    def test_scenario_08_invalid_state_city_combination_rejected(self):
        """Scenario 8: State: Tamil Nadu, City: Bengaluru -> Backend rejects mismatch."""
        job = JobPosting.query.filter_by(duration='3_months').first()
        if not job:
            job = JobPosting(title='Intern 3M', department='IT', location='Chennai', employment_type='Internship', duration='3_months', is_active=True, short_description='s', description='d')
            db.session.add(job)
            db.session.commit()

        resume_file = (io.BytesIO(b'%PDF-1.4 Mock resume'), 'resume.pdf')
        aadhaar_file = (io.BytesIO(b'%PDF-1.4 Mock aadhaar'), 'aadhaar.pdf')
        form_data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test.mismatch@example.com',
            'phone': '9876543210',
            'address': 'Some Address',
            'state': 'Tamil Nadu',
            'city': 'Bengaluru',  # Mismatch! Bengaluru is in Karnataka
            'pincode': '600001',
            'education_level': "Bachelor's Degree",
            'degree': 'B.Tech',
            'major': 'CS',
            'graduation_year': '2026',
            'resume': resume_file,
            'aadhaar': aadhaar_file
        }
        res = self.client.post(f'/careers/apply/{job.id}', data=form_data, content_type='multipart/form-data', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Selected city is not valid for state Tamil Nadu', res.data)

    # -------------------------------------------------------------
    # TEST SCENARIO 9: Refresh Return Callback -> No Duplicate Records
    # -------------------------------------------------------------
    def test_scenario_09_refresh_return_page_no_duplicates(self):
        """Scenario 9: Candidate refreshes success/return page -> No duplicate application or payment or new Application ID."""
        job, app_record = self._create_candidate_application(duration='3_months')
        self.client.post(f'/careers/apply/checkout/{app_record.id}', follow_redirects=False)
        payment = Payment.query.filter_by(application_id=app_record.id).first()

        # 1st Return
        res1 = self.client.get(f'/payment/cashfree/return?order_id={payment.cashfree_order_id}&sim_status=SUCCESS', follow_redirects=True)
        self.assertEqual(res1.status_code, 200)
        db.session.refresh(app_record)
        orig_code = app_record.application_code
        total_apps = JobApplication.query.filter_by(email=app_record.email).count()
        total_payments = Payment.query.filter_by(application_id=app_record.id).count()
        self.assertEqual(total_apps, 1)
        self.assertEqual(total_payments, 1)

        # 2nd Return (Page refresh simulation)
        res2 = self.client.get(f'/payment/cashfree/return?order_id={payment.cashfree_order_id}&sim_status=SUCCESS', follow_redirects=True)
        self.assertEqual(res2.status_code, 200)
        db.session.refresh(app_record)
        self.assertEqual(app_record.application_code, orig_code)
        self.assertEqual(JobApplication.query.filter_by(email=app_record.email).count(), 1)
        self.assertEqual(Payment.query.filter_by(application_id=app_record.id).count(), 1)

    # -------------------------------------------------------------
    # TEST SCENARIO 10: Duplicate Webhook Handling Idempotency
    # -------------------------------------------------------------
    def test_scenario_10_duplicate_webhook_idempotency(self):
        """Scenario 10: Cashfree webhook received multiple times -> Safely handled without duplicate applications or payments."""
        job, app_record = self._create_candidate_application(duration='3_months')
        self.client.post(f'/careers/apply/checkout/{app_record.id}', follow_redirects=False)
        payment = Payment.query.filter_by(application_id=app_record.id).first()

        webhook_payload = {
            'data': {
                'order': {'order_id': payment.cashfree_order_id, 'order_amount': 399.0},
                'payment': {'payment_status': 'SUCCESS', 'cf_payment_id': 'cf_wh_12345'}
            },
            'event_time': '2026-09-04T12:00:00Z',
            'type': 'PAYMENT_SUCCESS_WEBHOOK'
        }
        headers = {'x-webhook-signature': 'sim_sig', 'x-webhook-timestamp': '123456'}

        # 1st Webhook delivery
        wh_res1 = self.client.post('/payment/cashfree/webhook', json=webhook_payload, headers=headers)
        self.assertEqual(wh_res1.status_code, 200)
        self.assertEqual(wh_res1.json.get('status'), 'success')

        # 2nd Webhook delivery (Duplicate)
        wh_res2 = self.client.post('/payment/cashfree/webhook', json=webhook_payload, headers=headers)
        self.assertEqual(wh_res2.status_code, 200)
        self.assertEqual(wh_res2.json.get('status'), 'already_processed')

        # Ensure still 1 application and 1 payment record
        self.assertEqual(JobApplication.query.filter_by(email=app_record.email).count(), 1)
        self.assertEqual(Payment.query.filter_by(application_id=app_record.id).count(), 1)

    # -------------------------------------------------------------
    # TEST SCENARIO 11: Graduation Year > 2029 Rejected
    # -------------------------------------------------------------
    def test_scenario_11_graduation_year_max_2029(self):
        """Graduation year > 2029 is rejected by backend."""
        job = JobPosting.query.first()
        if not job:
            job, _ = self._create_candidate_application(duration='1_month')
        form_data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test.grad@example.com',
            'phone': '9876543210',
            'address': 'Address',
            'state': 'Tamil Nadu',
            'city': 'Chennai',
            'pincode': '600001',
            'education_level': "Bachelor's Degree",
            'degree': 'B.Tech',
            'major': 'CS',
            'graduation_year': '2032',  # Greater than 2029
            'resume': (io.BytesIO(b'%PDF-1.4 Mock resume'), 'resume.pdf')
        }
        res = self.client.post(f'/careers/apply/{job.id}', data=form_data, content_type='multipart/form-data', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Graduation Year cannot be greater than 2029', res.data)

    # -------------------------------------------------------------
    # TEST SCENARIO 12: Admin Dossier & Secure Document Access
    # -------------------------------------------------------------
    def test_scenario_12_admin_dossier_and_secure_documents(self):
        """Admin can view dossier with Address, State, City, Education, and securely download Aadhaar, PAN, College ID, Resume."""
        self.login_admin()
        job, app_record = self._create_candidate_application(duration='3_months', payment_status='paid', app_status='submitted')
        payment = Payment(
            application_id=app_record.id,
            cashfree_order_id='AM-APP-000001-PAY-001',
            cashfree_payment_session_id='session_123',
            amount=399.0,
            currency='INR',
            payment_status='paid',
            gateway='cashfree'
        )
        db.session.add(payment)
        db.session.commit()

        # Admin Dossier
        self.login_admin()
        res_dossier = self.client.get(f'/admin/applications/{app_record.id}')
        self.assertEqual(res_dossier.status_code, 200)
        html = res_dossier.data.decode('utf-8')
        self.assertIn('Arun', html)
        self.assertIn('Kumar', html)
        self.assertIn('123 Tech Park Avenue', html)
        self.assertIn('Tamil Nadu', html)
        self.assertIn('Chennai', html)
        self.assertIn('600001', html)
        self.assertIn('Cashfree Payment Record', html)

        # Secure Document Downloads (Admin authorized)
        res_resume = self.client.get(f'/admin/applications/{app_record.id}/document/resume')
        self.assertEqual(res_resume.status_code, 200)
        res_aadhaar = self.client.get(f'/admin/applications/{app_record.id}/document/aadhaar')
        self.assertEqual(res_aadhaar.status_code, 200)
        res_pan = self.client.get(f'/admin/applications/{app_record.id}/document/pan')
        self.assertEqual(res_pan.status_code, 200)
        res_cid = self.client.get(f'/admin/applications/{app_record.id}/document/college_id')
        self.assertEqual(res_cid.status_code, 200)

        self.logout_user()

        # Member unauthorized (403)
        self.login_member()
        res_unauth = self.client.get(f'/admin/applications/{app_record.id}/document/aadhaar')
        self.assertEqual(res_unauth.status_code, 403)
        self.logout_user()


if __name__ == '__main__':
    unittest.main()
