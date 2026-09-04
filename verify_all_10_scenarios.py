import os
import io
import re
from app import create_app
from models import db, User, JobPosting, JobApplication, Payment

app = create_app('development')
app.config['TESTING'] = True
app.config['WTF_CSRF_ENABLED'] = False
app.config['CASHFREE_ENVIRONMENT'] = 'test'
client = app.test_client()

with app.app_context():
    print("=" * 70)
    print("ANTI-MATRIX ADMIN CAREERS & CASHFREE INTERNSHIP - 10-STEP VERIFICATION")
    print("=" * 70)

    # -------------------------------------------------------------
    # TEST 1: Admin Login
    # -------------------------------------------------------------
    print("\n[TEST 1] Admin Login (admin@antimatrix.ai)...")
    res = client.post('/login', data={'email': 'admin@antimatrix.ai', 'password': 'Admin@AntiMatrix2026!'}, follow_redirects=True)
    assert res.status_code == 200, f"Login failed with status {res.status_code}"
    html = res.data.decode('utf-8')
    assert 'Admin Dashboard' in html, "Admin Dashboard link not found in navbar after admin login"
    assert 'Anti-Matrix Admin' in html, "Admin user name not found in navbar"
    print("[PASS] TEST 1: Admin signed in and 'Admin Dashboard' option is visible in navbar.")

    # -------------------------------------------------------------
    # TEST 2: Open Admin Dashboard
    # -------------------------------------------------------------
    print("\n[TEST 2] Access Admin Dashboard (/admin)...")
    res = client.get('/admin')
    assert res.status_code == 200, f"Dashboard failed with status {res.status_code}"
    html = res.data.decode('utf-8')
    assert 'Admin Dashboard' in html
    assert 'Total Jobs' in html
    assert 'Active Openings' in html
    assert 'Total Applications' in html
    assert 'Paid Submissions' in html or 'New Submissions' in html
    print("[PASS] TEST 2: Admin Dashboard opens with live database counters and widgets.")

    # -------------------------------------------------------------
    # TEST 3: Create 3-Month Internship Job Posting
    # -------------------------------------------------------------
    print("\n[TEST 3] Create Job Posting ('Software Engineer Intern', Duration: 3 Months)...")
    JobPosting.query.filter_by(title='Software Engineer Intern').delete()
    db.session.commit()

    job_data = {
        'title': 'Software Engineer Intern',
        'department': 'Engineering',
        'location': 'Chennai',
        'employment_type': 'Internship',
        'duration': '3_months',
        'short_description': 'Join our core platform engineering team to build high-performance web and cloud microservices.',
        'description': 'We are looking for an ambitious Software Engineer Intern in Chennai with solid foundations in Python, JavaScript, and database systems.',
        'skills': 'Python, Flask, React, PostgreSQL, Docker',
        'requirements': 'Pursuing Degree in CS/IT\nStrong data structures and algorithms\nExperience building web applications',
        'responsibilities': 'Write clean, maintainable backend code\nCollaborate with senior engineers on APIs\nWrite automated test suites',
        'salary': 'Rs 35,000 / month',
        'application_deadline': 'Oct 31, 2026',
        'is_active': 'true'
    }
    res = client.post('/admin/jobs/create', data=job_data, follow_redirects=True)
    assert res.status_code == 200, f"Job creation failed with status {res.status_code}"
    html = res.data.decode('utf-8')
    assert 'Software Engineer Intern' in html
    
    created_job = JobPosting.query.filter_by(title='Software Engineer Intern').first()
    assert created_job is not None, "Job was not persisted in database"
    assert created_job.department == 'Engineering'
    assert created_job.duration == '3_months'
    assert created_job.fee_inr == 399
    assert created_job.is_active is True
    print(f"[PASS] TEST 3: Internship Job 'Software Engineer Intern' (Duration: 3 Months, Fee: Rs. 399) saved to database.")

    # -------------------------------------------------------------
    # TEST 4: Dynamic Careers Page Listing
    # -------------------------------------------------------------
    print("\n[TEST 4] Verify Job Appears Dynamically on Public /careers with Duration & Fee...")
    res = client.get('/careers')
    assert res.status_code == 200, f"Careers page failed with status {res.status_code}"
    html = res.data.decode('utf-8')
    assert 'Software Engineer Intern' in html
    assert 'Chennai' in html
    assert '3 Months' in html
    assert '399' in html
    assert f'/careers/apply/{created_job.id}' in html
    print("[PASS] TEST 4: Job dynamically rendered on public /careers page with duration and Rs. 399 fee.")

    # -------------------------------------------------------------
    # TEST 5: Job-Specific Application Page
    # -------------------------------------------------------------
    print(f"\n[TEST 5] Open Job Application Page (/careers/apply/{created_job.id})...")
    res = client.get(f'/careers/apply/{created_job.id}')
    assert res.status_code == 200, f"Apply page failed with status {res.status_code}"
    html = res.data.decode('utf-8')
    assert 'Apply for Software Engineer Intern' in html
    assert '3 Months' in html
    assert '399' in html
    assert 'Aadhaar Card' in html
    assert 'College ID Card' in html
    assert 'Resume' in html
    print("[PASS] TEST 5: Job-specific application page loaded with full questionnaire sections and documents.")

    # -------------------------------------------------------------
    # TEST 6: Candidate Submits Application Questionnaire
    # -------------------------------------------------------------
    print("\n[TEST 6] Candidate Fills Application Questionnaire and Reaches Review Step...")
    JobApplication.query.filter_by(job_id=created_job.id, email='arun.kumar@example.com').delete()
    Payment.query.delete()
    db.session.commit()

    resume_file = (io.BytesIO(b"%PDF-1.4 Resume for Arun"), 'arun_resume.pdf')
    aadhaar_file = (io.BytesIO(b"%PDF-1.4 Aadhaar for Arun"), 'arun_aadhaar.pdf')
    college_id_file = (io.BytesIO(b"%PDF-1.4 College ID for Arun"), 'arun_college_id.pdf')

    candidate_data = {
        'first_name': 'Arun',
        'last_name': 'Kumar',
        'full_name': 'Arun Kumar',
        'email': 'arun.kumar@example.com',
        'phone': '9876543210',
        'address': '123 Tech Park, OMR Road',
        'state': 'Tamil Nadu',
        'city': 'Chennai',
        'pincode': '600096',
        'education_level': "Bachelor's Degree",
        'degree': 'B.Tech / B.E. (Bachelor of Technology / Engineering)',
        'major': 'Information Technology',
        'department': 'Department of IT',
        'college': 'Anna University',
        'year_of_study': '3rd Year',
        'current_cgpa': '8.75',
        'graduation_year': '2025',
        'experience': '6 months internship',
        'skills': 'Python, Flask, JavaScript, SQL, Git',
        'portfolio_url': 'https://arunkumar.dev',
        'linkedin_url': 'https://linkedin.com/in/arunkumar',
        'github_url': 'https://github.com/arunkumar',
        'cover_letter': 'I am eager to apply for the Software Engineer Intern role.',
        'why_join': 'Anti-Matrix has cutting-edge enterprise projects.',
        'resume': resume_file,
        'aadhaar': aadhaar_file,
        'college_id': college_id_file
    }

    res = client.post(f'/careers/apply/{created_job.id}', data=candidate_data, content_type='multipart/form-data', follow_redirects=False)
    assert res.status_code == 302, f"Expected redirect to review page, got {res.status_code}"
    
    app_record = JobApplication.query.filter_by(job_id=created_job.id, email='arun.kumar@example.com').first()
    assert app_record is not None, "Application not persisted in database"
    assert app_record.payment_status == 'pending'
    assert app_record.application_status == 'pending_payment'
    assert app_record.application_fee == 399
    assert os.path.exists(app_record.resume_path), "Uploaded resume was not saved on disk"
    assert os.path.exists(app_record.aadhaar_path), "Uploaded Aadhaar was not saved on disk"
    assert os.path.exists(app_record.college_id_path), "Uploaded College ID was not saved on disk"
    print(f"[PASS] TEST 6: Application questionnaire saved (ID: {app_record.application_code}), documents secured, status pending_payment.")

    # -------------------------------------------------------------
    # TEST 7: Review Application and Cashfree Checkout Creation
    # -------------------------------------------------------------
    print(f"\n[TEST 7] Review Step & Server-Side Fee Checkout (/careers/apply/review/{app_record.id})...")
    res_review = client.get(f'/careers/apply/review/{app_record.id}')
    assert res_review.status_code == 200
    html_rev = res_review.data.decode('utf-8')
    assert 'Application Review' in html_rev
    assert '399' in html_rev

    # Create Cashfree Checkout Order (Server calculates 399)
    res_checkout = client.post(f'/careers/apply/checkout/{app_record.id}', data={'amount': '1'}, follow_redirects=False)
    assert res_checkout.status_code == 302
    
    payment = Payment.query.filter_by(application_id=app_record.id).first()
    assert payment is not None, "Cashfree Payment record was not created"
    assert payment.amount == 399.0, f"Expected server-enforced amount 399.0, got {payment.amount}"
    assert payment.payment_status == 'pending'
    print(f"[PASS] TEST 7: Review verified, Cashfree order generated (Order ID: {payment.cashfree_order_id}, Amount: Rs. {payment.amount}).")

    # -------------------------------------------------------------
    # TEST 8: Server-Side Payment Verification & Success Page
    # -------------------------------------------------------------
    print(f"\n[TEST 8] Cashfree Return Callback & Server-Side Verification...")
    res_return = client.get(f'/payment/cashfree/return?order_id={payment.cashfree_order_id}&sim_status=SUCCESS', follow_redirects=True)
    assert res_return.status_code == 200
    html_success = res_return.data.decode('utf-8')
    assert 'Application Submitted Successfully' in html_success
    assert 'Paid' in html_success
    assert '399' in html_success
    assert app_record.application_code in html_success

    db.session.refresh(payment)
    db.session.refresh(app_record)
    assert payment.payment_status == 'paid'
    assert app_record.payment_status == 'paid'
    assert app_record.application_status == 'submitted'
    print(f"[PASS] TEST 8: Payment verified server-side, marked 'paid', application transitioned to 'submitted'.")

    # -------------------------------------------------------------
    # TEST 9: Admin Applications Dossier & Secure Document Access
    # -------------------------------------------------------------
    print(f"\n[TEST 9] Admin Dossier & Secure Document Authorization...")
    res_dossier = client.get(f'/admin/applications/{app_record.id}')
    assert res_dossier.status_code == 200
    html_dos = res_dossier.data.decode('utf-8')
    assert 'Arun Kumar' in html_dos
    assert 'Anna University' in html_dos
    assert '8.75' in html_dos
    assert 'Cashfree Payment Record' in html_dos

    # Download Aadhaar (Authorized Admin)
    res_aadhaar = client.get(f'/admin/applications/{app_record.id}/document/aadhaar')
    assert res_aadhaar.status_code == 200

    # Download College ID (Authorized Admin)
    res_cid = client.get(f'/admin/applications/{app_record.id}/document/college_id')
    assert res_cid.status_code == 200
    print("[PASS] TEST 9: Admin viewed complete dossier with Cashfree payment details and securely accessed documents.")

    # -------------------------------------------------------------
    # TEST 10: Logout & Protected Routes Verification
    # -------------------------------------------------------------
    print("\n[TEST 10] Logout & Verify Document / Admin Route Protection...")
    res_logout = client.get('/logout', follow_redirects=True)
    assert res_logout.status_code == 200
    
    # Guest cannot download Aadhaar
    res_unauth_doc = client.get(f'/admin/applications/{app_record.id}/document/aadhaar', follow_redirects=False)
    assert res_unauth_doc.status_code in [302, 308, 401, 403]

    # Guest cannot view /admin
    res_unauth_admin = client.get('/admin', follow_redirects=False)
    assert res_unauth_admin.status_code in [302, 308, 401, 403]
    print("[PASS] TEST 10: Logged out cleanly. Unauthenticated access to /admin and sensitive documents strictly protected.")

    print("\n" + "=" * 70)
    print("ALL 10 VERIFICATION SCENARIOS PASSED WITH 100% SUCCESS!")
    print("=" * 70)
