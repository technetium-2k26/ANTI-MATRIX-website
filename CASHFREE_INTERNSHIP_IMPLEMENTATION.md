# Anti-Matrix — Cashfree Internship Application & Payment Implementation Report

## Executive Summary
This document provides a comprehensive technical overview and audit report for the **Anti-Matrix Cashfree Internship Application and Duration-Based Payment Gateway Integration**.

The complete workflow has been integrated natively into the existing Flask application, preserving all existing design elements, typography, glassmorphic dark theme, animations, admin authentication, and job management while adding strict server-enforced pricing, multi-section candidate questionnaires, sensitive document security, Cashfree checkout, server-side payment verification, and candidate dossier management.

---

## 1. Existing Architecture Analyzed
- **Framework**: Flask (Application Factory pattern in `app.py`).
- **Database**: SQLite / SQLAlchemy ORM (`models/` package).
- **Authentication**: `Flask-Login` session authentication (`models/user.py`, `routes/auth.py`).
- **Authorization**: Role-based access control with `@admin_required` decorator (`routes/admin.py`).
- **Templates**: Jinja2 (`templates/base.html`, `templates/admin/`, `templates/pages/`).
- **Styles & Scripts**: Vanilla CSS Design Tokens (`static/css/styles.css`, `static/css/admin.css`) and Vanilla JavaScript.
- **Security**: CSRF Protection (`Flask-WTF`), Werkzeug secure filename sanitization.
- **Deployment**: Render / Gunicorn (`Procfile`, `requirements.txt`).

---

## 2. Files Modified
1. `config.py` — Added `INTERNSHIP_FEES`, `INTERNSHIP_PRICING`, Cashfree configuration parameters, document upload paths.
2. `requirements.txt` — Added `requests>=2.31.0` for Cashfree API communication.
3. `.env.example` — Added Cashfree configuration variables (`CASHFREE_CLIENT_ID`, `CASHFREE_CLIENT_SECRET`, etc.).
4. `models/__init__.py` — Exported `JobPosting`, `JobApplication`, `Payment`.
5. `models/job.py` — Extended `JobPosting` and `JobApplication` models; added dedicated `Payment` model.
6. `app.py` — Initialized document upload directories (`uploads/documents/`, `uploads/resumes/`) and exempted `/payment/cashfree/webhook` from CSRF.
7. `routes/main.py` — Updated application submission logic, review route, checkout route, Cashfree return route, and Cashfree webhook.
8. `routes/admin.py` — Updated job creation/editing for duration, application filtering, candidate dossier, and secure document access route `/admin/applications/<app_id>/document/<doc_type>`.
9. `templates/pages/careers.html` — Added dynamic duration and fee badges for internship positions.
10. `templates/pages/job_apply.html` — Implemented 4-section questionnaire with validation for Aadhaar, College ID, and Resume.
11. `templates/pages/job_apply_success.html` — Updated success display with Application Code (`AM-APP-000001`), duration, and payment status.
12. `templates/admin/create_job.html` & `templates/admin/edit_job.html` — Added Internship Duration selector (1 Month / 3 Months).
13. `templates/admin/jobs.html` — Added duration column in the job management table.
14. `templates/admin/applications.html` — Added duration, fee, and payment status badge columns with advanced filters.
15. `templates/admin/application_detail.html` — Added complete candidate dossier, education metrics, Cashfree transaction details, and authenticated document download links.
16. `static/css/admin.css` — Added payment badge styling (`paid`, `pending`, `failed`).
17. `verify_all_10_scenarios.py` — Updated end-to-end verification script for Cashfree internship lifecycle.

---

## 3. Files Created
1. `services/cashfree_service.py` — Modular service class encapsulating Cashfree REST API v2023-08-01 (Order Creation, Payment Verification, Webhook Signature Verification).
2. `services/__init__.py` — Exported `CashfreeService`.
3. `migrations/migrate_cashfree_internship.py` — Non-destructive SQLite migration adding duration, document paths, and payment columns.
4. `templates/pages/job_apply_review.html` — Candidate Application Review screen before checkout.
5. `templates/pages/payment_cashfree_checkout.html` — Cashfree Web Checkout SDK v3 integration page with fallback modal/links.
6. `templates/pages/payment_failed.html` — Payment failure handler with retry mechanism.
7. `templates/pages/payment_pending.html` — Payment pending state handler with refresh/retry options.
8. `test_cashfree_internship_system.py` — Complete unit and integration test suite (8 tests).

---

## 4. Database Changes
- **`job_postings` table**:
  - `duration` (`VARCHAR(32)`, Nullable) — Stores `1_month` or `3_months` (or `NULL` for standard full-time/part-time jobs).
- **`job_applications` table**:
  - `application_code` (`VARCHAR(32)`, Unique) — Human-readable tracking ID (`AM-APP-000001`).
  - `year_of_study` (`VARCHAR(64)`) — Year of study (e.g. 1st Year, 2nd Year, 3rd Year, Final Year).
  - `current_cgpa` (`VARCHAR(16)`) — Academic CGPA / Percentage.
  - `aadhaar_filename` (`VARCHAR(256)`) — Secure sanitized basename.
  - `aadhaar_path` (`VARCHAR(512)`) — Protected absolute path on disk.
  - `college_id_filename` (`VARCHAR(256)`) — Secure sanitized basename.
  - `college_id_path` (`VARCHAR(512)`) — Protected absolute path on disk.
  - `duration` (`VARCHAR(32)`) — Duration applied for (`1_month` / `3_months`).
  - `application_fee` (`INTEGER`) — Server-calculated fee in INR (199 or 399).
  - `payment_status` (`VARCHAR(32)`) — `pending`, `processing`, `paid`, `failed`, `cancelled`, or `exempt`.
  - `application_status` (`VARCHAR(32)`) — `pending_payment`, `submitted`, `reviewed`, `shortlisted`, `rejected`, `hired`.
- **`payments` table (New)**:
  - `id` (`INTEGER PRIMARY KEY AUTOINCREMENT`)
  - `application_id` (`INTEGER NOT NULL`, Foreign Key to `job_applications.id`)
  - `cashfree_order_id` (`VARCHAR(128) UNIQUE NOT NULL`)
  - `cashfree_payment_session_id` (`VARCHAR(256)`)
  - `amount` (`FLOAT NOT NULL`)
  - `currency` (`VARCHAR(8) DEFAULT 'INR'`)
  - `payment_status` (`VARCHAR(32) DEFAULT 'pending'`)
  - `gateway` (`VARCHAR(32) DEFAULT 'cashfree'`)
  - `cf_payment_id` (`VARCHAR(128)`)
  - `gateway_response` (`TEXT`)
  - `created_at` (`DATETIME`), `updated_at` (`DATETIME`)

---

## 5. Database Migration
- Safe, non-destructive migration script implemented in `migrations/migrate_cashfree_internship.py`.
- Evaluates existing SQLite `PRAGMA table_info` before applying `ALTER TABLE ... ADD COLUMN` statements.
- Preserves all existing job postings, admin accounts, and applications.
- Model defaults ensure backwards compatibility for pre-existing non-internship records.

---

## 6. New Routes

| Route | Method | Access | Description |
|---|---|---|---|
| `/careers/apply/review/<int:app_id>` | `GET` | Public / Candidate | Displays candidate application review summary before initiating payment. |
| `/careers/apply/checkout/<int:app_id>` | `POST` | Public / Candidate | Server calculates fee, generates Cashfree order, and redirects to checkout. |
| `/payment/cashfree/checkout/<int:payment_id>` | `GET` | Public / Candidate | Renders official Cashfree JS SDK v3 checkout interface. |
| `/payment/cashfree/return` | `GET`, `POST` | Public / Return Callback | Verifies payment server-side via Cashfree Orders API and updates status. |
| `/payment/cashfree/webhook` | `POST` | Cashfree Gateway | Idempotent HMAC-SHA256 signature verified webhook listener. |
| `/admin/applications/<int:app_id>/document/<string:doc_type>` | `GET` | Admin Only | Protected file stream for sensitive documents (`aadhaar`, `college_id`, `resume`). |

---

## 7. New Models & Fields
- `JobPosting`: Added properties `duration_display`, `fee_inr`, `fee_display`, `is_internship`.
- `JobApplication`: Added properties `formatted_code`, `payment_badge_class`, `is_paid`.
- `Payment`: Full transaction ledger tracking Cashfree order IDs, session tokens, verification payloads, and payment status lifecycle.

---

## 8. Cashfree Integration Method
- Direct official Cashfree REST API (API Version: `2023-08-01`).
- Cashfree Web Checkout SDK v3 (`https://sdk.cashfree.com/js/v3/cashfree.js`).
- Session-based checkout: The backend creates the order with `x-client-id`, `x-client-secret`, and receives `payment_session_id`, which the frontend SDK consumes to launch seamless checkout.

---

## 9. Cashfree Environment Variables
Defined in `.env.example` and loaded via `config.py`:
```env
CASHFREE_ENVIRONMENT=sandbox
CASHFREE_CLIENT_ID=your_cashfree_app_id
CASHFREE_CLIENT_SECRET=your_cashfree_secret_key
CASHFREE_API_VERSION=2023-08-01
CASHFREE_RETURN_URL=https://your-domain.com/payment/cashfree/return
CASHFREE_WEBHOOK_URL=https://your-domain.com/payment/cashfree/webhook
```

---

## 10. Sandbox Configuration
- Host: `https://sandbox.cashfree.com/pg`
- Set `CASHFREE_ENVIRONMENT=sandbox` in development/staging.
- JS SDK initializes in `{ mode: "sandbox" }`.

---

## 11. Production Configuration
- Host: `https://api.cashfree.com/pg`
- Set `CASHFREE_ENVIRONMENT=production`.
- JS SDK initializes in `{ mode: "production" }`.
- Credentials must be supplied strictly through environment variables (Render Environment Variables dashboard).

---

## 12. Internship Pricing
Enforced centrally in `config.py`:
```python
INTERNSHIP_FEES = {
    '1_month': 199,
    '3_months': 399
}
```

---

## 13. Server-Side Price Validation
- The backend queries `JobPosting.query.get(job_id)`.
- If `duration == '3_months'`, fee is strictly computed as `399`.
- If `duration == '1_month'`, fee is strictly computed as `199`.
- Client-submitted amounts (via hidden fields, tampering, query parameters) are ignored.
- Non-internship jobs are automatically assigned `fee = 0` and marked `payment_status='exempt'`.

---

## 14. Cashfree Order Creation
- Route: `POST /careers/apply/checkout/<app_id>`
- Backend constructs payload:
  ```json
  {
    "order_id": "AM-APP-000001-PAY-1788527607-FB986",
    "order_amount": 399.00,
    "order_currency": "INR",
    "customer_details": {
      "customer_id": "CUST-AM-000001",
      "customer_email": "candidate@example.com",
      "customer_phone": "9876543210",
      "customer_name": "Candidate Name"
    },
    "order_meta": {
      "return_url": "https://domain/payment/cashfree/return?order_id={order_id}",
      "notify_url": "https://domain/payment/cashfree/webhook"
    }
  }
  ```
- Sensitive candidate documents (Aadhaar, College ID, Resume) are **never** transmitted to Cashfree.

---

## 15. Payment Session
- Cashfree responds with `payment_session_id`.
- Stored securely in `Payment.cashfree_payment_session_id`.
- Passed to checkout view template for SDK consumption.

---

## 16. Cashfree Checkout
- Loaded via Cashfree official JS SDK v3 (`sdk.cashfree.com/js/v3/cashfree.js`).
- Initializes checkout instance:
  ```javascript
  const cashfree = Cashfree({ mode: "sandbox" });
  cashfree.checkout({
    paymentSessionId: "session_...",
    redirectTarget: "_self"
  });
  ```
- Client-side secret keys are never exposed.

---

## 17. Return URL
- Route: `GET/POST /payment/cashfree/return`
- Candidate returns with `order_id`.
- Backend does **NOT** assume payment succeeded; it queries Cashfree's `/pg/orders/{order_id}` and `/pg/orders/{order_id}/payments` to verify transaction truth.

---

## 18. Webhook
- Route: `POST /payment/cashfree/webhook`
- CSRF-exempted in `app.py`.
- Receives Cashfree asynchronous payment events (`PAYMENT_SUCCESS_WEBHOOK`, `PAYMENT_FAILED_WEBHOOK`).

---

## 19. Webhook Signature Verification
- Implemented in `CashfreeService.verify_webhook_signature`.
- Uses `x-webhook-signature` and `x-webhook-timestamp` headers.
- Computes HMAC-SHA256 of `timestamp + raw_body` against `CASHFREE_CLIENT_SECRET` and performs `hmac.compare_digest`.

---

## 20. Server-Side Payment Verification
- Validates that Cashfree order amount matches database fee (`payment.amount == cf_order.order_amount`).
- Checks Cashfree status is `PAID`.
- Executes atomic transaction:
  - `payment.payment_status = 'paid'`
  - `application.payment_status = 'paid'`
  - `application.application_status = 'submitted'`
  - `application.status = 'New'`

---

## 21. Payment Retry
- If payment fails or is cancelled, application remains in `pending_payment` state.
- Candidate is directed to `/payment/failed/<payment_id>` with a **"Try Payment Again"** action.
- Retrying creates a new unique Cashfree Order (`AM-APP-000001-PAY-002`) linked to the **same** application, preventing duplicate application clutter.

---

## 22. Duplicate Application Protection
- Query checks if candidate email + job ID has `payment_status == 'paid'` or `application_status == 'submitted'`.
- If already submitted, flashes warning: *"You have already applied for this position."* and blocks duplicate payments.
- If candidate has an unpaid draft (`pending_payment`), the system updates the draft and allows continuing to payment.

---

## 23. Secure Document Handling
- Uploaded files are stored in `uploads/documents/` (Aadhaar & College ID) and `uploads/resumes/` (Resume).
- Filenames sanitized with `secure_filename` and prefixed with UUIDs + job IDs.
- Path traversal (`../`), null bytes, and dangerous extensions (`.exe`, `.sh`, `.php`, `.js`, `.bat`) rejected.
- Documents are **not** accessible via public static URLs.
- Served strictly via `@admin_required` route `/admin/applications/<app_id>/document/<doc_type>` using `send_from_directory`.

---

## 24. Admin Dashboard Changes
- **Job Creation / Edit**: Added `Internship Duration` field (1 Month / 3 Months).
- **Job Table**: Added `Duration` column.
- **Applications Table**: Added `Duration`, `Application Fee`, and `Payment Status` badge (`Paid`, `Pending`, `Failed`). Added filters for Duration and Payment Status.
- **Application Dossier**: Displays Candidate Profile, Education & CGPA, Internship Details, Cashfree Order ID, Payment Amount, Payment Reference, and Secure Document Access links.

---

## 25. Tests Performed
1. `test_01_create_3month_internship_and_pricing`: Admin creates 3-month internship, validates ₹399 display on Careers.
2. `test_02_create_1month_internship_and_pricing`: Admin creates 1-month internship, validates ₹199 display.
3. `test_03_non_internship_normal_job`: Full-time job creation and submission with zero fee and payment exemption.
4. `test_04_internship_application_validation_and_review`: Multi-section validation, document storage, review redirection.
5. `test_05_price_tampering_defense`: Tampered client fee rejected; server enforces ₹399.
6. `test_06_cashfree_return_verification_and_success`: Verified return callback, status transitions, success page display.
7. `test_07_duplicate_application_protection`: Paid candidate blocked from duplicate submission.
8. `test_08_admin_application_dossier_and_secure_documents`: Admin dossier viewing, duration filters, authenticated document access, and 403 member rejection.
9. `test_delete_all_jobs.py`: Verified cascade deletion safety for payments and applications.
10. `verify_all_10_scenarios.py`: Full 10-step end-to-end integration test.

---

## 26. Test Results
- **Unit Test Discovery**: `Ran 18 tests in 10.968s — OK (0 failures, 0 errors)`
- **10-Step End-to-End Scenarios**: `100% Passed (10/10)`

---

## 27. Deployment Requirements
- No new system dependencies required (pure Python `requests` library added to `requirements.txt`).
- Compatible with Render Web Services running Gunicorn (`Procfile: web: gunicorn run:app`).
- Set environment variables in Render Dashboard:
  - `CASHFREE_CLIENT_ID`
  - `CASHFREE_CLIENT_SECRET`
  - `CASHFREE_ENVIRONMENT=production`
  - `CASHFREE_API_VERSION=2023-08-01`
  - `CASHFREE_RETURN_URL=https://<your-render-app>.onrender.com/payment/cashfree/return`
  - `CASHFREE_WEBHOOK_URL=https://<your-render-app>.onrender.com/payment/cashfree/webhook`

---

## 28. Known Limitations
- Email confirmation/notification dispatch is omitted in this phase as per strict project scope.
- In local SQLite development, concurrent write locks under extreme concurrency should be upgraded to PostgreSQL on production Render.

---

## Compliance Checklist

| Item | Status |
|---|---|
| Cashfree integration | **YES** |
| 1 Month ₹199 | **YES** |
| 3 Months ₹399 | **YES** |
| Dynamic duration | **YES** |
| Dynamic pricing | **YES** |
| Server-side price validation | **YES** |
| Cashfree order creation | **YES** |
| Cashfree checkout | **YES** |
| Payment verification | **YES** |
| Webhook | **YES** |
| Webhook signature verification | **YES** |
| Payment retry | **YES** |
| Duplicate protection | **YES** |
| Application submission | **YES** |
| Admin application display | **YES** |
| Secure document access | **YES** |
| Mobile responsive | **YES** |
| Database migration | **YES** |
| Render deployment compatible | **YES** |
| Email | **NOT IMPLEMENTED — INTENTIONALLY** |
