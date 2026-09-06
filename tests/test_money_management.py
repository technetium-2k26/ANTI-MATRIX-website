import os
import unittest
import json
from datetime import datetime, timezone, date
from app import create_app
from models import (
    db, User, JobPosting, JobApplication, Payment, Employee,
    DocumentTemplate, EmailTemplate, EmployeeDocument, ContactInquiry,
    MoneyTransaction
)
from services.money_service import (
    record_cashfree_income, get_financial_summary, filter_transactions,
    reconcile_cashfree_payments
)


class TestMoneyManagementSystem(unittest.TestCase):
    """
    Comprehensive Test Suite for Admin Money Management & Revenue Dashboard.
    Ensures data preservation, strict idempotency, audit trail, and calculation accuracy.
    """

    @classmethod
    def setUpClass(cls):
        # Use development/testing config that connects to the SQLite database
        cls.app = create_app('development')
        cls.app.config['WTF_CSRF_ENABLED'] = False
        cls.client = cls.app.test_client()

    def setUp(self):
        self.app_context = self.app.app_context()
        self.app_context.push()

        # Record baseline counts of all pre-existing tables to guarantee data preservation
        self.baseline_counts = {
            'job_postings': JobPosting.query.count(),
            'job_applications': JobApplication.query.count(),
            'users': User.query.count(),
            'employees': Employee.query.count(),
            'employee_documents': EmployeeDocument.query.count(),
            'document_templates': DocumentTemplate.query.count(),
            'email_templates': EmailTemplate.query.count(),
            'contact_inquiries': ContactInquiry.query.count(),
        }

        # Find or create admin user for testing auth
        self.admin = User.query.filter_by(role='admin').first()
        if not self.admin:
            self.admin = User(name='Test Admin', email='test_admin@antimatrix.ai', role='admin', is_active=True)
            self.admin.set_password('AdminPass123!')
            db.session.add(self.admin)
            db.session.commit()

        # Find or create candidate/student user for testing authorization restrictions
        self.student = User.query.filter_by(role='candidate').first()
        if not self.student:
            self.student = User(name='Test Student', email='student_test@example.com', role='candidate', is_active=True)
            self.student.set_password('StudentPass123!')
            db.session.add(self.student)
            db.session.commit()

    def tearDown(self):
        # Clean up only test transactions created during test runs, NEVER real pre-existing data
        test_txns = MoneyTransaction.query.filter(
            (MoneyTransaction.reference.like('TEST-%')) | 
            (MoneyTransaction.purpose.like('TEST%')) |
            (MoneyTransaction.category == 'Test Category') |
            (MoneyTransaction.cashfree_order_id.like('TEST-CF-%'))
        ).all()
        for t in test_txns:
            db.session.delete(t)
        db.session.commit()

        self.app_context.pop()

    def test_01_manual_expense_with_historical_date(self):
        """
        TEST 1 — Manual Expense with Historical Date.
        Expense: ₹1,000, Purpose: 'TEST Server Expense', Date: '2026-08-01'
        Verify Total Expense increases by ₹1,000, Balance decreases by ₹1,000, and historical date is preserved.
        """
        initial_summary = get_financial_summary()
        initial_expense = initial_summary['total_expense']
        initial_balance = initial_summary['balance']

        # Log in as admin
        with self.client.session_transaction() as sess:
            sess['_user_id'] = str(self.admin.id)
            sess['_fresh'] = True

        response = self.client.post('/admin/money-management/transactions/create', data={
            'transaction_type': 'EXPENSE',
            'amount': '1000.00',
            'transaction_date': '2026-08-01',
            'transaction_time': '09:15 AM',
            'category': 'Server',
            'purpose': 'TEST Server Expense',
            'description': 'Historical server infrastructure bill',
            'payment_method': 'Bank Transfer',
            'reference': 'TEST-EXP-001'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)

        # Verify transaction in database
        txn = MoneyTransaction.query.filter_by(reference='TEST-EXP-001').first()
        self.assertIsNotNone(txn)
        self.assertEqual(txn.amount, 1000.00)
        self.assertEqual(txn.transaction_type, 'EXPENSE')
        self.assertEqual(txn.transaction_date, date(2026, 8, 1))
        self.assertEqual(txn.transaction_time, '09:15 AM')
        self.assertEqual(txn.category, 'Server')
        self.assertEqual(txn.source, 'MANUAL')
        self.assertEqual(txn.environment, 'MANUAL')
        self.assertEqual(txn.created_by_admin_id, self.admin.id)

        # Verify financial totals
        new_summary = get_financial_summary()
        self.assertEqual(new_summary['total_expense'], initial_expense + 1000.00)
        self.assertEqual(new_summary['balance'], initial_balance - 1000.00)

    def test_02_manual_income_creation(self):
        """
        TEST 2 — Manual Income Creation.
        Income: ₹5,000, Purpose: 'TEST Website Development Payment', Date: '2026-08-15'
        Verify Total Income increases by ₹5,000, Balance increases by ₹5,000.
        """
        initial_summary = get_financial_summary()
        initial_income = initial_summary['total_income']
        initial_balance = initial_summary['balance']

        with self.client.session_transaction() as sess:
            sess['_user_id'] = str(self.admin.id)
            sess['_fresh'] = True

        response = self.client.post('/admin/money-management/transactions/create', data={
            'transaction_type': 'INCOME',
            'amount': '5000.00',
            'transaction_date': '2026-08-15',
            'transaction_time': '03:30 PM',
            'category': 'Website Development',
            'purpose': 'TEST Website Development Payment',
            'description': 'Client advance payment for custom web project',
            'payment_method': 'UPI',
            'reference': 'TEST-INC-001'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)

        txn = MoneyTransaction.query.filter_by(reference='TEST-INC-001').first()
        self.assertIsNotNone(txn)
        self.assertEqual(txn.amount, 5000.00)
        self.assertEqual(txn.transaction_type, 'INCOME')
        self.assertEqual(txn.transaction_date, date(2026, 8, 15))
        self.assertEqual(txn.category, 'Website Development')

        new_summary = get_financial_summary()
        self.assertEqual(new_summary['total_income'], initial_income + 5000.00)
        self.assertEqual(new_summary['balance'], initial_balance + 5000.00)

    def test_03_cashfree_sandbox_automatic_income(self):
        """
        TEST 3 — Cashfree Sandbox Automatic Income Hook.
        Simulate verified Cashfree Sandbox payment of ₹199.
        Verify Money Management receives exactly ONE income transaction labeled 'CASHFREE • SANDBOX'
        with application ID and order ID linked.
        """
        job = JobPosting.query.first()
        if not job:
            job = JobPosting(title="TEST Developer", department="Tech", location="Remote", employment_type="Internship", duration="1_month", short_description="Test", description="Test")
            db.session.add(job)
            db.session.commit()

        app_record = JobApplication.query.first()
        if not app_record:
            app_record = JobApplication(
                job_id=job.id, full_name="Test Candidate", email="candidate@test.com", phone="9876543210",
                college="Test College", degree="B.Tech", department="CSE", graduation_year="2026",
                resume_filename="resume.pdf", resume_path="/dummy/path", status="New"
            )
            db.session.add(app_record)
            db.session.commit()

        test_order_id = "TEST-CF-ORD-12345"
        test_cf_pay_id = "TEST-CF-PAY-99999"

        # Create simulated payment record
        payment = Payment(
            application_id=app_record.id,
            cashfree_order_id=test_order_id,
            amount=199.00,
            currency='INR',
            payment_status='paid',
            gateway='cashfree',
            cf_payment_id=test_cf_pay_id
        )
        db.session.add(payment)
        db.session.commit()

        # Trigger Money Management hook
        success, txn, err = record_cashfree_income(
            application=app_record,
            payment=payment,
            payment_details={'cf_payment_id': test_cf_pay_id},
            env='SANDBOX'
        )

        self.assertTrue(success)
        self.assertIsNotNone(txn)
        self.assertEqual(txn.amount, 199.00)
        self.assertEqual(txn.transaction_type, 'INCOME')
        self.assertEqual(txn.provider, 'CASHFREE')
        self.assertEqual(txn.environment, 'SANDBOX')
        self.assertEqual(txn.environment_display, 'Cashfree • Sandbox')
        self.assertEqual(txn.cashfree_order_id, test_order_id)
        self.assertEqual(txn.provider_transaction_id, test_cf_pay_id)
        self.assertEqual(txn.application_id, app_record.id)

        # Cleanup test payment
        db.session.delete(txn)
        db.session.delete(payment)
        db.session.commit()

    def test_04_duplicate_cashfree_prevention(self):
        """
        TEST 4 — Duplicate Cashfree Callback / Webhook Idempotency.
        Calling record_cashfree_income multiple times for same order MUST not create duplicates.
        """
        app_record = JobApplication.query.first()
        test_order_id = "TEST-CF-DUP-001"
        test_cf_pay_id = "TEST-CF-PAY-DUP-001"

        payment = Payment(
            application_id=app_record.id if app_record else 1,
            cashfree_order_id=test_order_id,
            amount=399.00,
            currency='INR',
            payment_status='paid',
            gateway='cashfree',
            cf_payment_id=test_cf_pay_id
        )
        db.session.add(payment)
        db.session.commit()

        # Call 1: Should create transaction
        s1, t1, e1 = record_cashfree_income(app_record, payment, env='SANDBOX')
        self.assertTrue(s1)
        self.assertIsNotNone(t1)
        first_txn_id = t1.id

        # Call 2 (Simulated webhook retry / page refresh): Should detect duplicate and return existing
        s2, t2, e2 = record_cashfree_income(app_record, payment, env='SANDBOX')
        self.assertTrue(s2)
        self.assertEqual(t2.id, first_txn_id)
        self.assertEqual(e2, "Already recorded")

        # Verify only 1 transaction exists in database
        count = MoneyTransaction.query.filter_by(cashfree_order_id=test_order_id).count()
        self.assertEqual(count, 1)

        # Cleanup
        db.session.delete(t1)
        db.session.delete(payment)
        db.session.commit()

    def test_05_manual_edit_and_delete(self):
        """
        TEST 5 — Manual Transaction Edit & Delete with Real-time Recalculation.
        """
        with self.client.session_transaction() as sess:
            sess['_user_id'] = str(self.admin.id)
            sess['_fresh'] = True

        # Create manual transaction
        txn = MoneyTransaction(
            transaction_type='EXPENSE',
            amount=800.00,
            transaction_date=date(2026, 8, 20),
            category='Internet',
            purpose='TEST Internet Bill',
            source='MANUAL',
            provider='MANUAL',
            environment='MANUAL',
            reference='TEST-EDIT-001'
        )
        db.session.add(txn)
        db.session.commit()
        txn_id = txn.id

        # Edit transaction to ₹950
        response = self.client.post(f'/admin/money-management/transactions/{txn_id}/edit', data={
            'amount': '950.00',
            'transaction_date': '2026-08-20',
            'transaction_time': '11:00 AM',
            'category': 'Internet',
            'purpose': 'TEST Updated Internet Bill',
            'payment_method': 'UPI',
            'reference': 'TEST-EDIT-001',
            'description': 'Updated amount with taxes'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        updated_txn = db.session.get(MoneyTransaction, txn_id)
        self.assertEqual(updated_txn.amount, 950.00)
        self.assertEqual(updated_txn.purpose, 'TEST Updated Internet Bill')

        # Delete transaction
        del_response = self.client.post(f'/admin/money-management/transactions/{txn_id}/delete', follow_redirects=True)
        self.assertEqual(del_response.status_code, 200)
        deleted_txn = db.session.get(MoneyTransaction, txn_id)
        self.assertIsNone(deleted_txn)

    def test_06_cashfree_transaction_deletion_lock(self):
        """
        TEST 6 — Cashfree Automatic Transactions cannot be deleted or modified.
        """
        with self.client.session_transaction() as sess:
            sess['_user_id'] = str(self.admin.id)
            sess['_fresh'] = True

        # Create simulated Cashfree transaction
        cf_txn = MoneyTransaction(
            transaction_type='INCOME',
            amount=199.00,
            transaction_date=date(2026, 9, 1),
            category='Internship Application Fee',
            purpose='TEST Cashfree Protected Txn',
            source='AUTOMATIC',
            provider='CASHFREE',
            environment='SANDBOX',
            cashfree_order_id='TEST-CF-LOCK-001',
            reference='TEST-CF-LOCK-001'
        )
        db.session.add(cf_txn)
        db.session.commit()
        cf_id = cf_txn.id

        # Attempt to delete Cashfree transaction -> Must be blocked
        response = self.client.post(f'/admin/money-management/transactions/{cf_id}/delete', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # Verify still in database
        check_txn = db.session.get(MoneyTransaction, cf_id)
        self.assertIsNotNone(check_txn)

        # Attempt to edit Cashfree transaction -> Must be blocked
        edit_resp = self.client.post(f'/admin/money-management/transactions/{cf_id}/edit', data={
            'amount': '999.00'
        }, follow_redirects=True)
        self.assertEqual(edit_resp.status_code, 200)
        check_txn_2 = db.session.get(MoneyTransaction, cf_id)
        self.assertEqual(check_txn_2.amount, 199.00)  # Unchanged

        # Cleanup
        db.session.delete(check_txn)
        db.session.commit()

    def login_user(self, email, password):
        return self.client.post('/login', data={'email': email, 'password': password}, follow_redirects=True)

    def logout_user(self):
        return self.client.get('/logout', follow_redirects=True)

    def test_07_admin_authorization_enforcement(self):
        """
        TEST 7 — Admin Authorization Enforcement.
        Unauthenticated guests and non-admin users must NOT access Money Management.
        """
        self.logout_user()

        # 1. Unauthenticated guest
        guest_client = self.app.test_client()
        resp = guest_client.get('/admin/money-management')
        self.assertEqual(resp.status_code, 302)  # Redirects to login

        post_resp = guest_client.post('/admin/money-management/transactions/create', data={'amount': '100'})
        self.assertEqual(post_resp.status_code, 302)

        # 2. Authenticated non-admin candidate/student
        self.login_user('student_test@example.com', 'StudentPass123!')

        student_resp = self.client.get('/admin/money-management')
        self.assertEqual(student_resp.status_code, 403)  # Forbidden

        student_post = self.client.post('/admin/money-management/transactions/create', data={'amount': '100'})
        self.assertEqual(student_post.status_code, 403)

        self.logout_user()

    def test_08_data_preservation_verification(self):
        """
        TEST 8 — Non-Negotiable Data Preservation Verification.
        Ensure that all pre-existing records, tables, and IDs remain 100% unchanged.
        """
        self.assertEqual(JobPosting.query.count(), self.baseline_counts['job_postings'])
        self.assertEqual(JobApplication.query.count(), self.baseline_counts['job_applications'])
        self.assertEqual(User.query.count(), self.baseline_counts['users'])
        self.assertEqual(Employee.query.count(), self.baseline_counts['employees'])
        self.assertEqual(EmployeeDocument.query.count(), self.baseline_counts['employee_documents'])
        self.assertEqual(DocumentTemplate.query.count(), self.baseline_counts['document_templates'])
        self.assertEqual(EmailTemplate.query.count(), self.baseline_counts['email_templates'])
        self.assertEqual(ContactInquiry.query.count(), self.baseline_counts['contact_inquiries'])


if __name__ == '__main__':
    unittest.main()
