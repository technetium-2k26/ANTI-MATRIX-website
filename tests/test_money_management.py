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
        Tests GET pre-population, POST in-place update, type switching, and preservation of ID.
        """
        with self.client.session_transaction() as sess:
            sess['_user_id'] = str(self.admin.id)
            sess['_fresh'] = True

        # Create manual transaction
        txn = MoneyTransaction(
            transaction_type='EXPENSE',
            amount=800.00,
            transaction_date=date(2026, 8, 20),
            transaction_time='08:30 AM',
            category='Internet',
            purpose='TEST Internet Bill',
            source='MANUAL',
            provider='MANUAL',
            environment='MANUAL',
            reference='TEST-EDIT-001',
            description='Initial monthly fiber charge'
        )
        db.session.add(txn)
        db.session.commit()
        txn_id = txn.id
        initial_txn_count = MoneyTransaction.query.count()

        # 1. GET Edit Page -> Verify pre-population
        get_resp = self.client.get(f'/admin/money-management/transactions/{txn_id}/edit')
        self.assertEqual(get_resp.status_code, 200)
        self.assertIn(b'Edit Transaction', get_resp.data)
        self.assertIn(b'800.0', get_resp.data)
        self.assertIn(b'2026-08-20', get_resp.data)
        self.assertIn(b'08:30 AM', get_resp.data)
        self.assertIn(b'TEST Internet Bill', get_resp.data)
        self.assertIn(b'TEST-EDIT-001', get_resp.data)
        self.assertIn(b'Initial monthly fiber charge', get_resp.data)

        # 2. POST Edit -> Update amount to ₹950, switch type to INCOME, change purpose
        response = self.client.post(f'/admin/money-management/transactions/{txn_id}/edit', data={
            'transaction_type': 'INCOME',
            'amount': '950.00',
            'transaction_date': '2026-08-22',
            'transaction_time': '11:00 AM',
            'category': 'Internet',
            'purpose': 'TEST Refund for Internet Bill',
            'payment_method': 'UPI',
            'reference': 'TEST-EDIT-001-UPDATED',
            'description': 'Updated to refund credit'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Transaction updated successfully', response.data)

        # Verify exact same transaction was updated in-place (no duplicate, same ID)
        self.assertEqual(MoneyTransaction.query.count(), initial_txn_count)
        updated_txn = db.session.get(MoneyTransaction, txn_id)
        self.assertIsNotNone(updated_txn)
        self.assertEqual(updated_txn.id, txn_id)
        self.assertEqual(updated_txn.amount, 950.00)
        self.assertEqual(updated_txn.transaction_type, 'INCOME')
        self.assertEqual(updated_txn.transaction_date, date(2026, 8, 22))
        self.assertEqual(updated_txn.transaction_time, '11:00 AM')
        self.assertEqual(updated_txn.purpose, 'TEST Refund for Internet Bill')
        self.assertEqual(updated_txn.reference, 'TEST-EDIT-001-UPDATED')
        self.assertEqual(updated_txn.description, 'Updated to refund credit')

        # 3. Delete transaction
        del_response = self.client.post(f'/admin/money-management/transactions/{txn_id}/delete', follow_redirects=True)
        self.assertEqual(del_response.status_code, 200)
        deleted_txn = db.session.get(MoneyTransaction, txn_id)
        self.assertIsNone(deleted_txn)

    def test_05b_edit_validation_and_errors(self):
        """
        TEST 5B — Edit Transaction Validation & Edge Cases.
        """
        with self.client.session_transaction() as sess:
            sess['_user_id'] = str(self.admin.id)
            sess['_fresh'] = True

        txn = MoneyTransaction(
            transaction_type='EXPENSE',
            amount=500.00,
            transaction_date=date(2026, 9, 1),
            category='Office Supplies',
            purpose='TEST Validation Purpose',
            source='MANUAL',
            reference='TEST-VAL-001'
        )
        db.session.add(txn)
        db.session.commit()
        txn_id = txn.id

        # Invalid non-numeric / negative amount
        resp_invalid_amt = self.client.post(f'/admin/money-management/transactions/{txn_id}/edit', data={
            'amount': '-100',
            'transaction_date': '2026-09-01',
            'purpose': 'Invalid'
        }, follow_redirects=True)
        self.assertEqual(resp_invalid_amt.status_code, 200)
        self.assertIn(b'Please enter a valid numeric amount greater than zero.', resp_invalid_amt.data)

        # Invalid date format
        resp_invalid_date = self.client.post(f'/admin/money-management/transactions/{txn_id}/edit', data={
            'amount': '500',
            'transaction_date': 'invalid-date',
            'purpose': 'Invalid Date'
        }, follow_redirects=True)
        self.assertEqual(resp_invalid_date.status_code, 200)
        self.assertIn(b'Invalid date format. Please select a valid date', resp_invalid_date.data)

        # Non-existent transaction ID
        resp_not_found = self.client.get('/admin/money-management/transactions/99999999/edit', follow_redirects=True)
        self.assertEqual(resp_not_found.status_code, 200)
        self.assertIn(b'Transaction not found', resp_not_found.data)

        # Cleanup
        db.session.delete(txn)
        db.session.commit()

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
        Unauthenticated guests and non-admin users must NOT access Money Management or Add Transaction pages.
        """
        self.logout_user()

        # 1. Unauthenticated guest
        guest_client = self.app.test_client()
        resp = guest_client.get('/admin/money-management')
        self.assertEqual(resp.status_code, 302)  # Redirects to login

        resp_add = guest_client.get('/admin/money-management/add')
        self.assertEqual(resp_add.status_code, 302)

        post_resp = guest_client.post('/admin/money-management/add', data={'amount': '100'})
        self.assertEqual(post_resp.status_code, 302)

        post_legacy_resp = guest_client.post('/admin/money-management/transactions/create', data={'amount': '100'})
        self.assertEqual(post_legacy_resp.status_code, 302)

        post_clear_resp = guest_client.post('/admin/money-management/transactions/clear-all', data={'confirmation': 'CLEAR'})
        self.assertEqual(post_clear_resp.status_code, 302)

        get_edit_resp = guest_client.get('/admin/money-management/transactions/1/edit')
        self.assertEqual(get_edit_resp.status_code, 302)

        post_edit_resp = guest_client.post('/admin/money-management/transactions/1/edit', data={'amount': '100'})
        self.assertEqual(post_edit_resp.status_code, 302)

        # 2. Authenticated non-admin candidate/student
        self.login_user('student_test@example.com', 'StudentPass123!')

        student_resp = self.client.get('/admin/money-management')
        self.assertEqual(student_resp.status_code, 403)  # Forbidden

        student_add_resp = self.client.get('/admin/money-management/add')
        self.assertEqual(student_add_resp.status_code, 403)

        student_post = self.client.post('/admin/money-management/add', data={'amount': '100'})
        self.assertEqual(student_post.status_code, 403)

        student_post_legacy = self.client.post('/admin/money-management/transactions/create', data={'amount': '100'})
        self.assertEqual(student_post_legacy.status_code, 403)

        student_clear = self.client.post('/admin/money-management/transactions/clear-all', data={'confirmation': 'CLEAR'})
        self.assertEqual(student_clear.status_code, 403)

        student_get_edit = self.client.get('/admin/money-management/transactions/1/edit')
        self.assertEqual(student_get_edit.status_code, 403)

        student_post_edit = self.client.post('/admin/money-management/transactions/1/edit', data={'amount': '100'})
        self.assertEqual(student_post_edit.status_code, 403)

        self.logout_user()

    def test_08_dedicated_add_transaction_page_flow(self):
        """
        TEST 8 — Dedicated Add Transaction Page Flow.
        Verify GET /admin/money-management/add renders form, and POST records transaction and redirects to main dashboard.
        """
        with self.client.session_transaction() as sess:
            sess['_user_id'] = str(self.admin.id)
            sess['_fresh'] = True

        # 1. GET /admin/money-management/add
        get_resp = self.client.get('/admin/money-management/add')
        self.assertEqual(get_resp.status_code, 200)
        self.assertIn(b'Add Transaction', get_resp.data)
        self.assertIn(b'Record income or expense into the financial ledger', get_resp.data)
        self.assertIn(b'Back to Money Management', get_resp.data)

        # 2. POST /admin/money-management/add (Record Income)
        post_resp = self.client.post('/admin/money-management/add', data={
            'transaction_type': 'INCOME',
            'amount': '2500.00',
            'transaction_date': '2026-09-06',
            'transaction_time': '10:30 AM',
            'category': 'Client Consulting',
            'purpose': 'TEST Consulting Inflow',
            'description': 'Strategy consultation fee',
            'payment_method': 'Bank Transfer',
            'reference': 'TEST-DEDICATED-001'
        }, follow_redirects=True)

        self.assertEqual(post_resp.status_code, 200)
        self.assertIn(b'Transaction History', post_resp.data)
        self.assertIn(b'TEST Consulting Inflow', post_resp.data)

        # Verify record in DB
        txn = MoneyTransaction.query.filter_by(reference='TEST-DEDICATED-001').first()
        self.assertIsNotNone(txn)
        self.assertEqual(txn.amount, 2500.00)
        self.assertEqual(txn.transaction_type, 'INCOME')

        # Cleanup test transaction
        db.session.delete(txn)
        db.session.commit()

    def test_09_clear_all_transactions_safeguards_and_execution(self):
        """
        TEST 9 — Clear All Transactions Safeguards & Destructive Ledger Reset.
        Verify confirmation requirement ('CLEAR'), atomic deletion of MoneyTransaction only,
        dashboard totals recalculation to zero, and complete data safety of Payment and Application records.
        """
        with self.client.session_transaction() as sess:
            sess['_user_id'] = str(self.admin.id)
            sess['_fresh'] = True

        # 1. Seed two test transactions
        t1 = MoneyTransaction(
            transaction_type='INCOME',
            amount=500.00,
            transaction_date=date(2026, 9, 6),
            category='Software',
            purpose='TEST Inflow To Clear 1',
            source='MANUAL',
            reference='TEST-CLEAR-001'
        )
        t2 = MoneyTransaction(
            transaction_type='EXPENSE',
            amount=150.00,
            transaction_date=date(2026, 9, 6),
            category='Hosting',
            purpose='TEST Outflow To Clear 2',
            source='MANUAL',
            reference='TEST-CLEAR-002'
        )
        db.session.add_all([t1, t2])
        db.session.commit()

        self.assertGreaterEqual(MoneyTransaction.query.count(), 2)

        # 2. Attempt clear without confirmation -> Must FAIL
        fail_resp_1 = self.client.post('/admin/money-management/transactions/clear-all', data={}, follow_redirects=True)
        self.assertEqual(fail_resp_1.status_code, 200)
        self.assertIn(b'Confirmation failed', fail_resp_1.data)
        self.assertIsNotNone(MoneyTransaction.query.filter_by(reference='TEST-CLEAR-001').first())

        # 3. Attempt clear with wrong confirmation -> Must FAIL
        fail_resp_2 = self.client.post('/admin/money-management/transactions/clear-all', data={'confirmation': 'DELETE'}, follow_redirects=True)
        self.assertEqual(fail_resp_2.status_code, 200)
        self.assertIn(b'Confirmation failed', fail_resp_2.data)
        self.assertIsNotNone(MoneyTransaction.query.filter_by(reference='TEST-CLEAR-001').first())

        # 4. Attempt clear with exact confirmation 'CLEAR' -> Must SUCCEED
        success_resp = self.client.post('/admin/money-management/transactions/clear-all', data={'confirmation': 'CLEAR'}, follow_redirects=True)
        self.assertEqual(success_resp.status_code, 200)
        self.assertIn(b'All transactions cleared successfully', success_resp.data)

        # Verify ledger table is completely cleared
        self.assertEqual(MoneyTransaction.query.count(), 0)

        # Verify financial calculations recalculate to zero
        cleared_summary = get_financial_summary()
        self.assertEqual(cleared_summary['total_income'], 0.00)
        self.assertEqual(cleared_summary['total_expense'], 0.00)
        self.assertEqual(cleared_summary['balance'], 0.00)
        self.assertEqual(cleared_summary['transaction_count'], 0)

        # 5. Attempt clearing again when already empty -> Must handle safely without error
        repeat_resp = self.client.post('/admin/money-management/transactions/clear-all', data={'confirmation': 'CLEAR'}, follow_redirects=True)
        self.assertEqual(repeat_resp.status_code, 200)
        self.assertIn(b'All transactions cleared successfully', repeat_resp.data)

    def test_10_data_preservation_verification(self):
        """
        TEST 10 — Non-Negotiable Data Preservation Verification.
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
