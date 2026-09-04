import os
import re
import time
import uuid
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, current_app, abort
from flask_login import current_user
from werkzeug.utils import secure_filename
from models import db, ContactInquiry, JobPosting, JobApplication

main_bp = Blueprint('main', __name__)

EMAIL_REGEX = re.compile(r'^\S+@\S+\.\S+$')
URL_REGEX = re.compile(r'^https?://\S+$', re.IGNORECASE)

SUBJECT_OPTIONS = [
    'New Project Inquiry',
    'Pricing & Packages',
    'Partnership Opportunity',
    'Support & Maintenance',
    'Careers',
    'Other'
]


@main_bp.route('/')
def home():
    return render_template('pages/home.html')


@main_bp.route('/about')
def about():
    return render_template('pages/about.html')


@main_bp.route('/services')
def services():
    return render_template('pages/services.html')


@main_bp.route('/pricing')
def pricing():
    # If user is authenticated, render the full protected pricing page.
    # If user is guest, render the locked access view matching ProtectedRoute.jsx
    if current_user.is_authenticated:
        return render_template('pages/pricing.html')
    return render_template('pages/pricing_locked.html')


@main_bp.route('/careers')
def careers():
    # Load all active job postings from the database
    jobs = JobPosting.query.filter_by(is_active=True).order_by(JobPosting.created_at.desc()).all()
    return render_template('pages/careers.html', jobs=jobs)


@main_bp.route('/careers/apply/<int:job_id>', methods=['GET', 'POST'])
def apply_job(job_id):
    job = db.session.get(JobPosting, job_id) or abort(404)
    if not job.is_active:
        flash('This position is currently not accepting new applications.', 'warning')
        return redirect(url_for('main.careers'))

    if request.method == 'POST':
        full_name = (request.form.get('full_name') or '').strip()
        email = (request.form.get('email') or '').strip()
        phone = (request.form.get('phone') or '').strip()
        college = (request.form.get('college') or '').strip()
        degree = (request.form.get('degree') or '').strip()
        department = (request.form.get('department') or '').strip()
        graduation_year = (request.form.get('graduation_year') or '').strip()
        experience = (request.form.get('experience') or '').strip()
        skills = (request.form.get('skills') or '').strip()
        portfolio_url = (request.form.get('portfolio_url') or '').strip()
        linkedin_url = (request.form.get('linkedin_url') or '').strip()
        github_url = (request.form.get('github_url') or '').strip()
        cover_letter = (request.form.get('cover_letter') or '').strip()
        why_join = (request.form.get('why_join') or '').strip()

        errors = []

        if not full_name:
            errors.append('Full Name is required.')
        if not email:
            errors.append('Email is required.')
        elif not EMAIL_REGEX.match(email):
            errors.append('Please provide a valid email address.')
        if not phone:
            errors.append('Phone number is required.')
        if not college:
            errors.append('College/University name is required.')
        if not degree:
            errors.append('Degree is required.')
        if not department:
            errors.append('Academic department is required.')
        if not graduation_year:
            errors.append('Graduation year is required.')
        if not skills:
            errors.append('Please list your relevant skills.')
        if not cover_letter:
            errors.append('Cover letter / statement of interest is required.')

        # Validate URLs if provided
        if portfolio_url and not URL_REGEX.match(portfolio_url):
            errors.append('Portfolio URL must start with http:// or https://')
        if linkedin_url and not URL_REGEX.match(linkedin_url):
            errors.append('LinkedIn URL must start with http:// or https://')
        if github_url and not URL_REGEX.match(github_url):
            errors.append('GitHub URL must start with http:// or https://')

        # Check for duplicate submission
        existing_app = JobApplication.query.filter_by(job_id=job.id, email=email).first()
        if existing_app:
            errors.append(f"An application for this position ({job.title}) has already been submitted with email '{email}'.")

        # Resume validation
        resume_file = request.files.get('resume')
        if not resume_file or not resume_file.filename:
            errors.append('Resume file (PDF, DOC, or DOCX) is required.')
        else:
            filename = resume_file.filename
            if '.' not in filename or filename.rsplit('.', 1)[1].lower() not in current_app.config['ALLOWED_EXTENSIONS']:
                errors.append('Invalid file format. Please upload your resume in PDF, DOC, or DOCX format.')

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('pages/job_apply.html', job=job, form_data=request.form)

        # Secure resume upload
        ext = resume_file.filename.rsplit('.', 1)[1].lower()
        safe_base = secure_filename(resume_file.filename.rsplit('.', 1)[0])[:30] or 'resume'
        unique_filename = f"resume_j{job.id}_{int(time.time())}_{uuid.uuid4().hex[:6]}_{safe_base}.{ext}"
        
        upload_folder = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)
        save_path = os.path.join(upload_folder, unique_filename)
        resume_file.save(save_path)

        # Create application record
        application = JobApplication(
            job_id=job.id,
            full_name=full_name,
            email=email,
            phone=phone,
            college=college,
            degree=degree,
            department=department,
            graduation_year=graduation_year,
            experience=experience,
            skills=skills,
            portfolio_url=portfolio_url or None,
            linkedin_url=linkedin_url or None,
            github_url=github_url or None,
            cover_letter=cover_letter,
            why_join=why_join or None,
            resume_filename=unique_filename,
            resume_path=save_path,
            status='New'
        )

        db.session.add(application)
        db.session.commit()

        flash(f"Application submitted successfully! Your application reference is {application.application_code}.", 'success')
        return redirect(url_for('main.job_apply_success', app_id=application.id))

    return render_template('pages/job_apply.html', job=job, form_data={})


@main_bp.route('/careers/apply/success/<int:app_id>')
def job_apply_success(app_id):
    application = db.session.get(JobApplication, app_id) or abort(404)
    return render_template('pages/job_apply_success.html', app=application, job=application.job)


@main_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        is_json = request.is_json
        data = request.get_json() if is_json else request.form

        name = (data.get('name') or '').strip()
        email = (data.get('email') or '').strip()
        phone = (data.get('phone') or '').strip()
        subject = (data.get('subject') or '').strip()
        message = (data.get('message') or '').strip()

        errors = {}
        if not name:
            errors['name'] = 'Name is required'

        if not email:
            errors['email'] = 'Email is required'
        elif not EMAIL_REGEX.match(email):
            errors['email'] = 'Enter a valid email address'

        if not subject:
            errors['subject'] = 'Please select a subject'

        if not message:
            errors['message'] = 'Message is required'
        elif len(message) < 20:
            errors['message'] = 'Message must be at least 20 characters'

        if errors:
            if is_json:
                return jsonify({'status': 'error', 'errors': errors}), 400
            for field, err in errors.items():
                flash(err, 'error')
            return render_template(
                'pages/contact.html',
                errors=errors,
                form_data={'name': name, 'email': email, 'phone': phone, 'subject': subject, 'message': message},
                subjects=SUBJECT_OPTIONS,
                success=False
            )

        # Store inquiry in database
        inquiry = ContactInquiry(
            name=name,
            email=email,
            phone=phone if phone else None,
            subject=subject,
            message=message
        )
        db.session.add(inquiry)
        db.session.commit()

        if is_json:
            return jsonify({
                'status': 'success',
                'message': 'Message sent! Thank you for reaching out. Our team will review your message and reply within 24 hours.'
            })

        return render_template('pages/contact.html', success=True, subjects=SUBJECT_OPTIONS, errors={})

    return render_template('pages/contact.html', subjects=SUBJECT_OPTIONS, errors={}, success=False)


@main_bp.route('/privacy')
def privacy():
    return render_template('pages/privacy.html')


@main_bp.route('/terms')
def terms():
    return render_template('pages/terms.html')
