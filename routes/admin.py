import os
from functools import wraps
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash,
    abort, current_app, send_from_directory
)
from flask_login import current_user
from models import db, JobPosting, JobApplication, Payment, User, Employee

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

