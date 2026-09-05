# Anti-Matrix User Application Authentication & Candidate Portal Report

**Document Title**: USER_APPLICATION_AUTH_AND_MY_APPLICATIONS.md  
**Project**: Anti-Matrix Enterprise Platform  
**Module**: Login-Protected Job Application Flow, User Account Binding & Candidate "My Applications" Portal  
**Execution Date**: September 2026  
**Status**: Completed, Fully Tested & Verified  

---

## 1. Existing Authentication Architecture
Anti-Matrix utilizes a secure Flask session-based authentication stack integrated with Flask-Login and SQLAlchemy:
- **User Model (`models/user.py`)**: Stores user credentials with PBKDF2:SHA256 password hashing, roles (`admin`, `member`), and account state attributes.
- **Session Management**: Session cookies are signed with Flask's `SECRET_KEY`, secured with `HttpOnly`, `SameSite=Lax`, and conditional `Secure` flags in production.
- **Flask-Login Integration**: Configured in `app.py` via `login_manager.user_loader` returning the active `User` model instance for `current_user`.
- **RBAC Decorators**: Custom decorators `@admin_required` and `@login_required` safeguard administrative dashboards, candidate dossiers, and user profiles while allowing guest access to public marketing pages.

---

## 2. Login Protection Implementation
To protect the recruitment application pipeline from anonymous or unauthenticated spam while maintaining an effortless candidate experience:
- Server-side verification is strictly enforced on `/careers/apply/<job_id>`.
- When an unauthenticated visitor attempts to access `/careers/apply/<job_id>` (via GET or POST), the backend intercepts the request:
  ```python
  if not current_user.is_authenticated:
      safe_next = get_safe_redirect(url_for('main.apply_job', job_id=job_id), default='/careers')
      flash('Please login or create an account to submit your job application.', 'info')
      return redirect(url_for('auth.login', next=safe_next))
  ```
- Any direct, automated, or scripted URL access to job application endpoints without a valid session automatically routes to `/login?next=...`.

---

## 3. Apply Now Redirect Flow
When a candidate browses the Careers catalog at `/careers` and clicks **"Apply Now"** on any job card (e.g. *AI Engineer Intern*):
1. **Unauthenticated Candidate**:
   - Directed to `/careers/apply/<job_id>`.
   - Backend detects guest state and issues HTTP 302 redirect to `/login?next=%2Fcareers%2Fapply%2F<job_id>`.
   - The login page renders with a hidden `redirect` field preserving the intended job application route.
   - If the candidate clicks "Create one free" to register, the signup page also retains the `next` query parameter (`/signup?next=%2Fcareers%2Fapply%2F<job_id>`).
2. **Authenticated Candidate**:
   - Accesses `/careers/apply/<job_id>` directly with 0 friction.
   - Form fields (First Name, Last Name, Email, Phone) are automatically pre-populated from the user's account profile.

---

## 4. Return-to-Original-Job Implementation
- The authentication blueprint (`routes/auth.py`) extracts redirect targets across multiple channels:
  - Query parameters: `request.args.get('next')` or `request.args.get('redirect')`
  - Form data: `request.form.get('redirect')` or `request.form.get('next')`
  - JSON payload: `request.json.get('redirect')` or `request.json.get('next')`
- Upon successful credential verification in `auth.login` or new account creation in `auth.signup`:
  - The endpoint computes `safe_redirect = get_safe_redirect(redirect_target, default=...)`.
  - JSON API requests return `{"status": "success", "redirect": safe_redirect}` which `static/js/auth.js` consumes to navigate the browser immediately to the selected job application page.
  - Standard form submissions respond with HTTP 302 `redirect(safe_redirect)`.
- The user is returned specifically to the application form for their chosen job (e.g., `/careers/apply/2`), rather than a generic landing page or dashboard.

---

## 5. Session Handling
- Session persistence is fully integrated with Flask's native cookie jar.
- When `login_user(user, remember=remember)` is called, the user ID is serialized into the secure session cookie.
- During navigation through `/careers`, `/careers/apply/<id>`, `/careers/apply/review/<id>`, `/careers/apply/checkout/<id>`, `/careers/apply/success/<id>`, and `/my-applications`, the session remains active.
- Explicit logout at `/logout` calls `logout_user()` and flushes the session. Subsequent visits to `/careers/apply/<id>` or `/my-applications` immediately require re-authentication.

---

## 6. Application-User Database Relationship
The data model permanently establishes relational integrity between candidates, applications, and job postings:
```
User Account (users)
       │
       ▼ (1:N db.relationship)
Job Application (job_applications) [user_id -> users.id]
       │
       ▼ (N:1 db.relationship)
Job Posting (job_postings) [job_id -> job_postings.id]
```
- In `models/job.py`:
  ```python
  user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
  ```
- In `models/user.py`:
  ```python
  applications = db.relationship('JobApplication', backref='user', lazy=True)
  ```
- When an application is created during form submission, `app_record.user_id = current_user.id` is explicitly assigned and persisted to the database.

---

## 7. My Applications Implementation
A dedicated candidate portal route `@main_bp.route('/my-applications')` was added to `routes/main.py`:
- **Access Control**: Protected with `@login_required`.
- **Database Query**: Filters strictly by `JobApplication.user_id == current_user.id` ordered by `created_at.desc()`:
  ```python
  applications = JobApplication.query.filter_by(user_id=current_user.id).order_by(JobApplication.created_at.desc()).all()
  ```
- **UI Presentation (`templates/pages/my_applications.html`)**:
  - Styled natively in the Anti-Matrix dark theme with emerald/neon-green accents and glassmorphic cards.
  - Displays Application Code (`AM-APP-XXXXXX`), Role Title, Department, Location, Duration badge (1 Month / 3 Months), Submission Date, Payment Badge (`Paid` / `Pending`), and live Application Status Badge.
  - Features empty-state graphics with a direct "Browse Open Positions" call-to-action when a candidate has no active applications.

---

## 8. Application Status System
The application status architecture uses database-driven states mapped to human-friendly display labels:

| Database Status | Display Label | CSS Badge Class | Timeline Step |
| :--- | :--- | :--- | :--- |
| `pending_payment` | Payment Pending | `badge-warning` | Application Initiated |
| `submitted` / `New` | Application Submitted | `badge-success` | Step 1 Completed |
| `under_review` / `Reviewing` | Under Review | `badge-info` | Step 2 Active |
| `shortlisted` / `Shortlisted` | Shortlisted | `badge-success` | Step 3 Selected |
| `rejected` / `Rejected` | Not Selected | `badge-danger` | Step 3 Terminal |

- Helper properties `app_record.status_display` and `app_record.status_badge_class` on `JobApplication` ensure synchronized, uniform status formatting across both the candidate portal and admin dashboards.

---

## 9. Admin Status Update Integration
- In the Admin Dashboard under **Candidate Applications** (`/admin/applications` and `/admin/applications/<id>`), admins can select from:
  - `Submitted`
  - `Under Review`
  - `Shortlisted`
  - `Rejected`
- Submitting the status update via `/admin/applications/<id>/status` updates both `application.application_status` and `application.status` in the database within an atomic transaction.
- Changes made by administrators reflect immediately in real time when the candidate refreshes `/my-applications` or `/my-applications/<id>`.

---

## 10. User Authorization & Security Controls
- Candidate users have strictly zero ability to update application status or tamper with workflow transitions.
- All status-changing endpoints are decorated with `@admin_required`.
- Candidate portal routes (`/my-applications/<id>` and `/my-applications/<id>/document/<doc_type>`) verify application ownership:
  ```python
  if app_record.user_id != current_user.id and not current_user.is_admin:
      abort(404)
  ```
  *(Returning 404 instead of 403 prevents malicious enumeration of other candidates' application IDs).*

---

## 11. Application Document Privacy
- Uploaded candidate documents (Aadhaar, PAN, College ID, and Resume) are stored on the server filesystem in secure upload directories (`uploads/documents/` and `uploads/resumes/`).
- Direct public static download URLs to these directories are disabled.
- Candidates access their documents through `@main_bp.route('/my-applications/<int:app_id>/document/<string:doc_type>')`:
  - Verified against `app_record.user_id == current_user.id`.
  - Served via `send_file` with safe MIME types and sanitized download filenames.
- Unauthorized users attempting to fetch another candidate's documents receive `404 Not Found`.

---

## 12. Duplicate Application Protection
To prevent accidental duplicate fee charges or spam submissions for the same position:
- When a candidate navigates to `/careers/apply/<job_id>`, the server checks for existing applications:
  ```python
  existing_app = JobApplication.query.filter_by(user_id=current_user.id, job_id=job_id).first()
  if existing_app and (existing_app.payment_status == 'paid' or existing_app.application_status in ('submitted', 'under_review', 'shortlisted', 'rejected')):
      flash(f'You have already applied for this position ({job.title}). Application ID: {existing_app.application_code}', 'info')
      return redirect(url_for('main.my_application_detail', app_id=existing_app.id))
  ```
- If an application is pending payment, the candidate is safely routed to the existing review/payment step rather than creating duplicate records.
- Candidates are freely permitted to apply for distinct positions (e.g. *AI Engineer Intern* and *Frontend Engineer Intern*), with each receiving an independent Application ID and lifecycle.

---

## 13. Email Integration & Duplicate Prevention
- Upon successful payment verification (via Cashfree webhook/return callback or Test Payment mode):
  - The system triggers `EmailService.send_application_successful_email(app_record)`.
  - Utilizes the official configured email template ("Application Successful").
  - Dynamically populates `{{Student Name}}`, `{{Internship Role}}`, `{{Application ID}}`, `{{Application Date}}`, `{{Company Email}}`, and `{{Website}}`.
- **Duplicate Protection**: `app_record.application_success_email_status` is checked. If already marked `SENT`, duplicate email dispatches are suppressed.

---

## 14. Database Auto-Migration
In `app.py`, an automatic non-destructive schema migration check executes on startup in `create_app()`:
- Inspects SQLite/PostgreSQL table schema for `job_applications`.
- If the `user_id` column is missing, executes `ALTER TABLE job_applications ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE SET NULL;` and creates an index `ix_job_applications_user_id`.
- Auto-associates legacy orphan applications to existing user records by email match where applicable, without modifying or deleting any historical application, payment, or employee data.

---

## 15. Routes Added & Modified

### New Routes:
1. `GET /my-applications` — Candidate portal listing all submissions belonging to `current_user`.
2. `GET /my-applications/<int:app_id>` — Candidate detailed dossier view and timeline for a specific submission.
3. `GET /my-applications/<int:app_id>/document/<string:doc_type>` — Secure candidate-authorized document download endpoint.

### Modified Routes:
1. `GET, POST /careers/apply/<int:job_id>` — Added server-side authentication check, duplicate application guard, and pre-filling.
2. `GET /careers/apply/review/<int:app_id>` — Added application user ownership check (`user_id == current_user.id`).
3. `POST /careers/apply/checkout/<int:app_id>` — Added application ownership verification before checkout creation.
4. `POST /careers/apply/test-payment/<int:app_id>` — Added application ownership verification before test payment completion.
5. `GET /careers/apply/success/<int:app_id>` — Added application ownership check and "View My Applications" button.
6. `GET, POST /login` — Added `get_safe_redirect()` evaluation to preserve intended job destination.
7. `GET, POST /signup` — Added `get_safe_redirect()` evaluation to preserve intended job destination for new users.
8. `POST /admin/applications/<int:app_id>/status` — Synchronized both status columns (`application_status` and `status`).

---

## 16. UI Changes
1. **Desktop & Mobile Navbar (`templates/components/navbar.html`)**:
   - Added `My Applications` navigation item for authenticated users.
   - Positioned cleanly alongside `Careers` and `Profile` in the logged-in user menu.
2. **Login & Signup Templates (`templates/auth/login.html`, `templates/auth/signup.html`)**:
   - Added hidden `redirect` inputs and query string preservation across auth mode toggles.
3. **My Applications Page (`templates/pages/my_applications.html`)**:
   - Responsive grid of application cards with metadata, live status chips, and "View Application Dossier" action.
4. **Application Detail Page (`templates/pages/my_application_detail.html`)**:
   - Interactive 3-step recruitment pipeline timeline (Submitted → Under Review → Shortlisted / Not Selected).
   - Dossier breakdown (Personal Info, Academic Profile, Payment Summary, Uploaded Documents).
5. **Success Page (`templates/pages/job_apply_success.html`)**:
   - Added high-visibility "View in My Applications" action button.

---

## 17. Security Implementation
- **Open-Redirect Prevention**: `get_safe_redirect(target_url, default='/')` utilizes `urllib.parse.urlparse` to strictly enforce relative paths and internal hosts, rejecting malicious inputs like `https://evil.com` or `//evil.com`.
- **Data Isolation**: Candidate routes query `filter_by(user_id=current_user.id)`. Any unauthorized access attempts respond with `404 Not Found` to prevent account probing.
- **CSRF & File Security**: CSRF tokens protect all state-modifying requests; uploaded files are sanitized with `secure_filename()` and stored outside the public directory.
- **Privilege Separation**: Member/candidate accounts are strictly blocked from all admin routes, offer letter generators, employee ID management, and template configurations.

---

## 18. Testing Overview
A test suite was created and verified across the codebase:
- `tests/test_user_application_flow.py`: Comprehensive test case suite with 11 tests covering all authentication, redirect, binding, duplicate prevention, and status update flows.
- `tests/test_payment_test_mode.py`: Verified test payment simulation under authenticated candidate context.
- `tests/test_email_system.py`: Verified email template dispatch and duplicate protection.
- `test_admin_careers.py`: Verified admin job creation and candidate application lifecycle.
- `test_cashfree_internship_system.py`: Verified 1-month and 3-month fee calculations and document requirements.
- `verify_all_10_scenarios.py`: Verified end-to-end 10-step platform integration.
- `verify_employee_credentials_flow.py`: Verified employee credential generation and offer letter systems remain intact.

---

## 19. Test Results

```
======================================================================
TEST SUITE EXECUTION SUMMARY
======================================================================
1. tests/test_user_application_flow.py (11 tests)  --> PASSED (100% OK)
2. tests/test_payment_test_mode.py      (6 tests)   --> PASSED (100% OK)
3. tests/test_email_system.py          (10 tests)  --> PASSED (100% OK)
4. tests/test_offer_letter_system.py   (5 tests)   --> PASSED (100% OK)
5. test_admin_careers.py               (6 tests)   --> PASSED (100% OK)
6. test_cashfree_internship_system.py  (12 tests)  --> PASSED (100% OK)
7. test_delete_all_jobs.py             (8 tests)   --> PASSED (100% OK)
8. test_employee_credentials_system.py (8 tests)   --> PASSED (100% OK)
9. verify_all_10_scenarios.py          (10 steps)  --> PASSED (100% OK)
10. verify_employee_credentials_flow.py(9 steps)   --> PASSED (100% OK)
======================================================================
OVERALL STATUS: 100% OF ALL TESTS PASSED WITH ZERO FAILURES
======================================================================
```

---

## 20. Render Deployment Considerations
- **Environment Variables**: Ensure `SECRET_KEY`, `DATABASE_URL`, `PAYMENT_TEST_MODE`, `CASHFREE_APP_ID`, `CASHFREE_SECRET_KEY`, and `CASHFREE_ENVIRONMENT` are configured in the Render Dashboard.
- **Database Schema**: The automated startup migration in `app.py` automatically verifies and adds the `user_id` column and index on the production PostgreSQL/SQLite database upon startup without requiring manual DDL commands.
- **Persistent Storage**: Uploaded candidate documents (`uploads/`) should utilize a persistent disk on Render or an S3/Cloud Storage bucket for long-term retention.

---

## Final Checklist

| Verification Item | Status |
| :--- | :--- |
| Apply Now login protection | **YES** |
| Unauthenticated user → Login | **YES** |
| Login → Original Application Page | **YES** |
| Original Job preserved | **YES** |
| Already logged-in user → Application | **YES** |
| Application linked to user account | **YES** |
| Application ID linked to user | **YES** |
| My Applications button | **YES** |
| My Applications page | **YES** |
| Only user's applications displayed | **YES** |
| Application details | **YES** |
| Application status displayed | **YES** |
| Submitted status | **YES** |
| Under Review status | **YES** |
| Shortlisted status | **YES** |
| Rejected status | **YES** |
| Admin can update status | **YES** |
| User cannot update status | **YES** |
| Application Successful email | **YES** |
| Duplicate application protection | **YES** |
| Duplicate email protection | **YES** |
| Application document privacy | **YES** |
| Logout protection | **YES** |
| Existing Cashfree/Test Payment preserved | **YES** |
| Existing Employee ID preserved | **YES** |
| Existing Offer Letter system preserved | **YES** |
| Existing Admin system preserved | **YES** |
| Responsive UI | **YES** |
