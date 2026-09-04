import os
import re
import html
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timezone
from flask import current_app
from models import db, JobApplication, Employee, EmployeeDocument, EmailTemplate, EmailLog


# =====================================================================
# DEFAULT OFFICIAL ANTI MATRIX EMAIL TEMPLATES
# =====================================================================

DEFAULT_APPLICATION_SUCCESSFUL_SUBJECT = "Application Successfully Submitted — {{Internship Role}} | {{Application ID}}"

DEFAULT_APPLICATION_SUCCESSFUL_BODY = """Dear {{Student Name}},

Thank you for applying for the **{{Internship Role}} Internship Opportunity at Anti Matrix**.

We are pleased to inform you that your internship application has been **successfully submitted and received**.

### Application Details

**Application ID:** {{Application ID}}
**Internship Role:** {{Internship Role}}
**Application Date:** {{Application Date}}

Your application is currently **under review by our team**. We kindly request you to allow us some time while we evaluate your application and submitted details.

If your application is shortlisted, you will receive a **confirmation/selection email** with the next steps and further instructions.

Please keep your **Application ID** for future reference when communicating with Anti Matrix regarding your application.

Thank you for your interest in building your skills and gaining practical experience with **Anti Matrix**.

Best Regards,
**Anti Matrix Team**
Internship & Career Opportunities
{{Company Email}}
{{Website}}"""

DEFAULT_OFFER_LETTER_SUBJECT = "Congratulations! You Have Been Shortlisted — {{Internship Role}} | Anti Matrix"

DEFAULT_OFFER_LETTER_BODY = """Dear {{Student Name}},

**Congratulations! 🎉**

We are pleased to inform you that you have been **successfully shortlisted for the {{Internship Role}} Internship at Anti Matrix**.

After reviewing your application and profile, our team is happy to move forward with you for this internship opportunity.

We have attached your **Internship Offer Letter** to this email. Kindly go through the offer letter carefully, sign it, and send the **signed copy back to us at {{Company Email}}**.

### Your Internship Details

**Application ID:** {{Application ID}}
**Internship Role:** {{Internship Role}}
**Internship Duration:** {{Internship Duration}}
**Start Date:** {{Start Date}}

Please make sure to return the signed offer letter at your earliest convenience so that we can complete the next steps of your internship onboarding.

We are excited to have you join **Anti Matrix** and look forward to seeing you learn, contribute, and grow with us.

Once again, **congratulations and welcome to the Anti Matrix internship program!** 🚀

Warm regards,
**Anti Matrix Team**
Internship & Career Opportunities
{{Company Email}}
{{Website}}"""


# =====================================================================
# MARKDOWN TO HTML EMAIL CONVERTER
# =====================================================================

def markdown_to_html_email(markdown_text, title="Anti Matrix Notification"):
    """
    Renders structured Markdown content into clean, responsive HTML email markup
    compatible with major email clients (Gmail, Outlook, Apple Mail, Webmail).
    Renders bold text, headings, lists, links, paragraphs, and emojis.
    """
    if not markdown_text:
        return ""

    lines = markdown_text.strip().split('\n')
    rendered_blocks = []
    
    in_list = False
    current_list_items = []

    def flush_list():
        nonlocal in_list, current_list_items, rendered_blocks
        if in_list and current_list_items:
            list_html = '<ul style="margin: 8px 0 16px 20px; padding: 0; color: #2d3748; line-height: 1.6;">'
            for item in current_list_items:
                list_html += f'<li style="margin-bottom: 6px;">{item}</li>'
            list_html += '</ul>'
            rendered_blocks.append(list_html)
            current_list_items = []
            in_list = False

    def inline_format(text):
        # Escape HTML entities first to prevent XSS
        safe_text = html.escape(text)
        # **bold**
        safe_text = re.sub(r'\*\*(.+?)\*\*', r'<strong style="color: #000000; font-weight: 700;">\1</strong>', safe_text)
        # *italic*
        safe_text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', safe_text)
        # `code`
        safe_text = re.sub(r'`(.+?)`', r'<code style="font-family: monospace; background: #f1f5f9; padding: 2px 6px; border-radius: 4px; font-size: 0.9em; color: #0f766e;">\1</code>', safe_text)
        # [link](url)
        safe_text = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2" target="_blank" style="color: #10b981; text-decoration: underline; font-weight: 600;">\1</a>', safe_text)
        return safe_text

    for raw_line in lines:
        line = raw_line.strip()

        if not line:
            flush_list()
            continue

        # ### Heading 3
        if line.startswith('### '):
            flush_list()
            heading_content = inline_format(line[4:].strip())
            rendered_blocks.append(
                f'<h3 style="font-size: 16px; font-weight: 800; color: #000000; margin: 20px 0 10px 0; padding-bottom: 6px; border-bottom: 2px solid #e2e8f0; text-transform: uppercase; letter-spacing: 0.04em;">{heading_content}</h3>'
            )
        # ## Heading 2
        elif line.startswith('## '):
            flush_list()
            heading_content = inline_format(line[3:].strip())
            rendered_blocks.append(
                f'<h2 style="font-size: 18px; font-weight: 800; color: #000000; margin: 24px 0 12px 0; padding-bottom: 6px; border-bottom: 2px solid #10b981;">{heading_content}</h2>'
            )
        # # Heading 1
        elif line.startswith('# '):
            flush_list()
            heading_content = inline_format(line[2:].strip())
            rendered_blocks.append(
                f'<h1 style="font-size: 22px; font-weight: 800; color: #000000; margin: 24px 0 14px 0;">{heading_content}</h1>'
            )
        # Bullet list item
        elif line.startswith('- ') or line.startswith('* ') or line.startswith('• '):
            in_list = True
            item_text = inline_format(line[2:].strip())
            current_list_items.append(item_text)
        # Standard paragraph
        else:
            flush_list()
            p_content = inline_format(line)
            rendered_blocks.append(
                f'<p style="margin: 0 0 14px 0; font-size: 15px; line-height: 1.65; color: #2d3748;">{p_content}</p>'
            )

    flush_list()
    body_content_html = "\n".join(rendered_blocks)

    # Full Email Wrapper HTML
    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{html.escape(title)}</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; -webkit-font-smoothing: antialiased;">
  <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #f8fafc; padding: 30px 15px;">
    <tr>
      <td align="center">
        <!-- Main Card Container -->
        <table width="100%" border="0" cellspacing="0" cellpadding="0" style="max-width: 620px; background-color: #ffffff; border-radius: 12px; overflow: hidden; border: 1px solid #e2e8f0; box-shadow: 0 10px 25px rgba(0,0,0,0.06);">
          
          <!-- Top Accent Header Banner -->
          <tr>
            <td style="background-color: #070a12; padding: 24px 32px; border-bottom: 3px solid #10b981; text-align: left;">
              <table width="100%" border="0" cellspacing="0" cellpadding="0">
                <tr>
                  <td>
                    <div style="font-size: 20px; font-weight: 900; color: #ffffff; letter-spacing: 0.06em;">
                      ANTI<span style="color: #10b981;">-</span>MATRIX
                    </div>
                    <div style="font-size: 11px; color: #94a3b8; letter-spacing: 0.12em; text-transform: uppercase; margin-top: 3px;">
                      Break The Matrix &bull; Think Different &bull; Create The Future
                    </div>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Email Body Content -->
          <tr>
            <td style="padding: 32px 32px 24px 32px; color: #2d3748;">
              {body_content_html}
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background-color: #f1f5f9; padding: 20px 32px; border-top: 1px solid #e2e8f0; text-align: center;">
              <p style="margin: 0 0 6px 0; font-size: 12px; color: #64748b; font-weight: 600;">
                Anti-Matrix &bull; Chennai, Tamil Nadu, India
              </p>
              <p style="margin: 0; font-size: 11px; color: #94a3b8;">
                This is an official automated notification from Anti-Matrix. For inquiries, contact <a href="mailto:info@antimatrix.co.in" style="color: #10b981; text-decoration: none;">info@antimatrix.co.in</a>.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""
    return full_html


# =====================================================================
# VARIABLE REPLACEMENT ENGINE
# =====================================================================

def replace_variables(template_str, variable_dict):
    """
    Replaces template variables dynamically, supporting multiple casing forms:
    e.g. {{Student Name}}, {{student_name}}, {{Student_Name}}
    """
    if not template_str:
        return ""

    result = template_str
    for key, val in variable_dict.items():
        val_str = str(val) if val is not None else ""
        
        # Handle given key
        result = result.replace(f"{{{{{key}}}}}", val_str)
        # Handle lower key
        result = result.replace(f"{{{{{key.lower()}}}}}", val_str)
        # Handle snake_case key
        snake_key = key.lower().replace(" ", "_")
        result = result.replace(f"{{{{{snake_key}}}}}", val_str)
        # Handle Title Case key
        title_key = key.title()
        result = result.replace(f"{{{{{title_key}}}}}", val_str)

    return result


# =====================================================================
# CORE EMAIL TRANSMISSION
# =====================================================================

def send_mime_email(recipient_email, subject, body_text, body_html=None, attachment_path=None, attachment_name=None):
    """
    Dispatches a multipart MIME email (HTML + Plain Text + Optional Attachment).
    Connects to SMTP if configured; otherwise logs simulated transmission in development.
    """
    smtp_server = os.environ.get('SMTP_SERVER')
    smtp_port = int(os.environ.get('SMTP_PORT', 587))
    smtp_user = os.environ.get('SMTP_USER')
    smtp_password = os.environ.get('SMTP_PASSWORD')
    sender_email = os.environ.get('SENDER_EMAIL', 'info@antimatrix.co.in')

    try:
        if smtp_server and smtp_user and smtp_password:
            msg = MIMEMultipart('mixed')
            msg['From'] = f"Anti-Matrix <{sender_email}>"
            msg['To'] = recipient_email
            msg['Subject'] = subject

            # Create alternative container for text and html
            alt_part = MIMEMultipart('alternative')
            alt_part.attach(MIMEText(body_text, 'plain', 'utf-8'))
            if body_html:
                alt_part.attach(MIMEText(body_html, 'html', 'utf-8'))
            msg.attach(alt_part)

            # Optional attachment
            if attachment_path and os.path.exists(attachment_path):
                att_name = attachment_name or os.path.basename(attachment_path)
                with open(attachment_path, 'rb') as f:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', f'attachment; filename="{att_name}"')
                    msg.attach(part)

            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)

            return True, "Email successfully sent via SMTP", None
        else:
            # Simulated Sandbox Mode
            print(f"[EMAIL SERVICE SIMULATION] Sent email to {recipient_email}")
            print(f"  Subject: {subject}")
            if attachment_path:
                print(f"  Attachment: {attachment_name or os.path.basename(attachment_path)}")
            return True, "Email successfully sent (sandbox mode)", "sim_msg_id_" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")

    except Exception as e:
        return False, str(e), None


# =====================================================================
# 1. APPLICATION SUCCESSFUL EMAIL DISPATCH
# =====================================================================

def send_application_successful_email(application):
    """
    Sends the official Application Successful confirmation email.
    Enforces strict duplicate sending protection.
    """
    if not application:
        return False, "Invalid application record."

    recipient_email = application.email
    if not recipient_email:
        return False, "Candidate does not have a registered email address."

    # Duplicate send check
    if application.application_success_email_status == 'SENT':
        return False, f"Application Successful email already sent on {application.application_success_email_sent_at}."

    job = application.job
    job_title = job.title if job else "Internship Position"
    app_date = application.created_at.strftime("%d/%m/%Y") if application.created_at else datetime.now(timezone.utc).strftime("%d/%m/%Y")
    company_email = current_app.config.get('CONTACT_EMAIL', 'info@antimatrix.co.in')
    website = "www.antimatrix.co.in"

    # Context dictionary
    variables = {
        'Student Name': application.full_name,
        'Internship Role': job_title,
        'Application ID': application.formatted_code,
        'Application Date': app_date,
        'Company Email': company_email,
        'Website': website,
        'employee_name': application.full_name,
        'job_title': job_title,
        'application_id': application.formatted_code,
        'application_date': app_date,
        'company_email': company_email,
        'website': website
    }

    # Load active email template
    tmpl = EmailTemplate.query.filter_by(template_type='application_successful').first()
    raw_subject = tmpl.subject if tmpl else DEFAULT_APPLICATION_SUCCESSFUL_SUBJECT
    raw_body = tmpl.body if tmpl else DEFAULT_APPLICATION_SUCCESSFUL_BODY

    subject = replace_variables(raw_subject, variables)
    body_text = replace_variables(raw_body, variables)
    body_html = markdown_to_html_email(body_text, title=subject)

    success, msg, provider_id = send_mime_email(
        recipient_email=recipient_email,
        subject=subject,
        body_text=body_text,
        body_html=body_html
    )

    now_utc = datetime.now(timezone.utc)
    if success:
        application.application_success_email_status = 'SENT'
        application.application_success_email_sent_at = now_utc
        log_status = 'SENT'
        error_msg = None
    else:
        application.application_success_email_status = 'FAILED'
        log_status = 'FAILED'
        error_msg = msg

    # Log to EmailLog
    email_log = EmailLog(
        recipient_email=recipient_email,
        template_type='application_successful',
        reference_id=application.formatted_code,
        subject=subject,
        body_preview=body_text[:200],
        status=log_status,
        provider_message_id=provider_id,
        error_message=error_msg,
        has_attachment=False,
        sent_at=now_utc
    )
    db.session.add(email_log)
    db.session.commit()

    return success, msg


# =====================================================================
# 2. OFFER LETTER / SHORTLISTED EMAIL DISPATCH
# =====================================================================

def send_offer_letter_shortlisted_email(employee, start_date=None):
    """
    Sends the official Offer Letter / Shortlisted email with the generated employee DOCX attached.
    Enforces strict ONE-TIME send protection.
    """
    if not employee or not employee.application:
        return False, "Invalid employee or missing application record."

    recipient_email = employee.candidate_email
    if not recipient_email:
        return False, "Candidate does not have a registered email address."

    emp_doc = employee.offer_letter_doc
    if not emp_doc or not os.path.exists(emp_doc.file_path):
        return False, "Offer Letter DOCX has not been generated yet. Please generate it first."

    # ONE-TIME SEND PROTECTION
    if emp_doc.email_status == 'sent':
        sent_time = emp_doc.sent_at.strftime('%b %d, %Y') if emp_doc.sent_at else 'earlier'
        return False, f"Offer Letter already sent on {sent_time}. Duplicate sending is prevented."

    app = employee.application
    job = employee.job
    job_title = job.title if job else "Internship Position"
    duration = app.duration_display if app and app.duration_display else (f"{job.duration.replace('_', ' ').title()}" if job and job.duration else "3 Months")
    joining_date = start_date or "Immediate / As mutually agreed"
    company_email = current_app.config.get('CONTACT_EMAIL', 'info@antimatrix.co.in')
    website = "www.antimatrix.co.in"

    variables = {
        'Student Name': employee.candidate_name,
        'Internship Role': job_title,
        'Application ID': app.formatted_code,
        'Internship Duration': duration,
        'Start Date': joining_date,
        'Company Email': company_email,
        'Website': website,
        'employee_name': employee.candidate_name,
        'employee_id': employee.employee_id,
        'job_title': job_title,
        'application_id': app.formatted_code,
        'internship_duration': duration,
        'start_date': joining_date,
        'company_email': company_email,
        'website': website
    }

    # Load active email template
    tmpl = EmailTemplate.query.filter_by(template_type='offer_letter').first()
    raw_subject = tmpl.subject if tmpl else DEFAULT_OFFER_LETTER_SUBJECT
    raw_body = tmpl.body if tmpl else DEFAULT_OFFER_LETTER_BODY

    subject = replace_variables(raw_subject, variables)
    body_text = replace_variables(raw_body, variables)
    body_html = markdown_to_html_email(body_text, title=subject)

    success, msg, provider_id = send_mime_email(
        recipient_email=recipient_email,
        subject=subject,
        body_text=body_text,
        body_html=body_html,
        attachment_path=emp_doc.file_path,
        attachment_name=emp_doc.file_name
    )

    now_utc = datetime.now(timezone.utc)
    if success:
        emp_doc.email_status = 'sent'
        emp_doc.status = 'SENT'
        emp_doc.sent_at = now_utc
        emp_doc.verified_at = now_utc
        emp_doc.email_error = None
        log_status = 'SENT'
        error_msg = None
    else:
        emp_doc.email_status = 'failed'
        emp_doc.email_error = msg
        log_status = 'FAILED'
        error_msg = msg

    # Log to EmailLog
    email_log = EmailLog(
        recipient_email=recipient_email,
        template_type='offer_letter',
        reference_id=employee.employee_id,
        subject=subject,
        body_preview=body_text[:200],
        status=log_status,
        provider_message_id=provider_id,
        error_message=error_msg,
        has_attachment=True,
        attachment_name=emp_doc.file_name,
        sent_at=now_utc
    )
    db.session.add(email_log)
    db.session.commit()

    return success, msg


# =====================================================================
# 3. PREVIEW & TEST EMAIL UTILITIES
# =====================================================================

def render_sample_email_preview(template_type):
    """
    Renders email subject and body using sample preview values.
    Does not modify any live database records.
    """
    sample_variables = {
        'Student Name': 'Rahul Kumar',
        'Internship Role': 'AI Engineer Intern',
        'Application ID': 'AM-APP-1001',
        'Application Date': '15/09/2026',
        'Internship Duration': '3 Months',
        'Start Date': '15/09/2026',
        'Company Email': 'info@antimatrix.co.in',
        'Website': 'www.antimatrix.co.in',
        'employee_name': 'Rahul Kumar',
        'employee_id': 'AM4827',
        'job_title': 'AI Engineer Intern',
        'application_id': 'AM-APP-1001',
        'internship_duration': '3 Months',
        'start_date': '15/09/2026',
        'company_email': 'info@antimatrix.co.in',
        'website': 'www.antimatrix.co.in'
    }

    tmpl = EmailTemplate.query.filter_by(template_type=template_type).first()
    if template_type == 'application_successful':
        raw_subject = tmpl.subject if tmpl else DEFAULT_APPLICATION_SUCCESSFUL_SUBJECT
        raw_body = tmpl.body if tmpl else DEFAULT_APPLICATION_SUCCESSFUL_BODY
    else:
        raw_subject = tmpl.subject if tmpl else DEFAULT_OFFER_LETTER_SUBJECT
        raw_body = tmpl.body if tmpl else DEFAULT_OFFER_LETTER_BODY

    subject = replace_variables(raw_subject, sample_variables)
    body_text = replace_variables(raw_body, sample_variables)
    body_html = markdown_to_html_email(body_text, title=subject)

    return {
        'subject': subject,
        'body_text': body_text,
        'body_html': body_html
    }


def send_test_email(template_type, recipient_email):
    """
    Sends a sample test email to the specified recipient.
    Does NOT create or modify any live application or employee records.
    """
    preview = render_sample_email_preview(template_type)
    test_subject = f"[TEST PREVIEW] {preview['subject']}"
    
    success, msg, provider_id = send_mime_email(
        recipient_email=recipient_email,
        subject=test_subject,
        body_text=preview['body_text'],
        body_html=preview['body_html']
    )

    # Log test send
    now_utc = datetime.now(timezone.utc)
    email_log = EmailLog(
        recipient_email=recipient_email,
        template_type='test',
        reference_id=f"TEST_{template_type.upper()}",
        subject=test_subject,
        body_preview=preview['body_text'][:200],
        status='SENT' if success else 'FAILED',
        provider_message_id=provider_id,
        error_message=None if success else msg,
        has_attachment=False,
        sent_at=now_utc
    )
    db.session.add(email_log)
    db.session.commit()

    return success, msg
