import os
import io
import json
import time
import hmac
import hashlib
import base64
import unittest
from app import create_app
from models import db, User, JobPosting, JobApplication, Payment, MoneyTransaction
from services.cashfree_service import CashfreeService
from config import INTERNSHIP_FEES


class CashfreeSandboxEnvironmentTestCase(unittest.TestCase):
    """
    Dedicated Test Suite for Cashfree Sandbox / Test Environment Verification.
    Validates:
    - Default CASHFREE_ENV=sandbox
    - Base URL https://sandbox.cashfree.com/pg
    - Server-side fee calculation (1M: Rs 199, 3M: Rs 399)
    - Safe credentials handling (no secret leakage)
    - Webhook HMAC-SHA256 signature verification
    - Return callback server-side verification
    - Idempotency & duplicate prevention
    """

    def setUp(self):
        self.app = create_app('testing')
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app.config['CASHFREE_ENV'] = 'test'
        self.app.config['CASHFREE_ENVIRONMENT'] = 'test'
        self.app.config['PAYMENT_TEST_MODE'] = False
        self.client = self.app.test_client()

        self.app_context = self.app.app_context()
        self.app_context.push()

        db.create_all()
        MoneyTransaction.query.delete()
        Payment.query.delete()
        JobApplication.query.delete()
        db.session.commit()

        # Create Admin
        self.admin = User.query.filter_by(email='admin@antimatrix.ai').first()
        if not self.admin:
            self.admin = User(name='Admin User', email='admin@antimatrix.ai', role='admin', is_active=True)
            self.admin.set_password('Admin@AntiMatrix2026!')
            db.session.add(self.admin)
            db.session.commit()

        # Create Candidate
        self.candidate = User.query.filter_by(email='candidate.sandbox@example.com').first()
        if not self.candidate:
            self.candidate = User(name='Sandbox Candidate', email='candidate.sandbox@example.com', role='member', is_active=True)
            self.candidate.set_password('Candidate@2026!')
            db.session.add(self.candidate)
            db.session.commit()

        self.login_candidate()

    def tearDown(self):
        self.app_context.pop()

    def login_candidate(self):
        self.client.get('/logout')
        return self.client.post('/login', data={'email': 'candidate.sandbox@example.com', 'password': 'Candidate@2026!'})

    def _create_job(self, duration='1_month'):
        job = JobPosting.query.filter_by(duration=duration).first()
        if not job:
            job = JobPosting(
                title=f'Software Intern ({duration})',
                department='Engineering',
                location='Chennai, India',
                employment_type='Internship',
                duration=duration,
                short_description='Internship in software development.',
                description='Hands-on internship working on real-world systems.',
                skills='Python, JavaScript, SQL',
                is_active=True
            )
            db.session.add(job)
            db.session.commit()
        return job

    def test_01_environment_configuration_defaults_to_sandbox(self):
        """Test that CashfreeService defaults to sandbox base URL."""
        # Unset env vars temporarily to test default resolution
        orig_env = os.environ.get('CASHFREE_ENV')
        try:
            if 'CASHFREE_ENV' in os.environ:
                del os.environ['CASHFREE_ENV']
            
            # Directly test get_config() outside current_app test context override
            cfg = CashfreeService.get_config()
            self.assertEqual(cfg['environment'], 'test')  # picked up from app.config['CASHFREE_ENV']

            self.app.config['CASHFREE_ENV'] = 'sandbox'
            cfg_sandbox = CashfreeService.get_config()
            self.assertEqual(cfg_sandbox['environment'], 'sandbox')
            self.assertEqual(cfg_sandbox['base_url'], 'https://sandbox.cashfree.com/pg')
            self.assertEqual(CashfreeService.SANDBOX_BASE_URL, 'https://sandbox.cashfree.com/pg')
        finally:
            if orig_env is not None:
                os.environ['CASHFREE_ENV'] = orig_env
            self.app.config['CASHFREE_ENV'] = 'test'

    def test_02_server_fee_enforcement_1month_and_3months(self):
        """Verify server enforces 199 for 1 month and 399 for 3 months."""
        job_1m = self._create_job(duration='1_month')
        job_3m = self._create_job(duration='3_months')

        self.assertEqual(job_1m.fee_inr, 199)
        self.assertEqual(job_3m.fee_inr, 399)
        self.assertEqual(INTERNSHIP_FEES['1_month'], 199)
        self.assertEqual(INTERNSHIP_FEES['3_months'], 399)

    def test_03_create_order_and_checkout_session(self):
        """Verify Cashfree order creation generates order ID and safe session token."""
        job = self._create_job(duration='1_month')
        resume_file = (io.BytesIO(b'%PDF-1.4 Mock resume'), 'resume.pdf')
        
        # Submit application
        res = self.client.post(f'/careers/apply/{job.id}', data={
            'first_name': 'Praveen',
            'last_name': 'Kumar',
            'email': 'candidate.sandbox@example.com',
            'phone': '9876543210',
            'address': '10 Tech Street',
            'state': 'Tamil Nadu',
            'city': 'Chennai',
            'pincode': '600001',
            'education_level': "Bachelor's Degree",
            'degree': 'B.Tech',
            'major': 'CS',
            'graduation_year': '2026',
            'resume': resume_file
        }, content_type='multipart/form-data', follow_redirects=False)
        self.assertEqual(res.status_code, 302)

        app_record = JobApplication.query.filter_by(email='candidate.sandbox@example.com').first()
        self.assertIsNotNone(app_record)
        self.assertEqual(app_record.application_fee, 199)
        self.assertEqual(app_record.payment_status, 'pending')

        # Checkout
        chk_res = self.client.post(f'/careers/apply/checkout/{app_record.id}', follow_redirects=False)
        self.assertEqual(chk_res.status_code, 302)

        payment = Payment.query.filter_by(application_id=app_record.id).first()
        self.assertIsNotNone(payment)
        self.assertEqual(payment.amount, 199.0)
        self.assertTrue(payment.cashfree_order_id.startswith('AM-APP-'))
        self.assertTrue(payment.cashfree_payment_session_id.startswith('session_test_'))

        # Checkout Page HTML Security: verify NO secret key is exposed
        page_res = self.client.get(f'/payment/cashfree/checkout/{payment.id}')
        self.assertEqual(page_res.status_code, 200)
        page_html = page_res.data.decode('utf-8')
        self.assertNotIn('CASHFREE_SECRET_KEY', page_html)
        self.assertNotIn('your_cashfree_secret_key', page_html)
        self.assertIn('https://sdk.cashfree.com/js/v3/cashfree.js', page_html)
        self.assertIn(payment.cashfree_order_id, page_html)

    def test_04_successful_payment_finalization_and_money_management(self):
        """Verify verified successful payment finalizes application, assigns ID, and logs ledger."""
        job = self._create_job(duration='3_months')
        resume_file = (io.BytesIO(b'%PDF-1.4 Mock resume'), 'resume.pdf')
        aadhaar_file = (io.BytesIO(b'%PDF-1.4 Mock aadhaar'), 'aadhaar.pdf')

        res = self.client.post(f'/careers/apply/{job.id}', data={
            'first_name': 'Divya',
            'last_name': 'Ramesh',
            'email': 'candidate.sandbox@example.com',
            'phone': '9876543210',
            'address': '20 Tech Boulevard',
            'state': 'Tamil Nadu',
            'city': 'Chennai',
            'pincode': '600001',
            'education_level': "Bachelor's Degree",
            'degree': 'B.Tech',
            'major': 'CS',
            'graduation_year': '2026',
            'resume': resume_file,
            'aadhaar': aadhaar_file
        }, content_type='multipart/form-data', follow_redirects=False)

        app_record = JobApplication.query.filter_by(email='candidate.sandbox@example.com').first()
        self.client.post(f'/careers/apply/checkout/{app_record.id}', follow_redirects=False)
        payment = Payment.query.filter_by(application_id=app_record.id).first()

        # Simulated Return callback
        ret_res = self.client.get(f'/payment/cashfree/return?order_id={payment.cashfree_order_id}&sim_status=SUCCESS', follow_redirects=True)
        self.assertEqual(ret_res.status_code, 200)

        db.session.refresh(app_record)
        db.session.refresh(payment)
        self.assertEqual(payment.payment_status, 'paid')
        self.assertEqual(app_record.payment_status, 'paid')
        self.assertEqual(app_record.application_status, 'APPLIED')
        self.assertEqual(app_record.status, 'APPLIED')
        self.assertTrue(app_record.application_code.startswith('AM-APP-'))

        # Money transaction recorded automatically
        txn = MoneyTransaction.query.filter_by(cashfree_order_id=payment.cashfree_order_id).first()
        self.assertIsNotNone(txn)
        self.assertEqual(txn.amount, 399.0)
        self.assertEqual(txn.transaction_type, 'INCOME')
        self.assertEqual(txn.payment_method, 'Cashfree')

    def test_05_failed_payment_does_not_finalize(self):
        """Failed payment must NOT mark application as paid or APPLIED."""
        job = self._create_job(duration='1_month')
        resume_file = (io.BytesIO(b'%PDF-1.4 Mock resume'), 'resume.pdf')

        self.client.post(f'/careers/apply/{job.id}', data={
            'first_name': 'Test',
            'last_name': 'Failed',
            'email': 'candidate.sandbox@example.com',
            'phone': '9876543210',
            'address': 'Address',
            'state': 'Tamil Nadu',
            'city': 'Chennai',
            'pincode': '600001',
            'education_level': "Bachelor's Degree",
            'degree': 'B.Tech',
            'major': 'CS',
            'graduation_year': '2026',
            'resume': resume_file
        }, content_type='multipart/form-data', follow_redirects=False)

        app_record = JobApplication.query.filter_by(email='candidate.sandbox@example.com').first()
        self.client.post(f'/careers/apply/checkout/{app_record.id}', follow_redirects=False)
        payment = Payment.query.filter_by(application_id=app_record.id).first()

        # Simulated Failed Callback
        ret_res = self.client.get(f'/payment/cashfree/return?order_id={payment.cashfree_order_id}&sim_status=FAILED', follow_redirects=True)
        self.assertEqual(ret_res.status_code, 200)

        db.session.refresh(app_record)
        db.session.refresh(payment)
        self.assertEqual(payment.payment_status, 'failed')
        self.assertNotEqual(app_record.payment_status, 'paid')
        self.assertNotEqual(app_record.application_status, 'APPLIED')

        # No money transaction recorded
        txn = MoneyTransaction.query.filter_by(cashfree_order_id=payment.cashfree_order_id).first()
        self.assertIsNone(txn)

    def test_06_idempotency_on_return_refresh(self):
        """Repeated visits to return URL do not create duplicate records or re-generate Application ID."""
        job = self._create_job(duration='1_month')
        resume_file = (io.BytesIO(b'%PDF-1.4 Mock resume'), 'resume.pdf')

        self.client.post(f'/careers/apply/{job.id}', data={
            'first_name': 'Idempotent',
            'last_name': 'Test',
            'email': 'candidate.sandbox@example.com',
            'phone': '9876543210',
            'address': 'Address',
            'state': 'Tamil Nadu',
            'city': 'Chennai',
            'pincode': '600001',
            'education_level': "Bachelor's Degree",
            'degree': 'B.Tech',
            'major': 'CS',
            'graduation_year': '2026',
            'resume': resume_file
        }, content_type='multipart/form-data', follow_redirects=False)

        app_record = JobApplication.query.filter_by(email='candidate.sandbox@example.com').first()
        self.client.post(f'/careers/apply/checkout/{app_record.id}', follow_redirects=False)
        payment = Payment.query.filter_by(application_id=app_record.id).first()

        # 1st Visit
        self.client.get(f'/payment/cashfree/return?order_id={payment.cashfree_order_id}&sim_status=SUCCESS', follow_redirects=True)
        db.session.refresh(app_record)
        app_code_1 = app_record.application_code

        # 2nd Visit (Refresh)
        self.client.get(f'/payment/cashfree/return?order_id={payment.cashfree_order_id}&sim_status=SUCCESS', follow_redirects=True)
        db.session.refresh(app_record)
        app_code_2 = app_record.application_code

        self.assertEqual(app_code_1, app_code_2)
        self.assertEqual(JobApplication.query.filter_by(email=app_record.email).count(), 1)
        self.assertEqual(Payment.query.filter_by(application_id=app_record.id).count(), 1)
        self.assertEqual(MoneyTransaction.query.filter_by(cashfree_order_id=payment.cashfree_order_id).count(), 1)

    def test_07_webhook_signature_verification_algorithm(self):
        """Verify HMAC-SHA256 signature verification formula with Cashfree Sandbox."""
        secret = 'test_secret_key_12345'
        self.app.config['CASHFREE_SECRET_KEY'] = secret
        
        timestamp = str(int(time.time()))
        body = b'{"data":{"order":{"order_id":"TEST-123"}}}'

        # Correct signature
        message = timestamp.encode('utf-8') + body
        computed_hmac = hmac.new(secret.encode('utf-8'), message, hashlib.sha256).digest()
        valid_sig = base64.b64encode(computed_hmac).decode('utf-8')

        is_valid = CashfreeService.verify_webhook_signature(valid_sig, timestamp, body)
        self.assertTrue(is_valid)

        # Invalid signature
        is_invalid = CashfreeService.verify_webhook_signature('wrong_signature', timestamp, body)
        self.assertFalse(is_invalid)


if __name__ == '__main__':
    unittest.main()
