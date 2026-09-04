"""
End-to-End Verification Script for Anti-Matrix Employee ID & Credential Generation System.
Tests full pipeline:
1. Admin Login & Dashboard Overview (+ Create Employee ID button).
2. Candidate Application + Paid Payment Record.
3. Accessing /admin/employees/create with candidate preview.
4. Generating unique random Employee ID (AM####) and cryptographically strong password.
5. Verifying DB storage: Only password_hash is stored, NO plaintext password.
6. Verifying Confirmation UI with Copy Employee ID, Copy Password, and Copy Credentials.
7. Viewing Employee Profile without plaintext password leakage.
8. Blocking duplicate employee creation for the same application.
9. Blocking employee creation for unpaid applications.
10. Verifying access control: Non-admin users are strictly blocked (403/302).
"""
import sys
import os
import io

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from models import db, User, JobPosting, JobApplication, Payment, Employee


def run_e2e_verification():
    print("=" * 75)
    print("ANTI-MATRIX EMPLOYEE ID & CREDENTIAL GENERATION - VERIFICATION SUITE")
    print("=" * 75)

    app = create_app('development')
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    client = app.test_client()

    with app.app_context():
        # Setup Admin
        admin = User.query.filter_by(email='admin@antimatrix.ai').first()
        if not admin:
            admin = User(name='Test Admin', email='admin@antimatrix.ai', role='admin', is_active=True)
            admin.set_password('Admin@AntiMatrix2026!')
            db.session.add(admin)
            db.session.commit()

        # Setup Member
        member = User.query.filter_by(email='member@example.com').first()
        if not member:
            member = User(name='Member User', email='member@example.com', role='member', is_active=True)
            member.set_password('Member@2026!')
            db.session.add(member)
            db.session.commit()

        # Setup Job
        job = JobPosting.query.filter_by(title='AI Solutions Engineer Intern').first()
        if not job:
            job = JobPosting(
                title='AI Solutions Engineer Intern',
                department='AI Solutions',
                location='Remote (Worldwide)',
                employment_type='Internship',
                duration='3_months',
                short_description='Develop production-ready LLM agents and multi-modal integrations.',
                description='We are seeking an ambitious engineer for enterprise AI projects.',
                skills='Python, PyTorch, LangChain, PostgreSQL, Docker',
                is_active=True
            )
            db.session.add(job)
            db.session.commit()

        # Step 1: Admin Login & Check Dashboard + Create Employee ID button
        print("\n[STEP 1] Admin Sign-In & Dashboard Button Verification...")
        client.post('/login', data={'email': 'admin@antimatrix.ai', 'password': 'Admin@AntiMatrix2026!'})
        res_dash = client.get('/admin/dashboard')
        assert res_dash.status_code == 200
        html_dash = res_dash.data.decode('utf-8')
        assert '+ Create Employee ID' in html_dash
        assert '/admin/employees/create' in html_dash
        assert 'Employees' in html_dash
        print("[PASS] STEP 1: '+ Create Employee ID' button and 'Employees' nav tab verified on Admin Dashboard.")

        # Step 2: Create Paid Candidate Application
        print("\n[STEP 2] Setting Up Verified Paid Candidate Application...")
        candidate = JobApplication.query.filter_by(email='raghav.sharma@example.com').first()
        if candidate:
            if candidate.employee:
                db.session.delete(candidate.employee)
            db.session.delete(candidate)
            db.session.commit()

        candidate = JobApplication(
            job_id=job.id,
            first_name='Raghav',
            last_name='Sharma',
            full_name='Raghav Sharma',
            email='raghav.sharma@example.com',
            phone='9876543210',
            address='88 Innovation Parkway',
            state='Maharashtra',
            city='Pune',
            pincode='411001',
            education_level="Bachelor's Degree",
            degree='B.Tech Artificial Intelligence',
            major='Artificial Intelligence',
            graduation_year='2026',
            resume_filename='raghav_resume.pdf',
            resume_path='uploads/resumes/raghav_resume.pdf',
            duration='3_months',
            application_fee=399,
            payment_status='paid',
            application_status='submitted',
            status='New'
        )
        db.session.add(candidate)
        db.session.flush()
        candidate.application_code = f"AM-APP-{candidate.id:06d}"
        db.session.commit()
        print(f"[PASS] STEP 2: Candidate {candidate.full_name} ({candidate.formatted_code}) registered with payment_status='paid'.")

        # Step 3: Open Create Employee ID page
        print("\n[STEP 3] Opening /admin/employees/create...")
        res_create_page = client.get(f'/admin/employees/create?application_id={candidate.id}')
        assert res_create_page.status_code == 200
        html_create = res_create_page.data.decode('utf-8')
        assert 'Create Employee ID' in html_create
        assert candidate.formatted_code in html_create
        assert 'Raghav Sharma' in html_create
        print("[PASS] STEP 3: Create Employee ID form displayed with candidate verification preview.")

        # Step 4: Generate Employee Credentials
        print("\n[STEP 4] Submitting Employee Creation Form...")
        res_submit = client.post('/admin/employees/create', data={'application_id': candidate.id})
        assert res_submit.status_code == 200
        html_cred = res_submit.data.decode('utf-8')
        assert 'Employee Account Created Successfully' in html_cred
        assert 'Copy Employee ID' in html_cred
        assert 'Copy Password' in html_cred
        assert 'Copy Credentials' in html_cred
        assert 'IMPORTANT SECURITY NOTICE' in html_cred

        # Step 5: Database Validation
        print("\n[STEP 5] Database Verification for Employee Record & Password Hash...")
        emp_record = Employee.query.filter_by(application_id=candidate.id).first()
        assert emp_record is not None, "Employee record not found in database"
        assert emp_record.employee_id.startswith('AM'), f"Invalid format: {emp_record.employee_id}"
        assert len(emp_record.employee_id) == 6, f"Expected 6 characters (AM####), got {emp_record.employee_id}"
        assert emp_record.employee_id[2:].isdigit(), "Expected 4 random digits after AM"
        
        # Verify Password Hash
        assert emp_record.password_hash is not None
        assert not emp_record.password_hash.startswith('AM'), "Plaintext password must not be stored in password_hash"
        assert 'scrypt:' in emp_record.password_hash or 'pbkdf2:' in emp_record.password_hash
        print(f"[PASS] STEP 5: Employee record created (ID: {emp_record.employee_id}), securely hashed in DB.")

        # Step 6: View Employee Profile (No plaintext password leak)
        print("\n[STEP 6] Visiting Employee Detail Page (/admin/employees/<id>)...")
        res_view = client.get(f'/admin/employees/{emp_record.employee_id}')
        assert res_view.status_code == 200
        html_view = res_view.data.decode('utf-8')
        assert emp_record.employee_id in html_view
        assert 'Raghav Sharma' in html_view
        assert candidate.formatted_code in html_view
        assert emp_record.password_hash not in html_view
        assert 'Generated Password' not in html_view
        print("[PASS] STEP 6: Employee Profile viewed without exposing password or password hash.")

        # Step 7: Duplicate Employee Creation Block
        print("\n[STEP 7] Testing Duplicate Employee Account Prevention...")
        res_dup = client.post('/admin/employees/create', data={'application_id': candidate.id}, follow_redirects=True)
        assert res_dup.status_code == 200
        assert f"Employee ID already exists: {emp_record.employee_id}" in res_dup.data.decode('utf-8')
        total_emp_for_app = Employee.query.filter_by(application_id=candidate.id).count()
        assert total_emp_for_app == 1
        print("[PASS] STEP 7: Duplicate Employee account prevented.")

        # Step 8: Unpaid Application Creation Block
        print("\n[STEP 8] Testing Unpaid Application Employee Creation Block...")
        unpaid_app = JobApplication(
            job_id=job.id,
            first_name='Unpaid',
            last_name='User',
            full_name='Unpaid User',
            email='unpaid.user@example.com',
            phone='9876543210',
            address='123 Test St',
            state='Karnataka',
            city='Bengaluru',
            pincode='560001',
            education_level="Bachelor's Degree",
            degree='B.Sc',
            major='CS',
            graduation_year='2026',
            resume_filename='unpaid.pdf',
            resume_path='uploads/resumes/unpaid.pdf',
            duration='1_month',
            application_fee=199,
            payment_status='pending',
            application_status='pending_payment',
            status='New'
        )
        db.session.add(unpaid_app)
        db.session.commit()

        res_unpaid = client.post('/admin/employees/create', data={'application_id': unpaid_app.id}, follow_redirects=True)
        assert res_unpaid.status_code == 200
        assert 'Employee ID cannot be created until the application payment is completed' in res_unpaid.data.decode('utf-8')
        assert Employee.query.filter_by(application_id=unpaid_app.id).first() is None
        print("[PASS] STEP 8: Unpaid application blocked from Employee ID creation.")

        # Step 9: Unauthorized User Block
        print("\n[STEP 9] Testing Access Control (Guest / Member)...")
        client.get('/logout')
        res_guest = client.get('/admin/employees/create')
        assert res_guest.status_code in [302, 308]

        client.post('/login', data={'email': 'member@example.com', 'password': 'Member@2026!'})
        res_member = client.get('/admin/employees/create')
        assert res_member.status_code == 403
        client.get('/logout')
        print("[PASS] STEP 9: Non-admin and guest users strictly blocked from employee management.")

        print("\n" + "=" * 75)
        print("ALL EMPLOYEE CREDENTIAL GENERATION VERIFICATION SCENARIOS PASSED 100%!")
        print("=" * 75)


if __name__ == '__main__':
    run_e2e_verification()
