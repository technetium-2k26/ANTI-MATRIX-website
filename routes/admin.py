import os
import uuid
import time
from functools import wraps
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash,
    abort, current_app, send_from_directory, jsonify
)
from flask_login import current_user
from werkzeug.utils import secure_filename
from models import (
    db, JobPosting, JobApplication, Payment, User, Employee,
    DocumentTemplate, EmailTemplate, EmployeeDocument
)
from services.offer_letter_service import (
    generate_offer_letter_docx, send_offer_letter_email,
    OfferLetterTemplateNotFoundError, OfferLetterTemplateFileMissingError,
    get_active_offer_letter_template
)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in with an administrator account to access this area.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        if getattr(current_user, 'role', '') != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('', strict_slashes=False)
@admin_bp.route('/', strict_slashes=False)
@admin_bp.route('/dashboard', strict_slashes=False)
@admin_required
def dashboard():
    total_jobs = JobPosting.query.count()
    active_jobs = JobPosting.query.filter_by(is_active=True).count()
    total_applications = JobApplication.query.count()
    new_applications = JobApplication.query.filter_by(status='New').count()
    paid_applications = JobApplication.query.filter_by(payment_status='paid').count()
    total_employees = Employee.query.count()

    recent_jobs = JobPosting.query.order_by(JobPosting.created_at.desc()).limit(5).all()
    recent_applications = JobApplication.query.order_by(JobApplication.created_at.desc()).limit(8).all()

    return render_template(
        'admin/dashboard.html',
        total_jobs=total_jobs,
        active_jobs=active_jobs,
        total_applications=total_applications,
        new_applications=new_applications,
        paid_applications=paid_applications,
        total_employees=total_employees,
        recent_jobs=recent_jobs,
        recent_applications=recent_applications
    )


@admin_bp.route('/jobs')
@admin_required
def jobs():
    status_filter = request.args.get('status', 'all').lower()
    dept_filter = request.args.get('dept', '').strip()
    search_query = request.args.get('q', '').strip()

    query = JobPosting.query

    if status_filter == 'active':
        query = query.filter_by(is_active=True)
    elif status_filter == 'inactive':
        query = query.filter_by(is_active=False)

    if dept_filter:
        query = query.filter(JobPosting.department.ilike(f'%{dept_filter}%'))

    if search_query:
        query = query.filter(
            (JobPosting.title.ilike(f'%{search_query}%')) |
            (JobPosting.location.ilike(f'%{search_query}%')) |
            (JobPosting.skills.ilike(f'%{search_query}%'))
        )

    all_jobs = query.order_by(JobPosting.created_at.desc()).all()
    total_unfiltered_jobs = JobPosting.query.count()
    departments = db.session.query(JobPosting.department).distinct().all()
    departments = [d[0] for d in departments if d[0]]

    return render_template(
        'admin/jobs.html',
        jobs=all_jobs,
        total_unfiltered_jobs=total_unfiltered_jobs,
        status_filter=status_filter,
        dept_filter=dept_filter,
        search_query=search_query,
        departments=departments
    )


@admin_bp.route('/jobs/delete-all', methods=['POST'])
@admin_required
def delete_all_jobs():
    confirmation = (request.form.get('confirmation') or '').strip()
    if confirmation != 'DELETE':
        flash('Deletion cancelled. You must type DELETE to confirm.', 'danger')
        return redirect(url_for('admin.jobs'))

    total_jobs = JobPosting.query.count()
    if total_jobs == 0:
        flash('There are no job postings to delete.', 'info')
        return redirect(url_for('admin.jobs'))

    try:
        Payment.query.delete()
        JobApplication.query.delete()
        JobPosting.query.delete()
        db.session.commit()
        flash('All job postings have been deleted successfully.', 'success')
    except Exception:
        db.session.rollback()
        flash('Unable to delete job postings. No changes were made.', 'danger')

    return redirect(url_for('admin.jobs'))


@admin_bp.route('/jobs/create', methods=['GET', 'POST'])
@admin_required
def create_job():
    if request.method == 'POST':
        title = (request.form.get('title') or '').strip()
        department = (request.form.get('department') or '').strip()
        location = (request.form.get('location') or '').strip()
        employment_type = (request.form.get('employment_type') or 'Full-time').strip()
        duration = (request.form.get('duration') or '').strip() or None
        short_description = (request.form.get('short_description') or '').strip()
        description = (request.form.get('description') or '').strip()
        requirements = (request.form.get('requirements') or '').strip()
        qualifications = (request.form.get('qualifications') or '').strip()
        experience = (request.form.get('experience') or '').strip()
        responsibilities = (request.form.get('responsibilities') or '').strip()
        skills = (request.form.get('skills') or '').strip()
        salary = (request.form.get('salary') or '').strip()
        application_deadline = (request.form.get('application_deadline') or '').strip()
        is_active = True if request.form.get('is_active') in ['true', '1', 'on'] else False

        errors = []
        if not title:
            errors.append('Job title is required.')
        if not department:
            errors.append('Department is required.')
        if not location:
            errors.append('Location is required.')
        if not short_description:
            errors.append('Short description is required.')
        if not description:
            errors.append('Full job description is required.')

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('admin/create_job.html', form_data=request.form)

        job = JobPosting(
            title=title,
            department=department,
            location=location,
            employment_type=employment_type,
            duration=duration,
            short_description=short_description,
            description=description,
            requirements=requirements,
            qualifications=qualifications,
            experience=experience,
            responsibilities=responsibilities,
            skills=skills,
            salary=salary,
            application_deadline=application_deadline,
            is_active=is_active
        )
        db.session.add(job)
        db.session.commit()

        flash(f"Job posting '{job.title}' created successfully.", 'success')
        return redirect(url_for('admin.jobs'))

    return render_template('admin/create_job.html', form_data={})


@admin_bp.route('/jobs/edit/<int:job_id>', methods=['GET', 'POST'])
@admin_required
def edit_job(job_id):
    job = db.session.get(JobPosting, job_id) or abort(404)

    if request.method == 'POST':
        title = (request.form.get('title') or '').strip()
        department = (request.form.get('department') or '').strip()
        location = (request.form.get('location') or '').strip()
        employment_type = (request.form.get('employment_type') or 'Full-time').strip()
        duration = (request.form.get('duration') or '').strip() or None
        short_description = (request.form.get('short_description') or '').strip()
        description = (request.form.get('description') or '').strip()
        requirements = (request.form.get('requirements') or '').strip()
        qualifications = (request.form.get('qualifications') or '').strip()
        experience = (request.form.get('experience') or '').strip()
        responsibilities = (request.form.get('responsibilities') or '').strip()
        skills = (request.form.get('skills') or '').strip()
        salary = (request.form.get('salary') or '').strip()
        application_deadline = (request.form.get('application_deadline') or '').strip()
        is_active = True if request.form.get('is_active') in ['true', '1', 'on'] else False

        errors = []
        if not title:
            errors.append('Job title is required.')
        if not department:
            errors.append('Department is required.')
        if not location:
            errors.append('Location is required.')
        if not short_description:
            errors.append('Short description is required.')
        if not description:
            errors.append('Full job description is required.')

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('admin/edit_job.html', job=job)

        job.title = title
        job.department = department
        job.location = location
        job.employment_type = employment_type
        job.duration = duration
        job.short_description = short_description
        job.description = description
        job.requirements = requirements
        job.qualifications = qualifications
        job.experience = experience
        job.responsibilities = responsibilities
        job.skills = skills
        job.salary = salary
        job.application_deadline = application_deadline
        job.is_active = is_active

        db.session.commit()
        flash(f"Job posting '{job.title}' updated successfully.", 'success')
        return redirect(url_for('admin.jobs'))

    return render_template('admin/edit_job.html', job=job)


@admin_bp.route('/jobs/toggle/<int:job_id>', methods=['POST'])
@admin_required
def toggle_job(job_id):
    job = db.session.get(JobPosting, job_id) or abort(404)
    job.is_active = not job.is_active
    db.session.commit()
    status_str = 'Active' if job.is_active else 'Inactive'
    flash(f"Job '{job.title}' is now {status_str}.", 'success')
    return redirect(request.referrer or url_for('admin.jobs'))


@admin_bp.route('/jobs/delete/<int:job_id>', methods=['POST'])
@admin_required
def delete_job(job_id):
    job = db.session.get(JobPosting, job_id) or abort(404)
    title = job.title
    db.session.delete(job)
    db.session.commit()
    flash(f"Job posting '{title}' and its applications have been safely removed.", 'info')
    return redirect(url_for('admin.jobs'))


@admin_bp.route('/applications')
@admin_required
def applications():
    job_id_filter = request.args.get('job_id', type=int)
    duration_filter = request.args.get('duration', '').strip()
    payment_status_filter = request.args.get('payment_status', 'all').strip()
    status_filter = request.args.get('status', 'all').strip()
    search_query = request.args.get('q', '').strip()

    query = JobApplication.query.join(JobPosting)

    if job_id_filter:
        query = query.filter(JobApplication.job_id == job_id_filter)

    if duration_filter and duration_filter.lower() != 'all':
        query = query.filter(JobApplication.duration == duration_filter)

    if payment_status_filter and payment_status_filter.lower() != 'all':
        query = query.filter(JobApplication.payment_status.ilike(payment_status_filter))

    if status_filter and status_filter.lower() != 'all':
        query = query.filter(JobApplication.status.ilike(status_filter))

    if search_query:
        query = query.filter(
            (JobApplication.full_name.ilike(f'%{search_query}%')) |
            (JobApplication.email.ilike(f'%{search_query}%')) |
            (JobApplication.phone.ilike(f'%{search_query}%')) |
            (JobApplication.college.ilike(f'%{search_query}%')) |
            (JobApplication.skills.ilike(f'%{search_query}%')) |
            (JobApplication.application_code.ilike(f'%{search_query}%')) |
            (JobPosting.title.ilike(f'%{search_query}%'))
        )

    all_applications = query.order_by(JobApplication.created_at.desc()).all()
    all_jobs = JobPosting.query.order_by(JobPosting.title.asc()).all()

    return render_template(
        'admin/applications.html',
        applications=all_applications,
        all_jobs=all_jobs,
        selected_job_id=job_id_filter,
        selected_duration=duration_filter,
        selected_payment_status=payment_status_filter,
        selected_status=status_filter,
        search_query=search_query
    )


@admin_bp.route('/applications/<int:app_id>')
@admin_required
def application_detail(app_id):
    application = db.session.get(JobApplication, app_id) or abort(404)
    return render_template('admin/application_detail.html', app=application, job=application.job)


@admin_bp.route('/applications/<int:app_id>/status', methods=['POST'])
@admin_required
def update_application_status(app_id):
    application = db.session.get(JobApplication, app_id) or abort(404)
    new_status = request.form.get('status', '').strip()
    valid_statuses = ['New', 'Reviewed', 'Shortlisted', 'Rejected', 'Hired']

    if new_status in valid_statuses:
        application.status = new_status
        status_map = {
            'New': 'submitted',
            'Reviewed': 'reviewed',
            'Shortlisted': 'shortlisted',
            'Rejected': 'rejected',
            'Hired': 'hired'
        }
        application.application_status = status_map.get(new_status, new_status.lower())
        db.session.commit()
        flash(f"Status for candidate {application.full_name} updated to '{new_status}'.", 'success')
    else:
        flash('Invalid status provided.', 'danger')

    return redirect(request.referrer or url_for('admin.application_detail', app_id=application.id))


@admin_bp.route('/applications/<int:app_id>/document/<string:doc_type>')
@admin_required
def download_document(app_id, doc_type):
    """Secure, authenticated document download route protecting sensitive candidate documents."""
    application = db.session.get(JobApplication, app_id) or abort(404)
    as_attachment = request.args.get('download', '0') == '1'

    if doc_type == 'resume':
        folder = current_app.config.get('UPLOAD_FOLDER_RESUMES', current_app.config['UPLOAD_FOLDER'])
        filename = application.resume_filename
    elif doc_type == 'aadhaar':
        folder = current_app.config.get('UPLOAD_FOLDER_DOCUMENTS', os.path.join(current_app.root_path, 'uploads', 'documents'))
        filename = application.aadhaar_filename
    elif doc_type == 'pan':
        folder = current_app.config.get('UPLOAD_FOLDER_DOCUMENTS', os.path.join(current_app.root_path, 'uploads', 'documents'))
        filename = application.pan_filename
    elif doc_type == 'college_id':
        folder = current_app.config.get('UPLOAD_FOLDER_DOCUMENTS', os.path.join(current_app.root_path, 'uploads', 'documents'))
        filename = application.college_id_filename
    else:
        abort(404)

    if not filename:
        flash(f"No {doc_type} file found for candidate {application.full_name}.", 'warning')
        return redirect(url_for('admin.application_detail', app_id=application.id))

    safe_filename = os.path.basename(filename)
    return send_from_directory(
        folder,
        safe_filename,
        as_attachment=as_attachment
    )


@admin_bp.route('/applications/<int:app_id>/resume')
@admin_required
def download_resume(app_id):
    """Resume download legacy alias."""
    return download_document(app_id, 'resume')


@admin_bp.route('/employees', methods=['GET'])
@admin_required
def employees():
    """List all registered employee accounts with search and filtering."""
    search_query = request.args.get('q', '').strip()
    status_filter = request.args.get('status', 'all').strip()

    query = Employee.query.join(JobApplication).join(JobPosting)

    if status_filter and status_filter.lower() != 'all':
        query = query.filter(Employee.account_status.ilike(status_filter))

    if search_query:
        query = query.filter(
            (Employee.employee_id.ilike(f'%{search_query}%')) |
            (JobApplication.full_name.ilike(f'%{search_query}%')) |
            (JobApplication.email.ilike(f'%{search_query}%')) |
            (JobApplication.application_code.ilike(f'%{search_query}%')) |
            (JobPosting.title.ilike(f'%{search_query}%'))
        )

    all_employees = query.order_by(Employee.created_at.desc()).all()
    return render_template(
        'admin/employees.html',
        employees=all_employees,
        search_query=search_query,
        selected_status=status_filter
    )


@admin_bp.route('/employees/create', methods=['GET', 'POST'])
@admin_required
def create_employee():
    """Create unique Employee ID and random secure password for a paid application."""
    if request.method == 'POST':
        app_id_raw = request.form.get('application_id')
        if not app_id_raw:
            flash('Please select an application to create an Employee ID.', 'danger')
            return redirect(url_for('admin.create_employee'))

        try:
            app_id = int(app_id_raw)
        except ValueError:
            flash('Invalid application identifier provided.', 'danger')
            return redirect(url_for('admin.create_employee'))

        application = db.session.get(JobApplication, app_id)
        if not application:
            flash('Selected candidate application does not exist.', 'danger')
            return redirect(url_for('admin.create_employee'))

        # Security Check 1: Must have completed payment
        if application.payment_status != 'paid':
            flash('Employee ID cannot be created until the application payment is completed.', 'danger')
            return redirect(url_for('admin.application_detail', app_id=application.id))

        # Security Check 2: Only 1 employee account per application
        if application.employee:
            flash(f"Employee ID already exists: {application.employee.employee_id} for candidate {application.full_name}.", 'warning')
            return redirect(url_for('admin.view_employee', employee_id=application.employee.employee_id))

        try:
            emp_id = Employee.generate_unique_employee_id()
            plaintext_password = Employee.generate_secure_password(12)

            employee = Employee(
                employee_id=emp_id,
                application_id=application.id,
                account_status='active'
            )
            employee.set_password(plaintext_password)

            db.session.add(employee)
            db.session.commit()

            # Render confirmation screen displaying credentials for copying
            # Plaintext password is provided ONLY in this immediate response and NEVER stored in DB
            return render_template(
                'admin/employee_credentials.html',
                employee=employee,
                plaintext_password=plaintext_password,
                app=application,
                job=application.job
            )
        except Exception as e:
            db.session.rollback()
            flash(f"Error creating employee account: {str(e)}", 'danger')
            return redirect(url_for('admin.create_employee', application_id=application.id))

    # GET request
    preselected_app_id = request.args.get('application_id', type=int)
    selected_app = None
    if preselected_app_id:
        selected_app = db.session.get(JobApplication, preselected_app_id)

    # Fetch eligible applications: paid applications that do not already have an employee account
    eligible_applications = JobApplication.query.outerjoin(Employee).filter(
        JobApplication.payment_status == 'paid',
        Employee.id.is_(None)
    ).order_by(JobApplication.created_at.desc()).all()

    return render_template(
        'admin/employee_create.html',
        eligible_applications=eligible_applications,
        selected_app=selected_app
    )


@admin_bp.route('/employees/<string:employee_id>', methods=['GET'])
@admin_required
def view_employee(employee_id):
    """View employee details (Application ID, Candidate, Job, Duration, Status, Created Date). Never reveals password_hash."""
    employee = Employee.query.filter_by(employee_id=employee_id).first_or_404()
    return render_template(
        'admin/employee_detail.html',
        employee=employee,
        app=employee.application,
        job=employee.application.job
    )


# =====================================================================
# TEMPLATE MANAGEMENT (EMAIL & DOCUMENT TEMPLATES)
# =====================================================================

@admin_bp.route('/templates', methods=['GET'])
@admin_required
def templates():
    """Template Management Hub for Email and Document Templates."""
    # Ensure standard email templates exist
    app_success_email = EmailTemplate.query.filter_by(template_type='application_successful').first()
    offer_letter_email = EmailTemplate.query.filter_by(template_type='offer_letter').first()
    
    # Active document templates
    offer_doc_template = DocumentTemplate.query.filter_by(template_type='offer_letter', is_active=True).order_by(DocumentTemplate.id.desc()).first()
    offer_template_file_exists = bool(offer_doc_template and offer_doc_template.file_path and os.path.exists(offer_doc_template.file_path))

    exp_doc_template = DocumentTemplate.query.filter_by(template_type='experience_letter', is_active=True).order_by(DocumentTemplate.id.desc()).first()
    exp_template_file_exists = bool(exp_doc_template and exp_doc_template.file_path and os.path.exists(exp_doc_template.file_path))

    cert_doc_template = DocumentTemplate.query.filter_by(template_type='certificate', is_active=True).order_by(DocumentTemplate.id.desc()).first()
    cert_template_file_exists = bool(cert_doc_template and cert_doc_template.file_path and os.path.exists(cert_doc_template.file_path))

    return render_template(
        'admin/templates.html',
        app_success_email=app_success_email,
        offer_letter_email=offer_letter_email,
        offer_doc_template=offer_doc_template,
        offer_template_file_exists=offer_template_file_exists,
        exp_doc_template=exp_doc_template,
        exp_template_file_exists=exp_template_file_exists,
        cert_doc_template=cert_doc_template,
        cert_template_file_exists=cert_template_file_exists
    )


@admin_bp.route('/templates/email/<string:template_type>', methods=['POST'])
@admin_required
def update_email_template(template_type):
    """Update subject and body for an Email Template."""
    valid_types = ['application_successful', 'offer_letter']
    if template_type not in valid_types:
        flash('Invalid email template type.', 'danger')
        return redirect(url_for('admin.templates'))

    subject = (request.form.get('subject') or '').strip()
    body = (request.form.get('body') or '').strip()

    if not subject or not body:
        flash('Subject and Body are required for email templates.', 'danger')
        return redirect(url_for('admin.templates'))

    email_tmpl = EmailTemplate.query.filter_by(template_type=template_type).first()
    if not email_tmpl:
        name_map = {
            'application_successful': 'Application Successful Confirmation',
            'offer_letter': 'Offer Letter Delivery'
        }
        email_tmpl = EmailTemplate(
            template_type=template_type,
            name=name_map.get(template_type, template_type.title()),
            subject=subject,
            body=body
        )
        db.session.add(email_tmpl)
    else:
        email_tmpl.subject = subject
        email_tmpl.body = body

    db.session.commit()
    flash(f"Email template '{email_tmpl.name}' updated successfully.", 'success')
    return redirect(url_for('admin.templates'))


@admin_bp.route('/templates/email/<string:template_type>/preview', methods=['GET'])
@admin_required
def preview_email_template(template_type):
    """Preview rendered HTML email with sample preview values."""
    valid_types = ['application_successful', 'offer_letter']
    if template_type not in valid_types:
        return jsonify({'error': 'Invalid template type'}), 400

    from services.email_service import render_sample_email_preview
    preview_data = render_sample_email_preview(template_type)
    return jsonify(preview_data)


@admin_bp.route('/templates/email/<string:template_type>/test', methods=['POST'])
@admin_required
def send_test_email_route(template_type):
    """Send a sample test email to an admin-specified recipient without modifying live records."""
    valid_types = ['application_successful', 'offer_letter']
    if template_type not in valid_types:
        flash('Invalid template type.', 'danger')
        return redirect(url_for('admin.templates'))

    recipient_email = (request.form.get('test_recipient') or '').strip()
    if not recipient_email:
        flash('Please specify a recipient email address for testing.', 'danger')
        return redirect(url_for('admin.templates'))

    from services.email_service import send_test_email
    success, msg = send_test_email(template_type, recipient_email)
    if success:
        flash(f"Test email sent to {recipient_email}: {msg}", 'success')
    else:
        flash(f"Failed to send test email: {msg}", 'danger')

    return redirect(url_for('admin.templates'))


@admin_bp.route('/templates/document/<string:template_type>/upload', methods=['POST'])
@admin_required
def upload_document_template(template_type):
    """Upload / replace a master DOCX template (Offer Letter, Experience Letter, Certificate)."""
    valid_types = ['offer_letter', 'experience_letter', 'certificate']
    if template_type not in valid_types:
        flash('Invalid document template type.', 'danger')
        return redirect(url_for('admin.templates'))

    uploaded_file = request.files.get('template_file')
    if not uploaded_file or not uploaded_file.filename:
        flash('Please select a DOCX template file to upload.', 'danger')
        return redirect(url_for('admin.templates'))

    original_filename = secure_filename(uploaded_file.filename) or uploaded_file.filename
    if not original_filename.lower().endswith('.docx'):
        flash('Only .docx Microsoft Word template files are accepted.', 'danger')
        return redirect(url_for('admin.templates'))

    templates_dir = os.path.join(current_app.root_path, 'uploads', 'templates')
    os.makedirs(templates_dir, exist_ok=True)

    # Secure unique stored filename to preserve history
    unique_suffix = f"{int(time.time())}_{uuid.uuid4().hex[:6]}"
    target_filename = f"{template_type}_{unique_suffix}.docx"
    target_path = os.path.join(templates_dir, target_filename)

    uploaded_file.save(target_path)

    name_map = {
        'offer_letter': 'Anti-Matrix Master Offer Letter',
        'experience_letter': 'Anti-Matrix Master Experience Letter',
        'certificate': 'Anti-Matrix Master Internship Certificate'
    }

    # Deactivate previous active templates of this type
    DocumentTemplate.query.filter_by(template_type=template_type, is_active=True).update({'is_active': False})

    new_doc_tmpl = DocumentTemplate(
        template_type=template_type,
        name=name_map.get(template_type, template_type.replace('_', ' ').title()),
        filename=uploaded_file.filename,
        file_path=target_path,
        is_active=True
    )
    db.session.add(new_doc_tmpl)
    db.session.commit()

    flash(f"Document template '{uploaded_file.filename}' uploaded and set as ACTIVE successfully.", 'success')
    return redirect(url_for('admin.templates'))


@admin_bp.route('/templates/document/<string:template_type>/download', methods=['GET'])
@admin_required
def download_document_template(template_type):
    """Download / preview the active master DOCX template file."""
    doc_tmpl = DocumentTemplate.query.filter_by(template_type=template_type, is_active=True).order_by(DocumentTemplate.id.desc()).first()
    if not doc_tmpl or not doc_tmpl.file_path or not os.path.exists(doc_tmpl.file_path):
        flash('Requested master template file is not available on storage. Please upload a template.', 'warning')
        return redirect(url_for('admin.templates'))

    return send_from_directory(
        os.path.dirname(doc_tmpl.file_path),
        os.path.basename(doc_tmpl.file_path),
        as_attachment=True,
        download_name=doc_tmpl.filename
    )


# =====================================================================
# OFFER LETTER GENERATION, PREVIEW, VERIFICATION & SENDING
# =====================================================================

@admin_bp.route('/employees/<string:employee_id>/offer-letter/generate', methods=['GET', 'POST'])
@admin_required
def generate_offer_letter(employee_id):
    """Generate personalized Offer Letter DOCX for selected Employee."""
    employee = Employee.query.filter_by(employee_id=employee_id).first_or_404()
    app_record = employee.application
    job = employee.job

    if not app_record or not job:
        flash('Employee is missing linked application or job posting data.', 'danger')
        return redirect(url_for('admin.view_employee', employee_id=employee.employee_id))

    active_template = DocumentTemplate.query.filter_by(template_type='offer_letter', is_active=True).order_by(DocumentTemplate.id.desc()).first()
    template_exists = bool(active_template and active_template.file_path and os.path.exists(active_template.file_path))

    if request.method == 'POST':
        custom_params = {
            'responsibilities': (request.form.get('responsibilities') or '').strip() or None,
            'key_tasks': (request.form.get('key_tasks') or '').strip() or None,
            'joining_date': (request.form.get('joining_date') or '').strip() or 'Immediate / As mutually agreed',
            'work_mode': (request.form.get('work_mode') or '').strip() or (job.location if job.location else 'Remote'),
            'conditions': (request.form.get('conditions') or '').strip() or 'satisfactory verification of academic credentials and submission of government identity documentation',
            'acceptance_deadline': (request.form.get('acceptance_deadline') or '').strip() or None
        }

        try:
            emp_doc, output_path = generate_offer_letter_docx(employee, custom_params)
            flash(f"Offer Letter for {employee.candidate_name} ({employee.employee_id}) generated successfully!", 'success')
            return redirect(url_for('admin.verify_offer_letter', employee_id=employee.employee_id))
        except (OfferLetterTemplateNotFoundError, OfferLetterTemplateFileMissingError) as e:
            flash(str(e), 'danger')
            return redirect(url_for('admin.generate_offer_letter', employee_id=employee.employee_id))
        except Exception as e:
            flash(f"Error generating Offer Letter: {str(e)}", 'danger')
            return redirect(url_for('admin.generate_offer_letter', employee_id=employee.employee_id))

    # GET request - Show parameter review form before generating
    return render_template(
        'admin/offer_letter_generate.html',
        employee=employee,
        app=app_record,
        job=job,
        active_template=active_template,
        template_exists=template_exists
    )


@admin_bp.route('/employees/<string:employee_id>/offer-letter/preview', methods=['GET'])
@admin_required
def preview_offer_letter(employee_id):
    """Download / preview the generated employee-specific Offer Letter DOCX."""
    employee = Employee.query.filter_by(employee_id=employee_id).first_or_404()
    emp_doc = employee.offer_letter_doc

    if not emp_doc or not os.path.exists(emp_doc.file_path):
        flash('Offer Letter has not been generated yet. Please generate it first.', 'warning')
        return redirect(url_for('admin.view_employee', employee_id=employee.employee_id))

    return send_from_directory(
        os.path.dirname(emp_doc.file_path),
        os.path.basename(emp_doc.file_path),
        as_attachment=True,
        download_name=emp_doc.file_name
    )


@admin_bp.route('/employees/<string:employee_id>/offer-letter/verify', methods=['GET'])
@admin_required
def verify_offer_letter(employee_id):
    """Pre-send verification view with email preview, locked recipient, and confirm button."""
    employee = Employee.query.filter_by(employee_id=employee_id).first_or_404()
    app_record = employee.application
    job = employee.job
    emp_doc = employee.offer_letter_doc

    if not emp_doc or not os.path.exists(emp_doc.file_path):
        flash('Offer Letter has not been generated yet. Please generate it first.', 'warning')
        return redirect(url_for('admin.generate_offer_letter', employee_id=employee.employee_id))

    # Load email template to preview formatted email
    from services.email_service import replace_variables, markdown_to_html_email, DEFAULT_OFFER_LETTER_SUBJECT, DEFAULT_OFFER_LETTER_BODY
    email_tmpl = EmailTemplate.query.filter_by(template_type='offer_letter').first()
    
    company_email = current_app.config.get('CONTACT_EMAIL', 'info@antimatrix.co.in')
    website = 'www.antimatrix.co.in'
    duration = app_record.duration_display or (f"{job.duration.replace('_', ' ').title()}" if job and job.duration else "3 Months")
    joining_date = 'Immediate / As mutually agreed'

    variables = {
        'Student Name': employee.candidate_name,
        'Internship Role': job.title if job else 'Internship Position',
        'Application ID': app_record.formatted_code,
        'Internship Duration': duration,
        'Start Date': joining_date,
        'Company Email': company_email,
        'Website': website,
        'employee_name': employee.candidate_name,
        'employee_id': employee.employee_id,
        'job_title': job.title if job else '',
        'department': job.department if job else '',
        'application_id': app_record.formatted_code,
        'internship_duration': duration,
        'start_date': joining_date,
        'company_email': company_email,
        'website': website
    }

    raw_subject = email_tmpl.subject if email_tmpl else DEFAULT_OFFER_LETTER_SUBJECT
    raw_body = email_tmpl.body if email_tmpl else DEFAULT_OFFER_LETTER_BODY

    subject_preview = replace_variables(raw_subject, variables)
    body_preview = replace_variables(raw_body, variables)
    body_html_preview = markdown_to_html_email(body_preview, title=subject_preview)

    return render_template(
        'admin/offer_letter_verify.html',
        employee=employee,
        app=app_record,
        job=job,
        emp_doc=emp_doc,
        subject_preview=subject_preview,
        body_preview=body_preview,
        body_html_preview=body_html_preview
    )


@admin_bp.route('/employees/<string:employee_id>/offer-letter/send', methods=['POST'])
@admin_required
def send_offer_letter(employee_id):
    """Explicit Verify & Send action sending the Offer Letter email with attachment."""
    employee = Employee.query.filter_by(employee_id=employee_id).first_or_404()
    emp_doc = employee.offer_letter_doc

    if not emp_doc:
        flash('No Offer Letter found for this employee. Please generate it first.', 'danger')
        return redirect(url_for('admin.generate_offer_letter', employee_id=employee.employee_id))

    # ONE-TIME SEND PROTECTION
    if emp_doc.email_status == 'sent':
        flash('Offer Letter already sent. Duplicate sending is prevented.', 'warning')
        return redirect(url_for('admin.view_employee', employee_id=employee.employee_id))

    success, message = send_offer_letter_email(employee)
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')

    return redirect(url_for('admin.view_employee', employee_id=employee.employee_id))


