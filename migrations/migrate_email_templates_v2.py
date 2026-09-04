import sqlite3
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from models import db, EmailTemplate
from services.email_service import (
    DEFAULT_APPLICATION_SUCCESSFUL_SUBJECT,
    DEFAULT_APPLICATION_SUCCESSFUL_BODY,
    DEFAULT_OFFER_LETTER_SUBJECT,
    DEFAULT_OFFER_LETTER_BODY
)


def run_migration():
    app = create_app('development')
    with app.app_context():
        print("Starting Email Templates & EmailLog migration...")
        
        # 1. Create tables if not present (including email_logs)
        db.create_all()

        # 2. Check and add columns to job_applications if using SQLite
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        if db_uri.startswith('sqlite:///'):
            db_path = db_uri.replace('sqlite:///', '')
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Check job_applications columns
                cursor.execute("PRAGMA table_info(job_applications);")
                cols = [c[1] for c in cursor.fetchall()]
                
                if 'application_success_email_status' not in cols:
                    print("Adding 'application_success_email_status' to job_applications table...")
                    cursor.execute("ALTER TABLE job_applications ADD COLUMN application_success_email_status VARCHAR(30) DEFAULT 'PENDING' NOT NULL;")
                
                if 'application_success_email_sent_at' not in cols:
                    print("Adding 'application_success_email_sent_at' to job_applications table...")
                    cursor.execute("ALTER TABLE job_applications ADD COLUMN application_success_email_sent_at DATETIME;")

                conn.commit()
                conn.close()

        # 3. Seed / Update official Application Successful Email Template
        app_tmpl = EmailTemplate.query.filter_by(template_type='application_successful').first()
        if not app_tmpl:
            app_tmpl = EmailTemplate(
                template_type='application_successful',
                name='Application Successful',
                subject=DEFAULT_APPLICATION_SUCCESSFUL_SUBJECT,
                body=DEFAULT_APPLICATION_SUCCESSFUL_BODY
            )
            db.session.add(app_tmpl)
            print("Created Application Successful email template.")
        else:
            app_tmpl.name = 'Application Successful'
            app_tmpl.subject = DEFAULT_APPLICATION_SUCCESSFUL_SUBJECT
            app_tmpl.body = DEFAULT_APPLICATION_SUCCESSFUL_BODY
            print("Updated Application Successful email template with official wording.")

        # 4. Seed / Update official Offer Letter / Shortlisted Email Template
        offer_tmpl = EmailTemplate.query.filter_by(template_type='offer_letter').first()
        if not offer_tmpl:
            offer_tmpl = EmailTemplate(
                template_type='offer_letter',
                name='Offer Letter / Shortlisted',
                subject=DEFAULT_OFFER_LETTER_SUBJECT,
                body=DEFAULT_OFFER_LETTER_BODY
            )
            db.session.add(offer_tmpl)
            print("Created Offer Letter / Shortlisted email template.")
        else:
            offer_tmpl.name = 'Offer Letter / Shortlisted'
            offer_tmpl.subject = DEFAULT_OFFER_LETTER_SUBJECT
            offer_tmpl.body = DEFAULT_OFFER_LETTER_BODY
            print("Updated Offer Letter / Shortlisted email template with official wording.")

        db.session.commit()
        print("Email Templates migration completed successfully.")


if __name__ == '__main__':
    run_migration()
