import re
from urllib.parse import urlparse
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, Employee, JobApplication

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

        identifier = (data.get('email') or data.get('identifier') or '').strip()
        password = data.get('password') or ''
        remember = bool(data.get('remember', False))
        if isinstance(data.get('remember'), str):
            remember = data.get('remember') in ('true', '1', 'on', 'yes')

        # Check for redirect inside POST payload
        post_target = data.get('redirect') or data.get('next') or raw_target
        redirect_target = get_safe_redirect(post_target)

        errors = {}
        if not identifier:
            errors['email'] = 'Email or Employee ID is required'

        if not password:
            errors['password'] = 'Password is required'
        elif len(password) < 6:
            errors['password'] = 'Password must be at least 6 characters'

        if errors:
            if is_json:
                return jsonify({'status': 'error', 'errors': errors}), 400
            for field, err in errors.items():
                flash(err, 'error')
            return render_template('auth/login.html', errors=errors, email=identifier, redirect_target=redirect_target)

        authenticated_user = None

        # 1. Check if identifier is an Employee ID (e.g. AM4827)
        emp_match = Employee.query.filter(Employee.employee_id.ilike(identifier)).first()
        if emp_match:
            if emp_match.check_password(password):
                # Valid Employee ID & Password -> Sync or create User account for candidate
                cand_email = emp_match.candidate_email.lower()
                user = User.query.filter_by(email=cand_email).first()
                if not user:
                    user = User(
                        name=emp_match.candidate_name or f"Employee {emp_match.employee_id}",
                        email=cand_email,
                        role='member'
                    )
                    user.set_password(password)
                    db.session.add(user)
                    db.session.commit()
                else:
                    user.set_password(password)
                    db.session.commit()
                authenticated_user = user
            else:
                errors['password'] = 'Invalid Employee ID or password'
                if is_json:
                    return jsonify({'status': 'error', 'errors': errors}), 401
                flash('Invalid Employee ID or password', 'error')
                return render_template('auth/login.html', errors=errors, email=identifier, redirect_target=redirect_target)

        # 2. Check if identifier is an Email Address
        elif EMAIL_REGEX.match(identifier):
            user = User.query.filter_by(email=identifier.lower()).first()
            emp_by_email = Employee.query.join(JobApplication).filter(JobApplication.email.ilike(identifier.lower())).first()

            if user and user.check_password(password):
                authenticated_user = user
            elif emp_by_email and emp_by_email.check_password(password):
                if not user:
                    user = User(
                        name=emp_by_email.candidate_name or identifier.split('@')[0].capitalize(),
                        email=identifier.lower(),
                        role='member'
                    )
                user.set_password(password)
                db.session.add(user)
                db.session.commit()
                authenticated_user = user
            elif not user:
                # For seamless demo and standard user creation
                user = User(
                    name=identifier.split('@')[0].capitalize(),
                    email=identifier.lower()
                )
                user.set_password(password)
                db.session.add(user)
                db.session.commit()
                authenticated_user = user
            else:
                errors['password'] = 'Invalid email or password'
                if is_json:
                    return jsonify({'status': 'error', 'errors': errors}), 401
                flash('Invalid email or password', 'error')
                return render_template('auth/login.html', errors=errors, email=identifier, redirect_target=redirect_target)

        else:
            errors['email'] = 'Enter a valid email address or Employee ID (e.g. AM4827)'
            if is_json:
                return jsonify({'status': 'error', 'errors': errors}), 400
            flash('Enter a valid email address or Employee ID (e.g. AM4827)', 'error')
            return render_template('auth/login.html', errors=errors, email=identifier, redirect_target=redirect_target)

        login_user(authenticated_user, remember=remember)

        if is_json:
            return jsonify({
                'status': 'success',
                'message': 'Welcome back!',
                'redirect': redirect_target,
                'user': authenticated_user.to_dict()
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

