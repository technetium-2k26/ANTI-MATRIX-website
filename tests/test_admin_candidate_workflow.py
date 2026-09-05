import os
import io
import unittest
from datetime import datetime, timezone
import docx
from flask import session
from app import create_app
from models import (
    db, User, JobPosting, JobApplication, Employee,
    DocumentTemplate, EmailTemplate, EmployeeDocument, EmailLog
)
from services.offer_letter_service import generate_offer_letter_docx
from services.email_service import (
    render_application_successful_email,
    render_shortlisted_offer_email,
    send_application_successful_email,
    send_offer_letter_shortlisted_email
)


class TestAdminCandidateWorkflow(unittest.TestCase):
    """
    Comprehensive Test Suite for Simplified Admin Candidate Workflow:
    APPLIED -> UNDER REVIEW -> SHORTLISTED -> AUTO-GENERATE OFFER LETTER -> SEND -> AUTO-GENERATE EMPLOYEE CREDENTIALS
    """

    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        db.create_all()

        # Create Admin Account
        self.admin = User(
            name='Test Administrator',
            email='admin@antimatrix.co.in',
            role='admin',
            is_active=True
        )
        self.admin.set_password('Admin@123456')
        db.session.add(self.admin)

        # Create Candidate Account
        self.candidate = User(
            name='Praveen R',
            email='candidate@example.com',
            role='student',
            is_active=True
        )
        self.candidate.set_password('Student@123456')
        db.session.add(self.candidate)

        # Create Job Posting
        self.job = JobPosting(
            title='AI Engineer Intern',
            department='Artificial Intelligence',
            location='Remote',
            employment_type='Internship',
            duration='3_months',
            short_description='Develop production machine learning models and NLP pipelines.',
            description='Detailed description for AI Engineer Intern.',
            skills='Python, PyTorch, Transformers, FastAPI',
            is_active=True
        )
        db.session.add(self.job)

        # Create Master Offer Letter Template DOCX
        self.templates_dir = os.path.join(self.app.root_path, 'uploads', 'templates')
        os.makedirs(self.templates_dir, exist_ok=True)
        self.master_docx_path = os.path.join(self.templates_dir, 'master_offer_test.docx')

        doc = docx.Document()
        doc.add_heading('ANTI-MATRIX OFFER OF INTERNSHIP', 0)
        doc.add_paragraph('Date: [DD/MM/YYYY]')
        doc.add_paragraph('Dear [Candidate Name],')
        doc.add_paragraph('We are pleased to offer you the position of [Job Title] (Ref: [Reference Number]) in the {{department}} department.')
        doc.add_paragraph('Internship Duration: {{internship_duration}}.')
        doc.add_paragraph('Responsibilities: [brief description of responsibilities]')
        doc.add_paragraph('Joining Date: [Joining Date]. Work Mode: [remote / hybrid / on-site].')
        doc.add_paragraph('Acceptance Deadline: [Acceptance Deadline].')
        doc.save(self.master_docx_path)

        self.doc_template = DocumentTemplate(
            template_type='offer_letter',
            name='Anti-Matrix Master Offer Letter',
            filename='master_offer_test.docx',
            file_path=self.master_docx_path,
            is_active=True
        )
        db.session.add(self.doc_template)

        # Seed Standard Email Templates
        self.app_email_tmpl = EmailTemplate(
            template_type='application_successful',
            name='Application Successful Confirmation',
            subject='Application Successfully Submitted — {{Internship Role}} | {{Application ID}}',
            body="""Dear {{Student Name}},

Thank you for applying for the **{{Internship Role}} Internship Opportunity at Anti Matrix**.
Your Application ID is **{{Application ID}}** submitted on **{{Application Date}}**.
Contact us at {{Company Email}}."""
        )
        db.session.add(self.app_email_tmpl)

        self.offer_email_tmpl = EmailTemplate(
            template_type='offer_letter',
            name='Offer Letter Delivery',
            subject='Congratulations! You Have Been Shortlisted — {{Internship Role}} | Anti Matrix',
            body="""Dear {{Student Name}},

Congratulations! You have been shortlisted for {{Internship Role}}.
Application ID: {{Application ID}}
Duration: {{Internship Duration}}
Start Date: {{Start Date}}."""
        )
        db.session.add(self.offer_email_tmpl)

        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        if os.path.exists(self.master_docx_path):
            try:
                os.remove(self.master_docx_path)
            except Exception:
                pass

    def login_admin(self):
        return self.client.post('/login', data={
            'email': 'admin@antimatrix.co.in',
            'password': 'Admin@123456'
        }, follow_redirects=True)

    def login_candidate(self):
        return self.client.post('/login', data={
            'email': 'candidate@example.com',
            'password': 'Student@123456'
        }, follow_redirects=True)

    def test_01_candidate_application_submission_defaults_to_applied_without_auto_email(self):
        """Test that submitting an application sets status=APPLIED and does NOT auto-send email immediately."""
        self.login_candidate()

        # Submit Application
        resume_bytes = io.BytesIO(b"%PDF-1.4 mock resume binary content")
        aadhaar_bytes = io.BytesIO(b"%PDF-1.4 mock aadhaar binary content")
        data = {
            'first_name': 'Praveen',
            'last_name': 'R',
            'email': 'candidate@example.com',
            'phone': '9876543210',
            'address': '123 Tech Park',
            'state': 'Tamil Nadu',
            'city': 'Chennai',
            'pincode': '600001',
            'education_level': 'Undergraduate',
            'degree': 'B.Tech',
            'major': 'Computer Science',
            'college': 'Anna University',
            'department': 'Computer Science',
            'year_of_study': 'Final Year',
            'graduation_year': '2026',
            'current_cgpa': '9.2',
            'resume': (resume_bytes, 'praveen_resume.pdf'),
            'aadhaar': (aadhaar_bytes, 'praveen_aadhaar.pdf')
        }
        res = self.client.post(f'/careers/apply/{self.job.id}', data=data, content_type='multipart/form-data', follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        app_record = JobApplication.query.filter_by(email='candidate@example.com').first()
        self.assertIsNotNone(app_record)

        # Complete Test Payment
        pay_res = self.client.post(f'/careers/apply/test-payment/{app_record.id}', follow_redirects=True)
        self.assertEqual(pay_res.status_code, 200)

        updated_app = db.session.get(JobApplication, app_record.id)
        # Status MUST be APPLIED
        self.assertEqual(updated_app.status, 'APPLIED')
        self.assertEqual(updated_app.application_status, 'APPLIED')
        self.assertEqual(updated_app.status_display, 'Applied')

        # Application Successful Email must NOT be sent automatically (status remains PENDING)
        self.assertEqual(updated_app.application_success_email_status, 'PENDING')
        self.assertIsNone(updated_app.application_success_email_sent_at)

        # Candidate My Applications must show 'Applied'
        my_apps_res = self.client.get('/my-applications')
        self.assertIn(b'Applied', my_apps_res.data)
        self.assertIn(updated_app.formatted_code.encode(), my_apps_res.data)

    def test_02_admin_view_applied_stage_and_mark_under_review(self):
        """Test Admin detail view in APPLIED stage and transition to UNDER_REVIEW."""
        app_record = JobApplication(
            job_id=self.job.id,
            user_id=self.candidate.id,
            full_name='Praveen R',
            email='candidate@example.com',
            phone='9876543210',
            duration='3_months',
            application_fee=399,
            payment_status='paid',
            status='APPLIED',
            application_status='APPLIED',
            resume_filename='resume.pdf',
            resume_path='/fake/resume.pdf'
        )
        db.session.add(app_record)
        db.session.commit()

        self.login_admin()

        # Admin opens application detail page
        detail_res = self.client.get(f'/admin/applications/{app_record.id}')
        self.assertEqual(detail_res.status_code, 200)
        self.assertIn(b'Mark as Under Review', detail_res.data)
        self.assertNotIn(b'EMPLOYEE CREDENTIALS GENERATED', detail_res.data)

        # Admin clicks Mark as Under Review
        post_res = self.client.post(f'/admin/applications/{app_record.id}/mark-under-review', follow_redirects=True)
        self.assertEqual(post_res.status_code, 200)

        updated_app = db.session.get(JobApplication, app_record.id)
        self.assertEqual(updated_app.status, 'UNDER_REVIEW')
        self.assertEqual(updated_app.status_display, 'Under Review')

        # Candidate My Applications must show Under Review
        self.client.get('/logout')
        self.login_candidate()
        my_apps_res = self.client.get('/my-applications')
        self.assertIn(b'Under Review', my_apps_res.data)

    def test_03_under_review_stage_email_preview_and_brevo_send(self):
        """Test Under Review stage displays real applicant values in email preview and dispatches via Brevo."""
        app_record = JobApplication(
            job_id=self.job.id,
            user_id=self.candidate.id,
            full_name='Praveen R',
            email='candidate@example.com',
            phone='9876543210',
            duration='3_months',
            application_fee=399,
            payment_status='paid',
            status='UNDER_REVIEW',
            application_status='UNDER_REVIEW',
            resume_filename='resume.pdf',
            resume_path='/fake/resume.pdf'
        )
        db.session.add(app_record)
        db.session.commit()

        # Verify real candidate data rendered
        preview = render_application_successful_email(app_record)
        self.assertIn('Praveen R', preview['body_text'])
        self.assertIn(app_record.formatted_code, preview['body_text'])
        self.assertIn('AI Engineer Intern', preview['body_text'])
        self.assertNotIn('{{Student Name}}', preview['body_text'])
        self.assertNotIn('{{Application ID}}', preview['body_text'])

        self.login_admin()
        detail_res = self.client.get(f'/admin/applications/{app_record.id}')
        self.assertEqual(detail_res.status_code, 200)
        self.assertIn(b'Praveen R', detail_res.data)
        self.assertIn(b'Send Application Successful Email', detail_res.data)

        # Dispatch Email
        send_res = self.client.post(f'/admin/applications/{app_record.id}/send-application-email', follow_redirects=True)
        self.assertEqual(send_res.status_code, 200)

        updated_app = db.session.get(JobApplication, app_record.id)
        self.assertEqual(updated_app.application_success_email_status, 'SENT')
        self.assertIsNotNone(updated_app.application_success_email_sent_at)

        # Duplicate send blocked
        dup_res = self.client.post(f'/admin/applications/{app_record.id}/send-application-email', follow_redirects=True)
        self.assertIn(b'already been sent', dup_res.data)

    def test_04_shortlisting_auto_generates_offer_letter(self):
        """Test marking application as SHORTLISTED auto-generates candidate-specific Offer Letter DOCX."""
        app_record = JobApplication(
            job_id=self.job.id,
            user_id=self.candidate.id,
            full_name='Praveen R',
            email='candidate@example.com',
            phone='9876543210',
            duration='3_months',
            application_fee=399,
            payment_status='paid',
            status='UNDER_REVIEW',
            application_status='UNDER_REVIEW',
            resume_filename='resume.pdf',
            resume_path='/fake/resume.pdf'
        )
        db.session.add(app_record)
        db.session.commit()

        self.login_admin()

        # Admin clicks Mark as Shortlisted
        post_res = self.client.post(f'/admin/applications/{app_record.id}/mark-shortlisted', follow_redirects=True)
        self.assertEqual(post_res.status_code, 200)

        updated_app = db.session.get(JobApplication, app_record.id)
        self.assertEqual(updated_app.status, 'SHORTLISTED')
        self.assertEqual(updated_app.status_display, 'Shortlisted')

        # Verify Offer Letter DOCX was generated automatically
        offer_doc = updated_app.offer_letter_doc
        self.assertIsNotNone(offer_doc)
        self.assertTrue(os.path.exists(offer_doc.file_path))

        # Check DOCX contents
        gen_doc = docx.Document(offer_doc.file_path)
        full_text = "\n".join([p.text for p in gen_doc.paragraphs])
        self.assertIn('Praveen R', full_text)
        self.assertIn(updated_app.formatted_code, full_text)
        self.assertIn('AI Engineer Intern', full_text)
        self.assertIn('Artificial Intelligence', full_text)

    def test_05_send_shortlist_offer_email_and_auto_generate_employee_credentials(self):
        """Test sending Shortlist Email + Offer Letter creates Employee and generates hashed temporary password."""
        app_record = JobApplication(
            job_id=self.job.id,
            user_id=self.candidate.id,
            full_name='Praveen R',
            email='candidate@example.com',
            phone='9876543210',
            duration='3_months',
            application_fee=399,
            payment_status='paid',
            status='SHORTLISTED',
            application_status='SHORTLISTED',
            resume_filename='resume.pdf',
            resume_path='/fake/resume.pdf'
        )
        db.session.add(app_record)
        db.session.commit()

        # Pre-generate offer letter
        generate_offer_letter_docx(app_record)

        self.login_admin()

        # Verify Shortlist email preview before sending
        preview = render_shortlisted_offer_email(app_record)
        self.assertIn('Praveen R', preview['body_text'])
        self.assertIn('AI Engineer Intern', preview['body_text'])
        self.assertNotIn('{{Student Name}}', preview['body_text'])

        # Admin clicks SEND SHORTLIST EMAIL + OFFER LETTER
        send_res = self.client.post(f'/admin/applications/{app_record.id}/send-shortlist-offer', follow_redirects=True)
        self.assertEqual(send_res.status_code, 200)

        updated_app = db.session.get(JobApplication, app_record.id)
        offer_doc = updated_app.offer_letter_doc
        self.assertEqual(offer_doc.email_status, 'sent')
        self.assertEqual(offer_doc.status, 'SENT')

        # Verify Employee record was created automatically
        self.assertIsNotNone(updated_app.employee)
        emp = updated_app.employee
        self.assertTrue(emp.employee_id.startswith('AM'))
        self.assertEqual(len(emp.employee_id), 6)  # AM + 4 digits = 6 chars
        self.assertTrue(emp.password_hash.startswith(('scrypt:', 'pbkdf2:')))

        # Verify credentials display banner in admin response
        self.assertIn(emp.employee_id.encode(), send_res.data)
        self.assertIn(b'EMPLOYEE CREDENTIALS GENERATED', send_res.data)

        # Refresh page (Idempotency check)
        refresh_res = self.client.get(f'/admin/applications/{app_record.id}')
        self.assertEqual(refresh_res.status_code, 200)
        self.assertEqual(Employee.query.filter_by(application_id=app_record.id).count(), 1)
        self.assertEqual(updated_app.employee.employee_id, emp.employee_id)

    def test_06_brevo_failure_prevents_employee_creation_and_allows_retry(self):
        """Test that if Brevo fails to send Offer Letter, Employee account is NOT created and retry is allowed."""
        app_record = JobApplication(
            job_id=self.job.id,
            user_id=self.candidate.id,
            full_name='Praveen R',
            email='invalid-email-fail',
            phone='9876543210',
            duration='3_months',
            application_fee=399,
            payment_status='paid',
            status='SHORTLISTED',
            application_status='SHORTLISTED',
            resume_filename='resume.pdf',
            resume_path='/fake/resume.pdf'
        )
        db.session.add(app_record)
        db.session.commit()

        generate_offer_letter_docx(app_record)

        self.login_admin()

        # Mock Brevo failure by patching send_brevo_email
        import services.email_service as es
        original_send_brevo = es.send_brevo_email
        es.send_brevo_email = lambda *args, **kwargs: (False, "Brevo API authentication error", None)

        try:
            send_res = self.client.post(f'/admin/applications/{app_record.id}/send-shortlist-offer', follow_redirects=True)
            self.assertIn(b'Failed to send Offer Letter email', send_res.data)

            updated_app = db.session.get(JobApplication, app_record.id)
            self.assertEqual(updated_app.offer_letter_doc.email_status, 'failed')
            # Employee must NOT be created on failure
            self.assertIsNone(updated_app.employee)

            # Retry after restoring send function
            es.send_brevo_email = original_send_brevo
            retry_res = self.client.post(f'/admin/applications/{app_record.id}/send-shortlist-offer', follow_redirects=True)
            self.assertEqual(retry_res.status_code, 200)

            updated_app_after = db.session.get(JobApplication, app_record.id)
            self.assertEqual(updated_app_after.offer_letter_doc.email_status, 'sent')
            self.assertIsNotNone(updated_app_after.employee)
        finally:
            es.send_brevo_email = original_send_brevo


if __name__ == '__main__':
    unittest.main()
