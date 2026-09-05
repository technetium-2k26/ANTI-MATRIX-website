import re
from urllib.parse import urlparse
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User

auth_bp = Blueprint('auth', __name__)

EMAIL_REGEX = re.compile(r'^\S+@\S+\.\S+$')


def get_safe_redirect(target_url, default='/'):
    """
    Validate redirect URL to prevent Open Redirect vulnerabilities.
    Only allows internal, relative application paths.
    """
    if not default:
        default = '/'
    if not target_url or not isinstance(target_url, str):
        return default
    target_url = target_url.strip()
    if not target_url.startswith('/') or target_url.startswith('//') or '\\' in target_url:
        return default
    try:
        parsed = urlparse(target_url)
        if parsed.netloc or parsed.scheme:
            return default
        return target_url
    except Exception:
        return default


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    raw_target = (
        request.args.get('next') or
        request.args.get('redirect') or
        request.form.get('redirect') or
        request.form.get('next')
    )
    redirect_target = get_safe_redirect(raw_target)
    
    if current_user.is_authenticated:
        return redirect(redirect_target)

    if request.method == 'POST':
        is_json = request.is_json
        data = request.get_json() if is_json else request.form

        email = (data.get('email') or '').strip()
        password = data.get('password') or ''
        remember = bool(data.get('remember', False))
        if isinstance(data.get('remember'), str):
            remember = data.get('remember') in ('true', '1', 'on', 'yes')

        # Check for redirect inside POST payload
        post_target = data.get('redirect') or data.get('next') or raw_target
        redirect_target = get_safe_redirect(post_target)

        errors = {}
        if not email:
            errors['email'] = 'Email is required'
        elif not EMAIL_REGEX.match(email):
            errors['email'] = 'Enter a valid email address'

        if not password:
            errors['password'] = 'Password is required'
        elif len(password) < 6:
            errors['password'] = 'Password must be at least 6 characters'

        if errors:
            if is_json:
                return jsonify({'status': 'error', 'errors': errors}), 400
            for field, err in errors.items():
                flash(err, 'error')
            return render_template('auth/login.html', errors=errors, email=email, redirect_target=redirect_target)

        # Authenticate user from database
        user = User.query.filter_by(email=email.lower()).first()
        if not user:
            # For seamless migration and demo compatibility, create the user if first time
            user = User(
                name=email.split('@')[0].capitalize(),
                email=email.lower()
            )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
        else:
            # If user exists, verify password
            if not user.check_password(password):
                errors['password'] = 'Invalid email or password'
                if is_json:
                    return jsonify({'status': 'error', 'errors': errors}), 401
                flash('Invalid email or password', 'error')
                return render_template('auth/login.html', errors=errors, email=email, redirect_target=redirect_target)

        login_user(user, remember=remember)

        if is_json:
            return jsonify({
                'status': 'success',
                'message': 'Welcome back!',
                'redirect': redirect_target,
                'user': user.to_dict()
            })

        return redirect(redirect_target)

    return render_template('auth/login.html', redirect_target=redirect_target, errors={})


@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    raw_target = (
        request.args.get('next') or
        request.args.get('redirect') or
        request.form.get('redirect') or
        request.form.get('next')
    )
    redirect_target = get_safe_redirect(raw_target)

    if current_user.is_authenticated:
        return redirect(redirect_target)

    if request.method == 'POST':
        is_json = request.is_json
        data = request.get_json() if is_json else request.form

        name = (data.get('name') or '').strip()
        email = (data.get('email') or '').strip()
        password = data.get('password') or ''
        confirm = data.get('confirm') or ''
        terms = bool(data.get('terms', False))
        if isinstance(data.get('terms'), str):
            terms = data.get('terms') in ('true', '1', 'on', 'yes')

        post_target = data.get('redirect') or data.get('next') or raw_target
        redirect_target = get_safe_redirect(post_target)

        errors = {}
        if not name:
            errors['name'] = 'Full name is required'

        if not email:
            errors['email'] = 'Email is required'
        elif not EMAIL_REGEX.match(email):
            errors['email'] = 'Enter a valid email address'

        if not password:
            errors['password'] = 'Password is required'
        elif len(password) < 8:
            errors['password'] = 'Password must be at least 8 characters'

        if not confirm:
            errors['confirm'] = 'Please confirm your password'
        elif confirm != password:
            errors['confirm'] = 'Passwords do not match'

        if not terms:
            errors['terms'] = 'You must accept the terms to continue'

        if errors:
            if is_json:
                return jsonify({'status': 'error', 'errors': errors}), 400
            for field, err in errors.items():
                flash(err, 'error')
            return render_template('auth/signup.html', errors=errors, name=name, email=email, redirect_target=redirect_target)

        # Check existing user
        user = User.query.filter_by(email=email.lower()).first()
        if user:
            user.name = name
            user.set_password(password)
        else:
            user = User(
                name=name,
                email=email.lower()
            )
            user.set_password(password)
            db.session.add(user)

        db.session.commit()
        login_user(user)

        if is_json:
            return jsonify({
                'status': 'success',
                'message': 'Account created successfully!',
                'redirect': redirect_target,
                'user': user.to_dict()
            })

        return redirect(redirect_target)

    return render_template('auth/signup.html', redirect_target=redirect_target, errors={})


@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    if current_user.is_authenticated:
        logout_user()
    return redirect(url_for('main.home'))

