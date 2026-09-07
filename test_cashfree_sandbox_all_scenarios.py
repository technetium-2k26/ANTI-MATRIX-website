import os
import io
import json
import time
import unittest
from unittest.mock import patch, MagicMock
from app import create_app
from models import db, User, JobPosting, JobApplication, Payment, MoneyTransaction
from services.cashfree_service import CashfreeService
from config import INTERNSHIP_FEES


class CashfreeSandboxAllScenariosTestCase(unittest.TestCase):
    """
    Comprehensive End-to-End Test Suite for all 10 Required Cashfree Sandbox Scenarios.
    Ensures zero data corruption and 100% compliance with production requirements.
    """

    def setUp(self):
        self.app = create_app('testing')
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app.config['CASHFREE_ENV'] = 'sandbox'
        self.app.config['CASHFREE_ENVIRONMENT'] = 'sandbox'
        self.app.config['CASHFREE_APP_ID'] = 'test_sandbox_app_id'
        self.app.config['CASHFREE_SECRET_KEY'] = 'test_sandbox_secret_key'
        self.app.config['CASHFREE_API_VERSION'] = '2025-01-01'
        self.app.config['PAYMENT_TEST_MODE'] = False
        self.client = self.app.test_client()

        self.app_context = self.app.app_context()
        self.app_context.push()

        db.create_all()

        # Create Primary Test Candidate User
        self.candidate = User.query.filter_by(email='candidate.sandbox@example.com').first()
        if not self.candidate:
            self.candidate = User(
                name='Sandbox Candidate',
                email='candidate.sandbox@example.com',
                role='member',
                is_active=True
            )
            self.candidate.set_password('Candidate@2026!')
            db.session.add(self.candidate)
            db.session.commit()

        # Create Secondary Candidate User (for cross-user authorization security tests)
        self.other_candidate = User.query.filter_by(email='other.candidate@example.com').first()
        if not self.other_candidate:
            self.other_candidate = User(
                name='Other Candidate',
                email='other.candidate@example.com',
                role='member',
                is_active=True
            )
            self.other_candidate.set_password('Other@2026!')
            db.session.add(self.other_candidate)
            db.session.commit()

        # Create Admin User
        self.admin = User.query.filter_by(email='admin.sandbox@example.com').first()
        if not self.admin:
            self.admin = User(
                name='Sandbox Admin',
                email='admin.sandbox@example.com',
                role='admin',
                is_active=True
            )
            self.admin.set_password('Admin@2026!')
            db.session.add(self.admin)
            db.session.commit()

        # Create 1 Month & 3 Month Job Postings
        self.job_1m = JobPosting.query.filter_by(title='Software Engineer Intern (1M Sandbox)').first()
        if not self.job_1m:
            self.job_1m = JobPosting(
                title='Software Engineer Intern (1M Sandbox)',
                department='Engineering',
                location='Chennai, India',
                employment_type='Internship',
                duration='1_month',
                short_description='1-month software engineering internship.',
                description='Hands-on experience with production systems.',
                skills='Python, Flask, JavaScript',
                is_active=True
            )
            db.session.add(self.job_1m)
            db.session.commit()

        self.job_3m = JobPosting.query.filter_by(title='AI Research Intern (3M Sandbox)').first()
        if not self.job_3m:
            self.job_3m = JobPosting(
                title='AI Research Intern (3M Sandbox)',
                department='Artificial Intelligence',
                location='Chennai, India',
                employment_type='Internship',
                duration='3_months',
                short_description='3-month AI research internship.',
                description='Advanced deep learning and LLM engineering.',
                skills='PyTorch, Transformers, Python',
                is_active=True
            )
            db.session.add(self.job_3m)
            db.session.commit()

        self.login_candidate()

    def tearDown(self):
        self.app_context.pop()

    def login_candidate(self):
        self.client.get('/logout')
        return self.client.post('/login', data={'email': 'candidate.sandbox@example.com', 'password': 'Candidate@2026!'})

    def login_other_candidate(self):
        self.client.get('/logout')
        return self.client.post('/login', data={'email': 'other.candidate@example.com', 'password': 'Other@2026!'})

    def login_admin(self):
        self.client.get('/logout')
        return self.client.post('/login', data={'email': 'admin.sandbox@example.com', 'password': 'Admin@2026!'})

    def _create_application(self, job, user=None, email='candidate.sandbox@example.com', name='Sandbox Candidate'):
        if user is None:
            user = self.candidate
        duration = job.duration or '1_month'
        fee = INTERNSHIP_FEES.get(duration, 199)

        doc_dir = os.path.join(self.app.root_path, 'uploads', 'documents')
        res_dir = os.path.join(self.app.root_path, 'uploads', 'resumes')
        os.makedirs(doc_dir, exist_ok=True)
        os.makedirs(res_dir, exist_ok=True)

        resume_path = os.path.join(res_dir, f'resume_{int(time.time())}.pdf')
        with open(resume_path, 'wb') as f:
            f.write(b'%PDF-1.4 Mock Candidate Resume')

        parts = name.split(' ', 1)
        app_record = JobApplication(
            user_id=user.id,
            job_id=job.id,
            first_name=parts[0],
            last_name=parts[1] if len(parts) > 1 else '',
            full_name=name,
            email=email,
            phone='9876543210',
            address='100 Anna Salai',
            state='Tamil Nadu',
            city='Chennai',
            pincode='600002',
            education_level="Bachelor's Degree",
            college='IIT Madras',
            department='CSE',
            degree='B.Tech',
            major='Computer Science',
            graduation_year='2026',
            current_cgpa=9.0,
            skills='Python, JavaScript, SQL',
            duration=duration,
            application_fee=fee,
            payment_status='pending',
            application_status='pending_payment',
            resume_filename='mock_resume.pdf',
            resume_path=resume_path,
            status='New'
        )
        db.session.add(app_record)
        db.session.commit()
        app_record.application_code = f"AM-APP-{app_record.id:06d}"
        db.session.commit()
        return app_record

    # -------------------------------------------------------------------------
    # TEST 1: 1 Month application -> Expected fee ₹199
    # -------------------------------------------------------------------------
    def test_01_one_month_application_fee_199(self):
        """TEST 1: 1 Month application calculates server fee of exactly ₹199."""
        app_rec = self._create_application(self.job_1m)
        self.assertEqual(app_rec.duration, '1_month')
        self.assertEqual(self.job_1m.fee_inr, 199)

        with patch('services.cashfree_service.requests.post') as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                'order_id': f'AM-APP-{app_rec.id:06d}-PAY-101',
                'payment_session_id': 'session_sandbox_1m_test_199',
                'order_amount': 199.00,
                'order_currency': 'INR',
                'order_status': 'ACTIVE'
            }
            mock_post.return_value = mock_resp

            res = self.client.post(f'/careers/apply/checkout/{app_rec.id}', follow_redirects=False)
            self.assertEqual(res.status_code, 302)

            payment = Payment.query.filter_by(application_id=app_rec.id).first()
            self.assertIsNotNone(payment)
            self.assertEqual(payment.amount, 199.00)
            self.assertEqual(payment.currency, 'INR')
            self.assertEqual(payment.cashfree_payment_session_id, 'session_sandbox_1m_test_199')

    # -------------------------------------------------------------------------
    # TEST 2: 3 Month application -> Expected fee ₹399
    # -------------------------------------------------------------------------
    def test_02_three_month_application_fee_399(self):
        """TEST 2: 3 Month application calculates server fee of exactly ₹399."""
        app_rec = self._create_application(self.job_3m)
        self.assertEqual(app_rec.duration, '3_months')
        self.assertEqual(self.job_3m.fee_inr, 399)

        with patch('services.cashfree_service.requests.post') as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                'order_id': f'AM-APP-{app_rec.id:06d}-PAY-301',
                'payment_session_id': 'session_sandbox_3m_test_399',
                'order_amount': 399.00,
                'order_currency': 'INR',
                'order_status': 'ACTIVE'
            }
            mock_post.return_value = mock_resp

            res = self.client.post(f'/careers/apply/checkout/{app_rec.id}', follow_redirects=False)
            self.assertEqual(res.status_code, 302)

            payment = Payment.query.filter_by(application_id=app_rec.id).first()
            self.assertIsNotNone(payment)
            self.assertEqual(payment.amount, 399.00)
            self.assertEqual(payment.currency, 'INR')
            self.assertEqual(payment.cashfree_payment_session_id, 'session_sandbox_3m_test_399')

    # -------------------------------------------------------------------------
    # TEST 3: Frontend attempts to submit wrong amount -> Backend ignores and enforces correct amount
    # -------------------------------------------------------------------------
    def test_03_frontend_amount_tampering_ignored(self):
        """TEST 3: Browser submits manipulated amounts (₹1, ₹0, ₹9999); server strictly enforces ₹399."""
        app_rec = self._create_application(self.job_3m)

        with patch('services.cashfree_service.requests.post') as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                'order_id': f'AM-APP-{app_rec.id:06d}-PAY-TAMPER',
                'payment_session_id': 'session_tamper_defense',
                'order_amount': 399.00,
                'order_currency': 'INR',
                'order_status': 'ACTIVE'
            }
            mock_post.return_value = mock_resp

            # Malicious submission attempting to tamper amount
            self.client.post(
                f'/careers/apply/checkout/{app_rec.id}',
                data={'amount': '1', 'order_amount': '0', 'fee': '9999'},
                follow_redirects=False
            )

            # Check Cashfree request payload sent by server
            called_payload = json.loads(mock_post.call_args[1]['data'])
            self.assertEqual(called_payload['order_amount'], 399.0, "Server must send exactly 399.0 regardless of client payload")

            payment = Payment.query.filter_by(application_id=app_rec.id).first()
            self.assertEqual(payment.amount, 399.0)

    # -------------------------------------------------------------------------
    # TEST 4: Checkout opens -> Application is NOT marked APPLIED yet
    # -------------------------------------------------------------------------
    def test_04_checkout_opened_application_remains_pending(self):
        """TEST 4: Merely opening checkout page does NOT mark application as paid or APPLIED."""
        app_rec = self._create_application(self.job_1m)

        with patch('services.cashfree_service.requests.post') as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                'order_id': f'AM-APP-{app_rec.id:06d}-PAY-OPEN',
                'payment_session_id': 'session_open_checkout',
                'order_amount': 199.00,
                'order_currency': 'INR',
                'order_status': 'ACTIVE'
            }
            mock_post.return_value = mock_resp

            self.client.post(f'/careers/apply/checkout/{app_rec.id}', follow_redirects=False)
            payment = Payment.query.filter_by(application_id=app_rec.id).first()

            # Render checkout page
            chk_res = self.client.get(f'/payment/cashfree/checkout/{payment.id}')
            self.assertEqual(chk_res.status_code, 200)
            self.assertIn(b'Connecting to Cashfree Gateway...', chk_res.data)

            # Assert application remains pending and NOT marked APPLIED
            db.session.refresh(app_rec)
            self.assertEqual(app_rec.payment_status, 'pending')
            self.assertEqual(app_rec.application_status, 'pending_payment')
            self.assertEqual(app_rec.status, 'New')
            self.assertEqual(payment.payment_status, 'pending')

    # -------------------------------------------------------------------------
    # TEST 5: Successful Sandbox payment -> Verification succeeds, application APPLIED, 1 MoneyTransaction
    # -------------------------------------------------------------------------
    def test_05_successful_sandbox_payment_flow(self):
        """TEST 5: Cashfree verification confirms SUCCESS -> Application APPLIED, Payment updated, 1 MoneyTransaction."""
        app_rec = self._create_application(self.job_1m)
        order_id = f'AM-APP-{app_rec.id:06d}-PAY-SUCCESS-5'

        payment = Payment(
            application_id=app_rec.id,
            cashfree_order_id=order_id,
            cashfree_payment_session_id='session_success_5',
            amount=199.0,
            currency='INR',
            payment_status='pending',
            gateway='cashfree'
        )
        db.session.add(payment)
        db.session.commit()

        # Mock Cashfree Get Payments for Order returning SUCCESS
        with patch('services.cashfree_service.requests.get') as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = [{
                'payment_status': 'SUCCESS',
                'cf_payment_id': 'cf_pay_sandbox_123456',
                'payment_amount': 199.00,
                'payment_currency': 'INR',
                'payment_time': '2026-09-07T04:00:00Z',
                'payment_method': {'upi': {'upi_id': 'testsuccess@gocash'}}
            }]
            mock_get.return_value = mock_resp

            ret_res = self.client.get(f'/payment/cashfree/return?order_id={order_id}', follow_redirects=True)
            self.assertEqual(ret_res.status_code, 200)

            # Verify Application updated
            db.session.refresh(app_rec)
            db.session.refresh(payment)
            self.assertEqual(payment.payment_status, 'paid')
            self.assertEqual(payment.cf_payment_id, 'cf_pay_sandbox_123456')
            self.assertEqual(app_rec.payment_status, 'paid')
            self.assertEqual(app_rec.application_status, 'APPLIED')
            self.assertEqual(app_rec.status, 'APPLIED')
            self.assertEqual(app_rec.application_code, f'AM-APP-{app_rec.id:06d}')

            # Verify exactly ONE MoneyTransaction recorded
            txns = MoneyTransaction.query.filter_by(cashfree_order_id=order_id).all()
            self.assertEqual(len(txns), 1)
            txn = txns[0]
            self.assertEqual(txn.amount, 199.0)
            self.assertEqual(txn.transaction_type, 'INCOME')
            self.assertEqual(txn.source, 'AUTOMATIC')
            self.assertEqual(txn.provider, 'CASHFREE')
            self.assertEqual(txn.provider_transaction_id, 'cf_pay_sandbox_123456')
            self.assertEqual(txn.environment, 'SANDBOX')

    # -------------------------------------------------------------------------
    # TEST 6: Failed payment -> Application NOT finalized as paid
    # -------------------------------------------------------------------------
    def test_06_failed_payment_rejected(self):
        """TEST 6: Cashfree returns FAILED payment status -> Application remains unpaid/failed, no MM transaction."""
        app_rec = self._create_application(self.job_1m)
        order_id = f'AM-APP-{app_rec.id:06d}-PAY-FAIL-6'

        payment = Payment(
            application_id=app_rec.id,
            cashfree_order_id=order_id,
            cashfree_payment_session_id='session_fail_6',
            amount=199.0,
            currency='INR',
            payment_status='pending',
            gateway='cashfree'
        )
        db.session.add(payment)
        db.session.commit()

        with patch('services.cashfree_service.requests.get') as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = [{
                'payment_status': 'FAILED',
                'cf_payment_id': 'cf_pay_failed_123',
                'payment_amount': 199.00,
                'payment_currency': 'INR',
                'payment_message': 'Bank declined transaction'
            }]
            mock_get.return_value = mock_resp

            ret_res = self.client.get(f'/payment/cashfree/return?order_id={order_id}', follow_redirects=True)
            self.assertEqual(ret_res.status_code, 200)
            self.assertIn(b'Payment Failed', ret_res.data)

            db.session.refresh(app_rec)
            db.session.refresh(payment)
            self.assertEqual(payment.payment_status, 'failed')
            self.assertEqual(app_rec.payment_status, 'failed')
            self.assertNotEqual(app_rec.application_status, 'APPLIED')

            # Ensure NO MoneyTransaction was created
            txns = MoneyTransaction.query.filter_by(cashfree_order_id=order_id).all()
            self.assertEqual(len(txns), 0)

    # -------------------------------------------------------------------------
    # TEST 7: Pending payment -> Application NOT finalized as paid
    # -------------------------------------------------------------------------
    def test_07_pending_payment_not_finalized(self):
        """TEST 7: Cashfree returns PENDING payment status -> Application remains pending, no MM transaction."""
        app_rec = self._create_application(self.job_1m)
        order_id = f'AM-APP-{app_rec.id:06d}-PAY-PENDING-7'

        payment = Payment(
            application_id=app_rec.id,
            cashfree_order_id=order_id,
            cashfree_payment_session_id='session_pending_7',
            amount=199.0,
            currency='INR',
            payment_status='pending',
            gateway='cashfree'
        )
        db.session.add(payment)
        db.session.commit()

        with patch('services.cashfree_service.requests.get') as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = [{
                'payment_status': 'PENDING',
                'cf_payment_id': 'cf_pay_pending_123',
                'payment_amount': 199.00,
                'payment_currency': 'INR'
            }]
            mock_get.return_value = mock_resp

            ret_res = self.client.get(f'/payment/cashfree/return?order_id={order_id}', follow_redirects=True)
            self.assertEqual(ret_res.status_code, 200)
            self.assertIn(b'Payment Pending', ret_res.data)

            db.session.refresh(app_rec)
            db.session.refresh(payment)
            self.assertEqual(payment.payment_status, 'pending')
            self.assertEqual(app_rec.payment_status, 'pending')
            self.assertNotEqual(app_rec.application_status, 'APPLIED')

            # Ensure NO MoneyTransaction was created
            txns = MoneyTransaction.query.filter_by(cashfree_order_id=order_id).all()
            self.assertEqual(len(txns), 0)

    # -------------------------------------------------------------------------
    # TEST 8: Refresh return URL twice -> No duplicate application, payment, MM transaction, or new Application ID
    # -------------------------------------------------------------------------
    def test_08_refresh_return_url_idempotency(self):
        """TEST 8: Multiple visits/refreshes to return URL do not duplicate records or regenerate Application ID."""
        app_rec = self._create_application(self.job_1m)
        order_id = f'AM-APP-{app_rec.id:06d}-PAY-REFRESH-8'
        orig_code = app_rec.application_code

        payment = Payment(
            application_id=app_rec.id,
            cashfree_order_id=order_id,
            cashfree_payment_session_id='session_refresh_8',
            amount=199.0,
            currency='INR',
            payment_status='pending',
            gateway='cashfree'
        )
        db.session.add(payment)
        db.session.commit()

        with patch('services.cashfree_service.requests.get') as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = [{
                'payment_status': 'SUCCESS',
                'cf_payment_id': 'cf_pay_refresh_888',
                'payment_amount': 199.00,
                'payment_currency': 'INR'
            }]
            mock_get.return_value = mock_resp

            # First Visit
            res1 = self.client.get(f'/payment/cashfree/return?order_id={order_id}', follow_redirects=True)
            self.assertEqual(res1.status_code, 200)

            # Second Visit (Refresh)
            res2 = self.client.get(f'/payment/cashfree/return?order_id={order_id}', follow_redirects=True)
            self.assertEqual(res2.status_code, 200)

            # Third Visit
            res3 = self.client.get(f'/payment/cashfree/return?order_id={order_id}', follow_redirects=True)
            self.assertEqual(res3.status_code, 200)

            db.session.refresh(app_rec)
            # Application ID strictly preserved
            self.assertEqual(app_rec.application_code, orig_code)

            # Only 1 payment record
            payments = Payment.query.filter_by(application_id=app_rec.id).all()
            self.assertEqual(len(payments), 1)

            # Only 1 MoneyTransaction recorded
            txns = MoneyTransaction.query.filter_by(cashfree_order_id=order_id).all()
            self.assertEqual(len(txns), 1)

    # -------------------------------------------------------------------------
    # TEST 9: User opens another user's order_id manually -> Access denied / safe failure
    # -------------------------------------------------------------------------
    def test_09_cross_user_order_access_denied(self):
        """TEST 9: Candidate B attempting to access Candidate A's return URL is denied access with no data leakage."""
        # Create application belonging to Candidate A
        app_rec_a = self._create_application(self.job_1m, user=self.candidate, email='candidate.a@example.com', name='Candidate A')
        order_id_a = f'AM-APP-{app_rec_a.id:06d}-PAY-USER-A'

        payment_a = Payment(
            application_id=app_rec_a.id,
            cashfree_order_id=order_id_a,
            cashfree_payment_session_id='session_user_a',
            amount=199.0,
            currency='INR',
            payment_status='pending',
            gateway='cashfree'
        )
        db.session.add(payment_a)
        db.session.commit()

        # Login as Candidate B (Other User)
        self.login_other_candidate()

        # Candidate B attempts to access Candidate A's order return URL
        res = self.client.get(f'/payment/cashfree/return?order_id={order_id_a}', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Access denied: You do not have permission to view this transaction', res.data)
        # Ensure Candidate A's application details are NOT leaked
        self.assertNotIn(b'Candidate A', res.data)

    # -------------------------------------------------------------------------
    # TEST 10: Cashfree API unavailable / network error -> Safe error, data intact, no fake payment
    # -------------------------------------------------------------------------
    def test_10_cashfree_api_unavailable_safe_error(self):
        """TEST 10: Network failure or 500 error from Cashfree PG -> Graceful error, data intact, no fake payment."""
        app_rec = self._create_application(self.job_1m)
        order_id = f'AM-APP-{app_rec.id:06d}-PAY-NETERR-10'

        payment = Payment(
            application_id=app_rec.id,
            cashfree_order_id=order_id,
            cashfree_payment_session_id='session_neterr_10',
            amount=199.0,
            currency='INR',
            payment_status='pending',
            gateway='cashfree'
        )
        db.session.add(payment)
        db.session.commit()

        with patch('services.cashfree_service.requests.get') as mock_get:
            mock_get.side_effect = Exception("Connection timed out to sandbox.cashfree.com")

            ret_res = self.client.get(f'/payment/cashfree/return?order_id={order_id}', follow_redirects=True)
            self.assertEqual(ret_res.status_code, 200)
            self.assertIn(b'Payment Failed', ret_res.data)

            # Assert database state remains clean, no fake success
            db.session.refresh(app_rec)
            db.session.refresh(payment)
            self.assertNotEqual(app_rec.payment_status, 'paid')
            self.assertNotEqual(app_rec.application_status, 'APPLIED')
            self.assertNotEqual(payment.payment_status, 'paid')

            # Ensure zero MoneyTransaction entries created
            txns = MoneyTransaction.query.filter_by(cashfree_order_id=order_id).all()
            self.assertEqual(len(txns), 0)


if __name__ == '__main__':
    unittest.main()
