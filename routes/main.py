import re
from flask import Blueprint, render_template, request, jsonify, flash
from flask_login import current_user
from models import db, ContactInquiry

main_bp = Blueprint('main', __name__)

EMAIL_REGEX = re.compile(r'^\S+@\S+\.\S+$')

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
    return render_template('pages/careers.html')


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
