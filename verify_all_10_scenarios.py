import os
import io
import re
from app import create_app
from models import db, User, JobPosting, JobApplication

app = create_app('development')
app.config['TESTING'] = True
app.config['WTF_CSRF_ENABLED'] = False
client = app.test_client()

with app.app_context():
    print("=" * 70)
    print("ANTI-MATRIX ADMIN CAREERS & APPLICATION SYSTEM - 10-STEP VERIFICATION")
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
    assert 'New Submissions' in html
    print("[PASS] TEST 2: Admin Dashboard opens with live database counters and widgets.")

    # -------------------------------------------------------------
    # TEST 3: Create Job Posting
    # -------------------------------------------------------------
    print("\n[TEST 3] Create Job Posting ('Software Engineer Intern')...")
    # Clean previous test job if exists
    JobPosting.query.filter_by(title='Software Engineer Intern').delete()
    db.session.commit()

    job_data = {
        'title': 'Software Engineer Intern',
        'department': 'Engineering',
        'location': 'Chennai',
        'employment_type': 'Internship',
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
    assert created_job.is_active is True
    print(f"[PASS] TEST 3: Job 'Software Engineer Intern' (ID: #{created_job.id}) saved to database.")

    # -------------------------------------------------------------
    # TEST 4: Dynamic Careers Page Listing
    # -------------------------------------------------------------
    print("\n[TEST 4] Verify Job Appears Dynamically on Public /careers...")
    res = client.get('/careers')
    assert res.status_code == 200, f"Careers page failed with status {res.status_code}"
    html = res.data.decode('utf-8')
    assert 'Software Engineer Intern' in html, "Software Engineer Intern not listed on public careers page"
    assert 'Chennai' in html, "Location Chennai not listed on public careers page"
    assert f'/careers/apply/{created_job.id}' in html, f"Apply link /careers/apply/{created_job.id} not found in careers HTML"
    print("[PASS] TEST 4: Job dynamically rendered on public /careers page without code changes.")

    # -------------------------------------------------------------
    # TEST 5: Job-Specific Application Page
    # -------------------------------------------------------------
    print(f"\n[TEST 5] Open Job Application Page (/careers/apply/{created_job.id})...")
    res = client.get(f'/careers/apply/{created_job.id}')
    assert res.status_code == 200, f"Apply page failed with status {res.status_code}"
    html = res.data.decode('utf-8')
    assert 'Apply for Software Engineer Intern' in html
    assert 'Engineering' in html
    assert 'Chennai' in html
    print("[PASS] TEST 5: Job-specific application page loaded with correct job details.")

    # -------------------------------------------------------------
    # TEST 6: Candidate Submits Application with Resume
    # -------------------------------------------------------------
    print("\n[TEST 6] Candidate Submits Application with PDF Resume...")
    # Clean previous application with this test email
    JobApplication.query.filter_by(job_id=created_job.id, email='arun.kumar@example.com').delete()
    db.session.commit()

    resume_bytes = b"%PDF-1.4 Mock resume content for Arun Kumar - Software Engineer Intern"
    resume_file = (io.BytesIO(resume_bytes), 'arun_kumar_resume.pdf')

    candidate_data = {
        'full_name': 'Arun Kumar',
        'email': 'arun.kumar@example.com',
        'phone': '+91 98765 43210',
        'college': 'Anna University',
        'degree': 'B.Tech Information Technology',
        'department': 'Department of IT',
        'graduation_year': '2025',
        'experience': '6 months internship',
        'skills': 'Python, Flask, JavaScript, SQL, Git',
        'portfolio_url': 'https://arunkumar.dev',
        'linkedin_url': 'https://linkedin.com/in/arunkumar',
        'github_url': 'https://github.com/arunkumar',
        'cover_letter': 'I am eager to apply for the Software Engineer Intern role at Anti-Matrix. I have built full-stack web applications and scalable APIs.',
        'why_join': 'Anti-Matrix has cutting-edge enterprise projects and an engineering-first culture.',
        'resume': resume_file
    }

    res = client.post(f'/careers/apply/{created_job.id}', data=candidate_data, content_type='multipart/form-data', follow_redirects=True)
    assert res.status_code == 200, f"Application submission failed with status {res.status_code}"
    html = res.data.decode('utf-8')
    assert 'Application Submitted Successfully' in html
    assert '#AM-' in html
    
    app_record = JobApplication.query.filter_by(job_id=created_job.id, email='arun.kumar@example.com').first()
    assert app_record is not None, "Application not persisted in database"
    assert app_record.status == 'New'
    assert os.path.exists(app_record.resume_path), "Uploaded resume file was not saved on disk"
    print(f"[PASS] TEST 6: Application submitted and assigned Tracking ID {app_record.application_code}.")

    # -------------------------------------------------------------
    # TEST 7: Admin Application List
    # -------------------------------------------------------------
    print("\n[TEST 7] View Candidate in Admin Applications List (/admin/applications)...")
    res = client.get('/admin/applications')
    assert res.status_code == 200, f"Applications list failed with status {res.status_code}"
    html = res.data.decode('utf-8')
    assert 'Arun Kumar' in html
    assert 'arun.kumar@example.com' in html
    assert 'Software Engineer Intern' in html
    print("[PASS] TEST 7: Candidate 'Arun Kumar' listed in admin candidate applications table.")

    # -------------------------------------------------------------
    # TEST 8: Admin Opens Application Dossier
    # -------------------------------------------------------------
    print(f"\n[TEST 8] Open Candidate Dossier (/admin/applications/{app_record.id})...")
    res = client.get(f'/admin/applications/{app_record.id}')
    assert res.status_code == 200, f"Application detail failed with status {res.status_code}"
    html = res.data.decode('utf-8')
    assert 'Arun Kumar' in html
    assert 'Anna University' in html
    assert 'B.Tech Information Technology' in html
    assert 'https://arunkumar.dev' in html
    assert 'View Resume' in html
    assert 'Download File' in html
    print("[PASS] TEST 8: Candidate profile dossier displays complete academic and technical data.")

    # -------------------------------------------------------------
    # TEST 9: Update Application Status
    # -------------------------------------------------------------
    print("\n[TEST 9] Update Candidate Status: New -> Reviewed...")
    res = client.post(f'/admin/applications/{app_record.id}/status', data={'status': 'Reviewed'}, follow_redirects=True)
    assert res.status_code == 200, f"Status update failed with status {res.status_code}"
    
    db.session.refresh(app_record)
    assert app_record.status == 'Reviewed', f"Expected status Reviewed, got {app_record.status}"
    
    # Confirm updated status reflects on dashboard
    res_dash = client.get('/admin')
    html_dash = res_dash.data.decode('utf-8')
    assert 'Reviewed' in html_dash
    print("[PASS] TEST 9: Status updated to 'Reviewed' in database and reflected on dashboard.")

    # -------------------------------------------------------------
    # TEST 10: Logout & Authorization Check
    # -------------------------------------------------------------
    print("\n[TEST 10] Logout & Verify Admin Access Security...")
    res_logout = client.get('/logout', follow_redirects=True)
    assert res_logout.status_code == 200
    html_logout = res_logout.data.decode('utf-8')
    assert 'Admin Dashboard' not in html_logout, "Admin Dashboard link still visible after logout"
    
    # Attempt unauthenticated access to /admin
    res_unauth = client.get('/admin', follow_redirects=False)
    assert res_unauth.status_code in [302, 308], f"Expected redirect, got {res_unauth.status_code}"
    print("[PASS] TEST 10: Logged out cleanly. Admin Dashboard link removed. Guest access to /admin blocked.")

    print("\n" + "=" * 70)
    print("ALL 10 VERIFICATION SCENARIOS PASSED WITH 100% SUCCESS!")
    print("=" * 70)
