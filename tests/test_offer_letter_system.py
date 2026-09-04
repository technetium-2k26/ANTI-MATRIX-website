import unittest
import os
import shutil
import tempfile
import docx
from datetime import datetime, timezone
from app import create_app
from models import db, User, JobPosting, JobApplication, Employee, EmployeeDocument, DocumentTemplate, EmailTemplate
from services.offer_letter_service import generate_offer_letter_docx, send_offer_letter_email, get_offer_letter_master_path


class TestOfferLetterSystem(unittest.TestCase):
    def setUp(self):
        """Set up test Flask app with in-memory or test SQLite database."""
        self.app = create_app('testing')
        self.app.config['WTF_CSRF_ENABLED'] = False
        
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        
        db.create_all()

        # Master template path
        self.master_template_path = os.path.join(self.app.root_path, 'uploads', 'templates', 'offer letter (Anti-matrix).docx')
        self.assertTrue(os.path.exists(self.master_template_path), f"Master template missing at {self.master_template_path}")

        # Seed or fetch Document Template
        self.doc_template = DocumentTemplate.query.filter_by(template_type='offer_letter').first()
        if not self.doc_template:
            self.doc_template = DocumentTemplate(
                template_type='offer_letter',
                name='Anti-Matrix Master Offer Letter',
                filename='offer letter (Anti-matrix).docx',
                file_path=self.master_template_path,
                is_active=True
            )
            db.session.add(self.doc_template)

        # Seed or fetch Email Templates
        self.email_tmpl_offer = EmailTemplate.query.filter_by(template_type='offer_letter').first()
        if not self.email_tmpl_offer:
            self.email_tmpl_offer = EmailTemplate(
                template_type='offer_letter',
                name='Offer Letter Delivery',
                subject='Offer Letter — {{job_title}} | {{employee_id}}',
                body='Dear {{employee_name}},\n\nCongratulations on your selection for {{job_title}} (Employee ID: {{employee_id}}).\n\nPlease find your official Offer Letter attached.\n\nBest Regards,\nAnti-Matrix'
            )
            db.session.add(self.email_tmpl_offer)

        self.email_tmpl_app = EmailTemplate.query.filter_by(template_type='application_successful').first()
        if not self.email_tmpl_app:
            self.email_tmpl_app = EmailTemplate(
                template_type='application_successful',
                name='Application Successful',
                subject='Application Successful — {{job_title}} | {{application_id}}',
                body='Dear {{employee_name}},\n\nYour application {{application_id}} for {{job_title}} has been received.\n\nRegards,\nAnti-Matrix'
            )
            db.session.add(self.email_tmpl_app)

        # Create Job 1: AI Engineer Intern
        self.job1 = JobPosting(
            title='AI Engineer Intern',
            department='Engineering',
            location='Remote / Hybrid',
            employment_type='Internship',
            duration='3_months',
            short_description='Work on cutting-edge generative AI models and neural networks.',
            description='Detailed description for AI Engineer Intern.',
            requirements='Python, PyTorch, LLMs, REST APIs',
            responsibilities='Lead model fine-tuning and API integration.',
            is_active=True
        )
        
        # Create Job 2: Full Stack Developer Intern
        self.job2 = JobPosting(
            title='Full Stack Developer Intern',
            department='Product Engineering',
            location='Chennai Office',
            employment_type='Internship',
            duration='3_months',
            short_description='Build scalable web applications and distributed systems.',
            description='Detailed description for Full Stack Developer Intern.',
            requirements='JavaScript, Python, React, Flask, PostgreSQL',
            responsibilities='Develop frontend components and backend services.',
            is_active=True
        )
        db.session.add_all([self.job1, self.job2])
        db.session.commit()

        # Create Candidate Application 1 (for John Doe)
        self.app1 = JobApplication(
            job_id=self.job1.id,
            application_code='AM-APP-000123',
            full_name='John Doe',
            email='john.doe@example.com',
            phone='+91 9876543210',
            duration='3_months',
            resume_filename='john_resume.pdf',
            resume_path='uploads/resumes/john_resume.pdf',
            application_fee=1999,
            payment_status='paid',
            application_status='submitted'
        )

        # Create Candidate Application 2 (for Jane Smith)
        self.app2 = JobApplication(
            job_id=self.job2.id,
            application_code='AM-APP-000456',
            full_name='Jane Smith',
            email='jane.smith@example.com',
            phone='+91 9123456780',
            duration='3_months',
            resume_filename='jane_resume.pdf',
            resume_path='uploads/resumes/jane_resume.pdf',
            application_fee=1999,
            payment_status='paid',
            application_status='submitted'
        )
        db.session.add_all([self.app1, self.app2])
        db.session.commit()

        # Create Admin User
        self.admin = User.query.filter_by(email='admin@antimatrix.ai').first()
        if not self.admin:
            self.admin = User(name='Test Admin', email='admin@antimatrix.ai', role='admin', is_active=True)
            self.admin.set_password('Admin@AntiMatrix2026!')
            db.session.add(self.admin)

        # Create Regular Member
        self.member = User.query.filter_by(email='member@example.com').first()
        if not self.member:
            self.member = User(name='Regular Member', email='member@example.com', role='member', is_active=True)
            self.member.set_password('Member@2026!')
            db.session.add(self.member)

        # Create Employee 1: AM4827
        self.emp1 = Employee(
            employee_id='AM4827',
            application_id=self.app1.id,
            account_status='active'
        )
        self.emp1.set_password('AMTestPass1@')

        # Create Employee 2: AM1934
        self.emp2 = Employee(
            employee_id='AM1934',
            application_id=self.app2.id,
            account_status='active'
        )
        self.emp2.set_password('AMTestPass2@')

        db.session.add_all([self.emp1, self.emp2])
        db.session.commit()

    def login_admin(self):
        return self.client.post('/login', data={'email': 'admin@antimatrix.ai', 'password': 'Admin@AntiMatrix2026!'}, follow_redirects=True)

    def login_member(self):
        return self.client.post('/login', data={'email': 'member@example.com', 'password': 'Member@2026!'}, follow_redirects=True)

    def logout(self):
        return self.client.get('/logout', follow_redirects=True)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_01_master_template_integrity(self):
        """Verify master template exists and contains required placeholders."""
        doc = docx.Document(self.master_template_path)
        all_text = "\n".join([p.text for p in doc.paragraphs])
        
        self.assertIn('[DD/MM/YYYY]', all_text)
        self.assertIn('[Candidate Name]', all_text)
        self.assertIn('[Reference Number]', all_text)
        self.assertIn('[Job Title]', all_text)
        self.assertIn('[brief description of responsibilities]', all_text)
        self.assertIn('[key tasks / deliverables]', all_text)
        self.assertIn('[Joining Date]', all_text)
        self.assertIn('[remote / hybrid / on-site]', all_text)
        self.assertIn('Anti-Matrix', all_text)

    def test_02_generate_offer_letter_for_employee_1(self):
        """Generate Offer Letter for Employee 1 (AM4827 - John Doe) and verify content and formatting."""
        emp_doc, output_path = generate_offer_letter_docx(self.emp1)

        self.assertTrue(os.path.exists(output_path))
        self.assertEqual(emp_doc.employee_id, self.emp1.id)
        self.assertEqual(emp_doc.file_name, 'AM4827_Offer_Letter.docx')
        self.assertEqual(emp_doc.status, 'GENERATED')
        self.assertEqual(emp_doc.email_status, 'not_sent')

        # Inspect generated DOCX
        doc = docx.Document(output_path)
        doc_text = "\n".join([p.text for p in doc.paragraphs])

        # Verify dynamic fields replaced
        self.assertIn('John Doe', doc_text)
        self.assertIn(self.app1.formatted_code, doc_text)
        self.assertIn('AI Engineer Intern', doc_text)
        self.assertNotIn('[Candidate Name]', doc_text)
        self.assertNotIn('[Reference Number]', doc_text)
        self.assertNotIn('[Job Title]', doc_text)

        # Verify formatting in Paragraph 2 (Dear John Doe,)
        p2 = doc.paragraphs[2]
        self.assertIn('Dear John Doe,', p2.text)
        self.assertTrue(p2.runs[0].bold, "Candidate greeting run should preserve bold formatting")

        # Verify formatting in Paragraph 3 (Ref.: AM-APP-...)
        p3 = doc.paragraphs[3]
        self.assertIn(f'Ref.: {self.app1.formatted_code}', p3.text)
        self.assertTrue(p3.runs[0].bold, "Reference number run should preserve bold formatting")

    def test_03_generate_offer_letter_for_employee_2_and_isolation(self):
        """Generate Offer Letter for Employee 2 (AM1934 - Jane Smith) and verify isolation from Employee 1."""
        emp_doc1, path1 = generate_offer_letter_docx(self.emp1)
        emp_doc2, path2 = generate_offer_letter_docx(self.emp2)

        self.assertNotEqual(path1, path2)
        self.assertTrue(os.path.exists(path1))
        self.assertTrue(os.path.exists(path2))

        # Check Doc 1
        doc1 = docx.Document(path1)
        text1 = "\n".join([p.text for p in doc1.paragraphs])
        self.assertIn('John Doe', text1)
        self.assertIn('AI Engineer Intern', text1)
        self.assertIn(self.app1.formatted_code, text1)
        self.assertNotIn('Jane Smith', text1)
        self.assertNotIn('Full Stack Developer Intern', text1)

        # Check Doc 2
        doc2 = docx.Document(path2)
        text2 = "\n".join([p.text for p in doc2.paragraphs])
        self.assertIn('Jane Smith', text2)
        self.assertIn('Full Stack Developer Intern', text2)
        self.assertIn(self.app2.formatted_code, text2)
        self.assertNotIn('John Doe', text2)
        self.assertNotIn('AI Engineer Intern', text2)

    def test_04_master_template_remains_unmodified_after_generations(self):
        """Verify that the master template DOCX on disk was never altered during generations."""
        # Generate for both employees
        generate_offer_letter_docx(self.emp1)
        generate_offer_letter_docx(self.emp2)

        # Inspect master template
        master_doc = docx.Document(self.master_template_path)
        master_text = "\n".join([p.text for p in master_doc.paragraphs])

        self.assertIn('[Candidate Name]', master_text)
        self.assertIn('[Reference Number]', master_text)
        self.assertIn('[Job Title]', master_text)
        self.assertNotIn('John Doe', master_text)
        self.assertNotIn('Jane Smith', master_text)
        self.assertNotIn('AM4827', master_text)
        self.assertNotIn('AM1934', master_text)

    def test_05_verify_and_send_offer_letter_email(self):
        """Test sending Offer Letter email and one-time delivery protection."""
        emp_doc, path = generate_offer_letter_docx(self.emp1)
        self.assertEqual(emp_doc.email_status, 'not_sent')

        # First send attempt -> should succeed
        success, msg = send_offer_letter_email(self.emp1)
        self.assertTrue(success)
        self.assertIn('successfully sent', msg.lower())

        # Check DB state
        updated_doc = db.session.get(EmployeeDocument, emp_doc.id)
        self.assertEqual(updated_doc.email_status, 'sent')
        self.assertEqual(updated_doc.status, 'SENT')
        self.assertIsNotNone(updated_doc.sent_at)
        self.assertIsNotNone(updated_doc.verified_at)

        # Second send attempt -> MUST be blocked by one-time send protection
        success2, msg2 = send_offer_letter_email(self.emp1)
        self.assertFalse(success2)
        self.assertIn('already sent', msg2.lower())

    def test_06_admin_routes_security_and_access_control(self):
        """Ensure unauthenticated and non-admin users cannot access template and document routes."""
        # 1. Unauthenticated user -> redirect to /login
        res = self.client.get('/admin/templates')
        self.assertEqual(res.status_code, 302)
        self.assertIn('/login', res.headers['Location'])

        res = self.client.get('/admin/employees/AM4827/offer-letter/generate')
        self.assertEqual(res.status_code, 302)
        self.assertIn('/login', res.headers['Location'])

        res = self.client.post('/admin/employees/AM4827/offer-letter/send')
        self.assertEqual(res.status_code, 302)
        self.assertIn('/login', res.headers['Location'])

        # 2. Non-admin regular member -> 403 Forbidden
        self.login_member()
        res_mem = self.client.get('/admin/templates')
        self.assertEqual(res_mem.status_code, 403)

        res_mem2 = self.client.get('/admin/employees/AM4827/offer-letter/generate')
        self.assertEqual(res_mem2.status_code, 403)

        res_mem3 = self.client.post('/admin/employees/AM4827/offer-letter/send')
        self.assertEqual(res_mem3.status_code, 403)
        self.logout()

    def test_07_admin_template_management_view_with_session(self):
        """Test template management routes with authenticated admin session."""
        self.login_admin()

        # View Template Hub
        res = self.client.get('/admin/templates')
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn('TEMPLATE MANAGEMENT', html.upper())
        self.assertIn('EMAIL TEMPLATES', html.upper())
        self.assertIn('DOCUMENT TEMPLATES', html.upper())
        self.assertIn('Offer Letter', html)
        self.assertIn('Experience Letter', html)
        self.assertIn('Certificate', html)

        # Test updating Email Template
        res_post = self.client.post('/admin/templates/email/offer_letter', data={
            'subject': 'Official Offer Letter — {{job_title}} | {{employee_id}}',
            'body': 'Dear {{employee_name}},\n\nHere is your official offer letter for {{job_title}}.\n\nAnti-Matrix Team'
        }, follow_redirects=True)
        self.assertEqual(res_post.status_code, 200)

        db.session.expire_all()
        updated_tmpl = EmailTemplate.query.filter_by(template_type='offer_letter').first()
        self.assertEqual(updated_tmpl.subject, 'Official Offer Letter — {{job_title}} | {{employee_id}}')
        self.assertIn('Anti-Matrix Team', updated_tmpl.body)

    def test_08_admin_generate_preview_and_verify_flow(self):
        """Test end-to-end admin generation and verification web endpoints."""
        self.login_admin()

        # 1. GET generation review page
        res = self.client.get('/admin/employees/AM4827/offer-letter/generate')
        self.assertEqual(res.status_code, 200)
        self.assertIn('Generate Master Offer Letter', res.get_data(as_text=True))
        self.assertIn('John Doe', res.get_data(as_text=True))
        self.assertIn('AM4827', res.get_data(as_text=True))

        # 2. POST to generate
        res_gen = self.client.post('/admin/employees/AM4827/offer-letter/generate', data={
            'joining_date': '15 October 2026',
            'work_mode': 'Remote (Chennai Team)',
            'responsibilities': 'Lead deep learning research and prompt engineering',
            'key_tasks': 'Build AGY integrations and model pipelines',
            'conditions': 'submission of ID and degree certificate',
            'acceptance_deadline': '22 October 2026'
        }, follow_redirects=True)
        self.assertEqual(res_gen.status_code, 200)
        gen_html = res_gen.get_data(as_text=True)
        self.assertIn('Offer Letter Generated Successfully', gen_html)
        self.assertIn('AM4827_Offer_Letter.docx', gen_html)

        # 3. GET preview (download generated DOCX)
        res_prev = self.client.get('/admin/employees/AM4827/offer-letter/preview')
        self.assertEqual(res_prev.status_code, 200)
        self.assertIn('application/vnd.openxmlformats-officedocument.wordprocessingml.document', res_prev.headers['Content-Type'])

        # 4. GET verify page
        res_ver = self.client.get('/admin/employees/AM4827/offer-letter/verify')
        self.assertEqual(res_ver.status_code, 200)
        ver_html = res_ver.get_data(as_text=True)
        self.assertIn('john.doe@example.com', ver_html)
        self.assertIn('Verify & Send Offer Letter', ver_html)

        # 5. POST to send email
        res_send = self.client.post('/admin/employees/AM4827/offer-letter/send', follow_redirects=True)
        self.assertEqual(res_send.status_code, 200)
        self.assertIn('successfully sent', res_send.get_data(as_text=True).lower())

        # 6. POST duplicate send -> should show already sent warning
        res_dup = self.client.post('/admin/employees/AM4827/offer-letter/send', follow_redirects=True)
        self.assertEqual(res_dup.status_code, 200)
        self.assertIn('already sent', res_dup.get_data(as_text=True).lower())


if __name__ == '__main__':
    unittest.main()
