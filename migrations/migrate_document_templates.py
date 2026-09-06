"""
Non-destructive database migration and seeder for Document & Email Templates.
Creates document_templates, email_templates, and employee_documents tables.
Seeds default master Offer Letter template and email templates.
"""
import sys
import os
import shutil

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from models import db, DocumentTemplate, EmailTemplate, EmployeeDocument


def run_migration():
    app = create_app(os.environ.get('FLASK_CONFIG', 'development'))
    with app.app_context():
        print("[MIGRATION] Creating tables for Document & Email Templates...")
        db.create_all()

        # Ensure upload directories exist
        os.makedirs(os.path.join(app.root_path, 'uploads', 'templates'), exist_ok=True)
        os.makedirs(os.path.join(app.root_path, 'uploads', 'generated_documents'), exist_ok=True)

        # Ensure default templates for all 4 internship categories are initialized
        from services.offer_letter_service import ensure_default_templates_initialized
        ensure_default_templates_initialized()
        print("[MIGRATION] Verified / Seeded 4 job-specific Offer Letter master templates.")

        # Seed default EmailTemplate for Application Successful
        app_success_email = EmailTemplate.query.filter_by(template_type='application_successful').first()
        if not app_success_email:
            app_success_email = EmailTemplate(
                template_type='application_successful',
                name='Application Successful Confirmation',
                subject='Application Received — {{job_title}} | {{application_id}}',
                body="""Dear {{employee_name}},

Congratulations! We have received your application for the {{job_title}} position at Anti-Matrix.

Application Reference ID: {{application_id}}
Internship Duration: {{internship_duration}}

Our talent acquisition team is reviewing your profile and credentials. We will update you shortly regarding the next steps in your recruitment process.

Best Regards,
Anti-Matrix Talent Acquisition Team
https://www.antimatrix.co.in"""
            )
            db.session.add(app_success_email)
            print("[MIGRATION] Seeded Application Successful email template.")

        # Seed default EmailTemplate for Offer Letter
        offer_letter_email = EmailTemplate.query.filter_by(template_type='offer_letter').first()
        if not offer_letter_email:
            offer_letter_email = EmailTemplate(
                template_type='offer_letter',
                name='Offer Letter Delivery',
                subject='Offer Letter — {{job_title}} | {{employee_id}}',
                body="""Dear {{employee_name}},

Congratulations! We are pleased to offer you an internship opportunity with Anti-Matrix.

Employee ID: {{employee_id}}
Application ID: {{application_id}}
Position: {{job_title}}
Department: {{department}}
Internship Duration: {{internship_duration}}

Please find your official Offer Letter attached to this email. Please review the terms, conditions, and joining details carefully.

Kindly confirm your acceptance of this offer on or before the acceptance deadline mentioned in the document.

Best Regards,
Anti-Matrix Human Resources
info@antimatrix.co.in
https://www.antimatrix.co.in"""
            )
            db.session.add(offer_letter_email)
            print("[MIGRATION] Seeded Offer Letter email template.")

        db.session.commit()
        print("[MIGRATION] SUCCESS: Document & Email template migration completed successfully.")


if __name__ == '__main__':
    run_migration()
