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

        # Check / Seed DocumentTemplate for Offer Letter
        master_template_name = 'offer letter (Anti-matrix).docx'
        master_template_path = os.path.join(app.root_path, 'uploads', 'templates', master_template_name)
        
        # If not present in uploads/templates, check known download sources
        if not os.path.exists(master_template_path):
            candidates = [
                r'C:\Users\Prave\Downloads\offer letter (Anti-matrix).docx',
                r'C:\Users\Prave\Desktop\offer letter (Anti-matrix).docx',
                r'C:\Users\Prave\Desktop\ANTI-MATRIX\offer letter (Anti-matrix).docx'
            ]
            for c in candidates:
                if os.path.exists(c):
                    shutil.copy(c, master_template_path)
                    print(f"[MIGRATION] Master template copied from {c} to {master_template_path}")
                    break

        offer_template = DocumentTemplate.query.filter_by(template_type='offer_letter').first()
        if not offer_template:
            offer_template = DocumentTemplate(
                template_type='offer_letter',
                name='Anti-Matrix Master Offer Letter',
                filename=master_template_name,
                file_path=master_template_path,
                is_active=True
            )
            db.session.add(offer_template)
            print("[MIGRATION] Seeded Offer Letter document template record.")

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
