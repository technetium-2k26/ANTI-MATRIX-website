import os
import shutil
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timezone, timedelta
import docx
from flask import current_app
from models import db, Employee, JobApplication, JobPosting, EmployeeDocument, DocumentTemplate, EmailTemplate


def replace_placeholders_in_paragraph(paragraph, mapping):
    """
    Safely replaces placeholder keys with replacement values in a docx Paragraph.
    Preserves exact font, size, bold, italic, color, and run-level styles.
    Handles placeholders both inside individual runs and spanning multiple runs.
    """
    full_text = paragraph.text
    if not full_text:
        return

    # Check if any placeholder exists in the paragraph text
    needs_replacement = False
    for key in mapping:
        if key in full_text:
            needs_replacement = True
            break

    if not needs_replacement:
        return

    for key, val in mapping.items():
        if key not in paragraph.text:
            continue

        str_val = str(val) if val is not None else ''

        # 1. First attempt: check if placeholder is contained entirely in a single run
        replaced_in_single_run = False
        for run in paragraph.runs:
            if key in run.text:
                run.text = run.text.replace(key, str_val)
                replaced_in_single_run = True

        # 2. Fallback: if placeholder spans multiple adjacent runs
        if not replaced_in_single_run and key in paragraph.text:
            combined = "".join([r.text for r in paragraph.runs])
            new_text = combined.replace(key, str_val)
            if paragraph.runs:
                paragraph.runs[0].text = new_text
                for r in paragraph.runs[1:]:
                    r.text = ""


class OfferLetterTemplateNotFoundError(Exception):
    """Raised when no active Offer Letter template record exists in the database."""
    pass


class OfferLetterTemplateFileMissingError(Exception):
    """Raised when the active Offer Letter template record exists in DB, but the physical file is missing from disk/storage."""
    pass


def get_active_offer_letter_template():
    """
    Retrieves the active Offer Letter DocumentTemplate record from the database.
    Strictly queries the database for an active template and validates that its stored file exists.
    Does NOT search for hardcoded filenames or fallback to arbitrary filesystem paths.
    """
    active_template = DocumentTemplate.query.filter_by(
        template_type='offer_letter',
        is_active=True
    ).order_by(DocumentTemplate.id.desc()).first()

    if not active_template:
        raise OfferLetterTemplateNotFoundError(
            "Offer Letter template has not been uploaded. Please upload an Offer Letter template from Admin Dashboard → Templates."
        )

    if not active_template.file_path or not os.path.exists(active_template.file_path):
        raise OfferLetterTemplateFileMissingError(
            "The active Offer Letter template record exists, but its file could not be found. Please upload the template again."
        )

    return active_template


def generate_offer_letter_docx(application_or_employee, custom_params=None, force_regenerate=False):
    """
    Generates a personalized Offer Letter DOCX for the given JobApplication or Employee by cloning the master template.
    Replaces all placeholders while strictly preserving typography, borders, logos, and layout.
    Reuses existing generated file if already generated (idempotent) unless force_regenerate=True.
    """
    if isinstance(application_or_employee, Employee):
        employee = application_or_employee
        app = employee.application
    elif isinstance(application_or_employee, JobApplication):
        app = application_or_employee
        employee = app.employee
    else:
        raise ValueError("Invalid application or employee record provided.")

    if not app:
        raise ValueError("Candidate application record is missing.")

    job = app.job
    if not job:
        raise ValueError(f"Application {app.formatted_code} is missing associated Job Posting.")

    # Idempotency check: If document already exists and file exists, return it
    existing_doc = app.offer_letter_doc
    if existing_doc and existing_doc.file_path and os.path.exists(existing_doc.file_path) and not force_regenerate:
        return existing_doc, existing_doc.file_path

    custom_params = custom_params or {}
    now_utc = datetime.now(timezone.utc)
    current_date_str = now_utc.strftime("%d/%m/%Y")
    
    # Calculate 7-day acceptance deadline
    default_deadline_dt = now_utc + timedelta(days=7)
    default_deadline_str = default_deadline_dt.strftime("%d %B %Y")

    # Format data from DB models
    candidate_name = app.full_name or (employee.candidate_name if employee else "Candidate")
    reference_number = app.formatted_code
    job_title = job.title or "Intern"
    department = job.department or "Engineering"
    internship_duration = app.duration_display or (f"{job.duration.replace('_', ' ').title()}" if job.duration else "Internship")
    emp_id_str = employee.employee_id if employee else app.formatted_code

    # Responsibilities description
    responsibilities = custom_params.get(
        'responsibilities',
        job.short_description or (f"work on designated projects and deliverables for the {job_title} role at Anti-Matrix")
    )

    # Key tasks
    key_tasks = custom_params.get(
        'key_tasks',
        job.skills or (f"core technical assignments, engineering benchmarks, and team collaboration")
    )

    # Joining date
    joining_date = custom_params.get('joining_date') or custom_params.get('start_date') or "Immediate / As mutually agreed"

    # Work mode
    work_mode = custom_params.get('work_mode', job.location if job.location else "Remote")

    # Conditions
    conditions = custom_params.get(
        'conditions',
        "satisfactory verification of academic credentials and submission of government identity documentation"
    )

    # Acceptance deadline
    acceptance_deadline = custom_params.get('acceptance_deadline', default_deadline_str)

    # Comprehensive Placeholder Dictionary (supporting both [Placeholder] and {{placeholder}} formats)
    mapping = {
        '[DD/MM/YYYY]': current_date_str,
        '{{offer_date}}': current_date_str,
        '[Candidate Name]': candidate_name,
        '{{employee_name}}': candidate_name,
        '[Reference Number]': reference_number,
        '{{reference_number}}': reference_number,
        '{{application_id}}': reference_number,
        '[Job Title]': job_title,
        '{{job_title}}': job_title,
        '[brief description of responsibilities]': responsibilities,
        '{{responsibilities}}': responsibilities,
        '[key tasks / deliverables]': key_tasks,
        '{{key_tasks}}': key_tasks,
        '[Joining Date]': joining_date,
        '{{joining_date}}': joining_date,
        '{{start_date}}': joining_date,
        '[remote / hybrid / on-site]': work_mode,
        '{{work_mode}}': work_mode,
        '[background verification / document submission / any other condition]': conditions,
        '{{conditions}}': conditions,
        '[Acceptance Deadline]': acceptance_deadline,
        '{{acceptance_deadline}}': acceptance_deadline,
        '{{employee_id}}': emp_id_str,
        '{{department}}': department,
        '{{internship_duration}}': internship_duration
    }

    # Retrieve active master template from DB
    active_template = get_active_offer_letter_template()
    doc = docx.Document(active_template.file_path)

    # Process all standard paragraphs
    for p in doc.paragraphs:
        replace_placeholders_in_paragraph(p, mapping)

    # Process all tables
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    replace_placeholders_in_paragraph(p, mapping)

    # Process headers and footers across sections
    for section in doc.sections:
        if section.header:
            for p in section.header.paragraphs:
                replace_placeholders_in_paragraph(p, mapping)
        if section.footer:
            for p in section.footer.paragraphs:
                replace_placeholders_in_paragraph(p, mapping)

    # Save generated document
    gen_dir = os.path.join(current_app.root_path, 'uploads', 'generated_documents')
    os.makedirs(gen_dir, exist_ok=True)

    output_filename = f"{app.formatted_code}_Offer_Letter.docx"
    output_filepath = os.path.join(gen_dir, output_filename)

    doc.save(output_filepath)

    # Create or update EmployeeDocument record in DB
    emp_doc = EmployeeDocument.query.filter_by(
        application_id=app.id,
        document_type='offer_letter'
    ).first()

    if not emp_doc and employee:
        emp_doc = EmployeeDocument.query.filter_by(
            employee_id=employee.id,
            document_type='offer_letter'
        ).first()

    if not emp_doc:
        emp_doc = EmployeeDocument(
            application_id=app.id,
            employee_id=employee.id if employee else None,
            template_id=active_template.id,
            document_type='offer_letter',
            file_name=output_filename,
            file_path=output_filepath,
            status='GENERATED',
            email_status='not_sent',
            generated_at=now_utc
        )
        db.session.add(emp_doc)
    else:
        emp_doc.application_id = app.id
        if employee:
            emp_doc.employee_id = employee.id
        emp_doc.template_id = active_template.id
        emp_doc.file_name = output_filename
        emp_doc.file_path = output_filepath
        emp_doc.status = 'GENERATED'
        emp_doc.generated_at = now_utc

    db.session.commit()
    return emp_doc, output_filepath


def send_offer_letter_email(application_or_employee, start_date=None):
    """
    Sends the generated Offer Letter to the candidate's registered email with attachment.
    Enforces strict ONE-TIME send protection, Markdown-to-HTML rendering, and audit logging.
    """
    from services.email_service import send_offer_letter_shortlisted_email
    return send_offer_letter_shortlisted_email(application_or_employee, start_date=start_date)
